# Knowledge Graph Completion Analysis

## Overview

This document analyses the completeness of our Music History knowledge graph (42,365 triples, 58 primary artists) and describes the strategy and results of using RAG to resolve identified gaps.

We apply the completeness metrics from Zaveri et al. (2015), as taught in Week 10:
- **CM1 — Schema completeness**: classes/properties represented vs total needed
- **CM2 — Property completeness**: how well entity properties are filled in
- **CM3 — Population completeness**: real-world entities represented vs what should exist
- **CM4 — Interlinking completeness**: cross-references between entities and external KGs

### Team Discussion

The completion analysis was discussed with the team during Meeting 3 (1 April 2026). The domain experts (Sofia, Davyd) reviewed the identified gaps and confirmed that the 5 ontology and 5 instance gaps accurately reflect the most impactful incompleteness in the KG. Key feedback from the team discussion:

- **Sofia (domain expert)** confirmed that the Umm Kulthum gap (I2) was the most critical instance-level issue, as she is one of the most important musicians of the 20th century and her absence weakens the KG's claim to cover "music history" comprehensively.
- **William (modelling expert)** noted that the `signedTo` temporal scoping gap (O1) is a modelling challenge — it requires either RDF reification or named graphs, both of which add complexity to SPARQL queries. The team agreed to document the gap and RAG results without implementing reification in the current version.
- **The team agreed** that RAG should be applied to all 10 gaps to demonstrate the completion methodology, with programmatic ingestion for the gaps where structured JSON output could be mapped directly to triples (I1, I4, I5, O2, O3, O4, O5).

---

## 5 Incomplete Ontology Elements

### O1. No temporal scoping on `signedTo` property
- **Gap**: `signedTo` links an artist to all their record labels simultaneously, with no time period. CQ17 shows all albums under all labels (cartesian product) because there's no way to know which label was active during which album's release.
- **Impact**: CQ17 results are inflated and imprecise (226 triples without temporal context).
- **CM1 metric**: The relationship lacks temporal qualification — no `startDate`/`endDate` modelled.
- **How to complete**: This requires reification or named graphs to attach time periods to the `signedTo` relationship. Wikidata has qualifiers on the P264 (record label) property that include start/end dates, but our current SPARQL query doesn't extract them.

### O2. `performedAt` property sparsely populated (5 triples)
- **Gap**: The `performedAt` property (Artist → Venue) has only 5 triples, all from LLM text extraction (Elvis Presley, Bob Marley, Bob Dylan). No structured source provides concert/venue data.
- **Impact**: CQs involving performances at venues are answerable but limited.
- **CM1 metric**: Property exists and is populated, but coverage is minimal.
- **How to complete**: Setlist.fm API is a specialised data source for live performance data. MusicBrainz has an `event` entity type with venue relationships. Wikipedia text sections about tours/concerts could be extracted via LLM prompting for additional artists.

### O3. `collaboratedWith` modelled via band/project entities, not always direct artist links
- **Gap**: MusicBrainz models collaborations as band/project entities (e.g., "Band Aid", "USA for Africa"), not as direct artist↔artist links. While we materialise symmetric triples (76 total), many are through group membership rather than direct pairwise collaborations.
- **Impact**: CQ14 (cross-country collaborations) returns 32 results, but could be richer with direct artist↔artist links.
- **CM1 metric**: The property is populated (76 triples) but the modelling pattern limits the collaboration network density.
- **How to complete**: LLM text extraction is the most effective approach — Wikipedia articles mention collaborations directly (e.g., "Bowie collaborated with Brian Eno"). After integrating a free-tier LLM API (Google Gemini) into the pipeline, extraction now covers 57/58 artists, significantly increasing collaboration data.

### O4. `founded` property barely represented (4 triples)
- **Gap**: Only 4 `founded` triples exist (John Lennon → The Beatles, John Lennon → Plastic Ono Band, Yoko Ono → Plastic Ono Band, Fela Kuti → Kalakuta Republic). Many artists founded bands, labels, or organisations that aren't captured.
- **Impact**: Queries about artist entrepreneurship and band formation are limited.
- **CM2 metric**: Property populated for < 1% of artists.
- **How to complete**: Extend the LLM text extraction prompt to specifically ask about organisations and bands the artist founded. Wikidata P112 (founded by) could also be queried.

