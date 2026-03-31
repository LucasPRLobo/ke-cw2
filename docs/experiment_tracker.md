# Experiment Tracker

Records findings, observations, and decisions from each data source experiment.

---

## Experiment 1: MusicBrainz API

**Date:** 2026-03-25
**Status:** Complete
**Test subjects:** David Bowie, The Beatles

### Data Structure

MusicBrainz uses UUIDs (MBIDs) for all entities. Data is accessed via `musicbrainzngs` Python library. Rate limit: 1 req/sec, no auth needed (just User-Agent).

### Fields Discovered → Ontology Mapping

| MusicBrainz Field | Ontology Entity/Property | Quality | Notes |
|---|---|---|---|
| `id` (MBID) | URI for any entity | Excellent | Use as `http://musicbrainz.org/artist/{mbid}` |
| `name` | `rdfs:label` / `foaf:name` | Excellent | |
| `type` (Person/Group) | `Artist` vs `Band` class | Excellent | Clean distinction |
| `country` | `countryOfOrigin` | Good | ISO country codes (GB, US) |
| `area.name` | `countryOfOrigin` (expanded) | Good | Full name (e.g., "England") |
| `begin-area.name` | `birthPlace` | Good | e.g., "Brixton" |
| `life-span.begin` | Birth date / band start | Excellent | ISO dates |
| `life-span.end` | Death date / band end | Excellent | ISO dates |
| `gender` | `gender` (new property) | Good | Only for Person types |
| `tag-list[].name` | `hasGenre` → `Genre` | Mixed | Noisy — needs filtering (see issues) |
| `tag-list[].count` | Genre confidence | Useful | Higher count = more reliable |
| `artist-relation-list` | Multiple properties | Excellent | Rich relationship types |
| `url-relation-list` | Cross-references | Excellent | Links to Discogs, Wikidata, Wikipedia, etc. |
| `release-list[].title` | `Album` entity | Good | Needs deduplication |
| `release-list[].date` | `releaseDate` | Good | ISO dates |
| `recording.title` | `Track` entity | Good | |
| `recording.length` | `duration` | Good | In milliseconds |

### Relationship Types Found

| MusicBrainz relation type | Ontology Property | Example | Has dates? | Has attributes? |
|---|---|---|---|---|
| `member of band` | `memberOf` | John Lennon → The Beatles | Yes (1960–1969) | Yes (guitar, lead vocals) |
| `collaboration` | `collaboratedWith` | Bowie → Band Aid | No | Yes (minor) |
| `instrumental supporting musician` | Could map to `collaboratedWith` or new property | Carlos Alomar → Bowie | No | Yes (guitar) |
| `married` | Not in our ontology | Bowie → Iman | Yes | No |
| `involved with` | Not in our ontology | Bowie → various | No | No |

### URL Relationship Types Found

| URL rel type | Target | Use in pipeline |
|---|---|---|
| `discogs` | `https://www.discogs.com/artist/10263` | Cross-reference to Discogs (Experiment 2) |
| `wikidata` | `https://www.wikidata.org/wiki/Q5383` | Cross-reference to Wikidata |
| `last.fm` | `https://www.last.fm/music/David+Bowie` | Potential text source |
| `allmusic` | `https://www.allmusic.com/artist/mn0000531986` | Not using |
| `IMDb` | `https://www.imdb.com/name/nm0000309/` | Not using |
| `free streaming` (Spotify) | `https://open.spotify.com/artist/0oSGxfWSnnOXhD2fKuz2Gy` | Could extract Spotify ID |
| `BBC Music page` | `https://www.bbc.co.uk/music/artists/...` | Not using (no API) |
| `official homepage` | `https://www.davidbowie.com/` | Not using |

**Note:** Wikipedia URL was not visible in Bowie's results — may need to go via Wikidata (Q5383) instead.

### Issues & Decisions

| Issue | Impact | Decision |
|---|---|---|
| **1456 releases for one artist** | Massive duplication from different pressings/countries | Use **release groups** instead of raw releases to deduplicate |
| **Tags are noisy** | "british", "uk", "actors", "arrangers" are not genres | Filter by count threshold (e.g., ≥5) or maintain a genre whitelist |
| **"influenced by" relationships sparse** | Not all artists have these | Supplement from Discogs profiles / Wikipedia text |
| **No Wikipedia URL in url-rels** | Can't directly link to Wikipedia article | Go via Wikidata ID or search Wikipedia by artist name |
| **`gender` not in our ontology** | Useful data we're not capturing | Add `gender` property to ontology |
| **`married`/`involved with` rels** | Exists in data but not in our ontology | Ignore for now — not relevant to music history scope |
| **Instrument data in member rels** | `attribute-list` contains instruments (guitar, drums, etc.) | Use to populate `playsInstrument` property |

### Sample Data Points

