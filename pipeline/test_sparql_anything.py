"""Test SPARQL Anything CONSTRUCT queries against cached JSON files.

Demonstrates the Week 8 course technique: mapping structured data to RDF
using SPARQL CONSTRUCT queries via SPARQL Anything (Facade-X model).
"""
import os
import tempfile
from urllib.parse import quote

from utils import run_sparql_anything

# Paths — use file:// URI with encoded spaces
MB_JSON = "file://" + quote(os.path.abspath("data/structured/musicbrainz_David_Bowie.json"))
DC_JSON = "file://" + quote(os.path.abspath("data/structured/discogs_David_Bowie.json"))
QUERY_DIR = "sparql_anything"
OUTPUT_DIR = "sparql_anything/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_query_with_file(query_template_path, json_path, output_path):
    """Read a SPARQL query template, inject the file path, write to temp file, run."""
    with open(query_template_path) as f:
        query_text = f.read()

    # Replace placeholder with actual absolute file path
    query_text = query_text.replace("PLACEHOLDER_FILE_PATH", json_path)

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".sparql", delete=False)
    tmp.write(query_text)
    tmp.close()

    try:
        run_sparql_anything(tmp.name, output_path)
    finally:
        os.unlink(tmp.name)


# Test 1: Map MusicBrainz artist data
print("=" * 60)
print("Test 1: MusicBrainz artist → RDF (SPARQL Anything)")
print("=" * 60)

mb_query = os.path.join(QUERY_DIR, "map_artist.sparql")
mb_output = os.path.join(OUTPUT_DIR, "artist_bowie.ttl")

try:
    run_query_with_file(mb_query, MB_JSON, mb_output)
    if os.path.exists(mb_output) and os.path.getsize(mb_output) > 0:
        with open(mb_output) as f:
            content = f.read()
        lines = content.strip().split("\n")
        print(f"  Output: {mb_output}")
        print(f"  Lines: {len(lines)}")
        print(f"  Preview:\n")
        print("\n".join(lines[:30]))
    else:
        print("  No output generated — check query syntax")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Map Discogs genre/style hierarchy
print(f"\n{'='*60}")
print("Test 2: Discogs genres/styles → RDF (SPARQL Anything)")
print("=" * 60)

dc_query = os.path.join(QUERY_DIR, "map_discogs_genres.sparql")
dc_output = os.path.join(OUTPUT_DIR, "genres_bowie.ttl")

try:
    run_query_with_file(dc_query, DC_JSON, dc_output)
    if os.path.exists(dc_output) and os.path.getsize(dc_output) > 0:
        with open(dc_output) as f:
            content = f.read()
        lines = content.strip().split("\n")
        print(f"  Output: {dc_output}")
        print(f"  Lines: {len(lines)}")
        print(f"  Preview:\n")
        print("\n".join(lines[:30]))
    else:
        print("  No output generated — check query syntax")
except Exception as e:
    print(f"  ERROR: {e}")

print(f"\n{'='*60}")
print("SPARQL Anything test complete")
print("=" * 60)
