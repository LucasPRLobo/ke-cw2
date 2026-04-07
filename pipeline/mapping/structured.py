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
from utils import normalise_genre, normalise_instrument, safe_uri, is_valid_genre

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


ISO_COUNTRY_NAMES = {
    "us": "United States", "gb": "United Kingdom", "de": "Germany",
    "fr": "France", "br": "Brazil", "jm": "Jamaica", "ng": "Nigeria",
    "za": "South Africa", "sn": "Senegal", "cu": "Cuba", "es": "Spain",
    "jp": "Japan", "kr": "South Korea", "in": "India", "at": "Austria",
    "pl": "Poland", "it": "Italy", "ru": "Russia", "cv": "Cape Verde",
    "ie": "Ireland", "au": "Australia", "ca": "Canada", "se": "Sweden",
    "nl": "Netherlands", "be": "Belgium", "ar": "Argentina", "mx": "Mexico",
    "eg": "Egypt", "il": "Israel", "pt": "Portugal",
}


def _typed_date_literal(date_str):
    """Return a Literal with the correct XSD datatype based on date precision."""
    if not date_str:
        return Literal(date_str)
    if len(date_str) == 10:     # YYYY-MM-DD
        return Literal(date_str, datatype=XSD.date)
    elif len(date_str) == 7:    # YYYY-MM → normalise to YYYY-MM-01
        return Literal(date_str + "-01", datatype=XSD.date)
    elif len(date_str) == 4:    # YYYY
        return Literal(date_str, datatype=XSD.gYear)
    else:
        return Literal(date_str)


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
    g.add((artist_uri, FOAF.name, Literal(mb_data["name"], lang="en")))
    g.add((artist_uri, RDFS.label, Literal(mb_data["name"], lang="en")))

    # --- Real name (from Discogs) ---
    if dc_data and dc_data.get("realname"):
        g.add((artist_uri, MH.realName, Literal(dc_data["realname"], lang="en")))

    # --- Country ---
    if mb_data.get("country"):
        country_code = mb_data["country"].lower()
        country_uri = MH[f"country/{country_code}"]
        g.add((country_uri, RDF.type, MH.Country))
        g.add((country_uri, RDFS.label, Literal(mb_data["country"], lang="en")))
        full_name = ISO_COUNTRY_NAMES.get(country_code)
        if full_name:
            g.add((country_uri, RDFS.label, Literal(full_name, lang="en")))
        g.add((artist_uri, MH.countryOfOrigin, country_uri))

    # --- Birth/death dates ---
    # Uses _typed_date_literal for correct XSD types: xsd:date, xsd:gYearMonth, xsd:gYear
    life_span = mb_data.get("life_span", {})
    if life_span.get("begin"):
        g.add((artist_uri, SCHEMA.birthDate, _typed_date_literal(life_span["begin"])))
    if life_span.get("end"):
        g.add((artist_uri, SCHEMA.deathDate, _typed_date_literal(life_span["end"])))

    # --- Gender ---
    if mb_data.get("gender"):
        g.add((artist_uri, SCHEMA.gender, Literal(mb_data["gender"])))

    # --- Birth place ---
    if mb_data.get("begin_area"):
        g.add((artist_uri, MH.birthPlace, Literal(mb_data["begin_area"])))

    # --- Genres from MusicBrainz tags (filtered) ---
    # Collect genre URIs for later propagation to albums (David's feedback Point 2)
    artist_genre_uris = set()

    for tag in mb_data.get("tags", []):
        if is_valid_genre(tag["name"], tag.get("count", 0)):
            genre_norm = normalise_genre(tag["name"])
            genre_uri = MH[f"genre/{genre_norm}"]
            if not any(g.triples((genre_uri, RDF.type, None))):
                g.add((genre_uri, RDF.type, MO.Genre))
                genre_label = genre_norm.replace("_", " ")
                g.add((genre_uri, RDFS.label, Literal(genre_label, lang="en")))
            g.add((artist_uri, MO.genre, genre_uri))
            artist_genre_uris.add(genre_uri)

    # --- Genres from Wikidata ---
    if wd_data:
        from config import GENRE_BLACKLIST
        for genre_name in wd_data.get("genres", []):
            genre_lower = genre_name.lower()
            if genre_lower in GENRE_BLACKLIST:
                continue
            genre_norm = normalise_genre(genre_name)
            # Also check the normalised name against the blacklist
            # (catches "film soundtrack" → "film_soundtrack" etc.)
            if genre_norm.replace("_", " ") in GENRE_BLACKLIST:
                continue
            genre_uri = MH[f"genre/{genre_norm}"]
            if not any(g.triples((genre_uri, RDF.type, None))):
                g.add((genre_uri, RDF.type, MO.Genre))
                genre_label = genre_norm.replace("_", " ")
                g.add((genre_uri, RDFS.label, Literal(genre_label, lang="en")))
            g.add((artist_uri, MO.genre, genre_uri))
            artist_genre_uris.add(genre_uri)

    # --- Genre/Style hierarchy from Discogs ---
    # Use an allowlist of valid Discogs music genres (not "Non-Music", "Stage & Screen" etc.)
    VALID_DISCOGS_GENRES = {
        "blues", "brass & military", "classical", "country", "electronic",
        "folk, world, & country", "funk / soul", "hip hop", "jazz", "latin",
        "pop", "reggae", "rock",
    }
    if dc_data:
        from config import GENRE_BLACKLIST
        for pair in dc_data.get("genre_style_pairs", []):
            genre_name = pair["genre"].lower()
            style_name = pair["style"].lower()
            # Only include pairs where the parent genre is a known music genre
            if genre_name not in VALID_DISCOGS_GENRES:
                continue
            if style_name in GENRE_BLACKLIST:
                continue
            genre_norm = normalise_genre(pair["genre"])
            style_norm = normalise_genre(pair["style"])
            genre_uri = MH[f"genre/{genre_norm}"]
            style_uri = MH[f"genre/{style_norm}"]
            g.add((genre_uri, RDF.type, MO.Genre))
            g.add((genre_uri, RDFS.label, Literal(genre_name, lang="en")))
            g.add((style_uri, RDF.type, MO.Genre))
            g.add((style_uri, RDFS.label, Literal(style_name, lang="en")))
            g.add((style_uri, MH.subgenreOf, genre_uri))

    # --- Artist relationships from MusicBrainz ---
    for rel in mb_data.get("artist_rels", []):
        target_mbid = rel.get("target_mbid")
        if not target_mbid:
            continue

        target_uri = MB[target_mbid]
        target_name = rel.get("target_name", "Unknown")
        g.add((target_uri, RDFS.label, Literal(target_name, lang="en")))

        rel_type = rel.get("type", "")
        direction = rel.get("direction", "")

        if rel_type == "member of band":
            # Skip eponymous groups (artist name == group name) to avoid
            # self-referencing member_of triples (e.g., "Bob Marley" member_of "Bob Marley")
            artist_name_lower = mb_data.get("name", "").lower().strip()
            target_name_lower = target_name.lower().strip()
            if artist_name_lower == target_name_lower:
                continue

            # Only type as MusicGroup if MB reports the target as type "Group"
            # and disambiguation doesn't indicate a label, project, or collective
            target_type = rel.get("target_type", "")
            target_disambig = rel.get("target_disambiguation", "").lower()
            NON_BAND_INDICATORS = {"label", "record label", "recording project",
                                   "side project", "collective", "production"}
            is_non_band = any(ind in target_disambig for ind in NON_BAND_INDICATORS)

            if direction == "forward":
                if is_non_band:
                    continue  # Skip — not a real performing band
                g.add((artist_uri, MO.member_of, target_uri))
                # Only type as MusicGroup if not already typed as SoloMusicArtist
                # (avoids disjointness violation: SoloMusicArtist ⊥ MusicGroup)
                if (target_type == "Group" or not target_type) and \
                   not any(g.triples((target_uri, RDF.type, MO.SoloMusicArtist))):
                    g.add((target_uri, RDF.type, MO.MusicGroup))
            else:
                g.add((target_uri, MO.member_of, artist_uri))
                if not any(g.triples((target_uri, RDF.type, MO.MusicGroup))):
                    g.add((target_uri, RDF.type, MO.SoloMusicArtist))

            # Instruments from attributes (normalised per RAG finding P20)
            for attr in rel.get("attributes", []):
                if attr not in ("original", "minor"):
                    normalised = normalise_instrument(attr)
                    if normalised is None:
                        continue  # Skip non-instruments (e.g., "eponymous")
                    inst_uri = MH[f"instrument/{normalise_genre(normalised)}"]
                    g.add((inst_uri, RDF.type, MO.Instrument))
                    g.add((inst_uri, RDFS.label, Literal(normalised, lang="en")))
                    member = artist_uri if direction == "forward" else target_uri
                    g.add((member, MH.playsInstrument, inst_uri))

        elif rel_type == "collaboration":
            g.add((artist_uri, MH.collaboratedWith, target_uri))
            g.add((target_uri, MH.collaboratedWith, artist_uri))  # symmetric

        elif rel_type == "influenced by":
            if direction == "forward":
                g.add((artist_uri, MH.influencedBy, target_uri))
                g.add((target_uri, MH.influenced, artist_uri))    # inverse
            else:
                g.add((target_uri, MH.influencedBy, artist_uri))
                g.add((artist_uri, MH.influenced, target_uri))    # inverse

        elif rel_type == "producer":
            if direction == "backward":
                g.add((artist_uri, MH.producedBy, target_uri))
                g.add((target_uri, MH.produced, artist_uri))
            else:
                g.add((target_uri, MH.producedBy, artist_uri))
                g.add((artist_uri, MH.produced, target_uri))

    # --- Instruments from Wikidata (normalised per RAG finding P20) ---
    if wd_data:
        for inst_name in wd_data.get("instruments", []):
            normalised = normalise_instrument(inst_name)
            if normalised is None:
                continue
            inst_uri = MH[f"instrument/{normalise_genre(normalised)}"]
            g.add((inst_uri, RDF.type, MO.Instrument))
            g.add((inst_uri, RDFS.label, Literal(normalised, lang="en")))
            g.add((artist_uri, MH.playsInstrument, inst_uri))

    # --- Awards from Wikidata (filtered) ---
    if wd_data:
        from config import AWARD_BLACKLIST_KEYWORDS, AWARD_BLACKLIST_EXACT
        for award_name in wd_data.get("awards", []):
            award_lower = award_name.lower()
            if award_lower in AWARD_BLACKLIST_EXACT:
                continue
            if any(kw in award_lower for kw in AWARD_BLACKLIST_KEYWORDS):
                continue
            award_uri = MH[f"award/{safe_uri(award_name)}"]
            g.add((award_uri, RDF.type, MH.Award))
            g.add((award_uri, RDFS.label, Literal(award_name, lang="en")))
            g.add((artist_uri, MH.wonAward, award_uri))

    # --- Record labels from Wikidata ---
    if wd_data:
        for label_name in wd_data.get("labels", []):
            label_uri = MH[f"label/{safe_uri(label_name)}"]
            g.add((label_uri, RDF.type, MH.RecordLabel))
            g.add((label_uri, RDFS.label, Literal(label_name, lang="en")))
            g.add((artist_uri, MH.signedTo, label_uri))

    # --- Influences from Wikidata ---
    if wd_data:
        for inf_name in wd_data.get("influences", []):
            inf_uri = MH[f"artist/{safe_uri(inf_name)}"]
            g.add((inf_uri, RDFS.label, Literal(inf_name, lang="en")))
            g.add((artist_uri, MH.influencedBy, inf_uri))
            g.add((inf_uri, MH.influenced, artist_uri))  # inverse

    # --- Release groups (albums) from MusicBrainz ---
    for rg in mb_data.get("release_groups", []):
        album_uri = MH[f"album/{rg['id']}"]
        g.add((album_uri, RDF.type, MO.Release))
        g.add((album_uri, RDFS.label, Literal(rg["title"], lang="en")))
        g.add((album_uri, DC.title, Literal(rg["title"], lang="en")))
        g.add((artist_uri, MH.released, album_uri))
        g.add((album_uri, MH.releasedBy, artist_uri))  # inverse

        if rg.get("first_release_date"):
            g.add((album_uri, MH.releaseDate, _typed_date_literal(rg["first_release_date"])))

        # Propagate artist genres to album (David's feedback Point 2)
        # Note: this is approximate — an artist's overall genres may not match
        # every album. Documented as a known limitation in the report.
        for genre_uri in artist_genre_uris:
            g.add((album_uri, MO.genre, genre_uri))

    # --- Tracks from MusicBrainz recordings ---
    for rg_id, tracks in mb_data.get("tracks", {}).items():
        album_uri = MH[f"album/{rg_id}"]
        for track in tracks:
            if track.get("id"):
                track_uri = MB_RECORDING[track["id"]]
                g.add((track_uri, RDF.type, MO.Track))
                g.add((track_uri, RDFS.label, Literal(track.get("title", "Unknown"), lang="en")))
                g.add((track_uri, DC.title, Literal(track.get("title", "Unknown"), lang="en")))
                g.add((album_uri, MH.hasTrack, track_uri))
                g.add((track_uri, MH.trackOn, album_uri))  # inverse
                if track.get("length"):
                    g.add((track_uri, MH.duration, Literal(int(track["length"]), datatype=XSD.integer)))

    # --- Compositions from Wikidata (classical) ---
    if wd_data:
        for comp in wd_data.get("compositions", []):
            comp_uri = MH[f"composition/{safe_uri(comp['title'])}"]
            g.add((comp_uri, RDF.type, MH.MusicalWork))
            g.add((comp_uri, RDFS.label, Literal(comp["title"], lang="en")))
            g.add((artist_uri, MH.composed, comp_uri))
            g.add((comp_uri, MH.composedBy, artist_uri))  # inverse
            if comp.get("date"):
                g.add((comp_uri, MH.compositionDate, _typed_date_literal(comp["date"])))
            if comp.get("genre"):
                from config import GENRE_BLACKLIST
                if comp["genre"].lower() not in GENRE_BLACKLIST:
                    genre_uri = MH[f"genre/{normalise_genre(comp['genre'])}"]
                    g.add((genre_uri, RDF.type, MO.Genre))
                    g.add((genre_uri, RDFS.label, Literal(comp["genre"].lower(), lang="en")))
                    g.add((comp_uri, MO.genre, genre_uri))

    return artist_uri


