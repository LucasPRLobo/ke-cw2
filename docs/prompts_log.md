# Prompts Log

This document records all prompts used throughout the project and the knowledge engineering task they belong to.

## Format

For each prompt, record:
- **Task**: Which KE task this prompt was used forrompt was used **LLM/Tool**: Which LLM or tool was used
- **Prompt**: The exact prompt text
- **Result summary**: Brief description of the output/result
- **Used in**: Where the result was applied

---

## P1 — Ontology Research

- **Task**: Existing ontology discovery
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "Research existing ontologies related to music history and arts/cultural heritage that could be used in a knowledge graph project. I need at least 2 existing ontologies that can be extended with subclasses and subproperties."
- **Result summary**: Identified 4 candidate ontologies: Music Ontology (MO), CIDOC-CRM, DOREMUS, and Schema.org. Recommended MO + CIDOC-CRM as the two to extend, with concrete subclass/subproperty suggestions for each.
- **Used in**: Ontology selection, extension planning

---

## P2 — Data Source Research

- **Task**: Data source discovery
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "Research data sources for a music history knowledge graph. I need at least 1 textual source and 1 structured source. Search for: MusicBrainz API, Spotify API, Wikidata SPARQL, Discogs API, Last.fm API, Wikipedia, BBC Music."
- **Result summary**: Identified 5 structured sources (MusicBrainz, Wikidata, Discogs, Spotify, Last.fm) and 3 textual sources (Wikipedia, BBC Music, MusicBrainz annotations). Recommended MusicBrainz (structured) + Wikipedia (textual) + Discogs (structured) as primary sources.
- **Used in**: Data source selection, pipeline planning

---

## P3 — LLM-Augmented Competency Questions

- **Task**: Competency question generation (LLM-augmented)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "You are a knowledge engineer and Music historian expert, that aims to write 10 competency questions for a knowledge graph that aims to represent information in the Music history Domain. Our goal is to define questions that aim to demonstrate the scope of the ontology we will be designing and that will help guide the creation of the entire system. Provide an initial draft of the 10 questions, analyse them and then provide suggestions of how should we proceed."
- **Prompt design justification**: The prompt was designed to (1) assign domain expertise to the LLM to produce historically grounded questions, (2) request analysis of the output to ensure self-critique and quality, (3) complement the 10 manual CQs by covering gaps identified in the manual set — specifically: record label relationships (signedTo), collaborations (collaboratedWith), genre origins, transitive influence chains, temporal evolution, aggregation queries, and cross-genre analysis.
- **Result summary**: Generated 10 CQs covering cultural/historical context (genre origins, label activity, cross-genre collaboration), lineage/influence (influence chains, genre bridging), commercial/industry (label switching, cross-genre producers), geographic spread (venue diversity, genre diffusion), and structural queries (career span and genre evolution). Analysis confirmed all 12 entities and 17 properties are covered across the combined 20 CQs. Identified potential issues with temporal modelling (CQ6, CQ10) and suggested simplifications.
- **Used in**: Competency questions (LLM-augmented set), ontology requirements

---

## P4 — CQ Prompt Design (Context & Planning)

- **Task**: Planning the LLM-augmented competency question generation approach
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompt**: "ok lets start by drafting the 10 extra cqs. I will open a new conversation just to have that. I have some example prompts that use different prompting techniques from a different cw for cq that I will provide here so that you can help me tune them to this project. For every prompt and response I get from the llm I will send them here for you to log them. I think for an initial prompt we could sort of explain the requirements for the questions/best practices and bring in some of the suggestions we had from the meeting on the structure of the ontology"
- **Prompt design justification**: This was a context-setting prompt to plan the approach for generating the 10 LLM-augmented CQs. The goal was to (1) leverage prompting techniques from prior coursework (role-based, few-shot, chain-of-thought, constrained output) and adapt them for the music history domain, (2) incorporate decisions from the team meeting (entity model with MusicalWork and Artist hierarchies, full timeline scope, genres as classification system), and (3) ensure the generated CQs complement the 10 manual CQs by covering gaps in record labels, collaborations, influence chains, geographic spread, and temporal evolution.
- **Result summary**: Produced a structured prompt template combining role-based (knowledge engineer + music historian), few-shot (3 example CQs with relationship paths), and constrained output (explicit requirements about complementing manual CQs, format specification). The prompt was designed to be used in a separate conversation for clean context.
- **Used in**: Prompt design for P5

---

## P5 — LLM-Augmented Competency Questions (Final)

