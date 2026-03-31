# LLM-Augmented Competency Questions: Prompt Design Justification

## Overview

This document explains how the prompts used to generate the 10 LLM-augmented competency questions were designed to produce questions that are relevant to the Music History domain and complement the 10 manually-created CQs.

## Manual CQs (Reference)

The following 10 CQs were manually created by the domain expert (Sofia Davis) leading a discussion with the full team:

1. What date was an album released?
2. What genre(s) did a given composer/artist write in?
3. What album was a given track released in?
4. Who produced a given album?
5. Which performers played in a given track?
6. What producer worked on albums of a given genre?
7. Who plays what instrument in a given band?
8. How many awards has a certain artist won?
9. What subgenres emerged from a given genre?
10. Which musical works were composed in a given era, and how much time later were they first recorded?

### Gap Analysis of Manual CQs

Before designing the LLM prompt, we analysed which ontology entities and relationships the manual CQs cover and which they miss:

**Covered by manual CQs:**
- Album ↔ Track (CQ 3)
- Album ↔ releaseDate (CQ 1)
- Artist ↔ Genre (CQ 2)
- Album ↔ Producer (CQ 4, 6)
- Track ↔ Performer (CQ 5)
- Band ↔ Member ↔ Instrument (CQ 7)
- Artist ↔ Award (CQ 8)
- Genre ↔ Subgenre (CQ 9)
- MusicalWork ↔ compositionDate ↔ Recording (CQ 10)

**NOT covered by manual CQs:**
- Record labels (`signedTo`) — no CQ tests label relationships
- Collaborations (`collaboratedWith`) — no CQ tests cross-artist collaboration
- Influence chains (`influencedBy`) — no CQ tests artist influence
- Geographic spread (`countryOfOrigin`) — no CQ tests where artists are from
- Temporal evolution — only CQ 10 touches on time, but from the composition angle
- Cross-entity aggregation — few CQs require counting or grouping

This gap analysis directly informed the prompt design.

## Prompt Design Process

### Step 1: Technique Selection

We drew on established prompting techniques from prior coursework experience:

| Technique | Purpose | Why chosen |
|---|---|---|
| **Role-based** | Assign dual expertise (knowledge engineer + music historian) | Produces questions that are both technically queryable via SPARQL and historically meaningful |
| **Few-shot** | Provide 3 example CQs with relationship paths | Sets the expected format, complexity level, and demonstrates multi-entity join patterns |
| **Constrained output** | Explicit requirements about what to cover and format | Ensures the LLM fills the identified gaps rather than duplicating manual CQs |

### Step 2: Context Design

The prompt included:
- **The full entity model** from the team meeting (MusicalWork hierarchy including classical compositions, Artist hierarchy including composers/producers/musicians/bands) — ensures domain relevance
- **All 10 manual CQs** — so the LLM can identify genuine gaps rather than generating duplicates
- **The ontology relationships** (released, hasTrack, hasGenre, subgenreOf, memberOf, etc.) — ensures generated CQs are answerable over our specific schema
- **Data sources** (MusicBrainz, Discogs, Wikipedia) — grounds the CQs in what data is actually available

### Step 3: Gap-Directed Constraints

The prompt explicitly directed the LLM to cover the gaps identified in the manual CQ analysis:

> "Cover relationships and entities that the manual CQs miss (especially: record labels, collaborations, influence chains, geographic spread, temporal evolution)"

This constraint is critical — without it, the LLM tends to generate CQs similar to the examples provided rather than complementary ones.

### Step 4: Iterative Refinement

The initial LLM output (Prompt P5) had three issues:
1. CQs 1-3 were too similar to the few-shot examples (a known limitation of few-shot prompting)
2. Some CQs used vague aggregations ("most active", "most commonly associated") that are hard to express in SPARQL
3. No CQ tested the MusicalWork→Recording distinction (classical compositions recorded centuries later)

A follow-up refinement prompt (P6) used **iterative refinement + chain-of-thought** to fix these specific issues:

> "Review the 10 competency questions you generated and refine them. Think step by step about each one..."

This produced the final set of 10 LLM CQs with all issues resolved.

## Final LLM-Augmented CQs

1. **Which award-winning artists were signed to a given record label?**
   - Path: Artist → wonAward → Award + Artist → signedTo → RecordLabel
   - Complements: Manual CQ 8 (awards) by adding the label dimension

