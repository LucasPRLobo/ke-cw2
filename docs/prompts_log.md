# Prompts Log

This document records all prompts used throughout the project and the knowledge engineering task they belong to.

## Format

For each prompt, record:
- **Task**: Which KE task this prompt was used for
- **Date**: When the prompt was used
- **Author**: Who used the prompt
- **LLM/Tool**: Which LLM or tool was used
- **Prompt**: The exact prompt text
- **Result summary**: Brief description of the output/result
- **Used in**: Where the result was applied

---

## P1 — Ontology Research

- **Task**: Existing ontology discovery
- **Date**: 2026-03-25
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "Research existing ontologies related to music history and arts/cultural heritage that could be used in a knowledge graph project. I need at least 2 existing ontologies that can be extended with subclasses and subproperties."
- **Result summary**: Identified 4 candidate ontologies: Music Ontology (MO), CIDOC-CRM, DOREMUS, and Schema.org. Recommended MO + CIDOC-CRM as the two to extend, with concrete subclass/subproperty suggestions for each.
- **Used in**: Ontology selection, extension planning

---

## P2 — Data Source Research

- **Task**: Data source discovery
- **Date**: 2026-03-25
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "Research data sources for a music history knowledge graph. I need at least 1 textual source and 1 structured source. Search for: MusicBrainz API, Spotify API, Wikidata SPARQL, Discogs API, Last.fm API, Wikipedia, BBC Music."
- **Result summary**: Identified 5 structured sources (MusicBrainz, Wikidata, Discogs, Spotify, Last.fm) and 3 textual sources (Wikipedia, BBC Music, MusicBrainz annotations). Recommended MusicBrainz (structured) + Wikipedia (textual) + Discogs (structured) as primary sources.
- **Used in**: Data source selection, pipeline planning

---

## P3 — LLM-Augmented Competency Questions

- **Task**: Competency question generation (LLM-augmented)
- **Date**: 2026-03-25
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "You are a knowledge engineer and Music historian expert, that aims to write 10 competency questions for a knowledge graph that aims to represent information in the Music history Domain. Our goal is to define questions that aim to demonstrate the scope of the ontology we will be designing and that will help guide the creation of the entire system. Provide an initial draft of the 10 questions, analyse them and then provide suggestions of how should we proceed."
- **Prompt design justification**: The prompt was designed to (1) assign domain expertise to the LLM to produce historically grounded questions, (2) request analysis of the output to ensure self-critique and quality, (3) complement the 10 manual CQs by covering gaps identified in the manual set — specifically: record label relationships (signedTo), collaborations (collaboratedWith), genre origins, transitive influence chains, temporal evolution, aggregation queries, and cross-genre analysis.
- **Result summary**: Generated 10 CQs covering cultural/historical context (genre origins, label activity, cross-genre collaboration), lineage/influence (influence chains, genre bridging), commercial/industry (label switching, cross-genre producers), geographic spread (venue diversity, genre diffusion), and structural queries (career span and genre evolution). Analysis confirmed all 12 entities and 17 properties are covered across the combined 20 CQs. Identified potential issues with temporal modelling (CQ6, CQ10) and suggested simplifications.
- **Used in**: Competency questions (LLM-augmented set), ontology requirements

---

## P4 — CQ Prompt Design (Context & Planning)

- **Task**: Planning the LLM-augmented competency question generation approach
- **Date**: 2026-03-27
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "ok lets start by drafting the 10 extra cqs. I will open a new conversation just to have that. I have some example prompts that use different prompting techniques from a different cw for cq that I will provide here so that you can help me tune them to this project. For every prompt and response I get from the llm I will send them here for you to log them. I think for an initial prompt we could sort of explain the requirements for the questions/best practices and bring in some of the suggestions we had from the meeting on the structure of the ontology"
- **Prompt design justification**: This was a context-setting prompt to plan the approach for generating the 10 LLM-augmented CQs. The goal was to (1) leverage prompting techniques from prior coursework (role-based, few-shot, chain-of-thought, constrained output) and adapt them for the music history domain, (2) incorporate decisions from the team meeting (entity model with MusicalWork and Artist hierarchies, full timeline scope, genres as classification system), and (3) ensure the generated CQs complement the 10 manual CQs by covering gaps in record labels, collaborations, influence chains, geographic spread, and temporal evolution.
- **Result summary**: Produced a structured prompt template combining role-based (knowledge engineer + music historian), few-shot (3 example CQs with relationship paths), and constrained output (explicit requirements about complementing manual CQs, format specification). The prompt was designed to be used in a separate conversation for clean context.
- **Used in**: Prompt design for P5