**David Bowie:**
- MBID: `5441c29d-3602-4898-b1a1-b77fa23b8e50`
- Type: Person, Country: GB, Born: 1947-01-08, Died: 2016-01-10
- Birth area: Brixton, Area: England
- Top tags: art rock (22), glam rock (22), alternative rock (12), pop (10)
- Discogs ID: 10263, Wikidata: Q5383
- 66 artist relationships, 81 URL relationships, 1456 releases

**The Beatles:**
- MBID: `b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d`
- Type: Group, Active: 1960–1970-04-10
- 9 members with instruments and date ranges
- Top tags: rock (45), pop (28), pop rock (23), british (22), merseybeat (14)

---

## Experiment 2: Discogs API

**Date:** 2026-03-25
**Status:** Complete
**Test subjects:** David Bowie (ID: 10263), The Beatles (ID: 82730)

### Data Structure

Discogs uses numeric IDs for entities. Accessed via REST API with `requests`. Rate limit: 25 req/min unauthenticated (with User-Agent). Distinguishes `release` (specific pressing) from `master` (canonical release).

### Fields Discovered → Ontology Mapping

| Discogs Field | Ontology Entity/Property | Quality | Notes |
|---|---|---|---|
| `id` | URI component | Good | Numeric, use as `http://discogs.com/artist/{id}` |
| `name` | `rdfs:label` | Good | |
| `realname` | `realName` (new property) | Good | "David Robert Jones" — MB doesn't have this |
| `namevariations` | Entity disambiguation | Excellent | 56 variations for Bowie — useful for text NER |
| `profile` | Text source for NER/LLM | Limited | Short (524 chars for Bowie), has Discogs markup |
| `urls` | Cross-references | Good | Includes Wikipedia URL directly |
| `members[].name` | `memberOf` | Moderate | No instruments, no dates, just active flag |
| `groups[].name` | `memberOf` (inverse) | Poor | Empty for Bowie despite known band memberships |
| Release `genres` | `hasGenre` → `Genre` | Good | Broad categories: Rock, Pop, Funk/Soul |
| Release `styles` | `subgenreOf` hierarchy | Excellent | Granular: Mod, Pop Rock, Soul, Acoustic, Vocal |
| Release `label` | `signedTo` → `RecordLabel` | Good | Available per release |
| Release `format` | Not in our ontology | Informational | "12\" Vinyl", "Acetate" — physical format data |
| Release `year` | `releaseDate` | Good | Year only (less precise than MB) |

### Genre vs Style Hierarchy (Key Finding)

Discogs separates genres (broad) from styles (sub-genres). This directly maps to our `subgenreOf` property:

| Genre (broad) | Styles (sub-genres) found |
|---|---|
| Rock | Mod, Pop Rock |
| Pop | Vocal, Acoustic |
| Funk / Soul | Soul |

This is much cleaner than MusicBrainz's flat tag list.

### Comparison: MusicBrainz vs Discogs

| Feature | MusicBrainz | Discogs | Winner |
|---|---|---|---|
| Artist basic info | name, type, country, gender, life-span | name, realname, 56 name variations | Complementary |
| Genre data | Flat tags (noisy) | genres + styles (hierarchical) | **Discogs** |
| Biography text | None | `profile` (short, with markup) | **Discogs** (but Wikipedia better) |
| Band members | 9 Beatles members with instruments + dates | 6 members, active flag only | **MusicBrainz** |
| Artist relationships | 66 rels (influenced by, collaboration, etc.) | Groups only | **MusicBrainz** |
| Cross-references | URL rels to many sources | URLs list | **MusicBrainz** |
| Release count | 1,456 (Bowie) | 10,629 (Bowie) | Both need deduplication |
| Record labels | Via release data | Via release `label` field | Comparable |

### Cross-Reference Test

MusicBrainz url-rels → extract Discogs ID from URL → fetch Discogs data: **CONFIRMED WORKING**
- `https://www.discogs.com/artist/10263` → ID `10263` → fetches David Bowie correctly

### Issues & Decisions

| Issue | Impact | Decision |
|---|---|---|
| **Profiles are short** | 524 chars for Bowie, not enough for rich text extraction | Use **Wikipedia** as primary text source, Discogs profile as supplement |
| **Discogs markup in profiles** | `[a1240431]` style links need parsing | Strip markup before NER/LLM extraction |
| **10,629 releases for Bowie** | Worse duplication than MB | Use `master` releases only to deduplicate |
| **No groups for Bowie** | Discogs doesn't track solo artist → band membership well | Rely on **MusicBrainz** for membership data |
| **No artist-to-artist relationships** | No influence, collaboration data | Rely on **MusicBrainz** for relationships |
| **Search works unauthenticated** | Can search without token | Use search for discovery, direct ID for known entities |
| **Wikipedia URL in Discogs** | `https://en.wikipedia.org/wiki/David_Bowie` in URLs | Alternative cross-reference path to Wikipedia |

