"""Ingest RAG completion results into the Knowledge Graph.

Reads the JSON outputs from the 10 RAG gap-filling prompts (P34–P43)
and adds the resolved triples to the KG. Uses label-based entity linking
to match RAG results to existing entities in the graph.

Course technique: KG Completion via RAG (Week 11) — programmatic ingestion.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF

from config import NAMESPACE_URI, MUSIC_ONTOLOGY_URI
from utils import normalise_genre, safe_uri

MO = Namespace(MUSIC_ONTOLOGY_URI)
MH = Namespace(NAMESPACE_URI)

RAG_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "rag_responses")


def _find_entity_by_label(g, name):
    """Find an entity URI by its rdfs:label or foaf:name."""
    name_lower = name.lower().strip()
    for s, p, o in g.triples((None, RDFS.label, None)):
        if str(o).lower().strip() == name_lower:
            return s
    for s, p, o in g.triples((None, FOAF.name, None)):
        if str(o).lower().strip() == name_lower:
            return s
    return None


def _get_or_create_country(g, code):
    """Get or create a country entity."""
    if not code or code in ("n/a", "unknown"):
        return None
    code_lower = code.lower()
    uri = MH[f"country/{code_lower}"]
    if not any(g.triples((uri, RDF.type, None))):
        g.add((uri, RDF.type, MH.Country))
        g.add((uri, RDFS.label, Literal(code.upper(), lang="en")))
    return uri


def _get_or_create_genre(g, genre_name):
    """Get or create a genre entity."""
    if not genre_name or genre_name in ("n/a", "unknown"):
        return None
    norm = normalise_genre(genre_name)
    uri = MH[f"genre/{norm}"]
    if not any(g.triples((uri, RDF.type, None))):
        g.add((uri, RDF.type, MO.Genre))
        g.add((uri, RDFS.label, Literal(genre_name.lower(), lang="en")))
    return uri


def ingest_i1_secondary_artists(g):
    """I1: Add country and genre to secondary artists."""
    path = os.path.join(RAG_DIR, "i1_secondary_artists_enrichment.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        name = entry["name"]
        entity = _find_entity_by_label(g, name)
        if not entity:
            continue

        # Country
        country_uri = _get_or_create_country(g, entry.get("country"))
        if country_uri and not any(g.triples((entity, MH.countryOfOrigin, None))):
            g.add((entity, MH.countryOfOrigin, country_uri))
            added += 1

        # Genre
        genre_uri = _get_or_create_genre(g, entry.get("primary_genre"))
        if genre_uri and not any(g.triples((entity, MO.genre, None))):
            g.add((entity, MO.genre, genre_uri))
            added += 1

    print(f"  [I1] Secondary artists: {added} triples added")
    return added


def ingest_i5_cover_composers(g):
    """I5: Add country, genre, and dates to cover composers."""
    path = os.path.join(RAG_DIR, "i5_cover_composers_enrichment.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        name = entry["name"]
        if name == "[traditional]":
            continue
        entity = _find_entity_by_label(g, name)
        if not entity:
            continue

        # Country
        country_uri = _get_or_create_country(g, entry.get("country"))
        if country_uri and not any(g.triples((entity, MH.countryOfOrigin, None))):
            g.add((entity, MH.countryOfOrigin, country_uri))
            added += 1

        # Genre
        genre_uri = _get_or_create_genre(g, entry.get("primary_genre"))
        if genre_uri and not any(g.triples((entity, MO.genre, None))):
            g.add((entity, MO.genre, genre_uri))
            added += 1

    print(f"  [I5] Cover composers: {added} triples added")
    return added


def ingest_o2_performed_at(g):
    """O2: Add performedAt triples."""
    path = os.path.join(RAG_DIR, "o2_performedat_events.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        artist = _find_entity_by_label(g, entry["artist"])
        if not artist:
            continue
        venue_name = entry["venue_or_event"]
        venue_uri = MH[f"venue/{safe_uri(venue_name)}"]
        if not any(g.triples((venue_uri, RDF.type, None))):
            g.add((venue_uri, RDF.type, MH.Venue))
            g.add((venue_uri, RDFS.label, Literal(venue_name, lang="en")))
        # Avoid duplicates
        if not any(g.triples((artist, MH.performedAt, venue_uri))):
            g.add((artist, MH.performedAt, venue_uri))
            added += 1

    print(f"  [O2] performedAt events: {added} triples added")
    return added


def ingest_o3_collaborations(g):
    """O3: Add direct collaboratedWith triples."""
    path = os.path.join(RAG_DIR, "o3_collaborations_direct.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        a1 = _find_entity_by_label(g, entry["artist1"])
        a2 = _find_entity_by_label(g, entry["artist2"])
        if not a1 or not a2 or a1 == a2:
            continue
        # Only add if both exist — avoid creating stub entities
        if not any(g.triples((a1, MH.collaboratedWith, a2))):
            g.add((a1, MH.collaboratedWith, a2))
            g.add((a2, MH.collaboratedWith, a1))  # symmetric
            added += 2

    print(f"  [O3] Direct collaborations: {added} triples added")
    return added


def ingest_o4_founded(g):
    """O4: Add founded triples."""
    path = os.path.join(RAG_DIR, "o4_founded_orgs.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        artist = _find_entity_by_label(g, entry["artist"])
        if not artist:
            continue
        org_name = entry["organisation"]
        # Check if org already exists in KG
        org_uri = _find_entity_by_label(g, org_name)
        if not org_uri:
            org_uri = MH[f"org/{safe_uri(org_name)}"]
            g.add((org_uri, RDFS.label, Literal(org_name, lang="en")))
            # Type based on category
            org_type = entry.get("type", "")
            if org_type == "label":
                g.add((org_uri, RDF.type, MH.RecordLabel))
            elif org_type == "band":
                g.add((org_uri, RDF.type, MO.MusicGroup))
            elif org_type in ("foundation", "cultural_org"):
                g.add((org_uri, RDF.type, MH.Organisation))
            else:
                g.add((org_uri, RDF.type, MH.Organisation))
        if not any(g.triples((artist, MH.founded, org_uri))):
            g.add((artist, MH.founded, org_uri))
            added += 1

    print(f"  [O4] Founded organisations: {added} triples added")
    return added


def ingest_o5_musical_periods(g):
    """O5: Add hasMusicalPeriod triples."""
    path = os.path.join(RAG_DIR, "o5_musical_periods.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    added = 0
    for entry in data:
        artist = _find_entity_by_label(g, entry["artist"])
        if not artist:
            continue
        period_name = entry["period"]
        period_uri = MH[f"period/{safe_uri(period_name)}"]
        if not any(g.triples((period_uri, RDF.type, None))):
            g.add((period_uri, RDF.type, MH.MusicalPeriod))
            g.add((period_uri, RDFS.label, Literal(period_name, lang="en")))
        if not any(g.triples((artist, MH.hasMusicalPeriod, period_uri))):
            g.add((artist, MH.hasMusicalPeriod, period_uri))
            added += 1

    print(f"  [O5] Musical periods: {added} triples added")
    return added


def ingest_i4_hildegard_genres(g):
    """I4: Add genres to Hildegard von Bingen."""
    path = os.path.join(RAG_DIR, "i4_hildegard_genres.json")
    if not os.path.exists(path):
        return 0
    data = json.load(open(path))
    artist = _find_entity_by_label(g, "Hildegard von Bingen")
    if not artist:
        return 0
    added = 0

    for genre_name in data.get("genres", []):
        genre_uri = _get_or_create_genre(g, genre_name)
        if genre_uri and not any(g.triples((artist, MO.genre, genre_uri))):
            g.add((artist, MO.genre, genre_uri))
            added += 1

    for period in data.get("musical_periods", []):
        period_name = period["period"]
        period_uri = MH[f"period/{safe_uri(period_name)}"]
        if not any(g.triples((period_uri, RDF.type, None))):
            g.add((period_uri, RDF.type, MH.MusicalPeriod))
            g.add((period_uri, RDFS.label, Literal(period_name, lang="en")))
        if not any(g.triples((artist, MH.hasMusicalPeriod, period_uri))):
            g.add((artist, MH.hasMusicalPeriod, period_uri))
            added += 1

    for inst_name in data.get("instruments", []):
        inst_uri = MH[f"instrument/{safe_uri(inst_name)}"]
        if not any(g.triples((inst_uri, RDF.type, None))):
            g.add((inst_uri, RDF.type, MO.Instrument))
            g.add((inst_uri, RDFS.label, Literal(inst_name, lang="en")))
        if not any(g.triples((artist, MH.playsInstrument, inst_uri))):
            g.add((artist, MH.playsInstrument, inst_uri))
            added += 1

    print(f"  [I4] Hildegard genres/periods/instruments: {added} triples added")
    return added


def ingest_all(g):
    """Run all RAG ingestion steps."""
    print("=" * 60)
    print("RAG COMPLETION INGESTION")
    print("=" * 60)

    total = 0
    total += ingest_i1_secondary_artists(g)
    total += ingest_i5_cover_composers(g)
    total += ingest_o2_performed_at(g)
    total += ingest_o3_collaborations(g)
    total += ingest_o4_founded(g)
    total += ingest_o5_musical_periods(g)
    total += ingest_i4_hildegard_genres(g)

    print(f"\n  Total RAG triples ingested: {total}")
    print(f"  Graph now has {len(g)} triples")
    return total


if __name__ == "__main__":
    g = Graph()
    g.parse("../ontology/music_history_kg.ttl", format="turtle")
    print(f"KG loaded: {len(g)} triples\n")

    ingest_all(g)

    g.serialize(destination="../ontology/music_history_kg.ttl", format="turtle")
    print(f"\nSaved to ontology/music_history_kg.ttl")