---

## P5 — LLM-Augmented Competency Questions (Final)

- **Task**: Competency question generation (LLM-augmented) — final version
- **Date**: 2026-03-27
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: Role-based + Few-shot + Constrained output
- **Prompt**:
```
You are a knowledge engineer and music historian expert designing a knowledge graph for the Music History domain.

CONTEXT:
We are building an ontology that represents music history with these key entity groups:

MusicalWork (broad concept):
- Albums, Tracks, Singles, Recordings
- Classical compositions (works that predate any recording)

Artist (broad concept):
- Composers, Producers
- Musicians (Singers, Instrumentalists)
- Bands/Groups

Other entities: Genre, Subgenre, Record Label, Award, Instrument, Country/Place

Key relationships: released, hasTrack, hasGenre, subgenreOf, memberOf, playsInstrument, producedBy, influencedBy, collaboratedWith, wonAward, signedTo, countryOfOrigin, compositionDate, releaseDate

Data sources: MusicBrainz (structured, JSON), Discogs (structured, JSON), Wikipedia (textual)

TASK:
Generate 10 competency questions that our knowledge graph must be able to answer via SPARQL queries. These must COMPLEMENT (not duplicate) the following 10 manually-created CQs:

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

Here are 3 examples of the style and complexity expected:
- "Which artists from a given country have won a specific award?" (requires: Artist → countryOfOrigin → Country + Artist → wonAward → Award)
- "What is the chain of influence between two artists across different genres?" (requires: Artist → influencedBy → Artist, transitive + hasGenre)
- "Which record labels were most active in a given genre during a specific decade?" (requires: Artist → signedTo → Label + hasGenre + releaseDate filtering)

REQUIREMENTS:
- Cover relationships and entities that the manual CQs miss (especially: record labels, collaborations, influence chains, geographic spread, temporal evolution)
- At least 3 questions should require joins across 3+ entity types
- Each question must be answerable with SPARQL over our ontology
- Include the relationship path for each CQ (e.g., Artist → property → Entity)
- No duplicates or simple rewordings of the manual CQs

Return: numbered list with CQ + relationship path for each.
```
- **Prompt design justification**:
  - **Role-based**: Assigned dual expertise (knowledge engineer + music historian) to produce questions that are both technically queryable and historically meaningful.
  - **Few-shot**: Provided 3 example CQs with explicit relationship paths to set the expected format and complexity level. Examples were chosen to demonstrate multi-entity joins and the types of gaps (awards + geography, influence chains, labels + temporal) the LLM should fill.
  - **Constrained output**: Explicitly listed which entities/relationships the manual CQs miss (record labels, collaborations, influence chains, geographic spread, temporal evolution) to direct the LLM toward complementary coverage. Required relationship paths for each CQ to ensure they're SPARQL-implementable.
  - **Context**: Included the full entity model from the team meeting (MusicalWork hierarchy, Artist hierarchy) and the 10 manual CQs so the LLM could identify genuine gaps rather than duplicating existing coverage.
- **Result summary**: Generated 10 CQs with relationship paths:
  1. Which artists from a given country have won a specific award? (Artist → countryOfOrigin + wonAward)
  2. What is the chain of influence between two artists across different genres? (Artist → influencedBy, transitive + hasGenre)
  3. Which record labels were most active in a given genre during a specific decade? (Artist → signedTo + released → hasGenre + releaseDate)
  4. Which artists have collaborated across different genres? (Artist → collaboratedWith + hasGenre, filter different)
  5. What instruments are most commonly associated with a given genre? (Artist → playsInstrument + hasGenre)
  6. Which bands have had members from more than one country? (Band ← memberOf ← Artist → countryOfOrigin, count distinct > 1)
  7. Which record labels has a given artist been signed to, and what albums released under each? (Artist → signedTo + released + releaseDate)
  8. Which composers influenced artists in a genre different from their own? (Composer ← influencedBy ← Artist, filter different genres)
  9. Which artists who won a given award were signed to the same record label? (Artist → wonAward + signedTo, group by label)
  10. How has the geographic spread of a genre changed over time? (MusicalWork → hasGenre + releaseDate + Artist → countryOfOrigin, group by decade/country)