### Sample Data Points

**David Bowie (Discogs):**
- ID: 10263, Real name: David Robert Jones
- 56 name variations, 21 URLs
- Profile: 524 chars, short biography with Discogs markup
- No groups listed (despite MusicBrainz showing 10+ bands)
- 10,629 releases

**The Beatles (Discogs):**
- ID: 82730
- 6 members (Pete Best + Stuart Sutcliffe marked inactive)
- Profile: 1,136 chars, good historical overview with Discogs markup
- No instruments or date ranges for members

---

## Experiment 3: Wikipedia API

**Date:** 2026-03-25
**Status:** Complete
**Test subjects:** David Bowie, Rock music, Origins of rock and roll, The Beatles, Grunge, Abbey Road, Grammy Award

### Data Structure

Wikipedia uses the MediaWiki API. Accessed via `requests` with User-Agent header. No auth needed. Returns clean plain text via `explaintext=True`. Supports batch fetching (up to 50 titles per request).

### Fields Discovered → Ontology Mapping

| Wikipedia Feature | Ontology Use | Quality | Notes |
|---|---|---|---|
| Article text (`extracts`) | Text source for NER/LLM triple extraction | Excellent | 85,851 chars for Bowie (164x more than Discogs) |
| Section structure (`parse/sections`) | Targeted extraction by topic | Excellent | 44 sections for Bowie, decade-by-decade career breakdown |
| Categories | Genre classification, awards, labels | Good | "Art rock musicians", "Brit Award winners", but noisy metadata categories mixed in |
| Internal links | Entity discovery, relationship hints | Good | 100+ entity references per article |
| Page ID | Stable identifier | Good | Numeric, consistent |

### Key Sections Found (David Bowie)

Sections most useful for triple extraction:
- **2. Music career** (+ decade subsections 2.1–2.11) — albums, collaborations, genres, labels
- **5. Musicianship** — instruments, style, influences
- **8. Legacy** — influence on other artists
- **9. Awards and achievements** — awards data
- **11. Discography** — album list (but structured sources are better for this)

### Article Availability

| Title tried | Result | Length |
|---|---|---|
| "David Bowie" | ✓ Works | 85,851 chars |
| "History of rock music" | ✗ Empty (redirect/missing) | 0 chars |
| "Rock music" | ✓ Works | 3,686 chars (intro only) |
| "Origins of rock and roll" | ✓ Works | 1,847 chars (intro only) |
| "The Beatles" | ✓ Works (batch) | Available |
| "Grunge" | ✓ Works (batch) | 2,364 chars (intro only) |
| "Abbey Road" | ✓ Works (batch) | 2,085 chars (intro only) |
| "Grammy Award" | ✗ Empty | 0 chars |

**Key lesson:** Not all guessed titles work. Use cross-references (Wikidata ID or Discogs URL) rather than guessing.

### Categories (David Bowie) — Useful Subset

| Category | Maps to |
|---|---|
| Art pop musicians | `hasGenre` → Art Pop |
| Art rock musicians | `hasGenre` → Art Rock |
| Glam rock musicians | `hasGenre` → Glam Rock |
| Brit Award winners | `wonAward` → Brit Award |
| Columbia Records artists | `signedTo` → Columbia Records |
| Rock and Roll Hall of Fame inductees | `wonAward` → Rock and Roll Hall of Fame |
| English male singers | `countryOfOrigin` → England |

Noisy categories to filter: "Articles with hCards", "CS1: long volume value", "All Wikipedia articles written in British English"

### Cross-Reference Tests

| Path | Result |
|---|---|
| MusicBrainz → Wikidata (Q5383) → Wikipedia ("David Bowie") | ✓ **Works** |
| Discogs URL → extract title → Wikipedia API | ✓ **Works** |
| Batch fetch (5 articles in one request) | ✓ **Works** |

### Comparison: Wikipedia vs Discogs as Text Source

| Feature | Wikipedia | Discogs Profile |
|---|---|---|
| Text length | 85,851 chars (Bowie) | 524 chars (Bowie) |
| Structure | 44 sections, decade-by-decade | Single paragraph |
| Historical depth | Full career, influences, legacy | Brief bio summary |
| Markup | Clean plain text | Discogs-specific `[a123]` links |
| Entity density | Very high (100+ internal links) | Low |

**Winner: Wikipedia** by a wide margin for text extraction.

### Issues & Decisions

| Issue | Impact | Decision |
|---|---|---|
| **Article titles not guessable** | Can't just guess "History of rock music" | Use cross-references (Wikidata ID or Discogs URL) to find articles |
| **Some articles return empty** | "Grammy Award", "History of rock music" | Try alternate titles or use Wikipedia search API |
| **Categories are noisy** | Metadata categories mixed with useful ones | Filter: keep only categories matching genre/award/label patterns |
| **Section HTML in titles** | `<i>Space Oddity</i>` in section names | Strip HTML tags when processing sections |
| **Very long articles** | 85K chars may be too much for LLM context | Extract specific sections (Music career, Legacy) rather than full article |

