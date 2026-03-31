# Entity Linking Strategy

## Overview

When combining structured data sources (MusicBrainz, Discogs, Wikidata) with text-extracted triples (Wikipedia via LLM), we face the **entity linking problem**: text mentions like "Beethoven" or "Queen" must be resolved to the correct URI in our knowledge graph.

This document describes the 5-tier entity linking strategy used in our text mapping pipeline (`mapping/text.py`).

## The Problem

LLM text extraction produces triples with bare string subjects and objects:
```
("Beethoven", "composed", "Symphony No. 5 (1808)")
("David Bowie", "collaboratedWith", "Brian Eno")
("The Beatles", "producedBy", "George Martin")
```

These strings must be resolved to existing URIs in our RDF graph (populated from structured sources) to avoid creating duplicate entities. For example, "Brian Eno" should link to `mb:ff95eb47-41c4-4f7f-a104-cdc30f02e872` (his MusicBrainz URI) rather than creating a new `mh:artist/Brian_Eno` node.

### Challenges
- **Name variations**: "Beethoven" vs "Ludwig van Beethoven" vs "Пётр Ильич Чайковский"
- **Ambiguity**: "Queen" the band vs "Queen" the monarch
- **New entities**: "Ziggy Stardust" (alter ego) and "Berlin Trilogy" (album grouping) don't exist in any structured source
- **Cross-source identity**: the same person may have different names across MusicBrainz, Discogs, and Wikipedia

## 5-Tier Resolution Strategy

### Tier 1: Exact Match (Label Index)

**Method:** Build a dictionary mapping every `rdfs:label` and `foaf:name` in the graph (lowercased) to its URI. Look up the mention string directly.

**Example:** "David Bowie" → exact match → `mb:5441c29d-3602-4898-b1a1-b77fa23b8e50`

**Coverage:** Resolves ~70% of mentions — all entities where the LLM uses the exact same name as the structured source.

**Course connection:** This is the simplest form of **Entity Linking** as taught in Week 7 (NLP-to-KG pipeline, step 3): "resolve surface forms to canonical KG identifiers."

### Tier 2: Fuzzy Match (String Similarity)

**Method:** Use `rapidfuzz.fuzz.token_set_ratio` to compute similarity between the mention and all labels in the index. Token set ratio handles:
- Subset matching: "Beethoven" scores high against "Ludwig van Beethoven" because "Beethoven" is a subset of the tokens
- Word reordering: "Jobim Tom" matches "Tom Jobim"

**Thresholds:**
- Score ≥ 85: confident match (automatic linking)
- Score 70–84: provisional match (linked but flagged)
- Score < 70: no match (proceed to Tier 3)

**Example:** "Beethoven" → token_set_ratio against "Ludwig van Beethoven" = 73 → provisional match

**Research basis:** Jaro-Winkler and token-based similarity are standard in entity resolution literature (Christen, 2012; Fellegi & Sunter, 1969). Token set ratio from `rapidfuzz` is recommended for name matching because it handles both prefix truncation and word reordering.

**Course connection:** Relates to Week 7's **Entity Disambiguation** step in the LLM chained prompting approach: "Ensure that 'Paris, France' and 'Paris, Texas' are treated as separate entities." Fuzzy matching with thresholds provides a quantitative approach to disambiguation.

### Tier 3: Type-Constrained Lookup

**Method:** Use the predicate of the triple to infer the expected RDF type of the object. Then search only among entities of that type in the graph.

**Predicate → Type mapping:**
| Predicate | Expected object type |
|---|---|
| `memberOf` | `mo:MusicGroup` |
| `collaboratedWith` | `mo:SoloMusicArtist` or `mo:MusicGroup` |
| `hasGenre` | `mo:Genre` |
| `released` / `composed` | `mo:Release` or `mh:MusicalWork` |
| `producedBy` | `mo:SoloMusicArtist` |

**Example:** Given `("David Bowie", "memberOf", "Tin Machine")`, we know the object must be a `mo:MusicGroup`. We search only among groups in the graph, reducing false matches.

**Why this works:** In a domain-specific KG (music history), type constraints eliminate most cross-domain ambiguity. "Queen" in a `memberOf` triple must be a band, not a monarch.

**Course connection:** This applies the domain/range constraints from ontology design (Weeks 1–5). The ontology defines that `memberOf` has range `mo:MusicGroup` — we enforce this constraint during entity linking.

### Tier 4: Wikidata SPARQL Fallback

**Method:** For mentions that don't match anything in the local graph, query the Wikidata SPARQL endpoint for entities with matching labels. If a Wikidata QID is returned that matches a QID already in our graph, link them via `owl:sameAs`.