def detect_cover_recordings(g):
    """Detect cover recordings using Wikidata + MusicBrainz work relationships.

    Strategy (David's feedback Point 3):
    1. Collect all MB work IDs from cached track data
    2. Batch query Wikidata for composers of those works (P435 → P86)
    3. Compare Wikidata composer against the performing artist
    4. If performer ≠ original composer AND composer is not a band member → cover
    5. Fallback: use MB work-rels composer data

    Uses Wikidata as authoritative source for composer attribution.
    """
    import json
    import os
    from SPARQLWrapper import SPARQLWrapper, JSON as SPJSON

    covers_found = 0

    # Step 1: Collect all work IDs and their track/artist info from cached MB data
    work_tracks = {}  # work_id → list of {track_id, track_title, artist_mbid, artist_name}
    artist_members = {}  # artist_mbid → set of member MBIDs

    cache_dir = "data/structured"
    if not os.path.exists(cache_dir):
        print("  [COVERS] No cached data — skipping")
        return 0

    for filename in os.listdir(cache_dir):
        if not filename.startswith("musicbrainz_"):
            continue
        with open(os.path.join(cache_dir, filename)) as f:
            mb_data = json.load(f)

        artist_mbid = mb_data.get("mbid")
        if not artist_mbid:
            continue

        # Build member set for this artist
        members = {artist_mbid}
        for rel in mb_data.get("artist_rels", []):
            if rel.get("type") == "member of band" and rel.get("target_mbid"):
                members.add(rel["target_mbid"])
        artist_members[artist_mbid] = members

        for rg_id, tracks in mb_data.get("tracks", {}).items():
            for track in tracks:
                work = track.get("work")
                if not work or not work.get("id"):
                    continue
                work_id = work["id"]
                if work_id not in work_tracks:
                    work_tracks[work_id] = {"title": work["title"], "tracks": [], "mb_composers": work.get("composers", [])}
                work_tracks[work_id]["tracks"].append({
                    "track_id": track["id"],
                    "artist_mbid": artist_mbid,
                })

    if not work_tracks:
        print("  [COVERS] No works found in track data — skipping")
        return 0

    print(f"  [COVERS] Found {len(work_tracks)} unique works across tracks")

    # Step 2: Batch query Wikidata for composers using MB work IDs
    COVER_CACHE_PATH = "data/structured/wikidata_work_composers.json"
    wd_composers = {}
    if os.path.exists(COVER_CACHE_PATH):
        with open(COVER_CACHE_PATH) as f:
            wd_composers = json.load(f)

    # Find works not yet in cache
    uncached_work_ids = [wid for wid in work_tracks if wid not in wd_composers]

    if uncached_work_ids:
        print(f"  [COVERS] Querying Wikidata for {len(uncached_work_ids)} work composers...")
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.addCustomHttpHeader("User-Agent", "KE-CW2-MusicHistory/0.1")

        # Batch in groups of 50
        import time
        for i in range(0, len(uncached_work_ids), 50):
            batch = uncached_work_ids[i:i+50]
            values = " ".join(f'"{wid}"' for wid in batch)
            query = f"""
            SELECT ?mbWorkId ?composerLabel ?composerMbId WHERE {{
              VALUES ?mbWorkId {{ {values} }}
              ?work wdt:P435 ?mbWorkId .
              ?work wdt:P86 ?composer .
              OPTIONAL {{ ?composer wdt:P434 ?composerMbId . }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            """
            try:
                sparql.setQuery(query)
                sparql.setReturnFormat(SPJSON)
                results = sparql.query().convert()
                for r in results["results"]["bindings"]:
                    wid = r["mbWorkId"]["value"]
                    composer_name = r["composerLabel"]["value"]
                    composer_mb = r.get("composerMbId", {}).get("value")
                    if wid not in wd_composers:
                        wd_composers[wid] = []
                    wd_composers[wid].append({
                        "name": composer_name,
                        "mbid": composer_mb,
                    })
                time.sleep(2)  # Respect Wikidata rate limits
            except Exception as e:
                print(f"  [COVERS] Wikidata query error: {e}")

            # Mark works with no results so we don't re-query
            for wid in batch:
                if wid not in wd_composers:
                    wd_composers[wid] = []

        # Save cache
        with open(COVER_CACHE_PATH, "w") as f:
            json.dump(wd_composers, f, indent=2)
        print(f"  [COVERS] Cached {len(wd_composers)} work composer lookups")

    # Step 3: Detect covers
    for work_id, work_data in work_tracks.items():
        # Get composers — prefer Wikidata, fallback to MB
        composers = wd_composers.get(work_id, [])
        if not composers:
            composers = work_data.get("mb_composers", [])
        if not composers:
            continue

        composer_mbids = {c.get("mbid") for c in composers if c.get("mbid")}

        for track_info in work_data["tracks"]:
            performer_mbid = track_info["artist_mbid"]
            performer_members = artist_members.get(performer_mbid, {performer_mbid})

            # Check if any composer is the performer or a band member
            if composer_mbids & performer_members:
                continue  # Composer is the performer or a band member — not a cover

            if not composer_mbids:
                # No MB IDs for composers — can't reliably compare
                continue

            # This is a cover
            track_uri = URIRef(f"http://musicbrainz.org/recording/{track_info['track_id']}")
            artist_uri = URIRef(f"http://musicbrainz.org/artist/{performer_mbid}")
            work_uri = MH[f"composition/{safe_uri(work_data['title'])}"]

            g.add((work_uri, RDF.type, MH.MusicalWork))
            g.add((work_uri, RDFS.label, Literal(work_data["title"], lang="en")))

            for composer in composers:
                if composer.get("mbid"):
                    composer_uri = URIRef(f"http://musicbrainz.org/artist/{composer['mbid']}")
                    # Deduplicate: if an artist with the same name already
                    # exists under a different MB URI, reuse that URI to
                    # avoid creating duplicate entities for the same person.
                    comp_name = composer["name"].strip().lower()
                    for existing_s in g.subjects(RDFS.label, Literal(composer["name"], lang="en")):
                        if existing_s != composer_uri and (existing_s, RDF.type, MO.MusicArtist) in g:
                            composer_uri = existing_s
                            break
                    g.add((composer_uri, RDF.type, MO.MusicArtist))
                    g.add((composer_uri, RDFS.label, Literal(composer["name"], lang="en")))
                    g.add((composer_uri, MH.composed, work_uri))
                    g.add((work_uri, MH.composedBy, composer_uri))  # inverse

            g.add((track_uri, RDF.type, MH.CoverRecording))
            g.add((track_uri, MH.covers, work_uri))
            g.add((track_uri, MO.performer, artist_uri))
            covers_found += 1

    print(f"  [COVERS] Found {covers_found} cover recordings")
    return covers_found


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
        } UNION {
            ?someone mh:influencedBy ?artist .
        } UNION {
            ?artist mh:influencedBy ?someone .
        } UNION {
            ?artist mh:composed ?work .
        }
        ?artist rdfs:label ?label .
        FILTER(STRSTARTS(STR(?artist), "http://musicbrainz.org/artist/"))
        FILTER(
            !EXISTS { ?artist mh:countryOfOrigin ?c } ||
            !EXISTS { ?artist mo:genre ?g }
        )
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
                raw = musicbrainzngs.get_artist_by_id(mbid, includes=["tags"])["artist"]
                # Extract top tags as genres
                tags = [t["name"] for t in raw.get("tag-list", [])
                        if int(t.get("count", 0)) >= 3]
                life_span = raw.get("life-span", {})
                cache[mbid] = {
                    "country": raw.get("country"),
                    "type": raw.get("type"),
                    "tags": tags,
                    "begin": life_span.get("begin"),
                    "end": life_span.get("end"),
                    "gender": raw.get("gender"),
                }
                api_calls += 1
            except Exception:
                cache[mbid] = {"country": None, "type": None, "tags": [], "begin": None, "end": None, "gender": None}
                continue
            detail = cache[mbid]

        # Country
        country = detail.get("country")
        if country and not any(g.triples((artist_uri, MH.countryOfOrigin, None))):
            country_code = country.lower()
            country_uri = MH[f"country/{country_code}"]
            g.add((country_uri, RDF.type, MH.Country))
            g.add((country_uri, RDFS.label, Literal(country, lang="en")))
            full_name = ISO_COUNTRY_NAMES.get(country_code)
            if full_name:
                g.add((country_uri, RDFS.label, Literal(full_name, lang="en")))
            g.add((artist_uri, MH.countryOfOrigin, country_uri))
            enriched += 1

        # Genres from tags
        from config import GENRE_BLACKLIST
        for tag_name in detail.get("tags", []):
            if tag_name.lower() in GENRE_BLACKLIST:
                continue
            genre_norm = normalise_genre(tag_name)
            genre_uri = MH[f"genre/{genre_norm}"]
            if not any(g.triples((artist_uri, MO.genre, genre_uri))):
                if not any(g.triples((genre_uri, RDF.type, None))):
                    g.add((genre_uri, RDF.type, MO.Genre))
                    g.add((genre_uri, RDFS.label, Literal(genre_norm.replace("_", " "), lang="en")))
                g.add((artist_uri, MO.genre, genre_uri))
                enriched += 1

        # Birth/death dates
        SCHEMA = Namespace("https://schema.org/")
        if detail.get("begin") and not any(g.triples((artist_uri, SCHEMA.birthDate, None))):
            g.add((artist_uri, SCHEMA.birthDate, _typed_date_literal(detail["begin"])))
            enriched += 1
        if detail.get("end") and not any(g.triples((artist_uri, SCHEMA.deathDate, None))):
            g.add((artist_uri, SCHEMA.deathDate, _typed_date_literal(detail["end"])))
            enriched += 1

        # Type (respecting disjointness)
        artist_type = detail.get("type", "")
        if artist_type == "Person" and not any(g.triples((artist_uri, RDF.type, MO.MusicGroup))):
            g.add((artist_uri, RDF.type, MO.SoloMusicArtist))
        elif artist_type == "Group" and not any(g.triples((artist_uri, RDF.type, MO.SoloMusicArtist))):
            g.add((artist_uri, RDF.type, MO.MusicGroup))

    # Save enrichment cache
    os.makedirs(os.path.dirname(ENRICHMENT_CACHE), exist_ok=True)
    with open(ENRICHMENT_CACHE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"  [ENRICH] Added {enriched} triples (country, genre, dates) for related artists ({api_calls} API calls, {len(results) - api_calls} cached)")
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

    # Second pass: merge duplicate mb: URIs (same label, different MBIDs)
    # MusicBrainz can have multiple entries for the same real-world artist
    mb_label_groups = {}
    for s, p, o in g.triples((None, RDFS.label, None)):
        uri_str = str(s)
        if uri_str.startswith("http://musicbrainz.org/artist/"):
            label_key = str(o).lower().strip()
            mb_label_groups.setdefault(label_key, set()).add(s)

    mb_merged = 0
    for label, uris in mb_label_groups.items():
        if len(uris) <= 1:
            continue

        uris_list = list(uris)
        # Pick canonical: prefer the one with rdf:type assigned
        canonical = None
        for u in uris_list:
            if any(g.triples((u, RDF.type, None))):
                canonical = u
                break
        if canonical is None:
            canonical = uris_list[0]

        for u in uris_list:
            if u == canonical:
                continue
            for s, p, o in list(g.triples((u, None, None))):
                g.remove((s, p, o))
                if p != RDFS.label or not any(g.triples((canonical, RDFS.label, o))):
                    g.add((canonical, p, o))
            for s, p, o in list(g.triples((None, None, u))):
                g.remove((s, p, o))
                g.add((s, p, canonical))
            mb_merged += 1

    print(f"  [CONSOLIDATE] Merged {consolidated} mh:→mb: + {mb_merged} mb:→mb: duplicates")
    return consolidated + mb_merged


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
        # Note: influencedBy is excluded because artists can be influenced by
        # non-musicians (e.g., Andy Warhol, Charlie Chaplin, Timothy Leary)
        if any(g.triples((None, MH.collaboratedWith, entity))) or \
           any(g.triples((entity, MH.collaboratedWith, None))) or \
           any(g.triples((entity, MH.composed, None))) or \
           any(g.triples((entity, MO.performer, None))):
            g.add((entity, RDF.type, MO.MusicArtist))
            assigned += 1
        elif any(g.triples((None, MH.influencedBy, entity))) or \
             any(g.triples((entity, MH.influencedBy, None))):
            # Influence targets may not be musicians — use broader Person type
            from rdflib.namespace import FOAF
            g.add((entity, RDF.type, FOAF.Person))
            assigned += 1
        elif any(g.triples((None, MO.member_of, entity))):
            g.add((entity, RDF.type, MO.MusicGroup))
            assigned += 1
        elif "artist" in uri_str or "mb" in uri_str:
            g.add((entity, RDF.type, MO.MusicArtist))
            assigned += 1

    print(f"  [TYPES] Assigned rdf:type to {assigned} orphan entities")
    return assigned