### Sample Data Points

**David Bowie (Wikipedia):**
- Page ID: 8786, Text: 85,851 chars, 44 sections
- Key sections: Music career (decade-by-decade), Musicianship, Legacy
- 50 categories, 100+ internal links
- Cross-ref from Wikidata Q5383 confirmed
- Cross-ref from Discogs URL confirmed

---

## Experiment 4: Cross-Referencing

**Date:** 2026-03-25
**Status:** Complete
**Test subjects:** David Bowie, The Beatles, Miles Davis, Nirvana, Ludwig van Beethoven

### Coverage Results

| Artist | MusicBrainz | Discogs | Wikipedia | Coverage |
|---|---|---|---|---|
| David Bowie | ✓ | ✓ (ID: 10263) | ✓ (3,051 chars) | 3/3 |
| The Beatles | ✓ | ✓ (ID: 82730) | ✓ (3,949 chars) | 3/3 |
| Miles Davis | ✓ | ✓ (ID: 23755) | ✓ (3,930 chars) | 3/3 |
| Nirvana | ✓ | ✓ (ID: 125246) | ✓ (2,489 chars) | 3/3 |
| Ludwig van Beethoven | ✓ | ✓ (ID: 95544) | ✓ (3,256 chars) | 3/3 |

**Result: 5/5 artists found in all 3 sources (100% coverage)**

### Cross-Reference Links in MusicBrainz

| Artist | Discogs URL | Wikidata URL | Direct Wikipedia URL |
|---|---|---|---|
| All 5 tested | ✓ All have | ✓ All have | ✗ None have |

**Key finding:** MusicBrainz never has a direct Wikipedia URL, but always has Wikidata. The path MusicBrainz → Wikidata → Wikipedia works reliably. Nirvana correctly resolved to "Nirvana (band)" — Wikidata handles disambiguation automatically.

### Confirmed Pipeline

```
MusicBrainz (search by name) → MBID
  ├── MB detail (tags, artist-rels, url-rels)
  ├── url-rels → Discogs ID → Discogs API (genres/styles, profile)
  └── url-rels → Wikidata ID → Wikipedia title → Wikipedia API (text)
```

### Combined Record Example (David Bowie)

```
Identifiers:  MBID=5441c29d-..., Discogs=10263, Wikipedia=8786, Wikidata=Q5383
Basic Info:   Name=David Bowie, Type=Person, Country=GB, Born=1947-01-08, Died=2016-01-10
Discogs:      Real Name=David Robert Jones, Profile=524 chars
MB Tags:      art rock, glam rock, alternative rock, pop, art pop
Wikipedia:    3,051 chars (intro), 85,851 chars (full), 50 categories
```

### Issues & Decisions

| Issue | Impact | Decision |
|---|---|---|
| **No direct Wikipedia URL in MB** | Need alternative path | Use Wikidata as bridge — works 100% of the time |
| **Wikipedia text is intro-only in batch** | 3K chars vs 85K full article | Use `exintro=True` for overview, fetch full article for deep extraction |
| **Rate limits across 3 APIs** | Pipeline is slow (sleep timers needed) | Accept for now; cache responses to avoid re-fetching |
| **Disambiguation** | "Nirvana" could be the band or the concept | Wikidata handles this correctly ("Nirvana (band)") |

---

## Experiment 5: Triple Extraction (Structured)

**Date:** 2026-03-25
**Status:** Complete
**Test subject:** David Bowie (MusicBrainz + Discogs → RDF via rdflib)

### Approach

Used `rdflib` in Python with manual field→triple mapping. Chose this over SPARQL Anything because our data comes from live API calls (JSON in memory), not static files.

### Namespaces Used

| Prefix | Namespace | Purpose |
|---|---|---|
| `mo:` | `http://purl.org/ontology/mo/` | Music Ontology — types (SoloMusicArtist, MusicGroup, Genre, Track, Instrument) |
| `mh:` | `http://example.org/music-history/` | Our custom namespace — properties and entities |
| `mb:` | `http://musicbrainz.org/artist/` | MusicBrainz artist URIs |
| `foaf:` | FOAF | `foaf:name` |
| `schema:` | Schema.org | `schema:birthDate`, `schema:deathDate`, `schema:gender` |
| `dc:` | Dublin Core | `dc:title` |
| `rdfs:` | RDFS | `rdfs:label` |

### Results

- **258 triples** generated for a single artist (David Bowie)
- **419 release groups** found (vs 1,456 raw releases) — deduplication via release groups works
- **14 tracks** mapped for first album with durations
- **12 genres** from MusicBrainz tags (filtered count ≥ 3)
- **3 Discogs genre→style mappings** (Rock→Mod, Pop→Vocal, etc.)
- **18 relationship triples** (band membership, collaborations)
- Turtle file saved to `ontology/experiment5_sample.ttl`

