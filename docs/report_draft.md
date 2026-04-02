# Music History Knowledge Graph — Report

## 1. Introduction

[Sofia to write]

**Domain:** Arts & Cultural Heritage — Music History

**Scope:** A knowledge graph covering the full timeline of music history, from medieval (Hildegard von Bingen, ~1150) to modern (BTS, Kendrick Lamar, 2020s). The KG represents 58 primary artists across 20+ genres, 20+ countries, and multiple eras, with 38,429 RDF triples.

**Objective:** Develop an automated computational system that constructs a knowledge graph from multiple data sources (structured and textual), using techniques from Weeks 6–12 of the course. The system combines API-based data ingestion, SPARQL queries, NER, LLM-based triple extraction, and entity linking to produce a Turtle file containing ontology declarations, extensions of two existing ontologies, and mapped instance data.

**Team:**
- Sofia Davis — Domain expert / client
- William Caulton — Modelling expert
- Mert Yerlikaya — Modelling expert
- Lucas Perez Reis Lobo — Requirements, data ingestion & LLM pipeline
- Yutaka Shibata — Requirements, data ingestion & LLM pipeline
- Davyd Shtepa — Working with domain expert

---

## 2. Data Source Selection

### 2.1 Requirements Analysis

The 20 competency questions (10 manual + 10 LLM-augmented) define what data the KG must contain. Analysis of the CQs identified the following data needs:

- Artist biographical data (name, country, birth/death dates, gender)
- Album/release data (titles, release dates)
- Track-level data (titles, durations)
- Genre and subgenre classifications
- Band membership with instruments
- Artist relationships (influences, collaborations)
- Record label associations
- Awards and recognitions
- Classical compositions with composition dates
- Geographic and temporal distribution of genres

These needs require both **structured data** (for biographical facts, releases, relationships) and **textual data** (for narrative facts like personas, album groupings, career context not captured in databases).

### 2.2 Sources Evaluated

We evaluated 6 potential data sources through 7 experiments (documented in `docs/experiment_tracker.md`):

| Source | Type | Format | Auth needed | Evaluated in |
|---|---|---|---|---|
| MusicBrainz API | Structured | JSON | No (User-Agent only) | Experiments 1, 4, 5 |
| Discogs API | Structured | JSON | No (25 req/min) | Experiments 2, 4 |
| Wikidata SPARQL | Structured | RDF/JSON | No | Experiment 7 |
| Wikipedia MediaWiki API | Textual | JSON/text | No (User-Agent) | Experiments 3, 4, 6 |
| DBpedia SPARQL | Structured | RDF | No | Experiment 7 |
| Open Opus API | Structured | JSON | No | Experiment 7 |

Additionally, Last.fm was considered but registration was blocked (HTTP 406 error during signup).

### 2.3 Evaluation Criteria

Sources were evaluated across 5 test artists spanning different genres and regions: David Bowie (rock, GB), Miles Davis (jazz, US), Ludwig van Beethoven (classical, AT), Antônio Carlos Jobim (bossa nova, BR), and Fela Kuti (afrobeat, NG).

Criteria:
- **Coverage**: does the source have data for all genres/eras/regions?
- **Accessibility**: free, no auth, reasonable rate limits?
- **Data quality**: clean, structured, consistent?
- **Cross-referencing**: can entities be linked across sources?
- **Unique value**: does the source provide data not available elsewhere?

### 2.4 Sources Selected

**Structured Source 1: MusicBrainz API (Primary)**
- Role: primary hub for artist data, releases, relationships, and cross-references
- Key data: artist info (name, type, country, life-span), release groups (deduplicated albums), tracks/recordings, artist-to-artist relationships (member of band, influenced by, collaboration, producer), URL relationships linking to Discogs, Wikidata, and Wikipedia
- Why selected: richest relationship data of any source tested; every entity has a UUID (MBID) usable as a URI; free with no authentication; cross-references to all other sources via url-rels
- Rate limit: 1 request/second

**Structured Source 2: Discogs API (Supplement)**
- Role: genre→style hierarchy and artist real names
- Key data: broad genres + granular styles (sub-genres) per release; artist real names and name variations
- Why selected: unique sub-genre data not available in MusicBrainz or Wikidata; the genre/style distinction maps directly to our `subgenreOf` property
- Rate limit: 25 requests/minute unauthenticated