def classify_multinational_bands(g):
    """Auto-classify bands with members from >1 country as MultinationalBand.

    Populates William's mh:MultinationalBand class from instance data.
    A band is multinational if its members have different countryOfOrigin values.
    """
    query = """
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX mh: <http://example.org/music-history/>

    SELECT ?band (COUNT(DISTINCT ?country) AS ?countryCount) WHERE {
        ?member mo:member_of ?band .
        ?band a mo:MusicGroup .
        ?member mh:countryOfOrigin ?country .
    }
    GROUP BY ?band
    HAVING (COUNT(DISTINCT ?country) > 1)
    """
    results = list(g.query(query))
    classified = 0
    for row in results:
        g.add((row.band, RDF.type, MH.MultinationalBand))
        classified += 1

    print(f"  [CLASSIFY] {classified} bands classified as MultinationalBand")
    return classified


def classify_international_collaborators(g):
    """Auto-classify artists who collaborated with artists from different countries.

    Uses the same hybrid modelling pattern as MultinationalBand: the class is
    declared in the ontology, but membership is computed via SPARQL because
    OWL2 cannot express cross-individual property value comparisons.
    """
    query = """
    PREFIX mh: <http://example.org/music-history/>

    SELECT DISTINCT ?artist WHERE {
        ?artist mh:collaboratedWith ?other .
        ?artist mh:countryOfOrigin ?c1 .
        ?other mh:countryOfOrigin ?c2 .
        FILTER(?c1 != ?c2)
    }
    """
    results = list(g.query(query))
    classified = 0
    for row in results:
        if (row.artist, RDF.type, MH.InternationalCollaborator) not in g:
            g.add((row.artist, RDF.type, MH.InternationalCollaborator))
            classified += 1

    print(f"  [CLASSIFY] {classified} artists classified as InternationalCollaborator")
    return classified