### Mapping Rules

| Source | Field | → RDF Triple |
|---|---|---|
| MB | `type=Person` | `(artist, rdf:type, mo:SoloMusicArtist)` |
| MB | `type=Group` | `(artist, rdf:type, mo:MusicGroup)` |
| MB | `name` | `(artist, foaf:name, "name")` + `(artist, rdfs:label, "name")` |
| MB | `country` | `(artist, mh:countryOfOrigin, "GB")` |
| MB | `life-span.begin` | `(artist, schema:birthDate, "1947-01-08"^^xsd:date)` |
| MB | `life-span.end` | `(artist, schema:deathDate, "2016-01-10"^^xsd:date)` |
| MB | `gender` | `(artist, schema:gender, "Male")` |
| MB | `begin-area.name` | `(artist, mh:birthPlace, "Brixton")` |
| MB | `tag-list` (count≥3) | `(artist, mo:genre, genre_uri)` |
| MB | `rel: member of band` | `(artist, mo:member_of, band_uri)` |
| MB | `rel: member attributes` | `(artist, mh:playsInstrument, instrument_uri)` |
| MB | `rel: collaboration` | `(artist, mh:collaboratedWith, other_uri)` |
| MB | `rel: influenced by` | `(artist, mh:influencedBy, other_uri)` |
| MB | release group title | `(artist, mh:released, album_uri)` + `(album, dc:title, "title")` |
| MB | release group date | `(album, mh:releaseDate, "1967-06")` |
| MB | recording title | `(album, mh:hasTrack, track_uri)` + `(track, dc:title, "title")` |
| MB | recording length | `(track, mh:duration, 129000^^xsd:integer)` |
| Discogs | `realname` | `(artist, mh:realName, "David Robert Jones")` |
| Discogs | `genres` | `(genre_uri, rdf:type, mo:Genre)` |
| Discogs | `styles` | `(style_uri, mh:subgenreOf, genre_uri)` |

### SPARQL Query Results

All 4 test queries returned correct results:

| Query (CQ) | Result |
|---|---|
| What genres does Bowie belong to? | 14 genres (including duplicates from case issue) |
| What bands was Bowie a member of? | 14 bands |
| What tracks are on albums? | 14 tracks on "David Bowie" |
| What subgenres exist? | 3 styles (Acoustic, Mod, Vocal) → subgenreOf → Rock, Pop |

### Issues Found — Must Fix Before Final Pipeline

| Issue | Impact | Fix |
|---|---|---|
| **Genre case duplication** | "Rock" (Discogs) and "rock" (MB) create separate URIs | Normalise all genre names to lowercase before URI creation |
| **Noisy tags leaking** | "actors", "british", "uk" passed count≥3 filter | Add genre whitelist or tag blacklist |
| **Subgenre duplication** | "Acoustic → subgenreOf → Pop" + "Acoustic → subgenreOf → pop" | Same case normalisation fix |
| **Tribute/cover bands in rels** | "David Brighton's Space Oddity" appeared as a band | Filter by relationship attributes or verify band type |

### Output File

`ontology/experiment5_sample.ttl` — 258 triples, clean Turtle format

---

## Experiment 6: Triple Extraction (Text)

**Date:** 2026-03-27
**Status:** Complete
**Test subject:** David Bowie Wikipedia intro (3,051 chars)

### Approach

Two techniques tested (both from Week 7):
1. **SpaCy NER** (`en_core_web_sm`) — entity extraction
2. **LLM prompting** — structured triple extraction (prompt designed, expected output simulated)

### SpaCy NER Results

- **88 entities found**, 75 relevant after filtering (PERSON, ORG, GPE, LOC, DATE, WORK_OF_ART, EVENT)
- **31 dates** extracted — useful for releaseDate, activeYears
- **12 unique persons**, 7 organisations, 6 works of art, 2 countries

**Significant misclassifications:**

| Entity | SpaCy Label | Actual Type | Impact |
|---|---|---|---|
| Young Americans | PERSON | Album | Wrong class |
| Low | PERSON | Album | Wrong class |
| Blackstar | PERSON | Album | Wrong class |
| Tin Machine | PERSON | Band | Wrong class |
| Twin Peaks | PERSON | Film | Wrong class |
| Labyrinth | PERSON | Film | Wrong class |
| Scary Monsters | ORG | Album | Wrong class |
| The Next Day | DATE | Album | Wrong class |
| Mars | LOC | Part of album title | Wrong class |

**Conclusion:** SpaCy `en_core_web_sm` is too weak for the music domain. Albums and films are consistently misclassified as PERSON. A larger model (`en_core_web_trf`) or domain fine-tuning would improve results.

### LLM Triple Extraction

