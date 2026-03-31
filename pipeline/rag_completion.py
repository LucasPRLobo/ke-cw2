"""RAG-based KG Completion — Prompt Generator.

Implements the Week 11 approach: KG as SPARQL-based retrieval source.
Pipeline:
  1. Run SPARQL query against the KG (retrieval)
  2. Verbalise returned triples into natural language
  3. Build augmented prompt with KG context
  4. Print prompt → user pastes into LLM chat
  5. User pastes response back → save to file

Usage: python rag_completion.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph, Namespace

# Load KG
g = Graph()
g.parse("../ontology/music_history_kg.ttl", format="turtle")
print(f"KG loaded: {len(g)} triples\n")

MH = Namespace("http://example.org/music-history/")
MO = Namespace("http://purl.org/ontology/mo/")


def retrieve_and_verbalise(title, sparql_query, format_fn):
    """Steps 1-2: Run SPARQL, verbalise results."""
    results = list(g.query(sparql_query))
    context = format_fn(results)
    return results, context


def print_prompt(number, title, context, task):
    """Step 3: Print the augmented prompt for manual LLM use."""
    print("=" * 70)
    print(f"RAG PROMPT {number}: {title}")
    print("=" * 70)
    print(f"SPARQL retrieved {len(context.splitlines())} lines of context")
    print()
    print("--- COPY BELOW THIS LINE ---")
    print()
    prompt = f"""You are a music historian helping to complete a knowledge graph about music history.

CONTEXT FROM OUR KNOWLEDGE GRAPH:
{context}

TASK:
{task}

Return ONLY valid JSON. No explanations."""
    print(prompt)
    print()
    print("--- COPY ABOVE THIS LINE ---")
    print()


# ============================================================
# RAG PROMPT 1: Fill missing producer relationships
# ============================================================
q1 = """
PREFIX mh: <http://example.org/music-history/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?albumTitle ?releaseDate WHERE {
    ?artist rdfs:label "David Bowie" .
    ?artist mh:released ?album .
    ?album dc:title ?albumTitle .
    OPTIONAL { ?album mh:releaseDate ?releaseDate }
}
ORDER BY ?releaseDate
LIMIT 15
"""

results1 = list(g.query(q1))
context1 = "David Bowie's albums in our knowledge graph:\n"
for row in results1:
    date = f" ({row.releaseDate})" if row.releaseDate else ""
    context1 += f"  - {row.albumTitle}{date}\n"

print_prompt(1, "Missing producers for David Bowie's albums",
    context1,
    "For each album listed above, who was the primary producer? "
    "Return as JSON array: [{\"album\": \"...\", \"producer\": \"...\"}]"
)


# ============================================================
# RAG PROMPT 2: Fill missing country data
# ============================================================
q2 = """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?artistName WHERE {
    { ?artist a mo:SoloMusicArtist } UNION { ?artist a mo:MusicGroup }
    ?artist rdfs:label ?artistName .
    FILTER NOT EXISTS { ?artist mh:countryOfOrigin ?c }
}
ORDER BY ?artistName
LIMIT 15
"""

results2 = list(g.query(q2))
context2 = "These musicians in our knowledge graph are missing country of origin:\n"
for row in results2:
    context2 += f"  - {row.artistName}\n"

print_prompt(2, "Missing country data for artists",
    context2,
    "For each musician listed above, what is their country of origin? "
    "Use ISO 2-letter country codes. "
    "Return as JSON array: [{\"artist\": \"...\", \"country_code\": \"...\", \"country_name\": \"...\"}]"
)


# ============================================================
# RAG PROMPT 3: Fill missing genres for influence targets
# ============================================================
q3 = """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?influencerName
       (GROUP_CONCAT(DISTINCT ?influencedName; separator=", ") AS ?influenced)
       (GROUP_CONCAT(DISTINCT ?genreName; separator=", ") AS ?influencedGenres)
WHERE {
    ?artist mh:influencedBy ?influencer .
    ?influencer rdfs:label ?influencerName .
    ?artist rdfs:label ?influencedName .
    OPTIONAL {
        ?artist mo:genre ?genre .
        ?genre rdfs:label ?genreName .
    }
    FILTER NOT EXISTS { ?influencer mo:genre ?g }
}
GROUP BY ?influencerName
LIMIT 10
"""

results3 = list(g.query(q3))
context3 = "These artists influenced other musicians but we don't know their genres:\n\n"
for row in results3:
    influenced = str(row.influenced) if row.influenced else "unknown"
    genres = str(row.influencedGenres) if row.influencedGenres else "unknown"
    context3 += f"  - {row.influencerName}\n"
    context3 += f"    Influenced: {influenced}\n"
    context3 += f"    Those artists play: {genres}\n\n"

print_prompt(3, "Missing genres for influence targets",
    context3,
    "Based on who these artists influenced and what genres those artists play, "
    "what genres do these influencer artists belong to? "
    "Return as JSON array: [{\"artist\": \"...\", \"genres\": [\"...\"]}]"
)


# ============================================================
# RAG vs PLAIN LLM Comparison
# ============================================================
q4 = """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?artistName (COUNT(DISTINCT ?award) AS ?awardCount) WHERE {
    ?artist mh:wonAward ?award .
    ?artist rdfs:label ?artistName .
}
GROUP BY ?artistName
ORDER BY DESC(?awardCount)
LIMIT 10
"""

results4 = list(g.query(q4))
context4 = "Award counts from our knowledge graph:\n"
for row in results4:
    context4 += f"  - {row.artistName}: {row.awardCount} awards\n"

print("=" * 70)
print("RAG vs PLAIN LLM COMPARISON")
print("=" * 70)
print()
print("Run BOTH prompts below in your LLM chat and compare the answers.")
print()
print("--- PLAIN PROMPT (no KG context) ---")
print()
print("How many awards has Quincy Jones won, and what are the most notable ones?")
print()
print("--- RAG PROMPT (with KG context) ---")
print()
print(f"""You are a music historian helping to verify and extend a knowledge graph.

CONTEXT FROM OUR KNOWLEDGE GRAPH:
{context4}
TASK:
Our KG says Quincy Jones has won 34 awards. Is this accurate? What are his most notable awards? Are there any major awards missing from our count?

Return as JSON: {{"total_awards_accurate": true/false, "notable_awards": ["..."], "missing_awards": ["..."]}}""")
print()
print("--- END ---")