- **Coverage analysis**: Record labels (CQs 3, 7, 9), Collaborations (CQ 4), Influence chains (CQs 2, 8), Geographic spread (CQs 1, 6, 10), Temporal evolution (CQs 3, 10). 8 of 10 require 3+ entity joins.
- **Used in**: Competency questions (LLM-augmented set), SPARQL query design

---

## P6 — LLM CQ Refinement (Iterative)

- **Task**: Competency question refinement (LLM-augmented) — fixing issues from P5
- **Date**: 2026-03-27
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: Iterative refinement + Chain-of-thought
- **Prompt**:
```
Review the 10 competency questions you generated and refine them. Think step by step about each one:

ISSUES TO FIX:
1. CQs 1, 2, and 3 are too similar to the examples I provided in the prompt. Replace them with genuinely new questions that still cover awards + geography, influence chains, and record labels but from a different angle.

2. Some CQs use vague aggregations ("most active", "most commonly associated") that are hard to express in SPARQL. Rephrase these as concrete, specific questions. For example, instead of "most active label in a genre", ask "which labels released more than N albums in a given genre?"

3. None of the CQs address the distinction between MusicalWork (a composition) and its Recordings/Albums. Our ontology covers classical compositions that were written centuries before being recorded. Add at least one CQ that tests this relationship, e.g., the relationship between a composer, a composition date, and later recordings.

4. For each revised CQ, verify that:
   - It does NOT duplicate any of the 10 manual CQs
   - It tests a DIFFERENT relationship path from every other LLM CQ
   - It can be answered with a concrete SPARQL SELECT or COUNT query
   - The relationship path is explicitly stated

Return the revised numbered list with CQ + relationship path for each.
```
- **Prompt design justification**:
  - **Iterative refinement** (from past CW Prompts 4, 10): Rather than regenerating from scratch, the prompt identifies specific issues and asks the LLM to fix them while preserving what worked. This is more efficient and produces higher quality than re-prompting.
  - **Chain-of-thought** (from past CW Prompt 3): "Think step by step about each one" encourages the LLM to evaluate each CQ individually rather than batch-replacing.
  - **Issue 1** was identified because the LLM simply copied the 3 few-shot examples from the original prompt instead of generating new questions — a known limitation of few-shot prompting.
  - **Issue 2** targeted vague language ("most active", "most commonly") that would produce ambiguous SPARQL. The fix guided the LLM toward concrete query patterns (SELECT, COUNT, HAVING, FILTER).
  - **Issue 3** incorporated the team's meeting discussion about classical compositions and the MusicalWork→Recording distinction, ensuring the LLM CQs cover this domain-specific requirement.
  - **Issue 4** added a verification checklist to force the LLM to self-validate each CQ against explicit criteria.
- **Result summary**: All 10 CQs revised successfully:
  1. Which award-winning artists were signed to a given record label? (Award + Label)
  2. Which artists that influenced a given artist also share at least one common genre? (Influence + shared Genre)
  3. Which record labels have released albums in more than N distinct genres? (Label → genre diversity, COUNT + HAVING)
  4. Which artists have collaborated with artists from a different country? (Collaboration + cross-country, FILTER)
  5. Which instruments appear in tracks of a given genre? (Track–Genre–Instrument)
  6. Which bands have members originating from more than one country? (Band–Member–Country, COUNT + HAVING)
  7. Which record labels has a given artist been signed to, and what albums released under each? (Artist–Label–Album timeline)
  8. Which composers have had their compositions recorded by artists from a different country? (Composer–Composition–Recording–Country, 4-entity join — tests the composition→recording distinction)
  9. Which artists who won a given award have collaborated with each other? (Award + Collaboration self-join)
  10. In which countries were artists active who released albums in a given genre during a given decade? (Genre–Decade–Country spread, 4-entity join)