Designed a structured prompt with 16 predicate types matching our ontology. Expected output: **20 triples** from the intro alone.

Sample triples extracted:
- `(David Bowie, realName, David Robert Jones)`
- `(David Bowie, collaboratedWith, Brian Eno)`
- `(David Bowie, collaboratedWith, Queen)`
- `(David Bowie, memberOf, Tin Machine)`
- `(David Bowie, released, Low)` + 7 more albums
- `(David Bowie, wonAward, Rock and Roll Hall of Fame)`
- `(David Bowie, hasGenre, glam rock)`
- `(David Bowie, hasGenre, plastic soul)`

### SpaCy vs LLM Comparison

| Aspect | SpaCy NER | LLM Extraction |
|---|---|---|
| Entities found | 88 (many misclassified) | Correct entities in context |
| Relations found | 0 (NER only) | 20 full triples |
| Domain accuracy | Poor (albums→PERSON) | Good (understands context) |
| Speed | Fast (local) | Slower (API call) |
| Best use | Entity discovery | Full triple extraction |

**Winner: LLM extraction** — finds both entities and relations with much better domain understanding.

### Text-Only Triples (Not in Structured Data)

These triples can ONLY be extracted from text, not from MusicBrainz or Discogs:

| Triple | Why it's text-only |
|---|---|
| `(David Bowie, wonAward, Grammy Award)` | Award data (6 Grammys) |
| `(David Bowie, wonAward, Brit Award)` | Award data (4 Brits) |
| `(David Bowie, wonAward, Rock and Roll Hall of Fame)` | Inducted 1996 |
| `(David Bowie, hasGenre, plastic soul)` | Not a standard tag in MB/Discogs |
| `(David Bowie, hasGenre, industrial)` | Mentioned in text only |
| `(David Bowie, hasGenre, jungle)` | Mentioned in text only |
| `(Low, partOf, Berlin Trilogy)` | Album grouping — no structured equivalent |
| `(Heroes, partOf, Berlin Trilogy)` | Album grouping |
| `(Lodger, partOf, Berlin Trilogy)` | Album grouping |
| `(Blackstar, chartPosition, #1 US Billboard 200)` | Chart data |
| `(David Bowie, alterEgo, Ziggy Stardust)` | Persona — unique to text |
| `(David Bowie, alterEgo, Thin White Duke)` | Persona — unique to text |

### Entity Linking Results

| Text Entity | MusicBrainz Match | Score | Correct? |
|---|---|---|---|
| Brian Eno | Brian Eno (ff95eb47...) | 100 | ✓ |
| Queen | Queen (0383dadf...) | 100 | ✓ |
| Tin Machine | Tin Machine (39dfc059...) | 100 | ✓ |
| Ziggy Stardust | Stardust Revue (2bcb6d35...) | 100 | ✗ (alter ego, not a real artist) |

**Entity linking works for real artists** but fails for fictional personas. Need to handle alter egos as a special case.

### Issues & Decisions

| Issue | Impact | Decision |
|---|---|---|
| **SpaCy misclassifies albums as PERSON** | Can't rely on SpaCy alone for entity typing | Use LLM extraction as primary; SpaCy as supplementary |
| **Entity linking fails for personas** | "Ziggy Stardust" matched wrong | Don't entity-link entities that are alter egos/personas |
| **LLM extraction needs API access** | Can't run locally in notebook | Use OpenAI/Claude API, or run prompt manually and paste results |
| **New properties discovered** | `alterEgo`, `partOf`, `chartPosition` not in ontology | Add these to ontology if needed |
| **Text adds unique value** | Awards, personas, album groups not in structured data | Text extraction is essential, not optional |

### Recommended Text Pipeline

```
1. Fetch Wikipedia article via Wikidata cross-reference
2. Extract key sections (Music career, Legacy, Musicianship)
3. Run LLM prompt for structured triple extraction
4. Optionally run SpaCy NER for entity validation
5. Link extracted entities to MusicBrainz MBIDs via search
6. Filter out persona/alter-ego false matches
7. Add new triples to the RDF graph
```

---

## Experiment 7: Data Source Evaluation

**Date:** 2026-03-27
**Status:** Complete
**Test artists:** Beethoven (Classical), Miles Davis (Jazz), David Bowie (Rock), Tom Jobim (Brazilian), Fela Kuti (African)
**Sources evaluated:** Wikidata SPARQL, DBpedia SPARQL, Open Opus API, MusicBrainz (baseline), Discogs (baseline)

### Wikidata SPARQL — Very Rich