### O5. `hasMusicalPeriod` limited to 3 instances
- **Gap**: Only 5 triples link 3 artists to musical periods (Beethoven → classical/romantic, Miles Davis → bebop movement, Bob Dylan → 1960s, Nina Simone → civil rights movement). Most artists lack period classification.
- **Impact**: Temporal/stylistic analysis of the KG is limited.
- **CM1 metric**: Property and class exist but are minimally populated.
- **How to complete**: Wikidata P2348 (time period) could provide era classifications. LLM extraction could classify artists into periods based on their biography text. A rule-based approach using birth/death dates and genre could also infer approximate periods.

---

## 5 Incomplete Instance Elements

### I1. 1,100+ secondary artists lack genre, birthDate, and country data
- **Gap**: The KG contains 1,241 artist entities, but only 58 are primary (fully processed through all 4 sources). The remaining ~1,183 are secondary references — band members, collaborators, influence targets, and cover composers — discovered through relationships. These have labels but minimal property data.
- **Impact**: CQ12 (influences sharing genres), CQ15 (instruments per genre), CQ20 (geographic spread) return incomplete results for secondary artists.
- **CM2 metric**: `countryOfOrigin` 11.4%, `genre` 4.6%, `wonAward` 4.1% across all artist entities. For the 58 primary artists: country 98.3%, genre 96.6%, awards 87.9%.
- **How to complete**: Extend the enrichment pass to also fetch genres and biographical data from MusicBrainz/Wikidata for secondary artists. The infrastructure already exists (the `enrich_related_artists` function fetches country data); it would need to be extended to also fetch genres, dates, and instruments.

### I2. Umm Kulthum severely under-represented
- **Gap**: Umm Kulthum (Egyptian singer) was processed by MusicBrainz but returned no Discogs ID and no Wikidata ID. Her node has minimal data compared to the average of ~700 triples per primary artist.
- **CM3 metric**: This artist is severely under-represented compared to peers.
- **How to complete**: The MusicBrainz entry may use an Arabic transliteration. Manual lookup of the correct Wikidata ID (Q190573) and Discogs ID would resolve this. Alternatively, a fuzzy search in Wikidata for "أم كلثوم" could find the correct entity.

### I3. LLM text extraction coverage (initially 16/58, now 57/58)
- **Gap (initial)**: Text-extracted triples were available for only 16 artists (298 triples, 28% coverage). The other 42 artists had no text enrichment.
- **Impact**: Text-unique data (alter egos, album groupings, producer relationships, narrative genres) was missing for 72% of artists.
- **Resolution**: Integrated a free-tier LLM API (Google Gemini) into the pipeline (`pipeline/llm_extraction.py`). The pipeline now automatically extracts triples from Wikipedia intros for all artists, using cached responses to avoid redundant API calls. Coverage increased from 16/58 (28%) to **57/58 (98%)**, yielding **887 text-extracted triples** (up from 298). The only remaining gap is Umm Kulthum (no Wikipedia cache due to incorrect MusicBrainz entity match — see I2).
- **CM3 metric**: Text extraction population completeness: 98% (up from 28%).

### I4. Hildegard von Bingen missing genre data
- **Gap**: The only primary artist without any genre assignment. As a medieval composer (~1150), her music predates modern genre classification systems. MusicBrainz tags don't cover medieval music well.
- **CM2 metric**: 1 of 58 primary artists (1.7%) missing genre.
- **How to complete**: Manual assignment of "medieval music" and "sacred music" genres, or extraction from her Wikipedia article via LLM.

### I5. Cover recording composers lack biographical data
- **Gap**: The cover detection step identified 373 cover recordings with 1,059 composed/composedBy triples linking to composer entities. These composers have names and MBIDs but no biographical data (country, dates, genres).
- **CM2 metric**: Composers represent a large population of uncharacterised entities.
- **How to complete**: Run a targeted enrichment pass on composer MBIDs to fetch their biographical data from MusicBrainz, similar to the existing `enrich_related_artists` function.

---

## RAG Strategy

### Approach

We use RAG (Retrieval Augmented Generation) as taught in Week 11 to resolve KG incompleteness. The approach:

1. **Identify a gap** from the analysis above
2. **Query the KG** via SPARQL to retrieve relevant context
3. **Verbalise** the retrieved triples into natural language
4. **Prompt an LLM** with the verbalised context + the gap question
5. **Parse the LLM response** into new triples
6. **Add to the KG** using the entity linking pipeline

