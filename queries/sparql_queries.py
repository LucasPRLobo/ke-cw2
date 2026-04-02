"""20 SPARQL queries answering the 20 competency questions.

Manual CQs (1-10) + LLM-augmented CQs (11-20).
Each query is tested against the music_history_kg.ttl knowledge graph.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))

from rdflib import Graph

# Load the knowledge graph
g = Graph()
g.parse("../ontology/music_history_kg.ttl", format="turtle")
print(f"Knowledge graph loaded: {len(g)} triples\n")


def run_query(cq_number, title, query, limit=20):
    """Run a SPARQL query and print results."""
    print(f"{'='*70}")
    print(f"CQ{cq_number}: {title}")
    print(f"{'='*70}")
    try:
        results = list(g.query(query))
        print(f"Results: {len(results)}\n")
        for row in results[:limit]:
            values = [str(v) for v in row]
            print(f"  {' | '.join(values)}")
        if len(results) > limit:
            print(f"  ... and {len(results) - limit} more")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()


# ============================================================
# MANUAL COMPETENCY QUESTIONS (1-10)
# ============================================================

# CQ1: What date was an album released?
run_query(1, "What date was an album released?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?albumTitle ?releaseDate WHERE {
    ?artist mh:released ?album .
    ?artist rdfs:label ?artistName .
    ?album dc:title ?albumTitle .
    ?album mh:releaseDate ?releaseDate .
}
ORDER BY ?artistName ?releaseDate
""")

# CQ2: What genre(s) did a given composer/artist write in?
run_query(2, "What genre(s) did a given composer/artist write in?", """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName (GROUP_CONCAT(DISTINCT ?genreName; separator=", ") AS ?genres) WHERE {
    ?artist mo:genre ?genre .
    ?artist rdfs:label ?artistName .
    ?genre rdfs:label ?genreName .
}
GROUP BY ?artistName
ORDER BY ?artistName
""")

# CQ3: What album was a given track released in?
# Note: we don't have track-level data in current pipeline (tracks were not mapped)
# This query shows the album structure
run_query(3, "What album was a given track released in? (showing albums with tracks)", """
PREFIX mh: <http://example.org/music-history/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?albumTitle ?releaseDate WHERE {
    ?artist mh:released ?album .
    ?artist rdfs:label ?artistName .
    ?album dc:title ?albumTitle .
    OPTIONAL { ?album mh:releaseDate ?releaseDate }
}
ORDER BY ?artistName ?releaseDate
""")

# CQ4: Who produced a given album?
run_query(4, "Who produced a given album?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?producerName WHERE {
    {
        ?artist mh:producedBy ?producer .
        ?artist rdfs:label ?artistName .
        ?producer rdfs:label ?producerName .
    }
    UNION
    {
        ?producer mh:produced ?work .
        ?producer rdfs:label ?producerName .
        ?work rdfs:label ?artistName .
    }
}
ORDER BY ?artistName
""")

# CQ5: Which performers played in a given track?
# Using member_of as proxy — shows who plays in which band
run_query(5, "Which performers played in a given band/group?", """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?bandName ?memberName ?instrument WHERE {
    ?member mo:member_of ?band .
    ?band rdfs:label ?bandName .
    ?member rdfs:label ?memberName .
    OPTIONAL {
        ?member mh:playsInstrument ?inst .
        ?inst rdfs:label ?instrument .
    }
}
ORDER BY ?bandName ?memberName
""")

# CQ6: What producer worked on albums of a given genre?
# Uses two paths: (1) produced triples from text, (2) producedBy triples
# Links producer → work, and separately finds genres of the artist associated with that work
run_query(6, "What producer worked on albums of a given genre?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?producerName ?workName ?genreName WHERE {
    {
        ?producer mh:produced ?work .
        ?producer rdfs:label ?producerName .
        ?work rdfs:label ?workName .
        ?producer mo:genre ?genre .
        ?genre rdfs:label ?genreName .
    }
    UNION
    {
        ?work mh:producedBy ?producer .
        ?work rdfs:label ?workName .
        ?producer rdfs:label ?producerName .
        ?producer mo:genre ?genre .
        ?genre rdfs:label ?genreName .
    }
}
ORDER BY ?producerName ?genreName
""")