| Artist | Genres | Instruments | Awards | Labels | Influences |
|---|---|---|---|---|---|
| David Bowie | 18 (rock, pop, electronic, alt rock...) | 8 (piano, guitar, sax, drums...) | 13+ (Grammy, Rock Hall of Fame...) | 14 (Mercury, Columbia, EMI, RCA, Virgin...) | 8 (Dylan, Beatles, Brel, Pink Floyd, Warhol...) |
| Beethoven | — | 2 (piano, violin) | 1 | — | 4 (Mozart, Bach, Haydn, Fux) |
| Miles Davis | 6 (jazz, bebop, fusion, hard bop, cool jazz) | 4 (trumpet, organ, synthesizer, flugelhorn) | 9+ (Rock Hall of Fame, NEA Jazz Masters...) | Yes | Yes |
| Tom Jobim | Not queried individually | — | — | — | — |
| Fela Kuti | Not queried individually | — | — | — | — |

**Key finding:** Wikidata has awards, instruments, influences, and record labels as **structured data already in RDF**. This eliminates the need for LLM text extraction for these fact types.

### DBpedia — Messy, Redundant

- Noisy data: template parameters leaking through (`b: no`, `v: no`, `fixAttempted: yes`)
- Has some useful fields: genre, birthName, instrument, occupation
- Has `owl:sameAs` links to external resources
- **Verdict:** Wikidata is cleaner and more complete. DBpedia is redundant.

### Open Opus — Excellent for Classical Only

- **250 Beethoven works** across Orchestral (44), Chamber (108), Keyboard (98)
- Rich metadata: opus numbers, titles, subtitles, composer epoch ("Early Romantic")
- **Classical artists only** — Miles Davis, Fela Kuti, Tom Jobim all return NOT FOUND
- **Verdict:** Strong classical supplement, but only useful for that genre

### MusicBrainz — Good Non-Western Coverage

| Artist | Country | Tags | Artist Rels | Discogs Link | Wikidata Link |
|---|---|---|---|---|---|
| Fela Kuti | NG | afrobeat, african, nigerian, jazz | 11 | ✓ | ✓ |
| Tom Jobim | BR | bossa nova, latin jazz, brazilian | 6 | ✓ | ✓ |
| Miriam Makeba | ZA | — | — | — | — |
| Youssou N'Dour | SN | — | — | — | — |

All non-Western artists found with cross-reference links intact.

### Final Source Selection

| Source | Include? | Role | Justification |
|---|---|---|---|
| **MusicBrainz** | **Yes — Primary structured** | Artist info, band membership, releases, tracks, cross-reference hub | Richest relationships, best coverage across all genres/regions |
| **Discogs** | **Yes — Supplement** | Genre→style hierarchy, real names | Unique sub-genre data not available elsewhere |
| **Wikidata** | **Yes — ADD (new)** | Awards, instruments, influences, record labels (structured RDF) | Eliminates need for LLM extraction of these facts. Already RDF. |
| **Wikipedia** | **Yes — Primary text** | Article text for LLM triple extraction of narrative facts | Personas, album groupings, career context — things not in any structured source |
| **Open Opus** | **Maybe — Classical supplement** | Classical compositions with opus numbers and genres | Only if we need deeper classical data than Wikidata provides |
| **DBpedia** | **No — Skip** | — | Redundant with Wikidata, much noisier data |

### Impact on Pipeline

Adding Wikidata changes what we need from Wikipedia text extraction:

| Fact type | Before (Experiments 1–6) | After (with Wikidata) |
|---|---|---|
| Awards | Wikipedia text → LLM extraction | **Wikidata SPARQL** (structured) |
| Instruments | Wikipedia text → LLM extraction | **Wikidata SPARQL** (structured) |
| Influences | Wikipedia text → LLM extraction | **Wikidata SPARQL** (structured) |
| Record labels | Wikipedia text → LLM extraction | **Wikidata SPARQL** (structured) |
| Genres | MusicBrainz tags (noisy) | MusicBrainz tags + **Wikidata P136** + Discogs genres/styles |
| Personas/alter egos | Wikipedia text → LLM extraction | Wikipedia text → LLM extraction (unchanged) |
| Album groupings (trilogies) | Wikipedia text → LLM extraction | Wikipedia text → LLM extraction (unchanged) |
| Career narrative | Wikipedia text → LLM extraction | Wikipedia text → LLM extraction (unchanged) |
| Classical compositions | MusicBrainz works | Wikidata P86 + optionally Open Opus |

---

## All Experiments Complete

### Revised Data Pipeline

```
                         MusicBrainz API
                        /       |        \
               Artist info   Releases   Relationships (memberOf)
               Tags/genres   Tracks     URL rels → Discogs ID + Wikidata ID
                                             |                    |
                                        Discogs API          Wikidata SPARQL
                                        /         \          /        |        \
                               Genre/Style    Profile   Awards   Instruments  Influences
                               hierarchy       text    Labels    Genres       Compositions
                                                          |
                                                     Wikipedia API
                                                     /           \
                                               Article text    Categories
                                                    |
                                            LLM Triple Extraction
                                            (personas, album groups,
                                             career narrative only)
                                                    |
                                                    v
                                          RDF Graph (rdflib → .ttl)
```