This follows the "KG as SPARQL-based retrieval source" pattern from Week 11.

### RAG Implementation

For each gap, we construct a prompt that:
- Provides KG context (what we already know about the entity)
- Asks specifically about the missing information
- Requests structured output (JSON triples)

The implementation is in `pipeline/rag_completion.py`.

### Example RAG Queries

#### RAG Query 1: Fill missing producer relationships (Gap O2/O3)

**Step 1 — Retrieve KG context:**
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
SELECT ?albumTitle ?releaseDate WHERE {
    ?artist rdfs:label "Michael Jackson"@en .
    ?artist mh:released ?album .
    ?album dc:title ?albumTitle .
    OPTIONAL { ?album mh:releaseDate ?releaseDate }
}
```

**Step 2 — Verbalise context:**
"Michael Jackson released the following albums: Off the Wall (1979), Thriller (1982), Bad (1987), Dangerous (1991), HIStory (1995)..."

**Step 3 — RAG prompt:**
```
Based on what we know about Michael Jackson's discography, who produced each of these albums?
Context from our knowledge graph: [verbalised triples]
Return as JSON: [{"album": "...", "producer": "..."}]
```

**Step 4 — LLM response:**

| Album | Producer (from RAG) | Confidence |
|---|---|---|
| Got to Be There (1972) | Hal Davis | High — well-documented Motown production |
| Ben (1972) | Hal Davis | High |
| Off the Wall (1979) | Quincy Jones | Confirmed (matches existing KG data) |
| Thriller (1982) | Quincy Jones | Confirmed |
| Bad (1987) | Quincy Jones | Confirmed |
| Dangerous (1991) | Michael Jackson / Teddy Riley / Bill Bottrell | Uncertain — flagged by LLM |
| HIStory (1995) | Michael Jackson | Uncertain — multiple collaborators |
| Invincible (2001) | Rodney Jerkins | Uncertain — fragmented production |

**Key finding:** The LLM proactively flagged uncertainty for 3 albums where production was distributed across multiple collaborators, recommending cross-referencing before ingestion. This demonstrates responsible KG construction — not all LLM outputs should be automatically ingested.

**New triples added (high confidence):**
- `(Got to Be There, producedBy, Hal Davis)`
- `(Ben, producedBy, Hal Davis)`

**Triples requiring human validation:**
- `(Dangerous, producedBy, Teddy Riley)` — uncertain, multiple producers
- `(HIStory, producedBy, Michael Jackson)` — uncertain, collaborative
- `(Invincible, producedBy, Rodney Jerkins)` — uncertain, fragmented

#### RAG Query 2: Fill missing country data (Gap I1)

**Step 1 — Retrieve artists missing country:**
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?artistName WHERE {
    ?artist a mo:SoloMusicArtist .
    ?artist rdfs:label ?artistName .
    FILTER NOT EXISTS { ?artist mh:countryOfOrigin ?c }
}
```

**Step 2 — RAG prompt:**
```
For each of these musicians, what country are they from?
Artists: [list from SPARQL]
Return as JSON: [{"artist": "...", "country_code": "..."}]
```

#### RAG Query 3: Fill missing genre data for influence targets (Gap I1)

