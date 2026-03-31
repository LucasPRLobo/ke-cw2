"""Map structured data from all sources to RDF triples."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF, OWL

from config import (
    NAMESPACE_URI, MUSICBRAINZ_ARTIST_URI,
    MUSICBRAINZ_RELEASE_URI, MUSICBRAINZ_RECORDING_URI,
    MUSIC_ONTOLOGY_URI, SCHEMA_URI,
)
from utils import normalise_genre, safe_uri, is_valid_genre

# Namespaces
MO = Namespace(MUSIC_ONTOLOGY_URI)
MH = Namespace(NAMESPACE_URI)
MB = Namespace(MUSICBRAINZ_ARTIST_URI)
MB_RELEASE = Namespace(MUSICBRAINZ_RELEASE_URI)
MB_RECORDING = Namespace(MUSICBRAINZ_RECORDING_URI)
SCHEMA = Namespace(SCHEMA_URI)
DC = Namespace("http://purl.org/dc/elements/1.1/")


def create_graph():
    """Create a new RDF graph with all namespace bindings."""
    g = Graph()
    g.bind("mo", MO)
    g.bind("mh", MH)
    g.bind("mb", MB)
    g.bind("mb_release", MB_RELEASE)
    g.bind("mb_recording", MB_RECORDING)
    g.bind("foaf", FOAF)
    g.bind("schema", SCHEMA)
    g.bind("dc", DC)
    return g


def map_artist(g, mb_data, dc_data=None, wd_data=None):
    """Map a single artist's data from all structured sources to RDF triples.

    Args:
        g: rdflib Graph to add triples to
        mb_data: dict from sources/musicbrainz.py
        dc_data: dict from sources/discogs.py (optional)
        wd_data: dict from sources/wikidata.py (optional)
    """
    if mb_data is None:
        return

    mbid = mb_data["mbid"]
    artist_uri = MB[mbid]

    # --- Type ---
    artist_type = mb_data.get("type", "")
    if artist_type == "Person":
        g.add((artist_uri, RDF.type, MO.SoloMusicArtist))
    elif artist_type == "Group":
        g.add((artist_uri, RDF.type, MO.MusicGroup))
    else:
        g.add((artist_uri, RDF.type, MO.MusicArtist))

    # --- Name ---
    g.add((artist_uri, FOAF.name, Literal(mb_data["name"])))
    g.add((artist_uri, RDFS.label, Literal(mb_data["name"])))

    # --- Real name (from Discogs) ---
    if dc_data and dc_data.get("realname"):
        g.add((artist_uri, MH.realName, Literal(dc_data["realname"])))

    # --- Country ---
    if mb_data.get("country"):
        country_uri = MH[f"country/{mb_data['country'].lower()}"]
        g.add((country_uri, RDF.type, MH.Country))
        g.add((country_uri, RDFS.label, Literal(mb_data["country"])))
        g.add((artist_uri, MH.countryOfOrigin, country_uri))

    # --- Birth/death dates ---
    # MusicBrainz dates can be partial (e.g., "1960" or "1960-01")
    # Only use xsd:date for full YYYY-MM-DD, otherwise store as string
    life_span = mb_data.get("life_span", {})
    if life_span.get("begin"):
        date_val = life_span["begin"]
        if len(date_val) == 10:  # YYYY-MM-DD
            g.add((artist_uri, SCHEMA.birthDate, Literal(date_val, datatype=XSD.date)))
        else:
            g.add((artist_uri, SCHEMA.birthDate, Literal(date_val)))
    if life_span.get("end"):
        date_val = life_span["end"]
        if len(date_val) == 10:  # YYYY-MM-DD
            g.add((artist_uri, SCHEMA.deathDate, Literal(date_val, datatype=XSD.date)))
        else:
            g.add((artist_uri, SCHEMA.deathDate, Literal(date_val)))

    # --- Gender ---
    if mb_data.get("gender"):
        g.add((artist_uri, SCHEMA.gender, Literal(mb_data["gender"])))

    # --- Birth place ---
    if mb_data.get("begin_area"):
        g.add((artist_uri, MH.birthPlace, Literal(mb_data["begin_area"])))

    # --- Genres from MusicBrainz tags (filtered) ---
    for tag in mb_data.get("tags", []):
        if is_valid_genre(tag["name"], tag.get("count", 0)):
            genre_name = normalise_genre(tag["name"])
            genre_uri = MH[f"genre/{genre_name}"]
            g.add((genre_uri, RDF.type, MO.Genre))
            g.add((genre_uri, RDFS.label, Literal(tag["name"].lower())))
            g.add((artist_uri, MO.genre, genre_uri))

    # --- Genres from Wikidata ---
    if wd_data:
        for genre_name in wd_data.get("genres", []):
            genre_norm = normalise_genre(genre_name)
            genre_uri = MH[f"genre/{genre_norm}"]
            g.add((genre_uri, RDF.type, MO.Genre))
            g.add((genre_uri, RDFS.label, Literal(genre_name.lower())))
            g.add((artist_uri, MO.genre, genre_uri))

    # --- Genre/Style hierarchy from Discogs ---
    if dc_data:
        for pair in dc_data.get("genre_style_pairs", []):
            genre_norm = normalise_genre(pair["genre"])
            style_norm = normalise_genre(pair["style"])
            genre_uri = MH[f"genre/{genre_norm}"]
            style_uri = MH[f"genre/{style_norm}"]
            g.add((genre_uri, RDF.type, MO.Genre))
            g.add((genre_uri, RDFS.label, Literal(pair["genre"].lower())))
            g.add((style_uri, RDF.type, MO.Genre))
            g.add((style_uri, RDFS.label, Literal(pair["style"].lower())))
            g.add((style_uri, MH.subgenreOf, genre_uri))

    # --- Artist relationships from MusicBrainz ---
    for rel in mb_data.get("artist_rels", []):
        target_mbid = rel.get("target_mbid")
        if not target_mbid:
            continue

        target_uri = MB[target_mbid]
        target_name = rel.get("target_name", "Unknown")
        g.add((target_uri, RDFS.label, Literal(target_name)))

        rel_type = rel.get("type", "")
        direction = rel.get("direction", "")

        if rel_type == "member of band":
            if direction == "forward":
                g.add((artist_uri, MO.member_of, target_uri))
                g.add((target_uri, RDF.type, MO.MusicGroup))
            else:
                g.add((target_uri, MO.member_of, artist_uri))
                g.add((target_uri, RDF.type, MO.SoloMusicArtist))

            # Instruments from attributes
            for attr in rel.get("attributes", []):
                if attr not in ("original", "minor"):
                    inst_uri = MH[f"instrument/{normalise_genre(attr)}"]
                    g.add((inst_uri, RDF.type, MO.Instrument))
                    g.add((inst_uri, RDFS.label, Literal(attr)))
                    member = artist_uri if direction == "forward" else target_uri
                    g.add((member, MH.playsInstrument, inst_uri))

        elif rel_type == "collaboration":
            g.add((artist_uri, MH.collaboratedWith, target_uri))

        elif rel_type == "influenced by":
            if direction == "forward":
                g.add((artist_uri, MH.influencedBy, target_uri))
            else:
                g.add((target_uri, MH.influencedBy, artist_uri))

        elif rel_type == "producer":
            if direction == "backward":
                g.add((artist_uri, MH.producedBy, target_uri))
                g.add((target_uri, MH.produced, artist_uri))
            else:
                g.add((target_uri, MH.producedBy, artist_uri))
                g.add((artist_uri, MH.produced, target_uri))

    # --- Instruments from Wikidata ---
    if wd_data:
        for inst_name in wd_data.get("instruments", []):
            inst_uri = MH[f"instrument/{normalise_genre(inst_name)}"]
            g.add((inst_uri, RDF.type, MO.Instrument))
            g.add((inst_uri, RDFS.label, Literal(inst_name)))
            g.add((artist_uri, MH.playsInstrument, inst_uri))

    # --- Awards from Wikidata ---
    if wd_data:
        for award_name in wd_data.get("awards", []):
            award_uri = MH[f"award/{safe_uri(award_name)}"]
            g.add((award_uri, RDF.type, MH.Award))
            g.add((award_uri, RDFS.label, Literal(award_name)))
            g.add((artist_uri, MH.wonAward, award_uri))

    # --- Record labels from Wikidata ---
    if wd_data:
        for label_name in wd_data.get("labels", []):
            label_uri = MH[f"label/{safe_uri(label_name)}"]
            g.add((label_uri, RDF.type, MH.RecordLabel))
            g.add((label_uri, RDFS.label, Literal(label_name)))
            g.add((artist_uri, MH.signedTo, label_uri))

    # --- Influences from Wikidata ---
    if wd_data:
        for inf_name in wd_data.get("influences", []):
            inf_uri = MH[f"artist/{safe_uri(inf_name)}"]
            g.add((inf_uri, RDFS.label, Literal(inf_name)))
            g.add((artist_uri, MH.influencedBy, inf_uri))

    # --- Release groups (albums) from MusicBrainz ---
    for rg in mb_data.get("release_groups", []):
        album_uri = MH[f"album/{rg['id']}"]
        g.add((album_uri, RDF.type, MO.Release))
        g.add((album_uri, RDFS.label, Literal(rg["title"])))
        g.add((album_uri, DC.title, Literal(rg["title"])))
        g.add((artist_uri, MH.released, album_uri))

        if rg.get("first_release_date"):
            g.add((album_uri, MH.releaseDate, Literal(rg["first_release_date"])))

    # --- Tracks from MusicBrainz recordings ---
    for rg_id, tracks in mb_data.get("tracks", {}).items():
        album_uri = MH[f"album/{rg_id}"]
        for track in tracks:
            if track.get("id"):
                track_uri = MB_RECORDING[track["id"]]
                g.add((track_uri, RDF.type, MO.Track))
                g.add((track_uri, RDFS.label, Literal(track.get("title", "Unknown"))))
                g.add((track_uri, DC.title, Literal(track.get("title", "Unknown"))))
                g.add((album_uri, MH.hasTrack, track_uri))
                if track.get("length"):
                    g.add((track_uri, MH.duration, Literal(int(track["length"]), datatype=XSD.integer)))

    # --- Compositions from Wikidata (classical) ---
    if wd_data:
        for comp in wd_data.get("compositions", []):
            comp_uri = MH[f"composition/{safe_uri(comp['title'])}"]
            g.add((comp_uri, RDF.type, MH.MusicalWork))
            g.add((comp_uri, RDFS.label, Literal(comp["title"])))
            g.add((artist_uri, MH.composed, comp_uri))
            if comp.get("date"):
                g.add((comp_uri, MH.compositionDate, Literal(comp["date"])))
            if comp.get("genre"):
                genre_uri = MH[f"genre/{normalise_genre(comp['genre'])}"]
                g.add((genre_uri, RDF.type, MO.Genre))
                g.add((genre_uri, RDFS.label, Literal(comp["genre"].lower())))
                g.add((comp_uri, MO.genre, genre_uri))

    return artist_uri


def enrich_related_artists(g, mb_rate_limit=1.1):
    """Second pass: fetch basic info for related artists that lack country data.

    Finds all artist URIs in the graph that have mo:member_of or
    mh:collaboratedWith relationships but no mh:countryOfOrigin.
    Fetches their country from MusicBrainz, with caching to avoid
    re-fetching on subsequent runs.
    """
    import musicbrainzngs
    import time
    import json
    import os

    ENRICHMENT_CACHE = "data/structured/enrichment_cache.json"

    # Load enrichment cache
    cache = {}
    if os.path.exists(ENRICHMENT_CACHE):
        with open(ENRICHMENT_CACHE, "r") as f:
            cache = json.load(f)

    # Find all MB artist URIs missing country
    query = """
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX mh: <http://example.org/music-history/>
    PREFIX mb: <http://musicbrainz.org/artist/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?artist ?label WHERE {
        {
            ?artist mo:member_of ?band .
        } UNION {
            ?someone mh:collaboratedWith ?artist .
        } UNION {
            ?artist mh:collaboratedWith ?someone .
        }
        ?artist rdfs:label ?label .
        FILTER(STRSTARTS(STR(?artist), "http://musicbrainz.org/artist/"))
        FILTER NOT EXISTS { ?artist mh:countryOfOrigin ?c }
    }
    """
    results = list(g.query(query))
    if not results:
        print("  [ENRICH] No related artists need enrichment")
        return 0

    print(f"  [ENRICH] Found {len(results)} related artists missing country data")
    enriched = 0
    api_calls = 0

    for row in results:
        artist_uri = row.artist
        label = str(row.label)
        mbid = str(artist_uri).replace("http://musicbrainz.org/artist/", "")

        # Check enrichment cache first
        if mbid in cache:
            detail = cache[mbid]
        else:
            try:
                time.sleep(mb_rate_limit)
                detail = musicbrainzngs.get_artist_by_id(mbid)["artist"]
                cache[mbid] = {
                    "country": detail.get("country"),
                    "type": detail.get("type"),
                }
                api_calls += 1
            except Exception:
                cache[mbid] = {"country": None, "type": None}
                continue
            detail = cache[mbid]

        country = detail.get("country")
        if country:
            country_uri = MH[f"country/{country.lower()}"]
            g.add((country_uri, RDF.type, MH.Country))
            g.add((country_uri, RDFS.label, Literal(country)))
            g.add((artist_uri, MH.countryOfOrigin, country_uri))
            enriched += 1

        # Also add type if missing
        artist_type = detail.get("type", "")
        if artist_type == "Person":
            g.add((artist_uri, RDF.type, MO.SoloMusicArtist))
        elif artist_type == "Group":
            g.add((artist_uri, RDF.type, MO.MusicGroup))

    # Save enrichment cache
    os.makedirs(os.path.dirname(ENRICHMENT_CACHE), exist_ok=True)
    with open(ENRICHMENT_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"  [ENRICH] Added country data for {enriched} artists ({api_calls} API calls, {len(results) - api_calls} cached)")
    return enriched


def consolidate_uris(g):
    """Merge mh:artist/ URIs with matching mb: URIs to eliminate duplicates.

    When Wikidata says 'David Bowie influencedBy Bob Dylan', it creates
    mh:artist/Bob_Dylan. But Bob Dylan already exists as mb:72c536dc-...
    This function finds these duplicates by label matching and replaces
    all references to the mh: URI with the mb: URI.
    """
    from rapidfuzz import fuzz

    # Build label → MB URI index
    mb_by_label = {}
    for s, p, o in g.triples((None, RDFS.label, None)):
        if str(s).startswith("http://musicbrainz.org/artist/"):
            mb_by_label[str(o).lower().strip()] = s

    # Find mh:artist/ URIs and try to match
    mh_prefix = "http://example.org/music-history/artist/"
    mh_uris = set()
    for s, p, o in g:
        for uri in [s, o]:
            if str(uri).startswith(mh_prefix):
                mh_uris.add(uri)

    consolidated = 0
    for mh_uri in mh_uris:
        # Get labels for this mh: URI
        labels = [str(o) for s, p, o in g.triples((mh_uri, RDFS.label, None))]
        if not labels:
            continue

        # Try exact match first
        mb_uri = None
        for label in labels:
            if label.lower().strip() in mb_by_label:
                mb_uri = mb_by_label[label.lower().strip()]
                break

        # Try fuzzy match if no exact match
        if mb_uri is None:
            for label in labels:
                for mb_label, mb_candidate in mb_by_label.items():
                    score = fuzz.token_set_ratio(label.lower(), mb_label)
                    if score >= 90:
                        mb_uri = mb_candidate
                        break
                if mb_uri:
                    break

        if mb_uri is None:
            continue

        # Replace all triples using mh_uri with mb_uri
        # As subject
        for s, p, o in list(g.triples((mh_uri, None, None))):
            g.remove((s, p, o))
            g.add((mb_uri, p, o))

        # As object
        for s, p, o in list(g.triples((None, None, mh_uri))):
            g.remove((s, p, o))
            g.add((s, p, mb_uri))

        consolidated += 1

    print(f"  [CONSOLIDATE] Merged {consolidated} duplicate URIs (mh:artist/ → mb:)")
    return consolidated


def assign_types_to_orphans(g):
    """Assign rdf:type to entities that have labels but no type.

    Infers type from the predicates used with the entity:
    - Object of influencedBy/collaboratedWith → mo:MusicArtist
    - Object of mo:member_of → mo:MusicGroup
    - Object of hasTrack → mo:Track
    """
    orphan_query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?entity WHERE {
        ?entity rdfs:label ?label .
        FILTER NOT EXISTS { ?entity rdf:type ?t }
    }
    """
    orphans = list(g.query(orphan_query))
    assigned = 0

    for row in orphans:
        entity = row.entity
        uri_str = str(entity)

        # Infer type from predicates
        if any(g.triples((None, MH.influencedBy, entity))) or \
           any(g.triples((None, MH.collaboratedWith, entity))) or \
           any(g.triples((entity, MH.influencedBy, None))) or \
           any(g.triples((entity, MH.collaboratedWith, None))):
            g.add((entity, RDF.type, MO.MusicArtist))
            assigned += 1
        elif any(g.triples((None, MO.member_of, entity))):
            g.add((entity, RDF.type, MO.MusicGroup))
            assigned += 1
        elif "artist" in uri_str or "mb" in uri_str:
            g.add((entity, RDF.type, MO.MusicArtist))
            assigned += 1

    print(f"  [TYPES] Assigned rdf:type to {assigned} orphan entities")
    return assigned
