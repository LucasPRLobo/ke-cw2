"""Evaluation: KG Answers vs Plain LLM Answers.

Generates paired prompts for 5 CQs:
- KG version: runs SPARQL query, formats results
- Plain LLM version: asks the same question without KG context

User runs both in an LLM chat and compares accuracy, detail, and grounding.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph


g = Graph()
g.parse("../ontology/music_history_kg.ttl", format="turtle")
print(f"KG loaded: {len(g)} triples\n")


comparisons = [
    {
        "cq": "CQ8",
        "question": "How many awards has David Bowie won?",
        "sparql": """
            PREFIX mh: <http://example.org/music-history/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?awardName WHERE {
                ?artist rdfs:label "David Bowie"@en .
                ?artist mh:wonAward ?award .
                ?award rdfs:label ?awardName .
            }
            ORDER BY ?awardName
        """,
    },
    {
        "cq": "CQ7",
        "question": "What instruments does John Lennon play?",
        "sparql": """
            PREFIX mh: <http://example.org/music-history/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?instrumentName WHERE {
                ?artist rdfs:label "John Lennon"@en .
                ?artist mh:playsInstrument ?inst .
                ?inst rdfs:label ?instrumentName .
            }
            ORDER BY ?instrumentName
        """,
    },
    {
        "cq": "CQ9",
        "question": "What subgenres emerged from rock music?",
        "sparql": """
            PREFIX mh: <http://example.org/music-history/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?subgenre WHERE {
                ?sub mh:subgenreOf ?parent .
                ?parent rdfs:label "rock"@en .
                ?sub rdfs:label ?subgenre .
            }
            ORDER BY ?subgenre
        """,
    },
    {
        "cq": "CQ12",
        "question": "Which artists influenced David Bowie and share a common genre with him?",
        "sparql": """
            PREFIX mh: <http://example.org/music-history/>
            PREFIX mo: <http://purl.org/ontology/mo/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?influencerName ?sharedGenre WHERE {
                ?artist rdfs:label "David Bowie"@en .
                ?artist mh:influencedBy ?influencer .
                ?artist mo:genre ?genre .
                ?influencer mo:genre ?genre .
                ?influencer rdfs:label ?influencerName .
                ?genre rdfs:label ?sharedGenre .
            }
            ORDER BY ?influencerName
        """,
    },
    {
        "cq": "CQ20",
        "question": "Which countries had artists releasing jazz albums in the 1960s?",
        "sparql": """
            PREFIX mh: <http://example.org/music-history/>
            PREFIX mo: <http://purl.org/ontology/mo/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?countryName WHERE {
                ?artist mo:genre ?genre .
                ?genre rdfs:label "jazz"@en .
                ?artist mh:countryOfOrigin ?country .
                ?country rdfs:label ?countryName .
                ?artist mh:released ?album .
                ?album mh:releaseDate ?date .
                FILTER(STRSTARTS(STR(?date), "196"))
            }
        """,
    },
]


print("=" * 70)
print("KG vs PLAIN LLM COMPARISON")
print("For each CQ, compare the KG answer with a plain LLM answer.")
print("=" * 70)

results = {}

for comp in comparisons:
    cq = comp["cq"]
    question = comp["question"]

    print(f"\n{'='*70}")
    print(f"{cq}: {question}")
    print(f"{'='*70}")

    # Run SPARQL
    try:
        rows = list(g.query(comp["sparql"]))
        values = []
        for row in rows:
            vals = [str(v) for v in row]
            values.append(" | ".join(vals))

        print(f"\n  KG ANSWER ({len(rows)} results):")
        for v in values[:15]:
            print(f"    - {v}")
        if len(values) > 15:
            print(f"    ... and {len(values) - 15} more")
    except Exception as e:
        values = []
        print(f"  KG ERROR: {e}")

    # Generate plain LLM prompt
    print(f"\n  PLAIN LLM PROMPT (paste into LLM chat):")
    print(f"    \"{question}\"")

    # Generate RAG prompt
    kg_context = "\n".join(f"  - {v}" for v in values[:20])
    print(f"\n  RAG PROMPT (paste into LLM chat):")
    print(f"    \"Our knowledge graph returns these results for '{question}':")
    print(f"    {kg_context}")
    print(f"    Are these results complete and accurate? What might be missing?\"")

    results[cq] = {
        "question": question,
        "kg_results_count": len(rows),
        "kg_results_sample": values[:20],
    }

# Save
output_path = "../docs/eval_kg_vs_llm.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'='*70}")
print("INSTRUCTIONS:")
print("1. For each CQ above, paste the PLAIN LLM PROMPT into a chat")
print("2. Then paste the RAG PROMPT into the same chat")
print("3. Compare: which answer is more accurate, detailed, grounded?")
print("4. Document the comparison in the report")
print(f"{'='*70}")
print(f"\nResults saved to {output_path}")
