"""Evaluation: Pipeline Performance Metrics.

Measures time, memory, per-stage timing, per-source contribution,
and output statistics for the automated KG construction pipeline.
"""
import sys
import os
import time
import tracemalloc
import json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph, Namespace, RDF, RDFS
from config import ARTISTS

MO = Namespace("http://purl.org/ontology/mo/")
MH = Namespace("http://example.org/music-history/")


def measure_pipeline_with_stages():
    """Measure pipeline performance with per-stage timing."""
    from sources.musicbrainz import fetch_artist as mb_fetch
    from sources.discogs import fetch_artist as dc_fetch
    from sources.wikidata import fetch_artist as wd_fetch
    from sources.wikipedia import fetch_artist as wp_fetch
    from mapping.structured import create_graph, map_artist, enrich_related_artists, consolidate_uris, assign_types_to_orphans
    from mapping.text import map_text_triples
    from ontology_header import add_ontology_header

    tracemalloc.start()
    total_start = time.time()

    # Stage 0: Ontology header
    stage0_start = time.time()
    g = create_graph()
    add_ontology_header(g)
    stage0_time = time.time() - stage0_start
    stage0_triples = len(g)

    # Stage 1: Data fetching + structured mapping
    stage1_start = time.time()
    artist_times = []
    triples_before_text = 0

    for artist_name in ARTISTS:
        artist_start = time.time()
        mb = mb_fetch(artist_name)
        if mb is None:
            continue
        dc = dc_fetch(mb.get("discogs_id"), artist_name)
        wd = wd_fetch(mb.get("wikidata_id"), artist_name)
        wp_title = wd.get("wikipedia_title") if wd else None
        wp = wp_fetch(wp_title, artist_name) if wp_title else None
        map_artist(g, mb, dc, wd)
        artist_time = time.time() - artist_start
        artist_times.append({"artist": artist_name, "time_seconds": round(artist_time, 3)})

    stage1_time = time.time() - stage1_start
    triples_after_structured = len(g)

    # Stage 2: Text mapping
    stage2_start = time.time()
    for artist_name in ARTISTS:
        map_text_triples(g, artist_name)
    stage2_time = time.time() - stage2_start
    triples_after_text = len(g)

    # Stage 3: Enrichment
    stage3_start = time.time()
    enrich_related_artists(g, mb_rate_limit=0)
    stage3_time = time.time() - stage3_start
    triples_after_enrich = len(g)

    # Stage 4: URI consolidation
    stage4_start = time.time()
    consolidate_uris(g)
    stage4_time = time.time() - stage4_start
    triples_after_consolidation = len(g)

    # Stage 5: Type assignment
    stage5_start = time.time()
    assign_types_to_orphans(g)
    stage5_time = time.time() - stage5_start
    triples_final = len(g)

    total_time = time.time() - total_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stages = {
        "0_ontology_header": {"time_seconds": round(stage0_time, 3), "triples_added": stage0_triples},
        "1_structured_mapping": {"time_seconds": round(stage1_time, 3), "triples_added": triples_after_structured - stage0_triples},
        "2_text_mapping": {"time_seconds": round(stage2_time, 3), "triples_added": triples_after_text - triples_after_structured},
        "3_enrichment": {"time_seconds": round(stage3_time, 3), "triples_added": triples_after_enrich - triples_after_text},
        "4_uri_consolidation": {"time_seconds": round(stage4_time, 3), "triples_added": triples_after_consolidation - triples_after_enrich},
        "5_type_assignment": {"time_seconds": round(stage5_time, 3), "triples_added": triples_final - triples_after_consolidation},
    }

    return g, {
        "total_time_seconds": round(total_time, 2),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "current_memory_mb": round(current / 1024 / 1024, 2),
        "artist_count": len(ARTISTS),
        "avg_time_per_artist": round(sum(t["time_seconds"] for t in artist_times) / len(artist_times), 3),
        "stages": stages,
        "artist_times": artist_times,
    }


