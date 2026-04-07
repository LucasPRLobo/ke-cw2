#!/usr/bin/env python3
"""Run all .rq SPARQL queries against the music history knowledge graph."""

import glob
import os
import sys

import rdflib

TTL_PATH = os.path.join(os.path.dirname(__file__), "..", "ontology", "music_history_kg.ttl")
QUERIES_DIR = os.path.dirname(__file__)


def main():
    g = rdflib.Graph()
    g.parse(TTL_PATH, format="turtle")
    print(f"Loaded {len(g)} triples from {os.path.basename(TTL_PATH)}\n")

    rq_files = sorted(glob.glob(os.path.join(QUERIES_DIR, "*.rq")))
    if not rq_files:
        print("No .rq files found.")
        sys.exit(1)

    passed = 0
    for path in rq_files:
        fname = os.path.basename(path)
        # Extract CQ number from filename like cq01.rq
        tag = fname.replace(".rq", "").upper().replace("CQ", "CQ")
        with open(path) as f:
            query = f.read()
        results = list(g.query(query))
        n = len(results)
        if n > 0:
            passed += 1
        print(f"[{tag}] {fname} — {n} results")
        for row in results[:3]:
            cols = []
            for val in row:
                s = str(val) if val is not None else "None"
                if len(s) > 80:
                    s = s[:77] + "..."
                cols.append(s)
            print(f"    {' | '.join(cols)}")
        print()

    total = len(rq_files)
    print(f"{passed}/{total} queries returned results")


if __name__ == "__main__":
    main()
