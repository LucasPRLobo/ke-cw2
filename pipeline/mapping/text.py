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
CONFIDENT_THRESHOLD = 90
PROVISIONAL_THRESHOLD = 80

# Stopwords to strip before fuzzy matching (reduces false matches on common words)
STOPWORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "is", "by"}


def _build_label_index(g):
    """Build a typed label → URI index from the existing graph.

    Includes rdfs:label and foaf:name for all entities.
    Returns dict: {lowercase_label: [(URI, set_of_rdf_types), ...]}
    """
    from rdflib.namespace import FOAF
    index = {}
    for s, p, o in g.triples((None, RDFS.label, None)):
        label = str(o).lower().strip()
        if label and not label.startswith("http"):
            types = frozenset(t for _, _, t in g.triples((s, RDF.type, None)))
            index.setdefault(label, []).append((s, types))
    for s, p, o in g.triples((None, FOAF.name, None)):
        label = str(o).lower().strip()
        if label and not label.startswith("http"):
            types = frozenset(t for _, _, t in g.triples((s, RDF.type, None)))
            index.setdefault(label, []).append((s, types))
    return index


def _strip_stopwords(text):
    """Remove common stopwords from a text string for improved matching."""
    tokens = text.lower().split()
    filtered = [t for t in tokens if t not in STOPWORDS]
    return " ".join(filtered) if filtered else text.lower()


def _pick_typed_entry(entries, expected_types):
    """Pick the best entry from a label index list, preferring type-compatible ones.

    Args:
        entries: list of (URI, frozenset_of_types) from label index
        expected_types: list of RDF types to prefer, or None

    Returns:
        (URI, is_type_match) tuple
    """
    if not entries:
        return None, False
    if not expected_types:
        return entries[0][0], False

    expected_set = set(expected_types)
    for uri, types in entries:
        if types & expected_set:
            return uri, True
    # No type match — return first entry
    return entries[0][0], False


def _tier1_exact_match(mention, label_index, expected_types=None):
    """Tier 1: Exact string match against label index, preferring type-compatible."""
    key = mention.lower().strip()
    if key in label_index:
        uri, type_match = _pick_typed_entry(label_index[key], expected_types)
        if uri:
            return uri, "exact"
    return None, None


def _tier2_fuzzy_match(mention, label_index, expected_types=None):
    """Tier 2: Fuzzy match with type filtering and stopword removal.

    Uses dual-scorer gate: both token_set_ratio AND token_sort_ratio
    must pass thresholds to prevent partial-token false matches.
    """
    if not label_index:
        return None, None

    mention_clean = _strip_stopwords(mention)
    keys = list(label_index.keys())
    keys_clean = [_strip_stopwords(k) for k in keys]

    result = process.extractOne(
        mention_clean,
        keys_clean,
        scorer=fuzz.token_set_ratio,
        score_cutoff=PROVISIONAL_THRESHOLD
    )

    if result is None:
        return None, None

    _, set_score, idx = result
    matched_label = keys[idx]

    # Dual-scorer gate: verify with token_sort_ratio to catch
    # cases where only a subset of tokens match
    sort_score = fuzz.token_sort_ratio(mention_clean, keys_clean[idx])
    if sort_score < PROVISIONAL_THRESHOLD - 15:
        return None, None

    # Type-filtered: prefer type-compatible match
    entries = label_index[matched_label]
    if expected_types:
        uri, type_match = _pick_typed_entry(entries, expected_types)
        if not type_match:
            # Fuzzy matched but wrong type — demote to provisional
            if set_score >= CONFIDENT_THRESHOLD:
                return uri, f"provisional({set_score})"
            return uri, f"provisional({set_score})"
    else:
        uri = entries[0][0]

    if set_score >= CONFIDENT_THRESHOLD:
        return uri, f"fuzzy({set_score})"
    else:
        return uri, f"provisional({set_score})"


def _tier3_type_constrained(mention, g, expected_types):
    """Tier 3: Type-constrained search — only matches entities of expected type."""
    mention_clean = _strip_stopwords(mention)
    best_score = 0
    best_uri = None
    for rdf_type in expected_types:
        for s, p, o in g.triples((None, RDF.type, rdf_type)):
            for s2, p2, label in g.triples((s, RDFS.label, None)):
                label_clean = _strip_stopwords(str(label))
                score = fuzz.token_set_ratio(mention_clean, label_clean)
                if score >= PROVISIONAL_THRESHOLD and score > best_score:
                    best_score = score
                    best_uri = s
    if best_uri:
        return best_uri, f"type_constrained({best_score})"
    return None, None