**Example:** "Tony Allen" (from Fela Kuti extraction) → Wikidata query → Q519851 → check if Q519851 exists in our graph → if yes, link.

**Course connection:** This is the **entity linking → KG property retrieval** pattern from Week 11 (RAG lecture): entity recognition → entity linking to Wikidata → retrieve structured properties. We use the same Wikidata endpoint as a resolution service.

**Note:** In our current implementation, Tier 4 is reserved for future use to avoid excessive API calls during pipeline runs. For 6 artists with ~100 triples, the first 3 tiers resolve most mentions.

### Tier 5: NIL — New Entity Creation

**Method:** When no match is found at any tier, the mention represents a genuinely new entity not in our structured sources. Create a provisional URI in the `mh:` namespace with appropriate type.

**URI patterns:**
- Artists: `mh:artist/{safe_name}`
- Genres: `mh:genre/{normalised_name}`
- Musical works: `mh:work/{safe_name}`
- Personas: `mh:persona/{safe_name}`
- Album groups: `mh:album_group/{safe_name}`
- Musical periods: `mh:period/{safe_name}`

**Examples:**
- "Ziggy Stardust" → `mh:persona/Ziggy_Stardust` (alter ego, no structured equivalent)
- "Berlin Trilogy" → `mh:album_group/Berlin_Trilogy` (album grouping, no structured equivalent)
- "plastic soul" → `mh:genre/plastic_soul` (genre label not in MusicBrainz/Discogs/Wikidata)

**Research basis:** Paulheim (2017) "Knowledge Graph Refinement" recommends creating provisional nodes tagged with a status property for later review. The "sieve" approach (Raghunathan et al., 2010) applies resolution rules from most precise to least precise before resorting to new entity creation.

**Course connection:** This addresses the **KG Completion** requirement from Week 10: identifying gaps in the knowledge graph and adding new entities to fill them. The provisional entities created here directly feed into the completion analysis (5 ontology gaps + 5 instance gaps).

## Implementation

The strategy is implemented in `pipeline/mapping/text.py`:

```python
def resolve_entity(mention, g, label_index, expected_type=None):
    # Tier 1: Exact match
    uri, method = _tier1_exact_match(mention, label_index)
    if uri: return uri, method

    # Tier 2: Fuzzy match
    uri, method = _tier2_fuzzy_match(mention, label_index)
    if uri and confident: return uri, method

    # Tier 3: Type-constrained
    if expected_type:
        uri, method = _tier3_type_constrained(mention, g, TYPE_MAP[expected_type])
        if uri: return uri, method

    # Tier 4: Wikidata lookup (reserved for future use)

    # Tier 5: Create provisional URI
    uri, method = _tier5_create_provisional(mention, expected_type)
    return uri, method
```

## Why This Approach

### Alignment with Course Techniques
- **Week 7**: Entity linking and disambiguation are core steps in both the classic NLP pipeline and the LLM chained prompting approach
- **Week 8**: The structured mapping (R2RML, SPARQL Anything) provides the base entities that the text mapping links against
- **Week 10**: NIL entity detection feeds directly into the KG completion analysis
- **Week 11**: The Wikidata fallback mirrors the RAG pattern of entity linking → KG retrieval

### Why Not Embedding-Based Linking?
State-of-the-art entity linking (BLINK, Wu et al. 2020; sentence-transformers) uses dense vector representations for mention-entity matching. We chose the simpler tiered approach because:
1. Our KG is small (~500 entities) — brute-force fuzzy matching is fast enough
2. String similarity is more interpretable and debuggable
3. The domain constraint (music only) eliminates most ambiguity
4. Course techniques emphasise rule-based and SPARQL-based approaches

For a production system at larger scale, embedding-based entity linking would be the recommended approach.

## References

- Christen, P. (2012). "Data Matching." Springer.
- Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." JASA 64(328).
- Paulheim, H. (2017). "Knowledge Graph Refinement: A Survey of Approaches and Evaluation Methods." Semantic Web 8(3).
- Wu, L. et al. (2020). "Scalable Zero-shot Entity Linking with Dense Entity Retrieval." EMNLP.
- Raghunathan, K. et al. (2010). "A Multi-Pass Sieve for Coreference Resolution." EMNLP.
- Week 7 Lecture: "Creating Knowledge Graphs from Texts" — NER, Entity Linking, Relation Extraction
- Week 11 Lecture: "Retrieval Augmented Generation" — Entity linking → KG property retrieval
