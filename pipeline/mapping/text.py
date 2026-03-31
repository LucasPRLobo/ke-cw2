"""Map LLM-extracted triples from Wikipedia text into the RDF graph.

Uses a 5-tier entity linking strategy to resolve text mentions
to existing URIs in the graph:
  Tier 1: Exact match against entity label index
  Tier 2: Fuzzy match using rapidfuzz token_set_ratio
  Tier 3: Type-constrained SPARQL lookup
  Tier 4: Wikidata SPARQL fallback
  Tier 5: NIL — create provisional URI for new entities

Course techniques applied:
  - Entity Linking (Week 7: NLP-to-KG pipeline, step 3)
  - Entity Disambiguation (Week 7: LLM chained prompting, step 3)
  - KG-enriched retrieval (Week 11: entity recognition → linking → KG property retrieval)
"""
import os
import sys
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdflib import Literal, URIRef
from rdflib.namespace import RDF, RDFS
from rapidfuzz import fuzz, process

from config import NAMESPACE_URI, MUSIC_ONTOLOGY_URI
from utils import normalise_genre, safe_uri

# Namespace shortcuts (must match structured.py)
from rdflib import Namespace
MO = Namespace(MUSIC_ONTOLOGY_URI)
MH = Namespace(NAMESPACE_URI)

# Predicate mapping: LLM predicate string → (RDF property, expected object type)
PREDICATE_MAP = {
    "released":          (MH.released,          "MusicalWork"),
    "composed":          (MH.composed,          "MusicalWork"),
    "collaboratedWith":  (MH.collaboratedWith,  "Artist"),
    "memberOf":          (MO.member_of,         "MusicGroup"),
    "hasMember":         (MH.hasMember,         "Artist"),
    "hasGenre":          (MO.genre,             "Genre"),
    "alterEgo":          (MH.alterEgo,          "Persona"),
    "albumGrouping":     (MH.albumGrouping,     "AlbumGroup"),
    "producedBy":        (MH.producedBy,        "Artist"),
    "produced":          (MH.produced,          "MusicalWork"),
    "performedAt":       (MH.performedAt,       "Venue"),
    "influencedBy":      (MH.influencedBy,      "Artist"),
    "hasMusicalPeriod":  (MH.hasMusicalPeriod,  "MusicalPeriod"),
    "pioneerOf":         (MH.pioneerOf,         "Genre"),
    "founded":           (MH.founded,           "Organisation"),
}

# RDF types for expected object types
TYPE_MAP = {
    "Artist":         [MO.SoloMusicArtist, MO.MusicGroup, MO.MusicArtist],
    "MusicGroup":     [MO.MusicGroup],
    "MusicalWork":    [MO.Release, MH.MusicalWork],
    "Genre":          [MO.Genre],
    "Persona":        [MH.Persona],
    "AlbumGroup":     [MH.AlbumGroup],
    "Venue":          [MH.Venue],
    "MusicalPeriod":  [MH.MusicalPeriod],
    "Organisation":   [MH.Organisation],
}

# Fuzzy match thresholds
EXACT_THRESHOLD = 100
CONFIDENT_THRESHOLD = 85
PROVISIONAL_THRESHOLD = 70


def _build_label_index(g):
    """Build a label → URI index from the existing graph.

    Includes rdfs:label and foaf:name for all entities.
    Returns dict: {lowercase_label: URI}
    """
    from rdflib.namespace import FOAF
    index = {}
    for s, p, o in g.triples((None, RDFS.label, None)):
        label = str(o).lower().strip()
        if label and not label.startswith("http"):
            index[label] = s
    for s, p, o in g.triples((None, FOAF.name, None)):
        label = str(o).lower().strip()
        if label and not label.startswith("http"):
            index[label] = s
    return index


def _tier1_exact_match(mention, label_index):
    """Tier 1: Exact string match against label index."""
    key = mention.lower().strip()
    if key in label_index:
        return label_index[key], "exact"
    return None, None


def _tier2_fuzzy_match(mention, label_index):
    """Tier 2: Fuzzy match using rapidfuzz token_set_ratio."""
    if not label_index:
        return None, None

    keys = list(label_index.keys())
    result = process.extractOne(
        mention.lower(),
        keys,
        scorer=fuzz.token_set_ratio,
        score_cutoff=PROVISIONAL_THRESHOLD
    )

    if result is None:
        return None, None

    matched_label, score, _ = result
    if score >= CONFIDENT_THRESHOLD:
        return label_index[matched_label], f"fuzzy({score})"
    else:
        return label_index[matched_label], f"provisional({score})"


def _tier3_type_constrained(mention, g, expected_types):
    """Tier 3: SPARQL query filtered by expected RDF type."""
    for rdf_type in expected_types:
        for s, p, o in g.triples((None, RDF.type, rdf_type)):
            for s2, p2, label in g.triples((s, RDFS.label, None)):
                score = fuzz.token_set_ratio(mention.lower(), str(label).lower())
                if score >= PROVISIONAL_THRESHOLD:
                    return s, f"type_constrained({score})"
    return None, None