def validate_and_clean(g):
    """Post-processing validation to catch and fix common data quality issues.

    Detects and removes:
    1. Self-referencing triples (A → property → A)
    2. Type mismatches (genre as alterEgo, artist as performedAt venue)
    3. Inverted producedBy triples (artist producedBy work instead of work producedBy artist)
    4. Incorrect entity linking results

    This step demonstrates that automated KG construction requires
    validation — LLMs are fast but introduce noise that must be caught.
    """
    removed = 0
    fixed = 0

    # 1. Remove self-referencing triples
    self_ref_props = [
        MH.alterEgo, MH.influencedBy, MH.collaboratedWith,
        MH.subgenreOf, MH.founded, MH.covers,
    ]
    for prop in self_ref_props:
        for s, p, o in list(g.triples((None, prop, None))):
            if s == o:
                g.remove((s, p, o))
                removed += 1

    # 2. Remove alterEgo where object is a Genre (entity linking error)
    for s, p, o in list(g.triples((None, MH.alterEgo, None))):
        if any(g.triples((o, RDF.type, MO.Genre))):
            g.remove((s, p, o))
            removed += 1

    # 3. Remove performedAt where object is a Genre (entity linking error)
    for s, p, o in list(g.triples((None, MH.performedAt, None))):
        if any(g.triples((o, RDF.type, MO.Genre))):
            g.remove((s, p, o))
            removed += 1

    # 4. Fix inverted producedBy — if subject is an Artist and object is a Work,
    #    the triple is inverted (should be Work producedBy Artist)
    for s, p, o in list(g.triples((None, MH.producedBy, None))):
        s_is_artist = any(g.triples((s, RDF.type, MO.MusicArtist))) or \
                      any(g.triples((s, RDF.type, MO.SoloMusicArtist))) or \
                      any(g.triples((s, RDF.type, MO.MusicGroup)))
        o_is_artist = any(g.triples((o, RDF.type, MO.MusicArtist))) or \
                      any(g.triples((o, RDF.type, MO.SoloMusicArtist))) or \
                      any(g.triples((o, RDF.type, MO.MusicGroup)))
        if s_is_artist and not o_is_artist:
            # Inverted — subject is artist, object should be the producer
            # Actually the whole triple is backwards: should be (work, producedBy, artist)
            # Remove the bad triple
            g.remove((s, p, o))
            removed += 1

    # 5. Fix inverted produced — same check
    for s, p, o in list(g.triples((None, MH.produced, None))):
        s_is_work = any(g.triples((s, RDF.type, MO.Release))) or \
                    any(g.triples((s, RDF.type, MO.Track))) or \
                    any(g.triples((s, RDF.type, MH.MusicalWork)))
        if s_is_work:
            # Work produced Artist — inverted
            g.remove((s, p, o))
            removed += 1

    # 6. Remove founded where object matches the subject's own label
    for s, p, o in list(g.triples((None, MH.founded, None))):
        s_labels = {str(l).lower() for _, _, l in g.triples((s, RDFS.label, None))}
        o_labels = {str(l).lower() for _, _, l in g.triples((o, RDFS.label, None))}
        if s_labels & o_labels:
            g.remove((s, p, o))
            removed += 1

    # 7. Remove subgenreOf self-loops (genre subgenreOf itself)
    for s, p, o in list(g.triples((None, MH.subgenreOf, None))):
        s_labels = {str(l).lower() for _, _, l in g.triples((s, RDFS.label, None))}
        o_labels = {str(l).lower() for _, _, l in g.triples((o, RDFS.label, None))}
        if s_labels & o_labels:
            g.remove((s, p, o))
            removed += 1

    # 8. Remove self-referencing member_of (A member_of A)
    for s, p, o in list(g.triples((None, MO.member_of, None))):
        s_labels = {str(l).lower() for _, _, l in g.triples((s, RDFS.label, None))}
        o_labels = {str(l).lower() for _, _, l in g.triples((o, RDFS.label, None))}
        if s == o or (s_labels & o_labels):
            g.remove((s, p, o))
            removed += 1

    # 9. Remove subgenreOf where parent is "non-music" (Discogs artifact)
    for s, p, o in list(g.triples((None, MH.subgenreOf, None))):
        o_labels = {str(l).lower() for _, _, l in g.triples((o, RDFS.label, None))}
        if 'non-music' in o_labels:
            g.remove((s, p, o))
            removed += 1

    # 10. Remove alterEgo where object is typed as Artist/MusicGroup (entity linking error)
    #    alterEgo should link to a Persona (stage name), not another artist entity
    for s, p, o in list(g.triples((None, MH.alterEgo, None))):
        o_is_artist = any(g.triples((o, RDF.type, MO.MusicArtist))) or \
                      any(g.triples((o, RDF.type, MO.SoloMusicArtist))) or \
                      any(g.triples((o, RDF.type, MO.MusicGroup)))
        if o_is_artist:
            g.remove((s, p, o))
            removed += 1

    # 9. Remove alterEgo where object is a Release/Track/MusicalWork (entity linking error)
    for s, p, o in list(g.triples((None, MH.alterEgo, None))):
        o_is_work = any(g.triples((o, RDF.type, MO.Release))) or \
                    any(g.triples((o, RDF.type, MO.Track))) or \
                    any(g.triples((o, RDF.type, MH.MusicalWork)))
        if o_is_work:
            g.remove((s, p, o))
            removed += 1

    # 12. Remove performedAt where object is typed as Release/Track (venue linking error)
    for s, p, o in list(g.triples((None, MH.performedAt, None))):
        o_is_work = any(g.triples((o, RDF.type, MO.Release))) or \
                    any(g.triples((o, RDF.type, MO.Track))) or \
                    any(g.triples((o, RDF.type, MH.MusicalWork)))
        if o_is_work:
            g.remove((s, p, o))
            removed += 1

    # 13. Remove collaboratedWith where object is a Track (entity linking error)
    #     e.g., "Montserrat Caballé" fuzzy-matched to a track title
    for s, p, o in list(g.triples((None, MH.collaboratedWith, None))):
        o_is_track = any(g.triples((o, RDF.type, MO.Track))) or \
                     any(g.triples((o, RDF.type, MH.CoverRecording)))
        if o_is_track:
            g.remove((s, p, o))
            removed += 1

    # 14. Remove produced where object is not a work (entity linking error)
    #     e.g., "Off the Wall - Michael Jackson" fuzzy-matched to "Michael Jackson"
    WORK_TYPES = {MO.Release, MO.Track, MH.MusicalWork}
    for s, p, o in list(g.triples((None, MH.produced, None))):
        o_types = {t for _, _, t in g.triples((o, RDF.type, None))}
        if o_types and not (o_types & WORK_TYPES):
            g.remove((s, p, o))
            removed += 1

    # 15. Remove collaboratedWith where object is a Release (entity linking error)
    #     e.g., "Stan Getz" fuzzy-matched to album "Getz / Gilberto"
    for s, p, o in list(g.triples((None, MH.collaboratedWith, None))):
        o_is_release = any(g.triples((o, RDF.type, MO.Release)))
        if o_is_release:
            g.remove((s, p, o))
            removed += 1

    # 16. Remove albumGrouping self-references (album grouped under itself)
    for s, p, o in list(g.triples((None, MH.albumGrouping, None))):
        s_labels = {str(l).lower() for _, _, l in g.triples((s, RDFS.label, None))}
        o_labels = {str(l).lower() for _, _, l in g.triples((o, RDFS.label, None))}
        if s_labels & o_labels:
            g.remove((s, p, o))
            removed += 1

    # 17. Resolve disjointness violations (SoloMusicArtist ⊥ MusicGroup)
    #     If an entity has both types, keep the one from its primary MB data:
    #     - If it has member_of triples (it IS a member) → keep SoloMusicArtist
    #     - If it has members (others are member_of it) → keep MusicGroup
    for s in list(set(s for s, _, _ in g.triples((None, RDF.type, MO.SoloMusicArtist)))):
        if any(g.triples((s, RDF.type, MO.MusicGroup))):
            # Has both types — resolve
            is_member = any(g.triples((s, MO.member_of, None)))
            has_members = any(g.triples((None, MO.member_of, s)))
            if has_members and not is_member:
                g.remove((s, RDF.type, MO.SoloMusicArtist))
            else:
                g.remove((s, RDF.type, MO.MusicGroup))
            removed += 1

    # 18. Deduplicate compositionDate — keep only the earliest date per work
    for s in set(s for s, _, _ in g.triples((None, MH.compositionDate, None))):
        dates = list(g.triples((s, MH.compositionDate, None)))
        if len(dates) > 1:
            # Keep the earliest date
            dates_sorted = sorted(dates, key=lambda x: str(x[2]))
            for _, dp, do in dates_sorted[1:]:
                g.remove((s, dp, do))
                removed += 1

    # 19. Remove orphan genres (Genre entities with no references)
    for s, _, _ in list(g.triples((None, RDF.type, MO.Genre))):
        if not any(g.triples((None, MO.genre, s))) and not any(g.triples((s, MH.subgenreOf, None))):
            # Remove all triples for this orphan genre
            for triple in list(g.triples((s, None, None))):
                g.remove(triple)
                removed += 1
            for triple in list(g.triples((None, None, s))):
                g.remove(triple)
                removed += 1

    # 20. Deduplicate genre labels — keep only the normalised label per genre entity
    for s, p, o in g.triples((None, RDF.type, MO.Genre)):
        labels = list(g.triples((s, RDFS.label, None)))
        if len(labels) > 1:
            # Derive the canonical label from the URI
            uri_suffix = str(s).split("/genre/")[-1] if "/genre/" in str(s) else None
            canonical = uri_suffix.replace("_", " ") if uri_suffix else None
            # Remove all labels except the canonical one
            for _, lp, lo in labels:
                if canonical and str(lo) != canonical:
                    g.remove((s, lp, lo))
                    removed += 1
            # Ensure canonical label exists
            if canonical and not any(g.triples((s, RDFS.label, None))):
                g.add((s, RDFS.label, Literal(canonical, lang="en")))
        elif len(labels) == 1:
            # Single label — check it matches the normalised form
            uri_suffix = str(s).split("/genre/")[-1] if "/genre/" in str(s) else None
            canonical = uri_suffix.replace("_", " ") if uri_suffix else None
            if canonical and str(labels[0][2]) != canonical:
                g.remove(labels[0])
                g.add((s, RDFS.label, Literal(canonical, lang="en")))

    # 21. Remove MusicArtist type from entities also typed as Release/Track/MusicalWork
    #     These are entity linking errors where album/track titles matched artist names
    work_types = {MO.Release, MO.Track, MH.MusicalWork, MH.CoverRecording}
    for s in list(set(s for s, _, _ in g.triples((None, RDF.type, MO.MusicArtist)))):
        s_types = set(t for _, _, t in g.triples((s, RDF.type, None)))
        if s_types & work_types:
            g.remove((s, RDF.type, MO.MusicArtist))
            if (s, RDF.type, MH.CollaboratingArtist) in g:
                g.remove((s, RDF.type, MH.CollaboratingArtist))
            removed += 1

    # 22. Remove mh:artist/ entities whose labels match existing track/composition titles
    #     These are LLM extraction errors where song names were resolved as new artist entities
    track_labels = set()
    for s, _, _ in g.triples((None, RDF.type, MO.Track)):
        for _, _, l in g.triples((s, RDFS.label, None)):
            track_labels.add(str(l).lower())
    comp_labels = set()
    for s, _, _ in g.triples((None, RDF.type, MH.MusicalWork)):
        for _, _, l in g.triples((s, RDFS.label, None)):
            comp_labels.add(str(l).lower())
    song_labels = track_labels | comp_labels

    mh_artist_prefix = "http://example.org/music-history/artist/"
    for s in list(set(s for s, _, _ in g.triples((None, RDF.type, MO.MusicArtist)))):
        if not str(s).startswith(mh_artist_prefix):
            continue
        s_labels = [str(l).lower() for _, _, l in g.triples((s, RDFS.label, None))]
        # Check if label matches a known track/composition title
        if any(l in song_labels for l in s_labels):
            for triple in list(g.triples((s, None, None))):
                g.remove(triple)
            for triple in list(g.triples((None, None, s))):
                g.remove(triple)
            removed += 1
            continue
        # Also remove mh:artist/ entities with no real artist relationships
        # (only type + label + genre) — likely song titles from failed entity linking
        all_triples = list(g.triples((s, None, None)))
        non_metadata = [t for t in all_triples
                       if t[1] not in (RDF.type, RDFS.label, MO.genre)]
        as_object = list(g.triples((None, None, s)))
        if not non_metadata and not as_object:
            for triple in list(g.triples((s, None, None))):
                g.remove(triple)
            removed += 1

    print(f"  [VALIDATE] Removed {removed} invalid triples, fixed {fixed}")
    return removed


