import os
import json
import re

from config import (
    CACHE_DIR_STRUCTURED, CACHE_DIR_TEXT,
    GENRE_BLACKLIST, MIN_TAG_COUNT,
)


def normalise_genre(name):
    """Normalise a genre/style name for URI creation.
    Lowercases, strips whitespace, replaces spaces and slashes with underscores.
    """
    return name.strip().lower().replace(" ", "_").replace("/", "_")


def safe_uri(text):
    """Convert any string to a valid URI component."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text.strip().replace(" ", "_"))


def cache_path(source, artist_name, subdir="structured"):
    """Get the cache file path for a given source and artist."""
    base = CACHE_DIR_STRUCTURED if subdir == "structured" else CACHE_DIR_TEXT
    safe_name = safe_uri(artist_name)
    return os.path.join(base, f"{source}_{safe_name}.json")


def cache_load(source, artist_name, subdir="structured"):
    """Load cached data if it exists, otherwise return None."""
    path = cache_path(source, artist_name, subdir)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def cache_save(source, artist_name, data, subdir="structured"):
    """Save data to cache."""
    path = cache_path(source, artist_name, subdir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def is_valid_genre(tag_name, tag_count=0):
    """Check if a tag should be treated as a genre."""
    return (
        tag_name.lower() not in GENRE_BLACKLIST
        and int(tag_count) >= MIN_TAG_COUNT
    )


def run_sparql_anything(query_file, output_file, values=None):
    """Run a SPARQL Anything CONSTRUCT query.

    Uses PySPARQL-Anything which auto-manages the Java jar.
    Requires Java 21+ installed.

    Args:
        query_file: path to the .sparql file
        output_file: path to write the .ttl output
        values: optional dict of variable bindings
    """
    import pysparql_anything as sa
    engine = sa.SparqlAnything()
    kwargs = {
        "query": query_file,
        "format": "TTL",
        "output": output_file,
    }
    if values:
        kwargs["values"] = values
    engine.run(**kwargs)