def measure_source_contribution(g):
    """Measure how many triples each source contributes."""

    # Count triples by predicate namespace to estimate source contribution
    mb_predicates = {"member_of", "released", "hasTrack", "duration"}
    dc_predicates = {"subgenreOf", "realName"}
    wd_predicates = {"wonAward", "signedTo", "composed", "compositionDate"}
    schema_predicates = {"birthDate", "deathDate", "gender"}
    text_predicates = {"alterEgo", "albumGrouping", "pioneerOf", "founded", "hasMusicalPeriod"}
    shared_predicates = {"genre", "playsInstrument", "influencedBy", "countryOfOrigin", "collaboratedWith", "producedBy", "produced"}

    pred_counts = defaultdict(int)
    for s, p, o in g:
        short = str(p).split("/")[-1].split("#")[-1]
        pred_counts[short] += 1

    mb_triples = sum(pred_counts.get(p, 0) for p in mb_predicates)
    dc_triples = sum(pred_counts.get(p, 0) for p in dc_predicates)
    wd_triples = sum(pred_counts.get(p, 0) for p in wd_predicates)
    schema_triples = sum(pred_counts.get(p, 0) for p in schema_predicates)
    text_triples = sum(pred_counts.get(p, 0) for p in text_predicates)
    shared_triples = sum(pred_counts.get(p, 0) for p in shared_predicates)
    metadata_triples = sum(pred_counts.get(p, 0) for p in ["label", "type", "title", "name", "comment", "domain", "range", "subClassOf", "subPropertyOf"])

    return {
        "musicbrainz_exclusive": mb_triples,
        "discogs_exclusive": dc_triples,
        "wikidata_exclusive": wd_triples,
        "schema_org": schema_triples,
        "text_extraction_exclusive": text_triples,
        "shared_across_sources": shared_triples,
        "metadata_and_ontology": metadata_triples,
        "total": len(g),
    }


def measure_output_stats(g):
    """Measure output KG statistics."""
    type_counts = defaultdict(int)
    for s, p, o in g.triples((None, RDF.type, None)):
        t = str(o).split("/")[-1].split("#")[-1]
        if t not in ("Class", "ObjectProperty", "DatatypeProperty", "Ontology"):
            type_counts[t] += 1

    pred_counts = defaultdict(int)
    for s, p, o in g:
        pred_counts[str(p).split("/")[-1].split("#")[-1]] += 1

    subjects = set(str(s) for s, p, o in g)

    ttl_path = "../ontology/music_history_kg.ttl"
    ttl_size = os.path.getsize(ttl_path) / 1024 if os.path.exists(ttl_path) else 0

    structured_files = len([f for f in os.listdir("data/structured") if f.endswith(".json")]) if os.path.exists("data/structured") else 0
    text_files = len([f for f in os.listdir("data/text") if f.endswith(".json")]) if os.path.exists("data/text") else 0

    return {
        "total_triples": len(g),
        "unique_subjects": len(subjects),
        "ttl_file_size_kb": round(ttl_size, 1),
        "cached_structured_files": structured_files,
        "cached_text_files": text_files,
        "triples_per_artist": round(len(g) / len(ARTISTS), 1),
        "type_counts": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "predicate_counts": dict(sorted(pred_counts.items(), key=lambda x: -x[1])),
    }


if __name__ == "__main__":
    print("=" * 60)
    print("PERFORMANCE EVALUATION")
    print("=" * 60)

    # Measure pipeline with per-stage timing
    print("\n--- Pipeline Execution (from cache) ---")
    g, perf = measure_pipeline_with_stages()

    print(f"\n  Total time: {perf['total_time_seconds']}s")
    print(f"  Peak memory: {perf['peak_memory_mb']} MB")
    print(f"  Artists: {perf['artist_count']}")
    print(f"  Avg time per artist: {perf['avg_time_per_artist']}s")

    # Per-stage timing
    print(f"\n--- Per-Stage Timing ---")
    print(f"  {'Stage':<30s} {'Time (s)':>10s} {'Triples added':>15s}")
    print(f"  {'-'*58}")
    for stage, data in perf["stages"].items():
        print(f"  {stage:<30s} {data['time_seconds']:>10.3f} {data['triples_added']:>15d}")

    # Slowest artists
    sorted_times = sorted(perf["artist_times"], key=lambda x: -x["time_seconds"])
    print(f"\n--- Slowest Artists ---")
    for t in sorted_times[:5]:
        print(f"  {t['artist']:30s}: {t['time_seconds']}s")

    # Source contribution
    print(f"\n--- Source Contribution ---")
    sources = measure_source_contribution(g)
    total = sources["total"]
    for src, count in sources.items():
        if src != "total":
            pct = count / total * 100 if total > 0 else 0
            print(f"  {src:30s}: {count:>6d} triples ({pct:.1f}%)")
    print(f"  {'TOTAL':30s}: {total:>6d}")

    # Output stats
    print(f"\n--- Output Statistics ---")
    stats = measure_output_stats(g)
    print(f"  Total triples: {stats['total_triples']}")
    print(f"  Unique subjects: {stats['unique_subjects']}")
    print(f"  Triples per artist: {stats['triples_per_artist']}")
    print(f"  TTL file size: {stats['ttl_file_size_kb']} KB")
    print(f"  Cached files: {stats['cached_structured_files']} structured, {stats['cached_text_files']} text")

    print(f"\n  Instances by type:")
    for t, c in stats["type_counts"].items():
        print(f"    {t:30s}: {c}")

    print(f"\n  Top predicates:")
    for p, c in list(stats["predicate_counts"].items())[:15]:
        print(f"    {p:30s}: {c}")

    # Save results
    results = {
        "performance": perf,
        "source_contribution": sources,
        "output_stats": stats,
    }
    output_path = "../docs/eval_performance_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")