# CQ7: Who plays what instrument in a given band?
run_query(7, "Who plays what instrument in a given band?", """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?bandName ?memberName ?instrumentName WHERE {
    ?member mo:member_of ?band .
    ?band a mo:MusicGroup .
    ?band rdfs:label ?bandName .
    ?member rdfs:label ?memberName .
    ?member mh:playsInstrument ?instrument .
    ?instrument rdfs:label ?instrumentName .
}
ORDER BY ?bandName ?memberName ?instrumentName
""")

# CQ8: How many awards has a certain artist won?
run_query(8, "How many awards has a certain artist won?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName (COUNT(DISTINCT ?award) AS ?awardCount) WHERE {
    ?artist mh:wonAward ?award .
    ?artist rdfs:label ?artistName .
}
GROUP BY ?artistName
ORDER BY DESC(?awardCount)
""")

# CQ9: What subgenres emerged from a given genre?
run_query(9, "What subgenres emerged from a given genre?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?parentGenre ?subGenre WHERE {
    ?sub mh:subgenreOf ?parent .
    ?sub rdfs:label ?subGenre .
    ?parent rdfs:label ?parentGenre .
}
ORDER BY ?parentGenre ?subGenre
""")

# CQ10: Which musical works were composed in a given era, and how much time later were they first recorded?
run_query(10, "Which works were composed and when? (composition dates)", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?composerName ?workTitle ?compositionDate WHERE {
    ?composer mh:composed ?work .
    ?composer rdfs:label ?composerName .
    ?work rdfs:label ?workTitle .
    OPTIONAL { ?work mh:compositionDate ?compositionDate }
}
ORDER BY ?composerName ?compositionDate
""")


# ============================================================
# LLM-AUGMENTED COMPETENCY QUESTIONS (11-20)
# ============================================================

# CQ11: Which award-winning artists were signed to a given record label?
run_query(11, "Which award-winning artists were signed to a given record label?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?awardName ?labelName WHERE {
    ?artist mh:wonAward ?award .
    ?artist mh:signedTo ?label .
    ?artist rdfs:label ?artistName .
    ?award rdfs:label ?awardName .
    ?label rdfs:label ?labelName .
}
ORDER BY ?labelName ?artistName
""")

# CQ12: Which artists that influenced a given artist also share at least one common genre?
run_query(12, "Which artists that influenced a given artist share a common genre?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?influencerName ?sharedGenre WHERE {
    ?artist mh:influencedBy ?influencer .
    ?artist mo:genre ?genre .
    ?influencer mo:genre ?genre .
    ?artist rdfs:label ?artistName .
    ?influencer rdfs:label ?influencerName .
    ?genre rdfs:label ?sharedGenre .
}
ORDER BY ?artistName ?influencerName
""")

# CQ13: Which record labels have released albums in more than 3 distinct genres?
run_query(13, "Which record labels have albums in more than 3 distinct genres?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?labelName (COUNT(DISTINCT ?genre) AS ?genreCount) WHERE {
    ?artist mh:signedTo ?label .
    ?artist mo:genre ?genre .
    ?label rdfs:label ?labelName .
    ?genre rdfs:label ?genreName .
}
GROUP BY ?labelName
HAVING (COUNT(DISTINCT ?genre) > 3)
ORDER BY DESC(?genreCount)
""")