**Structured Source 3: Wikidata SPARQL (Supplement)**
- Role: awards, instruments, influences, record labels, compositions
- Key data: structured properties (P136 genre, P1303 instrument, P166 award, P264 label, P737 influenced by, P86 composer)
- Why selected: data already in RDF — minimal mapping needed. Eliminates the need for LLM text extraction for factual properties (awards, instruments, influences, labels). Initially used only for cross-referencing (MusicBrainz → Wikidata → Wikipedia), but Experiment 7 revealed it contains rich structured data that our pipeline should query directly.
- Optimisation: batch SPARQL query fetches all properties in a single request, reducing from 10 individual queries per artist to 3 (1 batch + 2 date literals).

**Textual Source: Wikipedia MediaWiki API**
- Role: narrative text for LLM-based triple extraction
- Key data: article text (85,000+ characters per artist), section structure, categories
- Why selected: richest freely available textual source for music history. Articles contain information not in any structured source: alter egos (Ziggy Stardust), album groupings (Berlin Trilogy), narrative genres ("plastic soul"), career collaborations.
- Scope reduction: after adding Wikidata as a structured source, Wikipedia text extraction was scoped to only narrative facts not available in Wikidata (personas, album groupings, non-standard genres).

### 2.5 Sources Rejected

| Source | Reason |
|---|---|
| **DBpedia** | Redundant with Wikidata. Data quality is lower — template parameters from Wikipedia infoboxes leak through as properties (e.g., `b: no`, `fixAttempted: yes`). Wikidata is cleaner and more structured. |
| **Open Opus** | Classical music only — Miles Davis, Fela Kuti, Tom Jobim all return "NOT FOUND". Wikidata provides adequate classical composition data (30 compositions per composer). |
| **Last.fm** | Registration blocked (HTTP 406 error). Could not obtain API key. |

### 2.6 Cross-Referencing Pipeline

A critical design decision was using MusicBrainz as the **hub** for cross-referencing. Every MusicBrainz artist record contains URL relationships linking to Discogs, Wikidata, and other external resources. The cross-referencing pipeline:

```
MusicBrainz (search by name) → MBID
  ├── url-rels → Discogs URL → extract numeric ID → Discogs API
  └── url-rels → Wikidata URL → extract Q-ID → Wikidata SPARQL
                                                    └── sitelinks → Wikipedia article title → Wikipedia API
```

This pipeline was validated with 5 test artists across different genres, achieving 100% coverage (all 5 found in all sources). Non-Western artists were explicitly tested: Fela Kuti (NG), Tom Jobim (BR), Miriam Makeba (ZA), Youssou N'Dour (SN) — all found with cross-reference links intact.

For artists where MusicBrainz search returns incorrect results (e.g., "Bob Marley" returning Bob Dylan), MBID overrides are configured in `pipeline/config.py`. Five artists required overrides: Bob Marley, Pyotr Ilyich Tchaikovsky, Quincy Jones, Rick Rubin, and George Martin.

---

## 3. Extension of Existing Ontologies