2. **Which artists that influenced a given artist also share at least one common genre?**
   - Path: Artist → influencedBy → Artist + both Artist → hasGenre → Genre (intersect)
   - Fills gap: Influence relationships (not in any manual CQ)

3. **Which record labels have released albums in more than N distinct genres?**
   - Path: Artist → signedTo → RecordLabel + Artist → released → Album → hasGenre → Genre (COUNT DISTINCT)
   - Fills gap: Record labels (not in any manual CQ)

4. **Which artists have collaborated with artists from a different country?**
   - Path: Artist → collaboratedWith → Artist + both → countryOfOrigin → Country (FILTER differs)
   - Fills gaps: Collaborations + geography (neither in manual CQs)

5. **Which instruments appear in tracks of a given genre?**
   - Path: Track → hasGenre → Genre + Artist → playsInstrument → Instrument + Artist → performed → Track
   - Complements: Manual CQ 7 (instruments in bands) by linking instruments to genres

6. **Which bands have members originating from more than one country?**
   - Path: Band ← memberOf ← Artist → countryOfOrigin → Country (COUNT DISTINCT > 1)
   - Fills gap: Geographic spread of band membership (not in manual CQs)

7. **Which record labels has a given artist been signed to, and what albums released under each?**
   - Path: Artist → signedTo → RecordLabel + Artist → released → Album → releaseDate
   - Fills gap: Artist-label-album timeline (not in manual CQs)

8. **Which composers have had their compositions recorded by artists from a different country?**
   - Path: Composer → composed → Composition → hasRecording → Recording ← performed ← Artist → countryOfOrigin (4-entity join)
   - Complements: Manual CQ 10 (composition→recording) by adding the cross-country dimension
   - Tests the MusicalWork vs Recording distinction critical to our ontology

9. **Which artists who won a given award have collaborated with each other?**
   - Path: Artist → wonAward → Award + Artist → collaboratedWith → Artist (self-join, same award)
   - Fills gaps: Awards + collaborations combined (neither tested together in manual CQs)

10. **In which countries were artists active who released albums in a given genre during a given decade?**
    - Path: Album → hasGenre → Genre + Album → releaseDate (FILTER decade) + Artist → released → Album + Artist → countryOfOrigin → Country
    - Fills gaps: Geographic spread + temporal evolution (4-entity join)

## Coverage Verification

### Entity Coverage (Manual + LLM combined)

| Entity | Manual CQs | LLM CQs | Covered? |
|---|---|---|---|
| Artist/Composer/Producer | 2, 4, 5, 7, 8 | 1, 2, 4, 8, 9 | ✓ |
| Band | 7 | 6 | ✓ |
| Album | 1, 3, 4 | 3, 7, 10 | ✓ |
| Track | 3, 5 | 5 | ✓ |
| MusicalWork/Composition | 10 | 8 | ✓ |
| Genre/Subgenre | 2, 6, 9 | 2, 3, 5, 10 | ✓ |
| Instrument | 7 | 5 | ✓ |
| Record Label | — | 1, 3, 7 | ✓ (gap filled) |
| Award | 8 | 1, 9 | ✓ |
| Country/Place | — | 4, 6, 8, 10 | ✓ (gap filled) |

### Relationship Coverage (Manual + LLM combined)

| Relationship | Manual CQs | LLM CQs |
|---|---|---|
| released | 1 | 3, 7, 10 |
| hasTrack | 3 | — |
| hasGenre | 2, 6, 9 | 2, 3, 5, 10 |
| subgenreOf | 9 | — |
| memberOf | 7 | 6 |
| playsInstrument | 7 | 5 |
| producedBy | 4, 6 | — |
| influencedBy | — | 2 |
| collaboratedWith | — | 4, 9 |
| wonAward | 8 | 1, 9 |
| signedTo | — | 1, 3, 7 |
| countryOfOrigin | — | 4, 6, 8, 10 |
| releaseDate | 1, 10 | 7, 10 |
| compositionDate | 10 | 8 |

### SPARQL Complexity

| Complexity | Manual CQs | LLM CQs |
|---|---|---|
| Simple SELECT (1-2 joins) | 1, 2, 3, 4, 5 | 1, 2 |
| Medium (2-3 joins) | 6, 7, 8 | 4, 5, 7, 9 |
| Complex (3+ joins, aggregation) | 9, 10 | 3, 6, 8, 10 |

The LLM CQs are on average more complex than the manual CQs, with 8 of 10 requiring 3+ entity joins. This is by design — the manual CQs establish the basic ontology coverage while the LLM CQs test more advanced query patterns.