def assert_defined_class_instances(g):
    """Explicitly assert instances of defined classes based on their conditions.

    While a reasoner would infer these from owl:equivalentClass restrictions,
    we also assert them explicitly to ensure SPARQL queries can find them
    without requiring reasoning. (CW1 feedback: 'no instance inferred')

    Defined classes:
    - AwardWinningArtist: MusicArtist AND wonAward some MusicAward
    - CollaboratingArtist: MusicArtist AND collaboratedWith some MusicArtist
    - ProducerArtist: MusicArtist AND produced some work
    """
    asserted = 0

    # AwardWinningArtist
    query_award = """
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX mh: <http://example.org/music-history/>
    SELECT DISTINCT ?artist WHERE {
        ?artist mh:wonAward ?award .
        { ?artist a mo:MusicArtist } UNION
        { ?artist a mo:SoloMusicArtist } UNION
        { ?artist a mo:MusicGroup }
    }
    """
    for row in g.query(query_award):
        g.add((row.artist, RDF.type, MH.AwardWinningArtist))
        asserted += 1

    # CollaboratingArtist
    query_collab = """
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX mh: <http://example.org/music-history/>
    SELECT DISTINCT ?artist WHERE {
        ?artist mh:collaboratedWith ?other .
        { ?artist a mo:MusicArtist } UNION
        { ?artist a mo:SoloMusicArtist } UNION
        { ?artist a mo:MusicGroup }
    }
    """
    for row in g.query(query_collab):
        g.add((row.artist, RDF.type, MH.CollaboratingArtist))
        asserted += 1

    # ProducerArtist — check produced OR producedBy (inverse)
    query_producer = """
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX mh: <http://example.org/music-history/>
    SELECT DISTINCT ?artist WHERE {
        { ?artist mh:produced ?work } UNION
        { ?work mh:producedBy ?artist }
        { ?artist a mo:MusicArtist } UNION
        { ?artist a mo:SoloMusicArtist } UNION
        { ?artist a mo:MusicGroup }
    }
    """
    for row in g.query(query_producer):
        g.add((row.artist, RDF.type, MH.ProducerArtist))
        asserted += 1

    print(f"  [DEFINED] Asserted {asserted} defined class instances")
    return asserted