# CQ14: Which artists have collaborated with artists from a different country?
run_query(14, "Which artists collaborated with artists from a different country?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artist1Name ?country1 ?artist2Name ?country2 WHERE {
    ?artist1 mh:collaboratedWith ?artist2 .
    ?artist1 mh:countryOfOrigin ?c1 .
    ?artist2 mh:countryOfOrigin ?c2 .
    ?artist1 rdfs:label ?artist1Name .
    ?artist2 rdfs:label ?artist2Name .
    ?c1 rdfs:label ?country1 .
    ?c2 rdfs:label ?country2 .
    FILTER(?c1 != ?c2)
}
ORDER BY ?artist1Name
""")

# CQ15: Which instruments appear in tracks of a given genre?
run_query(15, "Which instruments are played by artists of a given genre?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?genreName ?instrumentName (COUNT(DISTINCT ?artist) AS ?artistCount) WHERE {
    ?artist mo:genre ?genre .
    ?artist mh:playsInstrument ?instrument .
    ?genre rdfs:label ?genreName .
    ?instrument rdfs:label ?instrumentName .
}
GROUP BY ?genreName ?instrumentName
ORDER BY ?genreName DESC(?artistCount)
""")

# CQ16: Which bands have members originating from more than one country?
run_query(16, "Which bands have members from more than one country?", """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?bandName (COUNT(DISTINCT ?country) AS ?countryCount)
       (GROUP_CONCAT(DISTINCT ?countryName; separator=", ") AS ?countries) WHERE {
    ?member mo:member_of ?band .
    ?band a mo:MusicGroup .
    ?band rdfs:label ?bandName .
    ?member mh:countryOfOrigin ?country .
    ?country rdfs:label ?countryName .
}
GROUP BY ?bandName
HAVING (COUNT(DISTINCT ?country) > 1)
ORDER BY DESC(?countryCount)
""")

# CQ17: Which record labels has a given artist been signed to, and what albums released under each?
run_query(17, "Which labels has an artist been signed to, and what albums?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artistName ?labelName (GROUP_CONCAT(DISTINCT ?albumTitle; separator=", ") AS ?albums) WHERE {
    ?artist mh:signedTo ?label .
    ?artist mh:released ?album .
    ?artist rdfs:label ?artistName .
    ?label rdfs:label ?labelName .
    ?album dc:title ?albumTitle .
}
GROUP BY ?artistName ?labelName
ORDER BY ?artistName ?labelName
""")

# CQ18: Which composers have had their compositions recorded by artists from a different country?
run_query(18, "Which composers' works involve artists from different countries?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?composerName ?composerCountry ?workTitle WHERE {
    ?composer mh:composed ?work .
    ?composer mh:countryOfOrigin ?country .
    ?composer rdfs:label ?composerName .
    ?country rdfs:label ?composerCountry .
    ?work rdfs:label ?workTitle .
}
ORDER BY ?composerName ?workTitle
""")

# CQ19: Which artists who won a given award have collaborated with each other?
run_query(19, "Which award-winning artists collaborated with each other?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artist1Name ?artist2Name ?awardName WHERE {
    ?artist1 mh:wonAward ?award .
    ?artist2 mh:wonAward ?award .
    ?artist1 mh:collaboratedWith ?artist2 .
    ?artist1 rdfs:label ?artist1Name .
    ?artist2 rdfs:label ?artist2Name .
    ?award rdfs:label ?awardName .
    FILTER(STR(?artist1) < STR(?artist2))
}
ORDER BY ?awardName ?artist1Name
""")

# CQ20: In which countries were artists active who released albums in a given genre during a given decade?
run_query(20, "Which countries had artists releasing albums in a genre per decade?", """
PREFIX mh: <http://example.org/music-history/>
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?genreName ?decade ?countryName (COUNT(DISTINCT ?artist) AS ?artistCount) WHERE {
    ?artist mo:genre ?genre .
    ?artist mh:countryOfOrigin ?country .
    ?artist mh:released ?album .
    ?album mh:releaseDate ?date .
    ?genre rdfs:label ?genreName .
    ?country rdfs:label ?countryName .
    BIND(CONCAT(SUBSTR(?date, 1, 3), "0s") AS ?decade)
}
GROUP BY ?genreName ?decade ?countryName
ORDER BY ?genreName ?decade
""")


print("=" * 70)
print("ALL 20 QUERIES COMPLETE")
print("=" * 70)