def _tier5_create_provisional(mention, expected_type):
    """Tier 5: Create a new provisional URI for an unresolved entity."""
    safe = safe_uri(mention)

    if expected_type == "Genre":
        return MH[f"genre/{normalise_genre(mention)}"], "new_genre"
    elif expected_type == "MusicalWork":
        return MH[f"work/{safe}"], "new_work"
    elif expected_type == "Artist":
        return MH[f"artist/{safe}"], "new_artist"
    elif expected_type == "MusicGroup":
        return MH[f"group/{safe}"], "new_group"
    elif expected_type == "Persona":
        return MH[f"persona/{safe}"], "new_persona"
    elif expected_type == "AlbumGroup":
        return MH[f"album_group/{safe}"], "new_album_group"
    elif expected_type == "MusicalPeriod":
        return MH[f"period/{safe}"], "new_period"
    elif expected_type == "Organisation":
        return MH[f"org/{safe}"], "new_org"
    else:
        return MH[f"entity/{safe}"], "new_entity"


def resolve_entity(mention, g, label_index, expected_type=None):
    """Resolve a text mention to a URI using the 5-tier strategy.

    Args:
        mention: string from LLM extraction
        g: the existing RDF graph
        label_index: dict from _build_label_index
        expected_type: string key into TYPE_MAP (e.g., "Artist", "Genre")

    Returns:
        (URI, resolution_method) tuple
    """
    # Tier 1: Exact match
    uri, method = _tier1_exact_match(mention, label_index)
    if uri:
        return uri, method

    # Tier 2: Fuzzy match
    uri, method = _tier2_fuzzy_match(mention, label_index)
    if uri and method and not method.startswith("provisional"):
        return uri, method

    # Tier 3: Type-constrained search
    if expected_type and expected_type in TYPE_MAP:
        uri3, method3 = _tier3_type_constrained(mention, g, TYPE_MAP[expected_type])
        if uri3:
            return uri3, method3

    # If fuzzy found a provisional match, use it
    if uri and method:
        return uri, method

    # Tier 4: Wikidata lookup (skip for now — expensive API call per entity)
    # Could be added later for production pipeline

    # Tier 5: Create provisional URI
    uri, method = _tier5_create_provisional(mention, expected_type or "entity")
    return uri, method


def map_text_triples(g, artist_name, extraction_file=None):
    """Map LLM-extracted triples from a JSON file into the RDF graph.

    Args:
        g: rdflib Graph (already populated with structured data)
        artist_name: artist name for logging and file lookup
        extraction_file: path to JSON file, or None to auto-detect

    Returns:
        dict with stats: {total, linked, provisional, new, skipped}
    """
    # Find the extraction file
    if extraction_file is None:
        safe = safe_uri(artist_name)
        extraction_file = f"data/text/llm_extraction_{safe}.json"

    if not os.path.exists(extraction_file):
        print(f"  [TXT] {artist_name}: no extraction file found at {extraction_file}")
        return {"total": 0, "linked": 0, "provisional": 0, "new": 0, "skipped": 0}

    with open(extraction_file) as f:
        triples = json.load(f)

    # Build label index from existing graph
    label_index = _build_label_index(g)

    stats = {"total": len(triples), "linked": 0, "provisional": 0, "new": 0, "skipped": 0}

    for triple in triples:
        subject_str = triple["subject"]
        predicate_str = triple["predicate"]
        object_str = triple["object"]

        # Look up predicate
        if predicate_str not in PREDICATE_MAP:
            print(f"  [TXT] Unknown predicate: {predicate_str}")
            stats["skipped"] += 1
            continue

        rdf_predicate, expected_obj_type = PREDICATE_MAP[predicate_str]

        # Resolve subject
        subject_uri, sub_method = resolve_entity(
            subject_str, g, label_index, expected_type="Artist"
        )

        # Resolve object
        object_uri, obj_method = resolve_entity(
            object_str, g, label_index, expected_type=expected_obj_type
        )

        # Add the triple
        g.add((subject_uri, rdf_predicate, object_uri))

        # Ensure both have labels
        if not any(g.triples((subject_uri, RDFS.label, None))):
            g.add((subject_uri, RDFS.label, Literal(subject_str)))
        if not any(g.triples((object_uri, RDFS.label, None))):
            g.add((object_uri, RDFS.label, Literal(object_str)))

        # Add type for new entities
        if obj_method and obj_method.startswith("new_"):
            if expected_obj_type in TYPE_MAP:
                g.add((object_uri, RDF.type, TYPE_MAP[expected_obj_type][0]))

        # Track stats
        if sub_method == "exact" or obj_method == "exact":
            stats["linked"] += 1
        elif "fuzzy" in str(sub_method) or "fuzzy" in str(obj_method):
            stats["linked"] += 1
        elif "provisional" in str(sub_method) or "provisional" in str(obj_method):
            stats["provisional"] += 1
        elif "new" in str(sub_method) or "new" in str(obj_method):
            stats["new"] += 1

    print(f"  [TXT] {artist_name}: {stats['total']} triples — "
          f"{stats['linked']} linked, {stats['provisional']} provisional, "
          f"{stats['new']} new, {stats['skipped']} skipped")

    return stats
