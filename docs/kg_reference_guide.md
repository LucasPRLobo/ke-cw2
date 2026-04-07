# KG Reference Guide for SPARQL Query Writing

**KG file:** `ontology/music_history_kg.ttl` (42,840 triples)

---

## Prefixes

```sparql
PREFIX mh:     <http://example.org/music-history/>
PREFIX mo:     <http://purl.org/ontology/mo/>
PREFIX schema: <http://schema.org/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
PREFIX dc:     <http://purl.org/dc/elements/1.1/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
PREFIX owl:    <http://www.w3.org/2002/07/owl#>
```

---

## 20 Competency Questions

### Manual CQs (1-10)
1. What date was an album released?
2. What genre(s) did a given composer/artist write in?
3. What album was a given track released in?
4. Who produced a given album?
5. Which performers played in a given band/group?
6. What producer worked on albums of a given genre?
7. Who plays what instrument in a given band?
8. How many awards has a certain artist won?
9. What subgenres emerged from a given genre?
10. Which works were composed and when?

### LLM-augmented CQs (11-20)
11. Which award-winning artists were signed to a given record label?
12. Which artists that influenced a given artist share a common genre?
13. Which record labels have albums in more than 3 distinct genres?
14. Which artists collaborated with artists from a different country?
15. Which instruments are played by artists of a given genre?
16. Which bands have members from more than one country?
17. Which labels has an artist been signed to, and what albums?
18. Which composers' works involve artists from different countries?
19. Which award-winning artists collaborated with each other?
20. Which countries had artists releasing albums in a genre per decade?

---

## Classes (with instance counts)

| Class | Instances | Description |
|---|---|---|
| `mo:Track` | 1,883 | A track on an album |
| `mo:Release` | 1,350 | An album release |
| `mo:MusicArtist` | 953 | Generic music artist (when Person/Group unknown) |
| `mh:MusicalWork` | 868 | A composition (classical works, songs) |
| `mo:Genre` | 375 | A music genre |
| `mh:CoverRecording` | 373 | A cover of another artist's composition |
| `mh:Award` | 279 | A music award instance |
| `mo:MusicGroup` | 151 | A band or ensemble |
| `mo:SoloMusicArtist` | 137 | An individual musician |
| `mh:RecordLabel` | 125 | A record label |
| `mo:Instrument` | 59 | A musical instrument |
| `mh:AwardWinningArtist` | 51 | *Defined class:* artist who won an award |
| `mh:CollaboratingArtist` | 46 | *Defined class:* artist who collaborated with another |
| `mh:Country` | 20 | A country (ISO code + full name) |
| `mh:ProducerArtist` | 7 | *Defined class:* artist who produced a release |
| `mh:Venue` | 5 | A concert venue or event |
| `mh:Persona` | 5 | A stage persona / alter ego |
| `mh:MultinationalBand` | 5 | A band with members from multiple countries |
| `mh:MusicalPeriod` | 3 | A historical music period (equivalent to `mh:Era`) |
| `mh:AlbumGroup` | 1 | A named album grouping (e.g., Berlin Trilogy) |
| `mh:Organisation` | 1 | An organisation founded by an artist |

**Note:** To match any artist (solo, group, or generic), use:
```sparql
{ ?artist a mo:SoloMusicArtist } UNION
{ ?artist a mo:MusicGroup } UNION
{ ?artist a mo:MusicArtist }
```

---

## Object Properties

| Property | Triples | Domain | Range | Notes |
|---|---|---|---|---|
| `mo:genre` | 11,012 | Artist/Release/Track | Genre | Most-used property |
| `mh:hasTrack` | 1,915 | Release | Track | |
| `mh:trackOn` | 1,915 | Track | Release | Inverse of hasTrack |
| `mh:released` | 1,373 | Artist | Release | |
| `mh:releasedBy` | 1,373 | Release | Artist | Inverse of released |
| `mh:composed` | 1,059 | Artist | MusicalWork | |
| `mh:composedBy` | 1,059 | MusicalWork | Artist | Inverse of composed |
| `mh:wonAward` | 455 | Artist | MusicAward | |
| `mh:covers` | 373 | CoverRecording | MusicalWork | |
| `mo:performer` | 373 | CoverRecording | Artist | |
| `mh:playsInstrument` | 240 | Artist | Instrument | |
| `mh:signedTo` | 226 | Artist | RecordLabel | |
| `mo:member_of` | 219 | Artist | MusicGroup | |
| `mh:subgenreOf` | 198 | Genre | Genre | **Transitive** |
| `mh:influencedBy` | 159 | Artist | Artist/Person | |
| `mh:influenced` | 159 | Artist/Person | Artist | Inverse of influencedBy |
| `mh:countryOfOrigin` | 141 | Artist | Country | |
| `mh:collaboratedWith` | 76 | Artist | Artist | **Symmetric** (both directions materialized) |
| `mh:produced` | 19 | Artist | Release | |
| `mh:producedBy` | 15 | Release | Artist | Inverse of produced |
| `mh:hasMember` | 13 | MusicGroup | SoloMusicArtist | |
| `mh:pioneerOf` | 10 | Artist | Genre | |
| `mh:albumGrouping` | 8 | Release | AlbumGroup | |
| `mh:performedAt` | 5 | Artist | Venue | |
| `mh:hasMusicalPeriod` | 5 | Artist | MusicalPeriod | |
| `mh:alterEgo` | 5 | Artist | Persona | |
| `mh:founded` | 4 | Artist | Organisation | |