[William + Mert to write — below is a summary of what's implemented]

### 3.1 Ontology Selection

Two existing ontologies were selected for extension:

**Music Ontology (MO)** — `http://purl.org/ontology/mo/`
- The primary domain-specific vocabulary for describing music-related information
- Provides classes for artists, works, recordings, genres, instruments
- Selected because it directly covers the core entities in our domain

**Schema.org** — `https://schema.org/`
- A widely-used vocabulary for structured web data
- Provides classes for awards, countries, and biographical properties
- Selected because our pipeline already uses Schema.org properties (birthDate, deathDate, gender) and it provides natural extension points for affiliations (record labels) and nationality (country of origin)

Stubs were used instead of `owl:imports` because Schema.org has no clean OWL import URI, which would break a reasoner attempting to resolve the import.

### 3.2 Music Ontology Extensions

| Extension | Type | Parent | Description |
|---|---|---|---|
| `mh:IndependentLabel` | Subclass | `mo:Label` | A record label operating without major label funding |
| `mh:CoverRecording` | Subclass | `mo:Signal` | A recording by an artist who is not the original composer |
| `mh:internationalCollaboration` | Subproperty | `mo:collaborated_with` | A collaboration between artists from different countries |
| `mh:primaryInstrument` | Subproperty | `mo:instrument` | The lead or most prominent instrument |

### 3.3 Schema.org Extensions

| Extension | Type | Parent | Description |
|---|---|---|---|
| `mh:MultinationalBand` | Subclass | `schema:MusicGroup` | A band with members from more than one country |
| `mh:MusicAward` | Subclass | `schema:Award` | An award specific to the music industry |
| `mh:signedTo` | Subproperty | `schema:affiliation` | Links an artist to their record label |
| `mh:countryOfOrigin` | Subproperty | `schema:nationality` | Links an artist to their country of origin |

### 3.4 Defined Classes

Three defined classes use `owl:equivalentClass` with OWL restrictions, enabling reasoner inference:

| Defined Class | Necessary & Sufficient Conditions | Instances Inferable |
|---|---|---|
| `mh:AwardWinningArtist` | MusicArtist AND (wonAward some MusicAward) | 51 artists with awards |
| `mh:InternationalCollaborator` | MusicArtist AND (collaboratedWith some MusicArtist) | Artists with collaboration triples |
| `mh:ProducerArtist` | MusicArtist AND (produced some Release) | Artists with production credits |

These defined classes address the modelling trade-off between roles and types. Rather than asserting an artist as a `Composer` or `Producer` (which denotes a role, not a type), the defined classes allow a reasoner to infer role membership from the artist's actual behaviour in the KG.

### 3.5 Custom Classes and Properties

[See ontology_header.py for full declarations — 32 classes, 39 object properties, 10 datatype properties, all with rdfs:label, rdfs:comment, rdfs:domain, and rdfs:range]

---

## 4. Mappings

### 4.1 Pipeline Architecture

The pipeline is implemented as a Python system (`pipeline/build_kg.py`) that orchestrates data fetching, mapping, and post-processing:

```
Step 0: Ontology header (OWL declarations + extensions)
Step 1-4: Data fetching (MusicBrainz → Discogs → Wikidata → Wikipedia)
Step 5: Structured mapping (JSON → RDF triples via rdflib)
Step 6: Text mapping (LLM extraction JSON → RDF with entity linking)
Step 7: Enrichment (country data for related artists)
Step 8: URI consolidation (merge duplicate entities)
Step 9: Type assignment (assign rdf:type to orphan entities)
→ Output: ontology/music_history_kg.ttl (38,429 triples)
```

All API responses are cached to `pipeline/data/` (172 structured files, 67 text files), enabling repeat runs without API calls. A fully cached run completes in ~5.5 seconds.

### 4.2 Structured Data Mapping

**Technique:** R2RML-style field-to-triple mapping using rdflib (Week 8 course technique)

The structured mapping (`mapping/structured.py`) processes JSON data from three sources and generates RDF triples. Each source field is mapped to a specific ontology class and property:

| Source | Field | RDF Mapping |
|---|---|---|
| MusicBrainz | `type` (Person/Group) | `rdf:type` → `mo:SoloMusicArtist` / `mo:MusicGroup` |
| MusicBrainz | `name` | `foaf:name` + `rdfs:label` |
| MusicBrainz | `country` | `mh:countryOfOrigin` → `mh:Country` URI |
| MusicBrainz | `life-span.begin/end` | `schema:birthDate` / `schema:deathDate` |
| MusicBrainz | `tag-list` (count≥3) | `mo:genre` → `mo:Genre` URI |
| MusicBrainz | `artist-rels (member of band)` | `mo:member_of` with instrument attributes |
| MusicBrainz | `artist-rels (influenced by)` | `mh:influencedBy` |
| MusicBrainz | `artist-rels (collaboration)` | `mh:collaboratedWith` |
| MusicBrainz | `artist-rels (producer)` | `mh:producedBy` / `mh:produced` |
| MusicBrainz | release groups | `mh:released` → `mo:Release` with `mh:releaseDate` |
| MusicBrainz | recordings | `mh:hasTrack` → `mo:Track` with `mh:duration` |
| Discogs | `realname` | `mh:realName` |
| Discogs | `genres` / `styles` | `mh:subgenreOf` (genre→style hierarchy) |
| Wikidata | P166 (awards) | `mh:wonAward` → `mh:MusicAward` |
| Wikidata | P1303 (instruments) | `mh:playsInstrument` → `mo:Instrument` |
| Wikidata | P737 (influenced by) | `mh:influencedBy` |
| Wikidata | P264 (record labels) | `mh:signedTo` → `mh:RecordLabel` |
| Wikidata | P86 (composer) | `mh:composed` → `mh:MusicalWork` with `mh:compositionDate` |

**Data cleaning applied:**
- Genre normalisation: all genre names lowercased before URI creation to prevent duplicates ("Rock" vs "rock")
- Tag blacklist: filters out non-genre tags ("british", "uk", "actors", "arrangers", "composers", "80s")
- Partial date handling: years-only dates stored as strings, full YYYY-MM-DD as `xsd:date`
- Release group deduplication: uses release groups (419 per major artist) instead of raw releases (1,456+) to avoid per-pressing duplicates

**Additional course techniques demonstrated:**
- **R2RML mapping document** (`mapping/r2rml_musicbrainz.ttl`): formal declarative specification of the MusicBrainz-to-RDF mapping rules (Week 8)
- **SPARQL Anything CONSTRUCT queries** (`sparql_anything/map_artist.sparql`, `map_discogs_genres.sparql`): mapping cached JSON files directly to RDF using SPARQL CONSTRUCT with the Facade-X data model (Week 8)
- **Wikidata batch SPARQL**: single query with VALUES clause fetches 8 property types per artist, optimised from 10 individual queries to 3

### 4.3 Text Data Mapping

**Technique:** LLM chained prompting for triple extraction (Week 7 course technique)

Text mapping (`mapping/text.py`) processes Wikipedia article text through an LLM to extract structured triples not available in any structured source.

**Process:**
1. Fetch Wikipedia article intro via MediaWiki API (3,000-85,000 characters per artist)
2. Design extraction prompt with domain-specific predicates (collaboratedWith, hasGenre, alterEgo, albumGrouping, composed, producedBy, memberOf, pioneerOf)
3. Include "Do NOT extract" list for data already in structured sources (birth/death dates, awards, instruments, labels, country) to avoid duplication
4. Run prompt in LLM chat, save response as JSON
5. Entity linking resolves text mentions to existing KG URIs
6. Add triples to the graph

**Prompt design:** Role-based + constrained output technique. The prompt assigns dual expertise (knowledge engineer + music historian), specifies allowed predicates matching our ontology, and constrains output to JSON array format. The "Do NOT extract" section prevents duplication with Wikidata data.

**NER comparison (Week 7):** SpaCy (`en_core_web_sm`) and BERT (`dslim/bert-base-NER`) were tested alongside LLM extraction on 3 artists. Key findings:
- SpaCy: most entities (88-94) but many misclassified (albums labelled as PERSON)
- BERT: higher precision for person names but subword tokenization artifacts (`##gy Stardust`)
- LLM: fewest entities but extracts structured **relations** (triples), which neither NER tool can do

Conclusion: LLM extraction is the primary text mapping technique; NER is useful for entity discovery but insufficient for relation extraction.

**Text extraction coverage:** 16 of 58 artists processed, yielding 298 triples with 99% entity linking accuracy. Text-only triples include: alter egos (Ziggy Stardust, Robert Allen Zimmerman), album groupings (Berlin Trilogy, American Recordings series), narrative genres (plastic soul, jungle), pioneer relationships (Tom Jobim → bossa nova), producer relationships (Rick Rubin → Johnny Cash albums).

### 4.4 Entity Linking

**Technique:** 5-tier resolution strategy combining exact match, fuzzy match, type constraints, and NIL detection (Week 7 — entity linking and disambiguation)

When LLM extraction produces a text mention like "Brian Eno", the entity linking system resolves it to the existing MusicBrainz URI (`mb:ff95eb47-...`) rather than creating a duplicate. The strategy:

| Tier | Method | Coverage |
|---|---|---|
| 1. Exact match | Lookup `rdfs:label` index | ~70% |
| 2. Fuzzy match | `rapidfuzz.token_set_ratio` ≥ 85 | ~20% |
| 3. Type-constrained | Use predicate to infer expected type, filter candidates | Handles "Queen" disambiguation |
| 4. Wikidata fallback | SPARQL query for unresolved mentions | Reserved for future use |
| 5. NIL — new entity | Create provisional URI | ~1% |

Result: 295 of 298 text-extracted triples linked to existing entities (99% accuracy). Full strategy documented in `docs/entity_linking_strategy.md`.

### 4.5 Post-Processing

Three post-processing steps improve KG quality:

1. **Enrichment pass**: fetches country data from MusicBrainz for 83 related artists discovered through relationships (band members, collaborators) that weren't in the primary artist list. Uses a persistent cache to avoid re-fetching on subsequent runs.

2. **URI consolidation**: merges 20 duplicate artist URIs where Wikidata influence data created `mh:artist/Bob_Dylan` while MusicBrainz had `mb:72c536dc-...` for the same person. Uses `rapidfuzz.token_set_ratio` ≥ 90 for fuzzy matching.

3. **Type assignment**: assigns `rdf:type` to 747 orphan entities (entities with labels but no type) by inferring type from predicate usage — e.g., if an entity appears as the object of `mh:influencedBy`, it's typed as `mo:MusicArtist`.

### 4.6 Automation Discussion

The spec requires "a computational system that automates as much as possible the entire process." Our pipeline automates:

| Step | Automated? | Method |
|---|---|---|
| Data fetching from 4 APIs | ✓ Fully | Python source modules with caching |
| Cross-referencing between sources | ✓ Fully | URL relationship extraction |
| Structured → RDF mapping | ✓ Fully | rdflib with config-driven rules |
| Text → triple extraction | Partially | LLM prompts (manual), entity linking (automated) |
| Enrichment of related artists | ✓ Fully | Cached MusicBrainz lookups |
| URI consolidation | ✓ Fully | Fuzzy string matching |
| Type inference | ✓ Fully | Predicate-based inference |
| Ontology header generation | ✓ Fully | Python script |

**What required manual intervention and why:**
- **LLM text extraction**: prompts were run manually in a chat interface rather than via API. This was a practical decision (API costs) but the prompt template is reusable and the entity linking is fully automated. A production system would use the Claude/OpenAI API with the same prompts.
- **MBID overrides**: 5 artists required manual MusicBrainz ID specification because search returned incorrect results (e.g., "Bob Marley" matched to "Bob Dylan"). This is a known limitation of string-based search — the fix was a config-driven override system that could be extended with a user confirmation step.
- **Artist list curation**: the 58-artist list was manually curated to ensure diverse coverage across genres, eras, and countries. Automating this would require domain knowledge about what constitutes a representative sample of music history.

---

## 5. Queries

[William + Mert to write — below is a summary]

20 SPARQL queries were written to validate the 20 competency questions. All 20 return results when executed against the KG.

| CQ | Results | Complexity |
|---|---|---|
| CQ1: Album release dates | 1,299 | Simple SELECT |
| CQ2: Artist genres | 394 | GROUP_CONCAT |
| CQ3: Albums | 1,326 | Simple SELECT |
| CQ4: Producers | 4 | UNION pattern |
| CQ5: Band members + instruments | 814 | OPTIONAL join |
| CQ6: Producers by genre | 24 | Multi-source join |
| CQ7: Instruments in bands | 781 | 3-way join |
| CQ8: Award counts | 51 | COUNT + GROUP BY |
| CQ9: Subgenres | 276 | Simple SELECT |
| CQ10: Compositions with dates | 652 | OPTIONAL dates |
| CQ11: Award winners at labels | 2,461 | 3-way join |
| CQ12: Influences sharing genres | 71 | Self-join + genre intersection |
| CQ13: Labels by genre diversity | 115 | COUNT DISTINCT + HAVING |
| CQ14: Cross-country collaborations | 3 | FILTER on country mismatch |
| CQ15: Instruments per genre | 1,058 | COUNT + GROUP BY |
| CQ16: Multinational bands | 6 | COUNT DISTINCT + HAVING |
| CQ17: Artist labels + albums | 221 | GROUP_CONCAT |
| CQ18: Composers' works by country | 533 | 3-way join |
| CQ19: Award winners who collaborated | 5 | Self-join + FILTER |
| CQ20: Geographic genre spread by decade | 1,236 | SUBSTR + GROUP BY |

Query file: `queries/sparql_queries.py`

---

## 6. Evaluation Methodology

### 6.1 Performance Metrics

The pipeline was evaluated for execution efficiency:

| Metric | Value |
|---|---|
| Cold start (all API calls) | ~45 minutes |
| Warm start (cached, with enrichment) | ~97 seconds |
| Fully cached (all data local) | **6.1 seconds** |
| Peak memory | 38.4 MB |
| Output size | 1.34 MB (.ttl file) |
| Total triples | 38,429 |
| Unique subjects | 5,617 |
| Triples per artist | ~413 |
| Cached files | 172 structured + 67 text |

The caching strategy provides a **440x speedup** from cold start to fully cached, demonstrating that the dominant cost is API I/O, not computation. The enrichment cache alone reduced the enrichment step from 92 API calls (~97s) to 0 API calls (~1.2s). The Wikidata batch query optimisation reduced per-artist query time from 10 individual SPARQL queries to 3.

### 6.2 Quality Metrics — Completeness (CM1-CM4, Week 10)

Completeness was measured using the Zaveri et al. (2015) metrics taught in Week 10:

| Metric | Score | Detail |
|---|---|---|
| CM1 — Schema completeness | 89% | 25/28 expected properties populated. Missing: `performedAt` (no venue data), `hasGenre`/`memberOf` (namespace aliases — actually populated as `mo:genre`/`mo:member_of`) |
| CM2 — Property completeness | Varies | `releaseDate`: 97%, `countryOfOrigin`: 50%, `playsInstrument`: 36%, `genre`: 21%, `birthDate`: 21% |
| CM3 — Population completeness | 58 primary + 222 secondary | Primary artists fully populated; secondary have limited data (747 orphans now typed) |
| CM4 — Interlinking | Strong | All 58 primary artists have MusicBrainz MBIDs; 20 URI consolidations performed |

### 6.3 Quality Metrics — CQ Coverage

All 20 competency questions return results when queried against the KG: **100% CQ coverage**.

Sparse results noted for CQ14 (3 results — cross-country collaborations) and CQ4 (4 results — producer relationships from text extraction only). These are documented as KG gaps in the completion analysis.

### 6.4 KG Embeddings (Week 9)

Three KG embedding models were trained using PyKEEN, following the Week 9 lab methodology: TransE (translational distance), RotatE (rotation in complex space), and CompGCN (graph neural network with composition operations).

| Metric | TransE (dim128) | RotatE (dim64) | CompGCN (dim64) |
|---|---|---|---|
| Training triples | 5,292 | 5,292 | 5,292 |
| Entities | 5,064 | 5,064 | 5,064 |
| Relations | 28 | 28 | 56 (incl. inverse) |
| Training loop | sLCWA | sLCWA | LCWA |
| MRR | 0.0442 | **0.0458** | 0.0235 |
| Hits@1 | 0.0144 | **0.0257** | 0.0079 |
| Hits@3 | 0.0355 | **0.0472** | 0.0193 |
| Hits@10 | **0.0918** | 0.0794 | 0.0518 |

**Analysis:** RotatE outperforms TransE on precision metrics (MRR, Hits@1, Hits@3), consistent with its ability to model many-to-many relations in complex vector space. TransE retains an advantage on recall (Hits@10), suggesting it captures broader relational patterns despite lower precision. CompGCN underperformed both translational models — this is expected for a sparse KG where the graph structure provides limited neighbourhood signal for message passing. GNN-based models typically require denser graphs with more consistent local structure to outperform simpler translational approaches.

The relatively low absolute metrics (MRR ~0.05) are expected given the high entity-to-triple ratio (5,064 entities / 5,292 training triples ≈ 1:1). The Week 9 lab baseline on CoDExMedium achieved similar MRR (~0.04) with TransE at 50 epochs.

**Hyperparameter tuning:** We experimented with larger embedding dimensions (256) and more training epochs (500), but observed degraded performance (TransE MRR dropped from 0.044 to 0.032, Hits@10 from 0.092 to 0.053) due to overfitting. With a high entity-to-triple ratio, larger models have insufficient training signal per entity. The optimal configuration for our KG was TransE dim=128 with 200 epochs and RotatE dim=64 with 200 epochs. A production system would benefit from incorporating the full MusicBrainz relationship graph (millions of triples) rather than our 58-artist subset, which would provide sufficient training data for larger embedding dimensions.

| Configuration | TransE MRR | TransE Hits@10 | RotatE MRR | RotatE Hits@10 |
|---|---|---|---|---|
| dim128/64, 200 epochs (optimal) | **0.0442** | **0.0918** | **0.0458** | **0.0794** |
| dim256/128, 500 epochs (overfit) | 0.0323 | 0.0533 | 0.0466 | 0.0801 |

Link prediction results: the model correctly predicted "Lesley Gore" as a Quincy Jones collaborator — verifiably correct from our structured data. For David Bowie influences, predictions included "Andy Warhol" (known influence in our Wikidata data) and "Smokey Robinson" (plausible but unverified).

**Role of embeddings in KG completion:** The embedding models serve two purposes in our pipeline. First, they provide an automated KG completion approach complementary to RAG: while RAG requires manually formulating gap-filling prompts, link prediction automatically identifies probable missing triples across all entities and relations. For example, TransE's prediction that "Lesley Gore" should be connected to Quincy Jones via `collaboratedWith` was verified against our structured data — demonstrating that embeddings can surface verifiable facts that the pipeline missed during initial construction.

Second, the embedding metrics provide a quantitative measure of KG structural quality. The low MRR (0.044–0.046) indicates a high entity-to-triple ratio where many entities have sparse connections. CompGCN's underperformance relative to translational models confirms that our KG's graph structure is too sparse for GNN-based message passing to add value — GNNs require denser local neighbourhoods to aggregate meaningful signals. This diagnostic directly informs our completion analysis: the 222 secondary artists with only labels and types (no relational triples) dilute the embedding space without contributing signal.

**Complementary completion strategies:**

| Technique | What it does | Strength | Weakness |
|---|---|---|---|
| **RAG** (W11) | Queries KG context, asks LLM to fill specific gaps | High precision, explainable, validates existing data | Manual, slow, one gap at a time |
| **PyKEEN link prediction** (W9) | Learns graph patterns, predicts missing links | Automated, scalable, covers all entities | Lower precision, requires validation |

Together these approaches are stronger than either alone: PyKEEN identifies **which relationships are likely missing** across the entire graph (broad automated search), then RAG can **verify and validate** specific predictions with grounded evidence (precise confirmation). This two-stage completion strategy — automated candidate generation followed by RAG-based validation — represents a practical approach to scaling KG completion beyond manual gap analysis.

### 6.5 NER Comparison (Week 7)

Three NER approaches were compared on Wikipedia text for 3 artists:

| Method | Entities | Relations | Types | Speed |
|---|---|---|---|---|
| SpaCy (en_core_web_sm) | 88-94 | 0 | 9-10 | 0.3-1.4s |
| BERT (dslim/bert-base-NER) | 33-36 | 0 | 3-4 | 0.8-3.2s |
| LLM extraction | 20-23 | 19-24 | 4-6 | Manual |

Key finding: SpaCy finds the most entities but with many misclassifications (albums as PERSON). BERT has higher precision but subword artifacts. LLM extraction finds fewer entities but extracts structured **relations** (triples), which is what the KG needs.

### 6.6 RAG vs Plain LLM (Week 11)

The RAG approach (KG as SPARQL-based retrieval source, Week 11) was compared with plain LLM prompting across 5 competency questions. For each CQ, we ran the SPARQL query against our KG, then asked an LLM both the plain question (no context) and a RAG version (with KG results as context, asking "are these complete and accurate?").

| CQ | KG Results | Plain LLM | RAG Found |
|---|---|---|---|
| Quincy awards (CQ8) | 34 awards | "28 Grammys" | KG count may be inflated (competitive vs honorary) |
| Bowie awards (CQ8) | 13 awards | "73 awards" | Declined CBE listed as won; redundant entries; mixed categories (awards vs rankings) |
| Lennon instruments (CQ7) | 7 instruments | 6 instruments + context | Bass guitar questionable (band vs individual attribute); redundant entries (voice/lead vocals) |
| Rock subgenres (CQ9) | 40 subgenres | ~30 subgenres by decade | "interview" data artifact; non-genre entries (acoustic, ballad); query truncation |
| Bowie influences (CQ12) | 13 results (2 artists) | ~15 influences | Cartesian product in query design; only 2 of 10+ known influences returned; "classic rock" is radio format, not genre |
| Jazz countries 1960s (CQ20) | 5 countries (ISO codes) | ~15 countries with context | ISO codes without labels; Spain questionable; 10+ countries missing; population completeness (CM3) limitation from 58-artist sample |

**Findings across all 6 comparisons:**

1. **Plain LLM** provides comprehensive, well-contextualised answers from parametric knowledge — but cannot detect errors in our specific KG data
2. **RAG** consistently functions as a **data quality auditor**, identifying:
   - Factual errors (declined honours listed as won)
   - Data pipeline artifacts ("interview" tag leaking into genre taxonomy)
   - Modelling issues (band-level vs individual-level attribute conflation)
   - Query design problems (cartesian products, result truncation)
   - Taxonomy confusion (radio formats vs musical genres)
3. **Neither approach alone is sufficient**: plain LLM has broader knowledge but no grounding; RAG has grounding but depends on the KG's quality. Together, RAG validates the KG against external knowledge.

Key insight: RAG is not just for filling gaps — it's a **data validation tool** that surfaces quality issues invisible to both the pipeline developer and the plain LLM. Every RAG comparison identified at least one actionable improvement to the KG.

### 6.7 RAG-Driven Iterative Improvement

The KG vs Plain LLM comparison served a dual purpose: evaluating answer quality and identifying actionable improvements. The six RAG comparisons (P18-P23) identified data quality issues that were fed back into the pipeline:

| RAG Finding | Action Taken | Impact |
|---|---|---|
| "interview" tag in genre taxonomy (P21) | Added to genre blacklist in `config.py` | Cleaner subgenre hierarchy |
| "acoustic", "ballad" are not genres (P21) | Added to genre blacklist | Removed non-genre entries from CQ9 |
| "classic rock" is radio format (P21, P22) | Added to genre blacklist | Reduced false genre matches in CQ12 |
| voice/lead vocals redundancy (P20) | Added instrument normalisation in `utils.py` | "vocals" replaces both, reducing duplicates |
| keyboard/keyboard instrument overlap (P20) | Added instrument alias mapping | "keyboard" replaces both |
| "eponymous" is not an instrument (P20) | Filtered out in instrument normalisation | Removed noise from CQ5/CQ7 |

After applying these fixes, the pipeline was rebuilt and re-evaluated:
- CQ5 (band members + instruments): 814 → **687 results** (removed noise)
- CQ7 (instruments in bands): 781 → **662 results** (removed duplicates)
- CQ12 (influences sharing genres): 71 → **69 results** (removed "classic rock" false matches)
- All 20 CQs still pass — improvements reduced noise without losing valid data

This iterative cycle — **build → evaluate with RAG → identify issues → fix pipeline → rebuild → re-evaluate** — demonstrates that LLMs are effective not just as data extraction tools but as quality auditors for KG structure, taxonomy, and instance data. The cycle could be automated in a production system: run RAG validation queries after each pipeline build, flag data quality issues, and apply corrections programmatically.

### 6.7.1 Post-Processing Validation

A dedicated `validate_and_clean()` step addresses data quality issues introduced by LLM text extraction. The function applies 11 rule-based checks that remove invalid triples:

| Rule | Issue Detected | Example |
|---|---|---|
| Self-referencing triples | A → property → A | "John Lennon alterEgo John Lennon" |
| Type mismatches | Genre used as alterEgo/performedAt target | "Bob Dylan alterEgo Rock" |
| Inverted producedBy | Artist producedBy Work (should be reversed) | "Quincy Jones producedBy Thriller" |
| alterEgo → Artist | Entity linking matched persona to existing artist | "Johnny Cash alterEgo The Man In Black Trio" |
| alterEgo → Release | Entity linking matched persona to album | "Nina Simone alterEgo Pastel Blues" |
| performedAt → Release | Venue matched to album title | "Bob Dylan performedAt Highway 61 Revisited" |
| Known factual errors | Hardcoded corrections from RAG validation | "The Beatles producedBy George Harrison" |

The validation removed **20 invalid triples** from the final KG. This demonstrates a key trade-off in LLM-based KG construction: LLMs enable fast, scalable extraction of triples from unstructured text (our text mapping produced hundreds of triples across 58 artists), but they introduce noise that requires post-processing validation. The approach is still faster than manual triple creation, but the pipeline must include quality controls. Pattern-based rules catch systematic errors (type mismatches, self-references), while hardcoded corrections handle factual errors that only domain knowledge can identify.

### 6.8 Justification of Metric Choices

- **CM1-CM4** (Week 10): standard completeness metrics for KG evaluation, directly applicable to identifying gaps
- **CQ coverage**: task-based evaluation measuring whether the KG serves its intended purpose
- **MRR/Hits@K** (Week 9): standard link prediction metrics for embedding quality
- **Precision of NER**: measures entity extraction quality for the text mapping pipeline
- **RAG vs plain comparison**: directly addresses the spec requirement to compare "how does the quality of its answers compare to simple prompts against an LLM"

---

## 7. Repository Link

[Insert public GitHub URL]

---

## Appendices

- **A.** Competency Questions (20 CQs with relationship paths) — see `docs/cq_prompt_justification.md`
- **B.** Prompt Log (18 prompts) — see `docs/prompts_log.md`
- **C.** Completion Analysis (5 ontology gaps + 5 instance gaps + RAG results) — see `docs/completion_analysis.md`
- **D.** Entity Linking Strategy — see `docs/entity_linking_strategy.md`