**Step 1 — Retrieve influence targets without genres:**
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?influencerName WHERE {
    ?artist mh:influencedBy ?influencer .
    ?influencer rdfs:label ?influencerName .
    FILTER NOT EXISTS { ?influencer mo:genre ?g }
}
```

**Step 2 — RAG prompt with KG context:**
```
Our knowledge graph contains these artists who influenced others but we don't know their genres:
[list]
The artists they influenced play these genres: [context from KG]
Based on this context and your knowledge, what genres do these influencers belong to?
```

### RAG-Driven Iterative Improvement Cycle

Beyond gap-filling, RAG served as a **data quality auditor** throughout the pipeline development. The six KG vs Plain LLM comparisons (Prompts P18-P23) identified actionable data quality issues that were fed back into the pipeline:

| RAG Finding | Action Taken | Impact |
|---|---|---|
| "interview" tag in genre taxonomy (P21) | Added to genre blacklist | Cleaner subgenre hierarchy |
| "acoustic", "ballad" are not genres (P21) | Added to genre blacklist | Removed non-genre entries |
| "classic rock" is radio format (P21, P22) | Added to genre blacklist | Reduced false genre matches |
| voice/lead vocals redundancy (P20) | Added instrument normalisation | Removed duplicates |
| keyboard/keyboard instrument overlap (P20) | Added instrument alias mapping | Consistent instrument names |
| "eponymous" is not an instrument (P20) | Filtered in normalisation | Removed noise |

This iterative cycle — **build → evaluate with RAG → identify issues → fix pipeline → rebuild → re-evaluate** — demonstrates that LLMs are effective not just as data extraction tools but as quality auditors for KG structure, taxonomy, and instance data.

### RAG Completion Results (P34–P43)

We executed 10 RAG prompts (one per gap) using the SPARQL retrieval → verbalise → prompt → parse cycle. Each prompt is documented in `docs/prompts_log.md` as P34–P43.

| Gap | Prompt | SPARQL Retrieved | RAG Output | Key Metric |
|---|---|---|---|---|
| O1 signedTo temporal | P34 | 226 artist-label pairs | 226 temporal ranges | 46% high confidence |
| O2 performedAt sparse | P35 | 5 existing triples | 113 new events | 5 → 115 triples (22x) |
| O3 collaboratedWith indirect | P36 | 39 existing pairs | 69 new direct pairs | 18 cross-primary |
| O4 founded sparse | P37 | 4 existing triples | 47 new entries | 17 link existing entities |
| O5 hasMusicalPeriod limited | P38 | 5 existing triples | 106 new assignments | 58/58 artists covered |
| I1 secondary artists | P39 | 1,099 missing data | 50 enriched (sample) | 94% resolved |
| I2 Umm Kulthum | P40 | 4 wrong triples | Full reconstruction | Wrong → correct entity |
| I3 text extraction 28%→98% | P41 | 42 artists missing | 87 triples (5 demo) + 589 via API | 57/58 artists covered |
| I4 Hildegard genres | P42 | 0 genres | 5 genres, 3 periods | Only genreless artist fixed |
| I5 cover composers | P43 | 330 missing data | 50 enriched (sample) | 94% resolved |

### Programmatic Ingestion of RAG Results

The RAG responses were saved as structured JSON files in `docs/rag_responses/`. We then wrote a programmatic ingestion script (`pipeline/ingest_rag_results.py`) that reads these JSON files and adds the resolved triples to the KG using label-based entity linking. This closes the full RAG loop:

```
Identify gap → SPARQL retrieval → RAG prompt → LLM response (JSON) → Programmatic ingestion → Enriched KG
```

The ingestion script is integrated into the main pipeline (`build_kg.py`, Step 14) and runs automatically after validation. Results from the ingestion:

| Gap | Triples Ingested | What was added |
|---|---|---|
| I1 Secondary artists | 90 | Country + genre for 45 secondary artists |
| I5 Cover composers | 90 | Country + genre for 45 composers |
| O2 performedAt | 106 | 106 iconic performances across 43 artists |
| O3 collaboratedWith | 50 | 25 new direct artist-artist pairs (symmetric) |
| O4 founded | 44 | 44 bands, labels, foundations, companies |
| O5 hasMusicalPeriod | 104 | Period assignments for all 58 artists |
| I4 Hildegard | 10 | 5 genres + 3 periods + 2 instruments |
| **Total** | **494** | |

**Impact on defined classes:** The new collaboration data triggered additional InternationalCollaborator inferences, raising defined class instances from 74 to 117 (+58%).

**KG size:** 40,742 triples (pre-enrichment) → 42,365 triples (post-RAG + full LLM extraction), a 3.9% increase with targeted, high-quality additions.

### RAG Results Summary

**Value of RAG over plain LLM prompting:**
- **Plain LLM**: Answers from parametric knowledge only, may hallucinate entity names not in our KG, cannot verify or challenge existing data
- **RAG**: Answers grounded in our actual KG data, fills specific gaps, confirms/contradicts existing triples, and the LLM can self-assess confidence levels

The RAG approach ensures the LLM's response is anchored to entities that already exist in our KG, making entity linking more reliable and avoiding hallucinated entity names. The LLM's self-assessment of confidence levels provides a quality signal for deciding which triples to ingest automatically vs review manually.

**Note on tooling:** The RAG workflow was executed using Claude Code (CLI agent), which enabled a tighter integration than a standard chat-based LLM. The agent could directly run SPARQL queries against the KG to retrieve context, write structured JSON output files, and execute Python scripts to programmatically ingest the results — all within the same conversation. This demonstrates the value of agentic LLM tooling for Knowledge Engineering tasks where the retrieval, reasoning, and ingestion steps benefit from direct access to the codebase and data files.

---

## Completeness Metrics Summary (Post-RAG)

| Metric | Pre-RAG | Post-RAG | Detail |
|---|---|---|---|
| **CM1 — Schema** | 93% | 97% | 29/30 declared object properties now have instance triples (performedAt: 5 → 111, hasMusicalPeriod: 5 → 109, founded: 4 → 48) |
| **CM2 — Property (primary)** | High | Higher | Country 98%, Genre 98% (Hildegard fixed), Instruments 81% (Hildegard added) |
| **CM2 — Property (all artists)** | Low | Improved | Country +7%, Genre +7% — 90 secondary artists enriched with country/genre |
| **CM3 — Population** | 58 primary | Same | Population unchanged; data density increased for existing entities |
| **CM4 — Interlinking** | Strong | Strong | MBIDs maintained; 25 new cross-entity collaboration links added |
| **Defined classes** | 74 | 188 | +154% — new collaborations (124 InternationalCollaborator) + producers (13 ProducerArtist) |
| **Total triples** | 40,742 | 42,365 | +494 RAG + ~1,100 LLM extraction triples |

---

## Data Quality Review and Corrections

Following the RAG completion phase, the KG was reviewed by the domain expert (Davyd) who identified several data quality issues. These were investigated, traced to their root causes, and fixed structurally in the pipeline.

### Issues Identified and Fixed

| Issue | Root Cause | Structural Fix | Impact |
|---|---|---|---|
| **76 non-music genres** (film, game, TV categories: "drama film", "comedy film", "action-adventure game", etc.) | Wikidata P136 returns all creative genres for a person, not just music genres | Added 60+ entries to `GENRE_BLACKLIST`; added blacklist check to text pipeline's genre creation | -~318 triples |
| **Duplicate genre labels** ("rock" vs "rock music", "ambient" vs "ambient music", "avantgarde" vs "avant-garde") | `normalise_genre()` didn't strip " music" suffix or normalise punctuation | Extended `normalise_genre()` to strip trailing " music", normalise `&`→`and`, merge variant spellings; added label deduplication in validation | Genres 375→253 |
| **Non-genre tags as genres** ("composer", "4x", "beholder", "glorious", "pianist", "flute", "sitar") | MusicBrainz community tags and Wikidata artefacts | Added to `GENRE_BLACKLIST` | -~250 triples |
| **Nationality tags as genres** ("austrian", "polish", "italian", "european", "russian") | Wikidata P136 and MusicBrainz tags don't distinguish nationality from genre | Added to `GENRE_BLACKLIST` | -~130 triples |
| **31 non-music awards** (military medals, honorary degrees, film acting awards, citizenship honours) | Wikidata P166 returns ALL awards without filtering | Added `AWARD_BLACKLIST_KEYWORDS` (pattern-based) + `AWARD_BLACKLIST_EXACT` to pipeline | -100 triples |
| **7 duplicate MusicalWork entities** (Beatles songs under both `/composition/` and `/work/` URIs) | Two code paths creating MusicalWork entities with different URI prefixes | Unified to `composition/` prefix in both `structured.py` and `text.py` | -27 triples |
| **10 duplicate MusicArtist entities** (same person with 2 MusicBrainz IDs) | MusicBrainz has duplicate entries for older/historical artists; cover detection created new URIs without checking existing | Added name-based deduplication in cover detection composer loop | -34 triples |
| **19 `released` range violations** (compositions/tracks linked via `released` instead of `composed`) | LLM text extraction confused "released" with "composed" for songs | Added range validation in `text.py`: if object is MusicalWork, auto-convert to `composed`; if Track/Label, skip | -26 triples |
| **10 `collaboratedWith` domain violations** (entities typed as `foaf:Person` only) | `assign_types_to_orphans` typed influence targets as Person, then text pipeline added collaboratedWith later | Text pipeline now adds `MusicArtist` type when creating `collaboratedWith` triples | +4 triples |
| **1 `producedBy` domain violation** (RecordLabel as subject) | LLM confused "American Recordings" label with album of same name | Added domain validation in `text.py`: subject must be `mo:Release` | -1 triple |
| **124 dates with `xsd:gYearMonth`** (not declared in ontology range) | `_typed_date_literal` created `xsd:gYearMonth` for YYYY-MM dates | Normalise YYYY-MM to YYYY-MM-01 with `xsd:date` | 0 (datatype fix) |
| **46 ontology labels missing `@en`** | `ontology_header.py` used bare `Literal()` without language tag | Added `lang="en"` to all ontology label declarations | 0 (tag fix) |
| **49 duplicate composition dates** (same work with multiple dates) | Wikidata returns multiple dates when title matches film screenings | Validation keeps only the earliest `compositionDate` per work | -48 triples |
| **40 orphan genres** (Genre entities with 0 references) | Created during Discogs mapping but never used by any entity | Validation removes Genre entities with no `mo:genre` or `subgenreOf` references | -~120 triples |

### Root Cause Analysis

The data quality issues fall into three categories:

1. **Source data ambiguity** (genres, awards): Wikidata properties like P136 (genre) and P166 (award received) don't distinguish between music-specific and general creative/civic categories. The fix was filtering — genre allowlist for Discogs, genre blacklist for MusicBrainz/Wikidata, award blacklist for Wikidata.

2. **Entity resolution failures** (duplicate URIs, range violations): The pipeline's entity linking and URI creation had blind spots — different code paths creating entities with different URI schemes, and the LLM confusing similar-named entities (album vs label, released vs composed). The fix was structural: unified URI prefixes, name-based deduplication, and domain/range validation before triple creation.

3. **Normalisation gaps** (duplicate genres, date types, language tags): Inconsistent normalisation across sources — MusicBrainz uses "rock", Wikidata uses "rock music"; dates arrive in mixed precision; labels lacked language tags. The fix was extending `normalise_genre()`, `_typed_date_literal()`, and adding `lang="en"` throughout.

### Reflection: LLM-Based KG Construction Trade-offs

The domain expert review surfaced an important insight about LLM-based KG construction: **LLMs are effective for fast, scalable triple extraction, but they introduce noise that requires post-processing validation and domain expert review.** The 19 `released` range violations, for example, arose because the LLM treated song titles as album releases — a distinction that requires domain knowledge to catch.

The iterative cycle of **build → review → trace root cause → fix structurally → rebuild** proved more effective than either pure automation or pure manual curation:
- Pure automation (no review): would leave 76 film genres, 31 non-music awards, and 19 range violations in the KG
- Pure manual curation: would not scale to 42,365 triples across 58 artists
- Hybrid approach: automated pipeline + domain expert review + structural fixes = clean KG with traceable corrections

This aligns with the RAG finding from the evaluation (§6.6): RAG is most valuable as a **data quality auditor**, not just a gap-filler. The domain expert review served the same role at a higher level — identifying systematic issues that pattern-based validation and RAG prompts couldn't catch because they require holistic domain understanding.

A parallel validation was performed by loading the TTL file into **Protégé** to verify that the ontology structure matched the team's modelling decisions. Despite the pipeline generating ontology declarations programmatically, Protégé revealed mismatches that only visual inspection could catch — for example, verifying that OWL2 property characteristics (symmetric, transitive, irreflexive, asymmetric) were correctly assigned, that inverse pairs were complete, and that class hierarchies reflected the planned taxonomy. This reinforces the finding that **automated KG construction requires manual ontology validation**: the pipeline can build structurally valid RDF, but only a human with Protégé (or equivalent tooling) can verify that the semantics match the design intent.

---

## Recommendations for Future Work

1. ~~**Extend text extraction to all 58 artists**~~ — **DONE**: integrated Google Gemini free-tier API into pipeline, now covers 57/58 artists (887 triples)
2. **Extend enrichment pass** to fetch genres, dates, and instruments for secondary artists (not just country)
3. **Implement temporal scoping** for `signedTo` using Wikidata qualifiers or reification
4. **Add concert/venue data** from Setlist.fm API or MusicBrainz events
5. **Improve Umm Kulthum** and other under-represented artists via manual Wikidata lookup
6. **Enrich cover composers** with biographical data from their MBIDs
7. **Wikidata genre filtering** — use Wikidata's class hierarchy (P31/P279) to programmatically distinguish music genres from film/game/TV genres, replacing the manual blacklist
8. **Award classification** — query Wikidata for award categories (P31) to auto-filter non-music awards rather than maintaining a keyword blacklist
