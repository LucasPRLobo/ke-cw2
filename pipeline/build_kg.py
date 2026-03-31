"""Main pipeline: fetch all sources and build the complete knowledge graph."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ARTISTS
from sources.musicbrainz import fetch_artist as mb_fetch
from sources.discogs import fetch_artist as dc_fetch
from sources.wikidata import fetch_artist as wd_fetch
from sources.wikipedia import fetch_artist as wp_fetch
from mapping.structured import create_graph, map_artist, enrich_related_artists, consolidate_uris, assign_types_to_orphans
from mapping.text import map_text_triples
from ontology_header import add_ontology_header


def build_knowledge_graph(artist_list, output_path="../ontology/music_history_kg.ttl"):
    """Build the complete knowledge graph from all sources.

    Args:
        artist_list: list of artist name strings
        output_path: where to save the .ttl file
    """
    g = create_graph()

    # Step 0: Add ontology header (class/property declarations + extensions)
    add_ontology_header(g)
    print(f"Ontology header added: {len(g)} triples")

    total = len(artist_list)
    failed = []

    for i, artist_name in enumerate(artist_list, 1):
        print(f"\n[{i}/{total}] {artist_name}")
        print("-" * 40)

        try:
            # Step 1: MusicBrainz (hub)
            mb = mb_fetch(artist_name)
            if mb is None:
                print(f"  SKIPPED — not found in MusicBrainz")
                failed.append(artist_name)
                continue

            # Step 2: Discogs (via cross-ref)
            try:
                dc = dc_fetch(mb.get("discogs_id"), artist_name)
            except Exception as e:
                print(f"  [DC] Error: {e} — continuing without Discogs")
                dc = None

            # Step 3: Wikidata (via cross-ref)
            try:
                wd = wd_fetch(mb.get("wikidata_id"), artist_name)
            except Exception as e:
                print(f"  [WD] Error: {e} — continuing without Wikidata")
                wd = None

            # Step 4: Wikipedia (via Wikidata title)
            try:
                wp_title = wd.get("wikipedia_title") if wd else None
                wp = wp_fetch(wp_title, artist_name) if wp_title else None
            except Exception as e:
                print(f"  [WP] Error: {e} — continuing without Wikipedia")
                wp = None

            # Step 5: Map structured data to RDF
            map_artist(g, mb, dc, wd)

            # Step 6: Enrich with LLM text extraction (if available)
            map_text_triples(g, artist_name)

            print(f"  Done — graph now has {len(g)} triples")

        except Exception as e:
            print(f"  ERROR: {e}")
            failed.append(artist_name)

    # Step 7: Enrich related artists (add country data to members/collaborators)
    print(f"\n{'='*60}")
    print("ENRICHMENT PASS — adding country data to related artists")
    print(f"{'='*60}")
    enrich_related_artists(g)
    print(f"Graph after enrichment: {len(g)} triples")

    # Step 8: Consolidate duplicate URIs (mh:artist/ → mb:)
    print(f"\n{'='*60}")
    print("URI CONSOLIDATION — merging duplicate artist URIs")
    print(f"{'='*60}")
    consolidate_uris(g)
    print(f"Graph after consolidation: {len(g)} triples")

    # Step 9: Assign types to orphan entities
    print(f"\n{'='*60}")
    print("TYPE ASSIGNMENT — adding rdf:type to untyped entities")
    print(f"{'='*60}")
    assign_types_to_orphans(g)
    print(f"Graph after type assignment: {len(g)} triples")

    # Save
    g.serialize(destination=output_path, format="turtle")
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"  Artists processed: {total - len(failed)}/{total}")
    print(f"  Failed: {failed if failed else 'none'}")
    print(f"  Total triples: {len(g)}")
    print(f"  Saved to: {output_path}")
    print(f"{'='*60}")

    return g


if __name__ == "__main__":
    build_knowledge_graph(ARTISTS)