---

## Datatype Properties

| Property | Triples | Domain | XSD Type | Example |
|---|---|---|---|---|
| `dc:title` | 3,192 | Release/Track | string | `"Abbey Road"@en` |
| `mh:duration` | 1,623 | Track | `xsd:integer` | `243000` (milliseconds) |
| `mh:releaseDate` | 1,283 | Release | `xsd:date` / `xsd:gYear` | `"1969-09-26"^^xsd:date` or `"1969"^^xsd:gYear` |
| `mh:compositionDate` | 494 | MusicalWork | `xsd:date` / `xsd:gYear` | `"1824"^^xsd:gYear` |
| `foaf:name` | 58 | Artist | string | `"David Bowie"@en` |
| `schema:birthDate` | 57 | Artist | `xsd:date` / `xsd:gYear` | `"1947-01-08"^^xsd:date` |
| `mh:birthPlace` | 57 | Artist | `xsd:string` | `"Brixton"@en` |
| `schema:gender` | 48 | Artist | string | `"Male"@en` |
| `mh:realName` | 47 | Artist | `xsd:string` | `"David Robert Jones"@en` |
| `schema:deathDate` | 42 | Artist | `xsd:date` / `xsd:gYear` | `"2016-01-10"^^xsd:date` |

---

## OWL2 Features in the Ontology

| Feature | Detail |
|---|---|
| **Symmetric** | `mh:collaboratedWith` — if A collabs with B, B collabs with A |
| **Transitive** | `mh:subgenreOf` — enables genre hierarchy traversal |
| **5 Inverse pairs** | `released/releasedBy`, `hasTrack/trackOn`, `composed/composedBy`, `influencedBy/influenced`, `produced/producedBy` |
| **3 Defined classes** | `AwardWinningArtist` (won award), `CollaboratingArtist` (has collab), `ProducerArtist` (produced release) — via `owl:equivalentClass` |
| **2 Disjoint axioms** | `SoloMusicArtist` disjoint with `MusicGroup`; `Track` disjoint with `Release` |
| **1 Equivalence** | `mh:MusicalPeriod` equivalent to `mh:Era` |
| **Subproperties** | `mh:collaboratedWith` subPropertyOf `mo:collaborated_with`; `mh:signedTo` subPropertyOf `schema:affiliation`; `mh:countryOfOrigin` subPropertyOf `schema:nationality` |

---

## Important Notes for Query Writing

1. **Language tags**: Labels use `@en`. To get the string value, use `STR(?label)` or match with `FILTER(LANG(?label) = "en")`
2. **Dates vary in precision**: Some are full dates (`"1969-09-26"^^xsd:date`), some are just years (`"1969"^^xsd:gYear`). Use `STR(?date)` and `SUBSTR()` for decade extraction.
3. **Countries**: Each country has two labels — ISO code (`"US"`) and full name (`"United States"`). Both are `@en` tagged.
4. **Inverse triples are materialized**: You can query `?album mh:releasedBy ?artist` instead of `?artist mh:released ?album`. Both work.
5. **Artist types**: Use UNION pattern (shown above) to match all artist subtypes, or query `mo:MusicArtist` for generic ones.
6. **Entity names**: Use `rdfs:label` for display names, `foaf:name` for the 58 primary artists, `dc:title` for albums/tracks.

---

## Example Query

```sparql
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# CQ1: What date was an album released?
SELECT ?album ?title ?date WHERE {
    ?album a mo:Release ;
           rdfs:label ?title ;
           mh:releaseDate ?date .
}
ORDER BY ?date
LIMIT 20
```