- **Task**: Competency question generation (LLM-augmented) — final version
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
- **LLM/Tool**: Claude (Opus 4.6) — used to identify candidate sources and design evaluation queries
- **Prompt**: "are these the best data sources? should we search a few extra ones and evaluate them to choose?" followed by "yes. look for artists for different genres, classical, jazz, rock, brazilian, african"
- **Prompt design justification**: The initial data source selection (P2) was done before experimentation. After completing 6 experiments, we revisited the choice to (1) evaluate sources we hadn't tested (Wikidata SPARQL, DBpedia, Open Opus), (2) test coverage across diverse genres and regions (not just Western rock/pop), and (3) document the selection process for the report. The evaluation used 5 test artists spanning Classical (Beethoven), Jazz (Miles Davis), Rock (David Bowie), Brazilian (Tom Jobim), and African (Fela Kuti) music.
- **Result summary**: Evaluated 6 sources total. Added Wikidata SPARQL as a primary structured source (awards, instruments, influences, labels already in RDF). Rejected DBpedia (redundant, noisy). Noted Open Opus as classical-only supplement. Confirmed MusicBrainz has good coverage of non-Western artists (Fela Kuti: NG, Tom Jobim: BR, Miriam Makeba: ZA, Youssou N'Dour: SN all found with cross-references). Key insight: Wikidata eliminates the need for LLM text extraction of awards, instruments, influences, and labels — these are already structured.
- **Used in**: Final data source selection (3 structured + 1 text), pipeline architecture revision

---

## P8 — LLM Text Extraction: David Bowie

- **Task**: Triple extraction from Wikipedia text (text mapping pipeline)
- **LLM/Tool**: Claude
- **Prompting technique**: Role-based + Constrained output
- **Prompt**: See `pipeline/sparql_anything/` — structured prompt with 8 predicate types, explicit "Do NOT extract" list for data already in structured sources (birth/death, awards, instruments, labels, country). Input: David Bowie Wikipedia intro (3,051 chars).
- **Prompt design justification**: The prompt was designed to complement structured data sources by extracting only narrative facts not available in MusicBrainz, Discogs, or Wikidata. The "Do NOT extract" section prevents duplication with Wikidata (which already provides awards, instruments, influences, and labels). Focused predicates (collaboratedWith, hasGenre, alterEgo, albumGrouping, etc.) target information unique to text.
- **Result summary**: 24 triples extracted — 11 albums released, 4 genres (including "plastic soul" and "jungle" not in structured sources), 3 album groupings (Berlin Trilogy), 2 collaborations (Brian Eno, Queen), 1 band membership (Tin Machine), 1 alter ego (Ziggy Stardust). All triples are factually correct.
- **Used in**: Text mapping pipeline, KG enrichment with narrative facts

---

## P9–P13 — LLM Text Extraction: Batch (5 artists)

- **Task**: Triple extraction from Wikipedia text (text mapping pipeline)
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
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query retrieved 15 David Bowie albums with release dates from the KG
- **Result summary**: 15 producer assignments returned. Tony Visconti identified as primary producer for 8 albums (Berlin Trilogy + others), Ken Scott for 4 (Ziggy Stardust era), Mike Vernon for debut, Harry Maslin for Station to Station, Bowie self-produced Diamond Dogs. LLM flagged co-production credits and uncertainties.
- **Used in**: KG Completion, RAG demonstration

---

## P16 — RAG: Missing Country Data

- **Task**: KG Completion — filling missing country of origin using RAG
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query found 15 artists/groups in the KG missing `countryOfOrigin`
- **Result summary**: 14 of 15 resolved with country codes (1 ambiguous — "Apple" correctly flagged as needing disambiguation). Includes Bob Marley & The Wailers (JM), Black Hippy (US), Coro Yoruba y Tambores Batá (CU). LLM provided contextual notes explaining each entity (e.g., "Class Of '55" is a Sun Records reunion project).
- **Used in**: KG Completion, RAG demonstration

---

## P17 — RAG: Missing Genres for Influence Targets

- **Task**: KG Completion — filling missing genre data for artists in influence chains using RAG
- **LLM/Tool**: Claude
- **Prompting technique**: RAG — KG as SPARQL-based retrieval source (Week 11)
- **Retrieval**: SPARQL query found 10 artists who influenced others but had no genre data in the KG. For each, the query also retrieved the genres of the artists they influenced — providing the LLM with contextual clues.
- **Prompt design justification**: The KG context provides two signals: (1) who these artists influenced and (2) what genres those influenced artists play. The LLM uses this indirect evidence plus its parametric knowledge to infer the influencer's genres. This is a genuine RAG use case — the retrieval step provides context that a plain prompt would lack.
- **Result summary**: 10 artists assigned genres. Notable results: Jimi Hendrix (rock, hard rock, blues rock, psychedelic rock), Hank Williams (country, honky-tonk, gospel), Lata Mangeshkar (playback singing, classical Indian music, Bollywood), Carter Family (country, folk, gospel, old-time music). These genre assignments would improve CQ12 (influences sharing genres) from 74 to potentially 100+ results if ingested into the KG.
- **Used in**: KG Completion, RAG demonstration, CQ12 improvement

---

## P18 — RAG vs Plain LLM Comparison: Quincy Jones Awards

- **Task**: Evaluation — comparing RAG-enriched vs plain LLM answers
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

## P19 — KG vs Plain LLM: David Bowie Awards (CQ8)

- **Task**: Evaluation — KG answer quality vs plain LLM
- **LLM/Tool**: Claude
- **Prompting technique**: Paired comparison (plain vs RAG)
- **KG answer**: 13 awards from SPARQL query
- **Plain LLM answer**: "73 awards from 188 nominations" — detailed breakdown of Grammys (6), BRITs (4), MTV VMAs (4), plus Rock and Roll Hall of Fame and Hollywood Walk of Fame
- **RAG answer**: Critically evaluated the KG's 13 results and found:
  1. **Factual error**: CBE listed as award won, but Bowie declined it — should be "honour declined"
  2. **Redundancy**: Commandeur des Arts et des Lettres and Ordre des Arts et des Lettres are the same distinction (grade within order)
  3. **Category confusion**: Rolling Stone's list and Great Britons are editorial rankings, not formal awards
  4. **Gaps**: Missing BRIT Awards, Ivor Novello Awards, competitive Grammys, posthumous awards
  5. **Recommendation**: Separate award types into `award won`, `award declined`, `honorary recognition`, `editorial ranking`
- **Comparison**:
  - Plain LLM: gives a confident number (73) with highlights — useful but ungrounded
  - RAG: identifies errors, redundancies, and category confusion in KG data — actionable for quality improvement
  - **Winner: RAG** — found a factual error (declined CBE), a redundancy, and a modelling issue (mixed award types)
- **Used in**: Evaluation section (KG vs plain LLM comparison)

---

## P20 — KG vs Plain LLM: John Lennon Instruments (CQ7)

- **Task**: Evaluation — KG answer quality vs plain LLM
- **LLM/Tool**: Claude
- **KG answer**: 7 instruments (bass guitar, guitar, harmonica, keyboard instrument, lead vocals, piano, voice)
- **Plain LLM answer**: Guitar (primary), harmonica, piano/keyboards, bass guitar (occasionally), banjo (childhood), percussion (informal). Notes he wasn't a virtuoso.
- **RAG answer**: Critically evaluated the KG's 7 results and found:
  1. **Accuracy concern**: bass guitar is questionable — McCartney was the bassist, Lennon rarely played it. May be a band→individual attribute conflation.
  2. **Redundancies**: "lead vocals"/"voice" are the same thing; "keyboard instrument"/"piano" overlap hierarchically
  3. **Gaps**: Missing rhythm guitar distinction, acoustic guitar, organ, mellotron, banjo, 12-string guitar
  4. **Recommendation**: remove bass guitar, collapse redundant pairs, add instrument specificity (rhythm vs lead guitar)
- **Comparison**:
  - Plain LLM: provides nuanced answer with context (banjo as first instrument, not virtuosic)
  - RAG: finds accuracy issue (bass guitar), redundancies, and suggests instrument granularity improvements
  - **Winner: RAG** — identifies a likely data error (bass guitar attribution) and modelling issues (redundant entries, insufficient specificity)
- **Key insight**: RAG reveals that the pipeline's instrument data from MusicBrainz conflates band-level and individual-level attributes, and that the ontology lacks granularity for instrument roles (rhythm vs lead guitar)
- **Used in**: Evaluation section (KG vs plain LLM comparison)

---

## P21 — KG vs Plain LLM: Rock Subgenres (CQ9)

- **Task**: Evaluation — KG answer quality vs plain LLM
- **LLM/Tool**: Claude
- **KG answer**: 40 subgenres (truncated display at 20)
- **Plain LLM answer**: ~30 subgenres organised by decade (1950s-2000s), with note about fluid boundaries
- **RAG answer**: Critically evaluated the KG's results and found:
  1. **Non-subgenre entries**: "acoustic" (production mode), "ballad" (song format), "interview" (data artifact), "country" (parent genre, not subgenre)
  2. **Category confusion**: "classic rock" is a radio format, not a subgenre; "experimental"/"avantgarde" are aesthetic modifiers, not genres
  3. **Data artifact**: "interview" leaked from content-type tags into genre taxonomy
  4. **Query truncation**: results stopped alphabetically at "krautrock" — suggests result limit was hit, missing punk, metal, progressive rock
  5. **Gaps**: punk rock, heavy metal, progressive rock, psychedelic rock, post-punk, new wave, shoegaze, britpop — all fundamental rock subgenres missing
  6. **Recommendation**: remove non-genre entries, reclassify borderline entries, fix query pagination
- **Comparison**:
  - Plain LLM: comprehensive, well-organised by decade, but generic (not grounded in our data)
  - RAG: found data artifacts ("interview"), category errors ("acoustic", "ballad"), truncation issue, and structural recommendations
  - **Winner: RAG** — identifies a data pipeline issue (content-type tags leaking into genre taxonomy), a query issue (truncation), and multiple modelling improvements
- **Key insight**: RAG reveals that the Discogs genre/style mapping introduced non-genre tags into the subgenre hierarchy, and that the SPARQL query's result display was truncated (the underlying data likely has more subgenres)
- **Used in**: Evaluation section (KG vs plain LLM comparison)

---

## P22 — KG vs Plain LLM: Bowie Influences + Shared Genres (CQ12)

- **Task**: Evaluation — KG answer quality vs plain LLM
- **LLM/Tool**: Claude
- **KG answer**: 13 results — Bob Dylan (3 genre matches) + The Beatles (10 genre matches)
- **Plain LLM answer**: ~15 influences organised by category (rock, soul, electronic, cabaret) with genre overlap analysis. Notes Bowie's chameleon nature.
- **RAG answer**: Critically evaluated and found:
  1. **Query design issue**: returns artist × genre cartesian product (Bob Dylan 3×, Beatles 10×) instead of distinct artists — query should GROUP BY artist
  2. **Content truncation**: only 2 artists returned, likely alphabetical cutoff — missing 10+ documented influences (Iggy Pop, Lou Reed, Marc Bolan, Little Richard, Kraftwerk, Brian Eno)
  3. **Genre taxonomy**: "classic rock" is a radio format, not a musical subgenre — inflates false matches
  4. **Accuracy**: Bob Dylan and The Beatles as influences are correct; genre overlaps are genuine
  5. **Recommendation**: restructure query to return distinct artists, raise result cap, remove format-classification terms from genre matching
- **Comparison**:
  - Plain LLM: rich, contextual, covers ~15 influences with genre analysis and cultural context
  - RAG: identifies query architecture problem (cartesian product), truncation, and taxonomy issues — actionable for both query and ontology improvement
  - **Winner: RAG for diagnostics, Plain LLM for answer quality** — RAG excels at finding structural issues in the KG/query layer; plain LLM provides better factual coverage
- **Key insight**: RAG reveals that the SPARQL query design (not just the data) needs improvement — the cartesian product between artists and genres obscures the real answer. This is a modelling insight that only emerges when the LLM can see the actual query results.
- **Used in**: Evaluation section (KG vs plain LLM comparison), query improvement recommendations

---

## P23 — KG vs Plain LLM: Jazz Countries in 1960s (CQ20)

- **Task**: Evaluation — KG answer quality vs plain LLM
- **LLM/Tool**: Claude
- **KG answer**: 5 countries (US, NG, ES, ZA, BR) as ISO codes
- **Plain LLM answer**: ~15 countries with detailed per-country analysis (US, UK, France, Germany, Scandinavia, Brazil, Japan, South Africa, Nigeria, Cuba, Canada, Argentina, Soviet Union/Eastern Europe)
- **RAG answer**: Critically evaluated and found:
  1. **Presentation issue**: ISO country codes without labels (NG, ZA, ES, BR) — opaque to non-specialists
  2. **Accuracy check**: US, BR, ZA, NG are defensible; ES (Spain) is the most questionable — may reflect a specific artist rather than broad jazz presence
  3. **Severe truncation**: only 5 of ~15 significant jazz countries — missing UK, France, Germany, Japan, Sweden, Denmark, Cuba, Canada, Argentina
  4. **Structural concern**: 5 countries for a global genre across a decade signals either query truncation, overly narrow "jazz" tagging, or sparse data coverage outside the US
  5. **Modelling issue**: graph may be conflating artist nationality with album release country — these are meaningfully different
  6. **Recommendation**: add country name labels, raise result limit, audit jazz genre tagging criteria, distinguish nationality from release country
- **Comparison**:
  - Plain LLM: comprehensive, ~15 countries with cultural context, decade-spanning analysis
  - RAG: identifies presentation problems (ISO codes), data sparsity, possible genre tagging issue, and nationality/release conflation
  - **Winner: Plain LLM for factual completeness, RAG for KG diagnostics** — the KG has only 58 artists so it cannot match the LLM's breadth, but RAG explains *why* the gap exists
- **Key insight**: RAG reveals that our KG's 58-artist sample creates an inherent coverage limitation for geographic queries — we can only return countries where our specific artists are from, not where jazz was historically active. This is a fundamental population completeness (CM3) issue.
- **Used in**: Evaluation section (KG vs plain LLM comparison), completion analysis

---

## P24–P28 — LLM Text Extraction: Batch 2 (5 artists)

- **Task**: Triple extraction from Wikipedia text — expanding coverage for sparse properties
- **LLM/Tool**: Claude
- **Prompting technique**: Role-based + Constrained output (same template as P8, with expanded predicate list)
- **Text source**: Wikipedia MediaWiki API intro text, cached by the pipeline in `pipeline/data/text/wikipedia_*.json`. Each text was fetched via `sources/wikipedia.py` using the cross-reference chain: MusicBrainz → Wikidata ID → Wikipedia sitelinks → Wikipedia article title → MediaWiki API `action=query&prop=extracts&explaintext=True&exintro=True`.
- **Artists processed**: Miles Davis (P24), Elvis Presley (P25), Bob Marley (P26), Freddie Mercury (P27), Nina Simone (P28)
- **Prompt design justification**: These 5 artists were selected to populate sparse properties identified in the KG audit: `producedBy` (1 triple), `alterEgo` (1), `pioneerOf` (1), `founded` (1), `hasMusicalPeriod` (2), `albumGrouping` (3). The prompt was expanded from P8 to include `pioneerOf`, `hasMusicalPeriod`, `founded`, and `performedAt` predicates specifically to target these gaps. The "Do NOT extract" list prevents duplication with Wikidata structured data (awards, instruments, labels, country).
- **Results**:
  - **Miles Davis** (P24): 29 triples — 7 genres (jazz, bebop, cool jazz, hard bop, modal jazz, post-bop, jazz fusion), 6 pioneerOf, 2 collaborations (Charlie Parker, Dizzy Gillespie), 5 albums, 2 quintet memberships, 1 musicalPeriod (bebop movement)
  - **Elvis Presley** (P25): 13 triples — 1 alterEgo (King of Rock and Roll), 1 pioneerOf (rockabilly), 4 genres, 4 releases, 3 performedAt (comeback special, Las Vegas, Aloha from Hawaii)
  - **Bob Marley** (P26): 17 triples — 1 pioneerOf (reggae), 3 genres (reggae, ska, rocksteady), 1 founded (Bob Marley and the Wailers), 2 memberOf, 7 releases, 1 performedAt (One Love Peace Concert)
  - **Freddie Mercury** (P27): 17 triples — 1 alterEgo (Farrokh Bulsara), 1 memberOf (Queen), 2 genres, 5 Queen releases, 4 collaborations (Montserrat Caballé, Brian May, Roger Taylor, John Deacon), 3 Queen member assertions
  - **Nina Simone** (P28): 17 triples — 2 alterEgo (Eunice Kathleen Waymon, High Priestess of Soul), 7 genres, 1 hasMusicalPeriod (civil rights movement), 7 releases
- **Total new triples**: 93 across 5 artists
- **Sparse properties populated**: pioneerOf (8 new), alterEgo (4 new), hasMusicalPeriod (2 new), performedAt (4 new), founded (1 new)
- **Used in**: Text mapping pipeline, populating sparse properties for CW1 counter-example requirement

---

## P29–P33 — LLM Text Extraction: Batch 3 (targeted sparse property population)

- **Task**: Triple extraction targeting `producedBy`, `albumGrouping`, `founded`, `alterEgo`
- **LLM/Tool**: Claude
- **Prompting technique**: Role-based + Constrained output with targeted emphasis ("Focus ESPECIALLY on: producedBy, albumGrouping...")
- **Text source**: Wikipedia MediaWiki API intro text, cached by the pipeline in `pipeline/data/text/wikipedia_*.json`. Cross-reference chain: MusicBrainz → Wikidata ID → Wikipedia sitelinks → MediaWiki API.
- **Artists processed**: Johnny Cash (P29), Led Zeppelin (P30), Nirvana (P31), Bob Dylan (P32), John Lennon (P33)
- **Prompt design justification**: These 5 artists were specifically selected because their Wikipedia texts mention: (1) famous producers (Rick Rubin→Cash, Jimmy Page→Led Zep, Butch Vig/Steve Albini→Nirvana), (2) named album groupings (American Recordings series), (3) founding of bands/organisations (Beatles, Plastic Ono Band). The prompts used "Focus ESPECIALLY on" directive to prioritise these sparse predicates over generic genre/release data.
- **Results**:
  - **Johnny Cash** (P29): 27 triples — 1 alterEgo (The Man in Black), 6 genres, 6 releases, 6 producedBy (all Rick Rubin), 6 albumGrouping (American Recordings series), 2 collaborations
  - **Led Zeppelin** (P30): 27 triples — 4 hasMember + 4 memberOf, 7 genres, 6 releases, 6 producedBy (all Jimmy Page)
  - **Nirvana** (P31): 19 triples — 4 hasMember + 4 memberOf, 3 genres, 1 pioneerOf (alternative rock), 4 releases, 3 producedBy (Jack Endino, Butch Vig, Steve Albini)
  - **Bob Dylan** (P32): 15 triples — 2 alterEgo (Robert Allen Zimmerman, Robert Dylan), 1 hasMusicalPeriod (1960s), 3 genres, 7 releases, 1 collaboratedWith (The Band), 1 performedAt (1965 Newport Folk Festival)
  - **John Lennon** (P33): 14 triples — 2 alterEgo (birth names), 2 founded (Beatles, Plastic Ono Band), 2 memberOf, 5 releases, 2 collaboratedWith (McCartney, Yoko Ono)
- **Total new triples**: 102 across 5 artists
- **Impact on sparse properties**:
  - `producedBy`: 1 → **15** (+14)
  - `albumGrouping`: 3 → **9** (+6)
  - `alterEgo`: 5 → **9** (+4)
  - `hasMember`: 5 → **13** (+8)
  - `founded`: 2 → **5** (+3)
  - `ProducerArtist` defined class: 2 → **7** instances
- **Used in**: Text mapping pipeline, addressing CW1 counter-example feedback

---

## P34 — RAG Completion: O1 — signedTo Temporal Scoping

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: O1 — `signedTo` has no temporal scoping (which label when?)
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT DISTINCT ?artistName ?labelName WHERE {
    ?artist foaf:name ?artistName .
    ?artist mh:signedTo ?label .
    ?label rdfs:label ?labelName .
}
ORDER BY ?artistName ?labelName
```
- **SPARQL results**: 226 artist-label pairs across 47 artists, all lacking temporal information
- **Verbalised context** (excerpt): "Aretha Franklin was signed to: Arista Records, Atlantic Records, Battle Records, Checker, Columbia Records, RCA, Warner Music Group" — repeated for all 47 artists
- **RAG prompt**: "You are a music historian helping to complete a knowledge graph about music history. CONTEXT FROM OUR KNOWLEDGE GRAPH: [47 artists with 226 signedTo relationships, no temporal data — full verbalised list]. TASK: Our KG has 226 signedTo relationships but none have temporal scoping. For each artist-label pair, provide approximate year ranges (start_year, end_year). If ongoing, use 'present'. Flag confidence level. Return as JSON: [{\"artist\": \"...\", \"label\": \"...\", \"start_year\": ..., \"end_year\": ..., \"confidence\": \"high/medium/low\"}]"
- **Result summary**:
  - LLM provided temporal ranges for all 226 pairs across 47 artists
  - **Confidence breakdown**: 104 high (46%), 77 medium (34%), 45 low (19%)
  - High-confidence results include well-documented signings: Aretha Franklin→Columbia (1960–1966), Beatles→Parlophone (1962–1970), Nirvana→Sub Pop (1988–1989), Johnny Cash→Sun Records (1955–1958)
  - Low-confidence results tend to be: obscure regional labels (Dominguinhos→Warner Music Brasil), reissue/compilation labels (Charly Records, Collectables), and early career singles (Aretha Franklin→Battle Records)
- **Evaluation**:
  - **What can be added**: The 104 high-confidence temporal ranges could be modelled using RDF reification or named graphs — e.g., `mh:signedTo_Statement` with `mh:startYear` and `mh:endYear` qualifiers. This would resolve CQ17's cartesian product issue
  - **What needs validation**: The 77 medium-confidence pairs need cross-referencing with Wikidata P264 qualifiers. The 45 low-confidence pairs should be verified against discography databases
  - **Modelling recommendation**: Use RDF reification pattern (statement nodes with temporal qualifiers) rather than adding new triples directly, as the temporal data qualifies an existing relationship
  - **Data quality issues discovered**:
    1. **Duplicate label entities**: "RCA" vs "RCA Records" (David Bowie, Dolly Parton), "EMI" vs "EMI Records" (Queen) — get identical temporal ranges, indicating entity duplication in the KG that should be resolved
    2. **Reissue labels**: Legacy Recordings, Charly Records, Collectables Records are reissue/compilation labels, not primary signings — temporal scoping is less meaningful for these
    3. **Parent/subsidiary overlap**: Sony Music vs Epic Records, Warner Bros vs Warner Music Group — overlapping periods are expected (subsidiary under parent)
  - **Key insight**: The RAG approach excels here because the LLM can reason about the temporal ordering of label relationships using its parametric knowledge while being grounded in the specific artist-label pairs that actually exist in our KG. A plain LLM prompt would not know which of the many possible labels are actually in our graph
- **Output file**: `docs/rag_responses/o1_signedto_temporal.json`
- **Used in**: Completion analysis (O1 gap), demonstrates RAG for temporal qualification of existing relationships

---

## P35 — RAG Completion: O2 — performedAt Sparse Population

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: O2 — `performedAt` sparsely populated (5 triples covering only 3 artists)
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?artistName ?venueName WHERE {
    ?artist mh:performedAt ?venue .
    ?artist foaf:name ?artistName .
    ?venue rdfs:label ?venueName .
}
ORDER BY ?artistName
```
- **SPARQL results**: 5 performedAt triples — Bob Dylan → 1965 Newport Folk Festival, Bob Marley → One Love Peace Concert, Elvis Presley → Aloha from Hawaii, Elvis Presley → Elvis (television comeback special), Elvis Presley → Las Vegas concert residency
- **Verbalised context**: "Our KG has only 5 performedAt triples across 3 of 58 artists. [list of 5 triples]. For each of these 58 primary artists, what are their 2-3 most iconic or historically significant live performances?"
- **RAG prompt**: The prompt provided KG context (the 5 existing triples + full list of 58 artists) and asked for 2-3 iconic performances per artist as JSON. Instructions: only include well-documented events; skip non-performing artists (producers like Rick Rubin, George Martin); skip classical composers where specific live performances are not well-documented
- **Result summary**:
  - **113 performance events** across **43 artists** (from 5 triples / 3 artists)
  - **110 new events** not already in KG; 3 confirm existing triples
  - **15 artists skipped** — appropriately: 6 classical composers (Vivaldi, Bach, Mozart, Beethoven, Chopin, Tchaikovsky, Verdi, Hildegard), 2 producers (Rick Rubin, George Martin), 2 niche artists (Dominguinhos, Luiz Gonzaga), Brian Eno (studio artist), Cesária Évora, Quincy Jones
  - **Decade distribution**: 1960s (26), 1970s (24), 1980s (20), 1990s (15), 2000s (8), 2010s (9) — good temporal spread
- **Evaluation**:
  - **High confidence events** (well-documented, widely known): Live Aid 1985 (Queen, David Bowie), The Beatles at Shea Stadium 1965, Nirvana MTV Unplugged 1993, Michael Jackson moonwalk at Motown 25 1983, Woodstock (Ravi Shankar), Concert for Bangladesh 1971
  - **Medium confidence** (documented but dates/details may need verification): Hermeto Pascoal at Jabour concerts, Fela Kuti at The Shrine, Umm Kulthum Thursday radio concerts, some festival years
  - **What can be added**: Most events are historically iconic and verifiable. This would increase `performedAt` from 5 to ~115 triples, a 22× increase, covering 43 vs 3 artists
  - **What needs validation**: Specific years for some events (e.g., Dolly Parton's Grand Ole Opry debut year, Duke Ellington Cotton Club start year). Cross-reference with Setlist.fm or Wikipedia for exact dates
  - **Modelling note**: Some entries are events (Live Aid), some are venues (Carnegie Hall), some are TV shows (Ed Sullivan Show). The `Venue` class may need to be generalised to `PerformanceEvent` or the existing class used flexibly
  - **Key insight**: The LLM appropriately self-filtered — skipping classical composers (no documented "concerts" in the modern sense), producers, and studio-focused artists. This demonstrates responsible RAG: the LLM understands the semantic gap between "composed music performed in churches/courts" (Bach, Mozart) and "performed at a venue/event" in the popular music sense
- **Output file**: `docs/rag_responses/o2_performedat_events.json`
- **Used in**: Completion analysis (O2 gap), demonstrates RAG for populating sparse properties

---

## P36 — RAG Completion: O3 — collaboratedWith Direct Artist↔Artist Links

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: O3 — `collaboratedWith` modelled indirectly via band/project entities, not direct artist↔artist links
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT DISTINCT ?name1 ?name2 WHERE {
    ?a1 mh:collaboratedWith ?a2 .
    { ?a1 foaf:name ?name1 } UNION { ?a1 rdfs:label ?name1 }
    { ?a2 foaf:name ?name2 } UNION { ?a2 rdfs:label ?name2 }
    FILTER(STR(?name1) < STR(?name2))
}
ORDER BY ?name1 ?name2
```
- **SPARQL results**: 39 unique collaboration pairs. Many link to group/project entities (Band Aid, USA for Africa, The Million Dollar Quartet, Charlie Parker Quintet) rather than direct artist↔artist relationships. The prompt listed all 39 pairs as context so the LLM could avoid duplication
- **Verbalised context**: "Our KG has 39 collaboratedWith pairs, but many are indirect — artist linked to a band/project entity rather than directly to another artist. [full list of 39 pairs]. For each of these 58 primary artists, what are their most notable direct collaborations with other individual artists?"
- **RAG prompt**: Asked for direct artist↔artist collaborations as JSON with project/work description and year. Instructed to skip classical composers, avoid duplicating existing pairs, and only include well-documented collaborations
- **Result summary**:
  - **75 collaboration entries** covering **70 unique pairs** across **37 primary artists**
  - **69 new pairs** not already in the KG (from existing 39 pairs)
  - **18 cross-primary collaborations** — both artists already exist in the KG (e.g., Duke Ellington↔John Coltrane, Frank Sinatra↔Antônio Carlos Jobim, David Bowie↔John Lennon, Bob Dylan↔Johnny Cash, Peter Gabriel↔Youssou N'Dour, Miles Davis↔John Coltrane)
  - **53 external collaborators** — new artist entities not yet in the KG (e.g., George Harrison, Eric Clapton, Art Garfunkel, Dr. Dre, Herbie Hancock, Thelonious Monk, Stevie Wonder)
- **Evaluation**:
  - **What can be added directly**: The 18 cross-primary pairs can be added immediately as `collaboratedWith` triples since both entities already exist in the KG. These are high-value because they densify the existing collaboration network
  - **What needs entity creation**: The 53 external collaborators would need new artist entities. Many of these (George Harrison, Eric Clapton, Herbie Hancock, Art Garfunkel) are well-known artists who could be created as secondary artist entities with the entity linking pipeline
  - **What needs validation**: A few entries are unusual — Nirvana↔William S. Burroughs (spoken word collaboration, technically correct but borderline), Nina Simone↔Langston Hughes (lyric collaboration, not musical performance), Led Zeppelin↔Roy Harper (loose association)
  - **Network density improvement**: Adding the 18 cross-primary pairs would create direct links where previously only indirect paths existed (e.g., Frank Sinatra is connected to Antônio Carlos Jobim only through "Tom Jobim e Orquestra" entity — the RAG identifies the direct Francis Albert Sinatra & Antonio Carlos Jobim album)
  - **Key insight**: RAG grounded in KG context allowed the LLM to (1) see which pairs already exist and avoid duplication, (2) focus on direct individual collaborations rather than band membership, and (3) provide the specific project/work that justifies the collaboration link, enabling traceability
- **Output file**: `docs/rag_responses/o3_collaborations_direct.json`
- **Used in**: Completion analysis (O3 gap), demonstrates RAG for densifying sparse relationship networks

---

## P37 — RAG Completion: O4 — founded Barely Represented

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: O4 — `founded` property barely represented (4 unique triples)
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?artistName ?orgName WHERE {
    ?artist mh:founded ?org .
    { ?artist foaf:name ?artistName } UNION { ?artist rdfs:label ?artistName }
    { ?org foaf:name ?orgName } UNION { ?org rdfs:label ?orgName }
}
ORDER BY ?artistName
```
- **SPARQL results**: 4 unique founded triples — Fela Kuti → Kalakuta Republic, John Lennon → Plastic Ono Band, John Lennon → The Beatles, Yoko Ono → Plastic Ono Band
- **Verbalised context**: "Our KG has only 4 founded triples across 3 artists. [list of 4 triples]. For each of these 58 primary artists, what bands, record labels, organisations, foundations, or companies did they found or co-found?"
- **RAG prompt**: Asked for founded organisations categorised by type (band, label, foundation, company, cultural_org) as JSON. Instructed to skip artists with no documented founding activity, avoid duplicating existing entries
- **Result summary**:
  - **47 founded entries** across **29 artists** (from 4 triples / 3 artists — a **12× increase**)
  - **All 47 are new** (not duplicating existing KG entries)
  - **29 artists skipped** — appropriately: classical composers (no organisations to found), artists with no documented founding activity
  - **By type**: 15 labels, 12 companies, 9 bands, 7 foundations, 4 cultural organisations
- **Evaluation**:
  - **High-value immediate additions (17)**: Organisations that already exist as entities in the KG — e.g., Bob Marley→Tuff Gong (label already in KG), Frank Sinatra→Reprise Records, Rick Rubin→Def Jam Recordings, Led Zeppelin→Swan Song Records, Peter Gabriel→Real World Records, The Beatles→Apple Records. These only need a `mh:founded` triple linking the existing artist to the existing entity
  - **New entities needed (30)**: Foundations (Dollywood Foundation, Heal the World Foundation, Mercury Phoenix Trust, WOMAD), production companies (MJJ Productions, AIR Studios, Daft Life Ltd.), and cultural organisations that would need to be created as new entities
  - **What needs validation**: Brian Eno→EG Records founding (he was signed to it, unclear if co-founder); David Bowie→MainMan (management company founded by Tony Defries, not Bowie); Yoko Ono→Fluxus (she was a participant, not a founder — George Maciunas founded Fluxus); Jean-Michel Jarre→Disques Dreyfus (Francis Dreyfus founded it, not Jarre)
  - **Key insight**: The RAG response surfaced a rich taxonomy of founding relationships beyond just bands — record labels (15), foundations (7), and cultural organisations (4) that the original KG modelling didn't anticipate. The `founded` property's range may need to be broadened from just `Organisation` to include `RecordLabel` and `Foundation` subclasses. Also, 17 of the 47 entries link to entities already in the KG (particularly record labels from `signedTo`), meaning those `founded` triples can be added with zero entity creation effort
- **Output file**: `docs/rag_responses/o4_founded_orgs.json`
- **Used in**: Completion analysis (O4 gap), demonstrates RAG for populating sparse properties and discovering entity type diversity

---

## P38 — RAG Completion: O5 — hasMusicalPeriod Limited to 3 Instances

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON) + domain context (artist dates and genres provided)
- **Gap addressed**: O5 — `hasMusicalPeriod` limited to 3 instances (5 triples)
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
SELECT ?artistName ?periodName WHERE {
    ?artist mh:hasMusicalPeriod ?period .
    { ?artist foaf:name ?artistName } UNION { ?artist rdfs:label ?artistName }
    ?period rdfs:label ?periodName .
}
ORDER BY ?artistName
```
- **SPARQL results**: 5 unique hasMusicalPeriod triples — Bob Dylan → 1960s, Ludwig van Beethoven → classical, Ludwig van Beethoven → romantic, Miles Davis → bebop movement, Nina Simone → civil rights movement
- **Verbalised context**: "Our KG has only 5 hasMusicalPeriod triples covering 3 artists. [list of 5 triples]. For each of these 58 primary artists, what musical period or historical era do they belong to?" The prompt also provided birth/death dates and genres for each artist to enable the LLM to make grounded period assignments
- **RAG prompt**: Asked for period assignments categorised by type (stylistic, cultural, temporal) as JSON. Instructed to use established musicological period names and allow multiple period assignments per artist
- **Result summary**:
  - **112 period assignments** across all **58 artists** (from 5 triples / 3 artists — a **22× increase**)
  - **74 unique periods** identified — rich temporal/stylistic taxonomy
  - **106 genuinely new** entries; 6 overlap with existing KG concepts (Classical, Romantic for other classical composers)
  - **By type**: 66 stylistic (59%), 40 cultural (36%), 6 temporal (5%)
  - **100% artist coverage** — every primary artist assigned at least one period
- **Evaluation**:
  - **Most connected periods**: World music revival (6 artists — Cesária Évora, Buena Vista Social Club, Paul Simon, Peter Gabriel, Miriam Makeba, Youssou N'Dour), Romantic (4 — Beethoven, Chopin, Verdi, Tchaikovsky), Counterculture era (4 — John Lennon, The Beatles, Ravi Shankar, Yoko Ono), British Invasion (3 — The Beatles, John Lennon, George Martin)
  - **High confidence**: Classical composers to their established periods (Baroque, Classical, Romantic, Medieval), well-defined movements (British Invasion, Harlem Renaissance, Punk rock era, Grunge era)
  - **Medium confidence**: Cultural/political period assignments (Pan-African movement for Fela Kuti, Egyptian nationalist movement for Umm Kulthum, Post-colonial Caribbean for Bob Marley) — musicologically defensible but more interpretive
  - **Key insight**: The LLM's period assignments create a rich cross-cutting taxonomy that connects artists across genre boundaries through shared temporal and cultural contexts. The "World music revival" period links artists from 5 different countries/genres, while "Counterculture era" links rock, classical Indian, and avant-garde artists. This kind of cross-genre, cross-cultural linking is exactly what the `hasMusicalPeriod` property was designed for but couldn't achieve with only 3 instances
  - **Modelling consideration**: 74 unique period names would need to be created as `MusicalPeriod` entities. Some could be consolidated (e.g., "Bebop era" vs existing "bebop movement"). A controlled vocabulary of ~40–50 canonical periods would be more practical
- **Output file**: `docs/rag_responses/o5_musical_periods.json`
- **Used in**: Completion analysis (O5 gap), demonstrates RAG for populating sparse properties with domain-specific classification

---

## P39 — RAG Completion: I1 — Secondary Artists Lack Genre/Country Data

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: I1 — 1,100+ secondary artists lack genre, country, and birthDate data
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT (COUNT(DISTINCT ?artist) AS ?total) WHERE {
    { ?artist a mo:SoloMusicArtist } UNION { ?artist a mo:MusicGroup } UNION { ?artist a mo:MusicArtist }
    FILTER NOT EXISTS { ?artist mh:countryOfOrigin ?c }
    FILTER NOT EXISTS { ?artist mo:genre ?g }
}
```
- **SPARQL results**: 1,099 artists lacking both country and genre data. The prompt focused on the 50 most connected secondary artists (those appearing in influencedBy, collaboratedWith, composed, or member_of relationships)
- **Verbalised context**: "Our KG has 1,241 artist entities, but only 58 are fully enriched. The remaining ~1,183 have labels but no genre, country, or biographical data. Here are the 50 most connected secondary artists — for each, provide country (ISO 2-letter code), primary genre, and whether they are a musician"
- **RAG prompt**: Asked for country, primary_genre, and is_musician flag for each of 50 secondary artists. Non-musicians get "n/a" for genre, unknown entities get "unknown" for country
- **Result summary**:
  - **50 entries** — 44 musicians, 6 non-musicians
  - **Country data**: 49/50 resolved (98%) — US dominates (29), then GB (6), DE (5), IT (3), JM (2), plus CL, BE, BR, CU (1 each). 1 unknown (Plato Kostic)
  - **Genre data**: 41/44 musicians resolved (93%) — jazz (7), rock and roll (5), baroque (4), country (2), soul (2), film score (2). 3 unknowns (Georg Bongartz, Luis Barzaga, Plato Kostic)
  - **Non-musicians identified**: Alejandro Jodorowsky (filmmaker), Allan Kaprow (artist), Allen Ginsberg (poet), Andy Warhol (artist), Bertolt Brecht (playwright), Charlie Chaplin (actor/filmmaker) — these are correctly in the KG as influence sources, but should not receive genre assignments
- **Evaluation**:
  - **What can be added**: Country triples for 49 artists, genre triples for 41 musicians. This is a high-confidence batch — well-known artists like Ella Fitzgerald, Herbie Hancock, Hank Williams, Count Basie have unambiguous country/genre data
  - **What needs validation**: 3 obscure entities (Georg Bongartz, Luis Barzaga, Plato Kostic) — likely early band members or minor collaborators with little public documentation
  - **Scalability insight**: This RAG approach works for the top 50, but the remaining 1,049 secondary artists would need a **programmatic approach** — using MusicBrainz MBIDs (which many already have) to batch-fetch country/genre data from the MusicBrainz API, similar to the existing `enrich_related_artists` function in the pipeline
  - **Key insight**: The LLM correctly identified 6 non-musicians among the 50, which is valuable metadata — it prevents incorrect genre/instrument assignments and could inform a new `mh:NonMusicalInfluence` class or similar modelling pattern
- **Output file**: `docs/rag_responses/i1_secondary_artists_enrichment.json`
- **Used in**: Completion analysis (I1 gap), demonstrates RAG for batch enrichment of sparse entity properties

---

## P40 — RAG Completion: I2 — Umm Kulthum Severely Under-Represented

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON) — comprehensive entity reconstruction
- **Gap addressed**: I2 — Umm Kulthum severely under-represented (wrong MusicBrainz entity matched)
- **SPARQL retrieval query**:
```sparql
# Retrieved all triples for the mismatched Umm Kulthum entity
SELECT ?p ?o WHERE {
    <http://musicbrainz.org/artist/6fbe9563-4c92-41dc-bdbc-63480427a58e> ?p ?o .
}
```
- **SPARQL results**: Only 4 triples — all belonging to "UMM" (electronic music project), not the real Umm Kulthum. Entity has: type MusicArtist (wrong), label "UMM", 1 release (wrong artist's album), name "UMM". No country, genres, awards, instruments, or external IDs
- **Verbalised context**: "Our KG matched the wrong MusicBrainz entity for Umm Kulthum. The current URI (6fbe9563) belongs to 'UMM', an electronic music project. The real Umm Kulthum (1898–1975, Egyptian singer, أم كلثوم) is one of the most important musicians of the 20th century but has essentially zero representation in our KG."
- **RAG prompt**: Asked for comprehensive entity data covering 8 categories: biographical, musical, discography, awards, influences, labels, performances, and correct external identifiers. Requested structured JSON output
- **Result summary**:
  - **Correct identifiers**: Wikidata Q190573 (high confidence), Discogs 365498 (high), MusicBrainz MBID 0c326960-bc95-41b0-b202-52a1e40b705e (medium — needs verification)
  - **Biographical**: Born ~1898 in Tamay-ez-Zahayra, Egypt; died 1975-02-03; real name Fatima Ibrahim el-Beltagi; female
  - **Musical**: 3 genres (Arabic classical music, Tarab, Egyptian popular music), vocals, 2 musical periods (Golden Age of Arabic music, Egyptian nationalist movement)
  - **Discography**: 5 key recordings — Alf Leila Wa Leila (1969), Enta Omri (1964), Al-Atlal (1966), Fakkarouni (1957), Amal Hayati (1965)
  - **Awards**: 6 honours including Egypt's Order of Perfection and "Star of the East" title
  - **Influences**: 4 influenced_by (Sheikh Abu al-Ila Mohamed, Zakariyya Ahmad, Mohamed el-Qasabgi, Abdo el-Hamouli), 7 influenced (Fairuz, Abdel Halim Hafez, Warda Al-Jazairia, Amr Diab, etc.)
  - **Labels**: Sono Cairo, Cairophon, EMI Arabia
  - **Performances**: 4 events including the iconic Thursday night radio concerts (1934–1970s)
- **Evaluation**:
  - **Resolution approach**: The existing URI should be replaced entirely — remove all triples for MBID 6fbe9563 and create a new entity with the correct MBID. This requires: (1) delete wrong triples, (2) create new URI with correct MBID, (3) populate all properties from this RAG response
  - **High confidence data**: Wikidata QID, country (EG), genres, major albums, awards, Olympia concert
  - **Medium confidence**: MBID (multiple Umm Kulthum entries exist in MusicBrainz — search returns several), exact birth date (sources vary: 1898 vs ~1904), influence lists
  - **Low confidence**: Some label names (exact romanisation varies), Carnegie Hall 1967 venue
  - **Root cause of gap**: The pipeline's MusicBrainz search used the romanised name "Umm Kulthum" which matched "UMM" (electronic project) due to fuzzy string matching. The correct search would use the Arabic name "أم كلثوم" or search by Wikidata cross-reference. This is a known limitation of name-based entity resolution for non-Latin script artists
  - **Key insight**: This is the clearest example of RAG value — the LLM provides comprehensive, structured data for an artist that the automated pipeline completely failed to resolve. The RAG output could serve as the seed data for manually creating the correct entity, demonstrating that RAG complements automated pipelines where entity resolution fails
- **Output file**: `docs/rag_responses/i2_umm_kulthum_enrichment.json`
- **Used in**: Completion analysis (I2 gap), demonstrates RAG for entity reconstruction where automated pipeline fails

---

## P41 — RAG Completion: I3 — LLM Text Extraction Coverage (28% → demonstration batch)

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Role-based + Constrained output (JSON) — same template as P8/P24–P33 text extraction prompts
- **Gap addressed**: I3 — LLM text extraction covers only 16/58 artists (28%)
- **SPARQL retrieval**: Verified that the 5 target artists exist in the KG with structured data (Aretha Franklin: 91 triples, Ravi Shankar: 72, Kraftwerk: 71, Tupac Shakur: 35, Youssou N'Dour: via rdfs:label) but have **no text-extracted predicates** (alterEgo, albumGrouping, producedBy, pioneerOf, performedAt, hasMusicalPeriod, founded)
- **Verbalised context**: "Our pipeline has extracted text-unique triples for 16/58 artists (Batches 1–3, P8/P24–P33). The remaining 42 artists are missing text-unique data. To demonstrate the RAG approach for this gap, we extract structured triples for 5 diverse artists: Aretha Franklin (soul/R&B, US), Ravi Shankar (Indian classical, IN), Kraftwerk (electronic, DE), Tupac Shakur (hip-hop, US), Youssou N'Dour (mbalax, SN)"
- **RAG prompt**: For each of the 5 artists, extract 10-15 structured triples using the established predicate vocabulary (released, composed, collaboratedWith, memberOf, hasMember, hasGenre, alterEgo, albumGrouping, producedBy, produced, performedAt, influencedBy, hasMusicalPeriod, pioneerOf, founded). Return as JSON per artist with subject-predicate-object triples
- **Artist selection justification**: 5 artists chosen for maximum diversity: Aretha Franklin (soul/R&B, US, female, Civil Rights era), Ravi Shankar (Indian classical, India, cross-cultural bridge), Kraftwerk (electronic, Germany, pioneering technology in music), Tupac Shakur (hip-hop, US, 1990s), Youssou N'Dour (mbalax, Senegal, world music)
- **Result summary**:
  - **87 triples** across 5 artists (average 17.4 per artist — consistent with existing batches' 16.7 average)
  - **Predicate distribution**: released (20), hasGenre (16), collaboratedWith (8), performedAt (8), hasMusicalPeriod (8), producedBy (7), pioneerOf (6), alterEgo (5), founded (5), influencedBy (2), hasMember (2)
  - **Text-unique predicates**: 39/87 triples (44%) use predicates only available via text extraction (alterEgo, producedBy, pioneerOf, performedAt, hasMusicalPeriod, founded) — these are data that structured sources cannot provide
  - **Notable extractions**: Aretha Franklin → "Queen of Soul" (alterEgo), Tupac Shakur → "2Pac" and "Makaveli" (alterEgo), Ravi Shankar → "Indian classical music in the West" (pioneerOf), Kraftwerk → "electronic music" and "synth-pop" (pioneerOf), Youssou N'Dour → "King of Mbalax" (alterEgo)
- **Evaluation**:
  - **Scalability projection**: At 17.4 triples/artist, extracting the remaining 37 unprocessed artists would yield ~644 new triples, of which ~283 would be text-unique. Combined with existing 298 text triples (16 artists) + 87 new (5 artists), total would reach ~1,229 text-extracted triples
  - **Coverage improvement**: This batch raises text extraction from 16/58 (28%) to 21/58 (36%). Full extraction would reach 100%
  - **Consistency**: The average triples per artist (17.4) closely matches existing batches (Batch 1: 17.2, Batch 2: 18.6, Batch 3: 20.4), demonstrating the prompt template produces consistent output
  - **Key insight**: 44% of extracted triples use text-unique predicates that no structured API provides. This validates the text extraction pipeline as complementary to — not redundant with — the MusicBrainz/Wikidata/Discogs structured data sources
- **Output file**: `docs/rag_responses/i3_text_extraction_batch4.json`
- **Used in**: Completion analysis (I3 gap), demonstrates RAG for scalable text extraction
- **Follow-up**: Based on this demonstration, the same prompt template was automated via `pipeline/llm_extraction.py` using Google Gemini free-tier API. The pipeline now extracts triples for all 58 artists automatically (57/58 successful — Umm Kulthum lacks Wikipedia cache). Total text-extracted triples increased from 298 (16 artists, manual) to 887 (57 artists, automated). This resolved the I3 gap.

---

## P42 — RAG Completion: I4 — Hildegard von Bingen Missing Genre Data

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON) — domain-expert musicological classification
- **Gap addressed**: I4 — Hildegard von Bingen is the only primary artist without any genre assignment
- **SPARQL retrieval**: Retrieved all 36 triples for Hildegard's entity (URI: musicbrainz.org/artist/2d923f7b-...). Has: type SoloMusicArtist, country DE, birth 1098-09-16, death 1179-09-17, gender Female, birthPlace Bermersheim, 25 releases, 2 composed works (Dendermonde Codex, Ordo Virtutum), realName. Missing: genres (0), instruments (0), influences (0), musical periods (0)
- **Verbalised context**: "Hildegard von Bingen (1098–1179) has 36 triples including 25 album releases (modern recordings of her works), but zero genre assignments. As a medieval abbess and composer, her music predates modern genre classification. MusicBrainz has no tags for her. She is the only primary artist out of 58 with no genre."
- **RAG prompt**: Asked for genres, musical periods, instruments, influences (both directions), and notable compositions with types (hymn, sequence, antiphon, morality play). Requested established musicological terms
- **Result summary**:
  - **5 genres**: medieval music, sacred music, plainchant, monophonic music, liturgical music
  - **3 musical periods**: Medieval (stylistic), Romanesque (cultural), 12th-century Renaissance (temporal)
  - **3 instruments**: voice (soprano/mezzo-soprano range), organ (modern performances only), symphonia (hurdy-gurdy, referenced in her writings)
  - **Influences**: 3 influenced_by (Gregorian chant tradition, Rule of Saint Benedict, Notker Balbulus), 5 influenced (Pérotin/Léonin Notre-Dame school, 20th-century early music revival, Arvo Pärt, Sofia Gubaidulina, contemporary new age)
  - **10 compositions**: Ordo Virtutum (morality play, ~1151), Symphonia armonie celestium revelationum (song cycle, ~1150–1160), 8 individual sequences/hymns/antiphons
- **Evaluation**:
  - **What can be added immediately**: "medieval music" and "sacred music" as genre entities — these are established musicological categories with no ambiguity. "plainchant" is also unambiguous. All 3 would resolve the only-artist-without-genre gap
  - **What needs consideration**: "monophonic music" and "liturgical music" are technical/functional descriptors rather than genres in the same sense as "jazz" or "rock". Whether to include them depends on the granularity of the genre taxonomy
  - **Modelling insight**: The LLM correctly identified that the 25 releases in the KG are **modern recordings** of her works by ensembles (Sequentia, Gothic Voices, Anonymous 4), not releases by Hildegard herself. This is a unique modelling pattern in the KG — a composer whose works are only available as interpretive recordings 900 years later. The `released` predicate may be semantically imprecise here; `composed` would be more appropriate for her original works
  - **Root cause of gap**: MusicBrainz community tagging is heavily biased toward popular music. Medieval sacred music has no active tagging community on the platform, so artists like Hildegard receive zero genre tags even when they have substantial discographies
  - **Key insight**: This is the clearest demonstration of RAG compensating for structured source limitations. MusicBrainz, Wikidata, and Discogs all failed to provide genre data for Hildegard because their taxonomies don't adequately cover pre-modern music. The LLM's musicological knowledge fills this gap with appropriate terminology
- **Output file**: `docs/rag_responses/i4_hildegard_genres.json`
- **Used in**: Completion analysis (I4 gap), demonstrates RAG for filling gaps where structured sources have systematic blind spots

---

## P43 — RAG Completion: I5 — Cover Recording Composers Lack Biographical Data

- **Task**: KG Completion via RAG (Week 11)
- **LLM/Tool**: Claude (Opus 4.6)
- **Prompting technique**: RAG (KG as SPARQL-based retrieval source) + Constrained output (JSON)
- **Gap addressed**: I5 — 330 cover recording composers lack biographical data (country, genre, birth/death dates)
- **SPARQL retrieval query**:
```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?composerName (COUNT(DISTINCT ?work) AS ?works) WHERE {
    ?work mh:composedBy ?composer .
    ?composer rdfs:label ?composerName .
    FILTER NOT EXISTS { ?composer mh:countryOfOrigin ?c }
}
GROUP BY ?composerName
ORDER BY DESC(?works)
LIMIT 50
```
- **SPARQL results**: 330 unique composers without country data. Focused on the 50 most prolific (by number of composed works in the KG). Top composers: [traditional] (14 works), J. Leslie McFarland (10), Big Bill Broonzy (7), Georges Bizet (7), The Notorious B.I.G. (5), Harold Arlen (5)
- **Verbalised context**: "Our KG's cover detection identified 373 cover recordings linked to 330 unique composers. These composers have names and MBIDs but no country, genre, or biographical data. Here are the 50 most prolific. For each, provide country (ISO 2-letter code), primary genre, birth year, and death year."
- **RAG prompt**: For each of 50 composers, provide country, primary_genre, birth_year, death_year. Use "n/a" for [traditional], "unknown" for obscure entities, "living" for death_year where applicable
- **Result summary**:
  - **Country resolved**: 47/50 (94%) — US dominates (42), then JM (2), FR (1), CV (1), HU (1). 2 unknown, 1 n/a ([traditional])
  - **Genre resolved**: 47/50 (94%) — soul (7), musical theatre (5), country (5), hip-hop (4), jazz (4), rock and roll (4), R&B (3), pop (3), blues (2), tin pan alley (2), plus opera, morna, folk, reggae, doo-wop, film score, operetta, Philadelphia soul
  - **Birth year known**: 44/50 (88%)
  - **Death year known**: 44/50 — including 8 still living (Berry Gordy, Carole King, Smokey Robinson, Tom Paxton, Mike Stoller, Brian Holland, Diddy, Stevie J)
  - **3 unresolvable**: J. Leslie McFarland (unknown — possibly obscure songwriter), Christine Yarian (unknown), Plato Kostic (unknown)
- **Evaluation**:
  - **Entity linking opportunities**: 8 composers overlap with existing KG entities under different names — 2Pac (= Tupac Shakur, primary artist), The Notorious B.I.G., Lee "Scratch" Perry, Little Richard, Billie Holiday, Smokey Robinson, Carole King, Diana Ross. These represent duplicate entities that should be consolidated via `owl:sameAs` or URI merging
  - **Genre distribution insight**: The composer population is dominated by American songwriters (84%), reflecting the US-centric nature of recorded cover versions. The genre mix (soul, musical theatre, country, R&B, tin pan alley) reveals a "Great American Songbook" + Motown + Nashville pattern — these are the traditions whose songs are most frequently covered
  - **Scalability**: The remaining 280 composers could be enriched programmatically via their MusicBrainz MBIDs — the `enrich_related_artists` pipeline function already handles this. The RAG approach here demonstrates the method; the MBID-based batch approach would be production-ready
  - **Key insight**: The RAG response surfaced an important data quality issue — **8 entity duplicates** where the same person appears as both a primary/secondary artist (e.g., Tupac Shakur) and a cover composer (2Pac). This is a direct consequence of the pipeline processing cover composers as new entities without checking for existing matches. The entity linking step should cross-reference composer names against existing artist labels
- **Output file**: `docs/rag_responses/i5_cover_composers_enrichment.json`
- **Used in**: Completion analysis (I5 gap), demonstrates RAG for batch enrichment of sparse entities and entity deduplication discovery

---