def _tier5_create_provisional(mention, expected_type):
    """Tier 5: Create a new provisional URI for an unresolved entity."""
    safe = safe_uri(mention)

    if expected_type == "Genre":
        from config import GENRE_BLACKLIST
        if mention.lower().strip() in GENRE_BLACKLIST:
            return None, "blacklisted_genre"
        return MH[f"genre/{normalise_genre(mention)}"], "new_genre"
    elif expected_type == "MusicalWork":
        return MH[f"composition/{safe}"], "new_work"
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

    Priority order: exact match → type-constrained → fuzzy match → provisional.
    Type-constrained (Tier 3) runs before fuzzy (Tier 2) when expected_type is
    available, because type filtering is strictly more precise than untyped fuzzy.

    Args:
        mention: string from LLM extraction
        g: the existing RDF graph
        label_index: dict from _build_label_index (typed)
        expected_type: string key into TYPE_MAP (e.g., "Artist", "Genre")

    Returns:
        (URI, resolution_method) tuple
    """
    expected_types = TYPE_MAP.get(expected_type) if expected_type else None

    # Tier 1: Exact match (type-aware)
    uri, method = _tier1_exact_match(mention, label_index, expected_types)
    if uri:
        return uri, method

    # Tier 3: Type-constrained search (run BEFORE fuzzy to prevent cross-type errors)
    if expected_types:
        uri3, method3 = _tier3_type_constrained(mention, g, expected_types)
        if uri3:
            return uri3, method3

    # Tier 2: Fuzzy match (type-aware, with dual-scorer gate)
    uri, method = _tier2_fuzzy_match(mention, label_index, expected_types)
    if uri and method and not method.startswith("provisional"):
        return uri, method

    # If fuzzy found a provisional match, use it
    if uri and method:
        return uri, method

    # Tier 4: Wikidata lookup (skip — expensive API call per entity)

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

        # Determine expected subject type from the predicate
        # Most predicates have an Artist subject, but producedBy and albumGrouping
        # have a MusicalWork subject
        SUBJECT_TYPE_MAP = {
            "producedBy": "MusicalWork",
            "albumGrouping": "MusicalWork",
        }
        expected_sub_type = SUBJECT_TYPE_MAP.get(predicate_str, "Artist")

        # Resolve subject
        subject_uri, sub_method = resolve_entity(
            subject_str, g, label_index, expected_type=expected_sub_type
        )

        # Resolve object
        object_uri, obj_method = resolve_entity(
            object_str, g, label_index, expected_type=expected_obj_type
        )

        # Skip if resolution returned None (e.g. blacklisted genre)
        if subject_uri is None or object_uri is None:
            stats["skipped"] += 1
            continue

        # Validate "producedBy" domain: subject must be a Release.
        # LLM sometimes confuses labels/groups with albums.
        if predicate_str == "producedBy":
            sub_types = set(g.objects(subject_uri, RDF.type))
            if MO.Release not in sub_types:
                stats["skipped"] += 1
                continue

        # Validate "released" range: object must be a Release, not a
        # Track, MusicalWork, or RecordLabel.  If the LLM linked to a
        # MusicalWork, silently convert to composed/composedBy instead.
        if predicate_str == "released":
            obj_types = set(g.objects(object_uri, RDF.type))
            is_work = MH.MusicalWork in obj_types or MO.MusicalWork in obj_types
            is_release = MO.Release in obj_types
            if not is_release:
                if is_work and (subject_uri, MH.composed, object_uri) not in g:
                    g.add((subject_uri, MH.composed, object_uri))
                    g.add((object_uri, MH.composedBy, subject_uri))
                stats["skipped"] += 1
                continue

        # Add the triple
        g.add((subject_uri, rdf_predicate, object_uri))

        # Add inverse/symmetric triples for key properties
        if predicate_str == "producedBy":
            g.add((object_uri, MH.produced, subject_uri))
        elif predicate_str == "produced":
            g.add((object_uri, MH.producedBy, subject_uri))
        elif predicate_str == "collaboratedWith":
            g.add((object_uri, rdf_predicate, subject_uri))  # symmetric
            # Ensure both endpoints are typed as MusicArtist
            for endpoint in (subject_uri, object_uri):
                if not any(g.triples((endpoint, RDF.type, MO.MusicArtist))):
                    g.add((endpoint, RDF.type, MO.MusicArtist))
        elif predicate_str == "released":
            g.add((object_uri, MH.releasedBy, subject_uri))  # inverse
        elif predicate_str == "composed":
            g.add((object_uri, MH.composedBy, subject_uri))  # inverse
        elif predicate_str == "influencedBy":
            g.add((object_uri, MH.influenced, subject_uri))  # inverse

        # Ensure both have labels
        if not any(g.triples((subject_uri, RDFS.label, None))):
            g.add((subject_uri, RDFS.label, Literal(subject_str, lang="en")))
        if not any(g.triples((object_uri, RDFS.label, None))):
            g.add((object_uri, RDFS.label, Literal(object_str, lang="en")))

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