- **Verification**: All 10 confirmed: no duplicates with manual CQs, unique relationship paths, concrete SPARQL patterns, 8 of 10 require 3+ entity joins. CQ8 specifically addresses the MusicalWork composition→recording distinction.
- **Used in**: Final LLM-augmented competency questions, SPARQL query design

---

## P7 — Data Source Evaluation

- **Task**: Data source evaluation and selection
- **Date**: 2026-03-27
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude (Opus 4.6) — used to identify candidate sources and design evaluation queries
- **Prompt**: "are these the best data sources? should we search a few extra ones and evaluate them to choose?" followed by "yes. look for artists for different genres, classical, jazz, rock, brazilian, african"
- **Prompt design justification**: The initial data source selection (P2) was done before experimentation. After completing 6 experiments, we revisited the choice to (1) evaluate sources we hadn't tested (Wikidata SPARQL, DBpedia, Open Opus), (2) test coverage across diverse genres and regions (not just Western rock/pop), and (3) document the selection process for the report. The evaluation used 5 test artists spanning Classical (Beethoven), Jazz (Miles Davis), Rock (David Bowie), Brazilian (Tom Jobim), and African (Fela Kuti) music.
- **Result summary**: Evaluated 6 sources total. Added Wikidata SPARQL as a primary structured source (awards, instruments, influences, labels already in RDF). Rejected DBpedia (redundant, noisy). Noted Open Opus as classical-only supplement. Confirmed MusicBrainz has good coverage of non-Western artists (Fela Kuti: NG, Tom Jobim: BR, Miriam Makeba: ZA, Youssou N'Dour: SN all found with cross-references). Key insight: Wikidata eliminates the need for LLM text extraction of awards, instruments, influences, and labels — these are already structured.
- **Used in**: Final data source selection (3 structured + 1 text), pipeline architecture revision

---

## P8 — LLM Text Extraction: David Bowie

- **Task**: Triple extraction from Wikipedia text (text mapping pipeline)
- **Date**: 2026-03-29
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: Role-based + Constrained output
- **Prompt**: See `pipeline/sparql_anything/` — structured prompt with 8 predicate types, explicit "Do NOT extract" list for data already in structured sources (birth/death, awards, instruments, labels, country). Input: David Bowie Wikipedia intro (3,051 chars).
- **Prompt design justification**: The prompt was designed to complement structured data sources by extracting only narrative facts not available in MusicBrainz, Discogs, or Wikidata. The "Do NOT extract" section prevents duplication with Wikidata (which already provides awards, instruments, influences, and labels). Focused predicates (collaboratedWith, hasGenre, alterEgo, albumGrouping, etc.) target information unique to text.
- **Result summary**: 24 triples extracted — 11 albums released, 4 genres (including "plastic soul" and "jungle" not in structured sources), 3 album groupings (Berlin Trilogy), 2 collaborations (Brian Eno, Queen), 1 band membership (Tin Machine), 1 alter ego (Ziggy Stardust). All triples are factually correct.
- **Used in**: Text mapping pipeline, KG enrichment with narrative facts

---

## P9–P13 — LLM Text Extraction: Batch (5 artists)

- **Task**: Triple extraction from Wikipedia text (text mapping pipeline)
- **Date**: 2026-03-29
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: Role-based + Constrained output (same template as P8, adapted per artist)
- **Artists processed**: The Beatles, Ludwig van Beethoven, Fela Kuti, Quincy Jones, Antônio Carlos Jobim (Tom Jobim)
- **Prompt design justification**: Same template as P8 with minor predicate additions per artist type — `hasMember` added for bands, `composed`/`hasMusicalPeriod`/`influencedBy` for classical composers, `produced` for producers, `pioneerOf`/`founded` for genre innovators. Each prompt was tailored to the predicates most likely present in that artist's text.
- **Results summary**:
  - **The Beatles** (P9): 24 triples — 4 members, 7 genres (skiffle, beat, psychedelia, hard rock, folk, Indian music), 6 albums, producedBy George Martin, Lennon→Quarrymen membership, Lennon-McCartney collaboration
  - **Beethoven** (P10): 19 triples — 2 musical periods (Classical, Romantic), 4 influences (Haydn, Mozart, Neefe, his father), 12 compositions with dates (symphonies, concertos, opera, quartets)
  - **Fela Kuti** (P11): 7 triples — Afrobeat genre, Africa '70 membership, Tony Allen as member, founded Kalakuta Republic, Afrobeat's roots in West African music + funk + jazz
  - **Quincy Jones** (P12): 18 triples — jazz/pop genres, produced 4 albums (Off the Wall, Thriller, Bad, We Are the World), composed 7 film scores, collaboratedWith 4 artists (Sinatra, Basie, Lesley Gore, Michael Jackson)
  - **Tom Jobim** (P13): 11 triples — bossa nova/samba/cool jazz genres, pioneerOf bossa nova, composed The Girl from Ipanema, collaboratedWith 3 artists (Getz, Gilberto, Sinatra), 3 albums
- **Total**: 79 triples from 5 artists (avg 15.8 per artist)
- **Used in**: Text mapping pipeline, KG enrichment with narrative facts

---

## P14 — RAG: Producer Gap Resolution

- **Task**: KG Completion — filling missing producer relationships using RAG
- **Date**: 2026-03-30
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: RAG (Retrieval Augmented Generation) — KG-enriched prompt (Week 11)
- **Retrieval step**: SPARQL query against the KG to retrieve Michael Jackson's album list and existing producer data
- **SPARQL query used**:
```sparql
SELECT ?albumTitle ?releaseDate WHERE {
    ?artist rdfs:label "Michael Jackson" .
    ?artist mh:released ?album .
    ?album dc:title ?albumTitle .
    OPTIONAL { ?album mh:releaseDate ?releaseDate }
}
```
- **Prompt**:
```
You are a music historian helping to complete a knowledge graph. Our KG contains Michael Jackson's discography but is missing producer information for most albums.

CONTEXT FROM OUR KNOWLEDGE GRAPH:
Michael Jackson's albums:
- Got to Be There (1972), Ben (1972), Off the Wall (1979), Thriller (1982), Bad (1987), Dangerous (1991), HIStory (1995), Invincible (2001)

Our KG already knows that Quincy Jones produced Off the Wall, Thriller, and Bad.

TASK: For each album listed above, who was the primary producer?
Return as JSON: [{"album": "...", "producer": "...", "year": "..."}]
```
- **Prompt design justification**: This demonstrates the RAG pattern from Week 11 — retrieving structured context from the KG (album list + existing producer facts) and providing it to the LLM to fill specific gaps. The context grounds the LLM's response in our actual data, preventing hallucinated album titles and ensuring entity alignment. The "Our KG already knows" line tests whether the LLM confirms or contradicts existing data.
- **Result summary**: LLM confirmed Quincy Jones for Off the Wall/Thriller/Bad (matching existing KG data) and added new producers: Hal Davis (Got to Be There, Ben), Teddy Riley / Michael Jackson (Dangerous — flagged as uncertain), Michael Jackson (HIStory — flagged as uncertain), Rodney Jerkins (Invincible — flagged as uncertain). The LLM proactively flagged uncertainty for albums with multiple co-producers, recommending cross-referencing with AllMusic/Discogs before ingestion. This demonstrates responsible KG construction — not all LLM outputs should be automatically ingested.
- **RAG vs plain LLM comparison**: A plain prompt "Who produced Michael Jackson's albums?" would produce the same factual answers but without grounding in our specific album list. The RAG approach ensures: (1) we only ask about albums actually in our KG, (2) the LLM confirms/contradicts existing data, (3) the response maps directly to existing entities.
- **Used in**: KG Completion analysis, RAG strategy demonstration

---

## P15 — RAG: Producer Gap for David Bowie

- **Task**: KG Completion — filling missing producer relationships using RAG
- **Date**: 2026-03-30
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query retrieved 15 David Bowie albums with release dates from the KG
- **Result summary**: 15 producer assignments returned. Tony Visconti identified as primary producer for 8 albums (Berlin Trilogy + others), Ken Scott for 4 (Ziggy Stardust era), Mike Vernon for debut, Harry Maslin for Station to Station, Bowie self-produced Diamond Dogs. LLM flagged co-production credits and uncertainties.
- **Used in**: KG Completion, RAG demonstration

---

## P16 — RAG: Missing Country Data

- **Task**: KG Completion — filling missing country of origin using RAG
- **Date**: 2026-03-30
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query found 15 artists/groups in the KG missing `countryOfOrigin`
- **Result summary**: 14 of 15 resolved with country codes (1 ambiguous — "Apple" correctly flagged as needing disambiguation). Includes Bob Marley & The Wailers (JM), Black Hippy (US), Coro Yoruba y Tambores Batá (CU). LLM provided contextual notes explaining each entity (e.g., "Class Of '55" is a Sun Records reunion project).
- **Used in**: KG Completion, RAG demonstration

---

## P17 — RAG: Missing Genres for Influence Targets

- **Task**: KG Completion — filling missing genre data for artists in influence chains using RAG
- **Date**: 2026-03-30
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query found 10 artists who influenced others but had no genre data in the KG. For each, the query also retrieved the genres of the artists they influenced — providing the LLM with contextual clues.
- **Prompt design justification**: The KG context provides two signals: (1) who these artists influenced and (2) what genres those influenced artists play. The LLM uses this indirect evidence plus its parametric knowledge to infer the influencer's genres. This is a genuine RAG use case — the retrieval step provides context that a plain prompt would lack.
- **Result summary**: 10 artists assigned genres. Notable results: Jimi Hendrix (rock, hard rock, blues rock, psychedelic rock), Hank Williams (country, honky-tonk, gospel), Lata Mangeshkar (playback singing, classical Indian music, Bollywood), Carter Family (country, folk, gospel, old-time music). These genre assignments would improve CQ12 (influences sharing genres) from 74 to potentially 100+ results if ingested into the KG.
- **Used in**: KG Completion, RAG demonstration, CQ12 improvement

---

## P18 — RAG vs Plain LLM Comparison: Quincy Jones Awards

- **Task**: Evaluation — comparing RAG-enriched vs plain LLM answers
- **Date**: 2026-03-30
- **Author**: Lucas Perez Reis Lobo
- **LLM/Tool**: Claude
- **Prompting technique**: Two prompts — (1) plain zero-shot, (2) RAG with KG context from SPARQL query
- **Retrieval**: SPARQL query `SELECT ?artistName (COUNT(DISTINCT ?award) AS ?awardCount) WHERE { ?artist mh:wonAward ?award . ?artist rdfs:label ?artistName } GROUP BY ?artistName ORDER BY DESC(?awardCount) LIMIT 10`
- **Question**: "How many awards has Quincy Jones won, and what are the most notable ones?"
- **Results**:
  - **Plain LLM**: Answered 28 Grammys + 1 Emmy + 1 Tony + 2 honorary Oscars. Detailed and well-structured but no awareness of our KG data.
  - **RAG LLM**: Given our KG's claim of 34 awards, the LLM critically evaluated this number, identified a discrepancy (28 competitive Grammys + other awards = ~30, not 34), flagged uncertainty, and refused to fabricate missing awards to avoid "KG data corruption." Recommended cross-referencing with Wikidata and Recording Academy records.
- **Key finding**: The RAG approach discovered a potential **data quality issue** in our KG — the 34 award count from Wikidata may include both competitive and honorary awards, which the plain LLM wouldn't have caught because it doesn't know what our KG claims. This demonstrates that RAG is not just for filling gaps but also for **validating existing data**.
- **Translation of LLM transparency note**: "Critical warning for KG integrity: the number 34 is plausible but not verifiable solely from sources processed in this session. Inserting this value as 'true' without external cross-referencing would introduce untracked uncertainty into the graph. Strongly recommend a direct query to Wikidata or the Recording Academy before validating this field."
- **Used in**: Evaluation methodology (RAG vs plain LLM quality comparison), KG completion analysis

---

<!-- Add new entries below -->