### Source Summary

- **Structured sources (3):** MusicBrainz (JSON), Discogs (JSON), Wikidata (RDF/SPARQL)
- **Text source (1):** Wikipedia (MediaWiki API)
- **Exceeds minimum requirement** of 1 structured + 1 text source

---

## SPARQL Query Analysis

**Date:** 2026-03-30
**Status:** 20 queries written, 17 return results, 3 return empty

### Results Summary

| CQ | Title | Results | Status |
|---|---|---|---|
| 1 | Album release dates | 574 | ✓ |
| 2 | Artist genres | 217 | ✓ |
| 3 | Albums (no track-level data) | 582 | ✓ (partial) |
| 4 | Who produced an album | 4 | ✓ (limited to LLM-extracted) |
| 5 | Performers in bands | 530 | ✓ |
| 6 | Producers by genre | 0 | ✗ See Gap 1 |
| 7 | Instruments in bands | 516 | ✓ |
| 8 | Awards per artist | 23 artists, Quincy Jones leads with 34 | ✓ |
| 9 | Subgenres | 112 | ✓ |
| 10 | Compositions with dates | 372 | ✓ |
| 11 | Award winners at labels | 1,343 | ✓ |
| 12 | Influencers sharing genres | 12 | ✓ (mostly self-referencing) |
| 13 | Labels with 3+ genres | 81 | ✓ |
| 14 | Cross-country collaborations | 0 | ✗ See Gap 2 |
| 15 | Instruments per genre | 661 | ✓ |
| 16 | Multinational bands | 0 | ✗ See Gap 3 |
| 17 | Artist labels + albums | 125 | ✓ |
| 18 | Composers' works by country | 294 | ✓ |
| 19 | Award winners who collaborated | 4 | ✓ |
| 20 | Genre geographic spread by decade | 751 | ✓ |

### Gaps Identified

**Gap 1 — CQ6: Producer→Album→Genre link broken**
- **Problem:** LLM text extraction creates `produced` triples like `("Quincy Jones", produced, "Off the Wall - Michael Jackson (1979)")`. The object is a free-text string, not the album URI that exists in the graph from MusicBrainz. So the SPARQL query can't join `produced` → album → genre.
- **Root cause:** The text mapping entity linker creates a new `mh:work/` URI for the produced album because the LLM includes the artist name and year in the album title (e.g., "Off the Wall - Michael Jackson (1979)"), which doesn't fuzzy-match "Off the Wall" in the graph.
- **Fix needed:** Strip artist name and year from album titles in LLM extraction before entity linking, or add album alias matching.

**Gap 2 — CQ14: Cross-country collaborations empty**
- **Problem:** `collaboratedWith` targets lack `countryOfOrigin`. When text extraction links "Brian Eno" to the existing MB URI, the graph has Brian Eno's country (GB) on his main artist node. But collaborations from the David Bowie text link to Brian Eno via `mh:collaboratedWith` — the query joins `?artist1 mh:collaboratedWith ?artist2` + `?artist2 mh:countryOfOrigin ?c2`, which should work IF the target URI has country data.
- **Root cause:** The `collaboratedWith` targets from text extraction may resolve to a different URI than the one with `countryOfOrigin`. Need to check if entity linking is resolving to the correct MB URI.
- **Fix needed:** Verify entity linking for collaboration targets, ensure they resolve to MB URIs that have country data.

**Gap 3 — CQ16: Multinational bands empty**
- **Problem:** Band members via `mo:member_of` are extracted from MusicBrainz artist-rels. The member nodes (e.g., John Lennon as member of The Beatles) have `rdfs:label` but not `countryOfOrigin`. Country data is only attached to artists processed as primary pipeline entries (the 25 artists in our list).
- **Root cause:** When the pipeline processes The Beatles, it finds member relationships linking to John Lennon's MBID. But John Lennon is not in our 25-artist list, so his node only has a label — no country, no birth date, etc. The country data would only be there if John Lennon were also processed as a primary artist.
- **Fix needed:** For band members discovered via relationships, propagate basic info (country, type) from MusicBrainz to their nodes. Or add key band members to the artist list.

### Additional Observations

- **CQ12 (influences sharing genres):** Returns 12 results but all are Beethoven self-referencing (he influenced himself in the Wikidata data — likely a data quality issue). Real cross-artist influence+genre matches are missing because influence targets from Wikidata (e.g., "Bob Dylan" influencing David Bowie) create `mh:artist/` URIs that don't have genre data attached.
- **CQ17 (artist labels + albums):** Shows every album for every label — the `signedTo` relationship is artist-level, not album-level, so all albums appear under all labels. This is a modelling limitation, not a bug.
- **CQ11 (award winners at labels):** 1,343 results because it's a cartesian product of awards × labels per artist. Expected behaviour but very large.
