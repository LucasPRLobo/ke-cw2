"""LLM-based triple extraction from Wikipedia text.

Uses a free-tier LLM API to extract structured triples from
unstructured Wikipedia article text. Results are cached as JSON
files to avoid re-calling the API on subsequent pipeline runs.

Course technique: Week 7 — LLM chained prompting for triple extraction.
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import safe_uri

TEXT_DIR = os.path.join(os.path.dirname(__file__), "data", "text")

EXTRACTION_PROMPT = """You are a knowledge engineer and music historian. Extract structured triples from this Wikipedia article intro about {artist_name}.

Use ONLY these predicates:
- released (artist released album)
- composed (artist composed work)
- collaboratedWith (artist collaborated with another artist)
- memberOf (artist is member of group)
- hasMember (group has member)
- hasGenre (artist/work has genre)
- alterEgo (artist has stage persona or alter ego)
- albumGrouping (album belongs to a named series)
- producedBy (album/work was produced by producer)
- produced (producer produced album/work)
- performedAt (artist performed at venue/event)
- influencedBy (artist was influenced by another artist)
- hasMusicalPeriod (artist belongs to musical period/era)
- pioneerOf (artist pioneered a genre)
- founded (artist founded organisation/band/label)

Do NOT extract: birth/death dates, country, gender, awards, instruments, record labels — these come from structured sources.

Return ONLY a JSON array of objects with "subject", "predicate", "object" fields.
No explanation, no markdown, just the JSON array.

Article text:
{text}"""


def _call_llm(prompt):
    """Call an LLM API. Tries multiple free-tier providers in order."""

    # Try 1: Google Gemini (free tier: 15 RPM, 1M tokens/min)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            resp = requests.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
            }, timeout=60)
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Strip markdown code fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            return text.strip()
        except Exception as e:
            print(f"    [LLM] Gemini failed: {e}")

    # Try 2: Groq (free tier: 30 RPM)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            import requests
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                },
                timeout=60
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            return text.strip()
        except Exception as e:
            print(f"    [LLM] Groq failed: {e}")

    # Try 3: Anthropic (if key available)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"    [LLM] Anthropic failed: {e}")

    return None


def extract_triples(artist_name, force=False):
    """Extract triples from Wikipedia text for an artist using LLM API.

    Uses cached extraction if available (unless force=True).
    Reads Wikipedia intro from cached text file.

    Returns:
        list of dicts with subject/predicate/object, or None if failed
    """
    safe = safe_uri(artist_name)
    extraction_path = os.path.join(TEXT_DIR, f"llm_extraction_{safe}.json")
    wiki_path = os.path.join(TEXT_DIR, f"wikipedia_{safe}.json")

    # Use cache if available
    if os.path.exists(extraction_path) and not force:
        return json.load(open(extraction_path))

    # Need Wikipedia text
    if not os.path.exists(wiki_path):
        print(f"    [LLM] {artist_name}: no Wikipedia text cached")
        return None

    wiki_data = json.load(open(wiki_path))
    intro = wiki_data.get("intro", "")
    if not intro or len(intro) < 100:
        print(f"    [LLM] {artist_name}: Wikipedia intro too short ({len(intro)} chars)")
        return None

    # Call LLM
    prompt = EXTRACTION_PROMPT.format(artist_name=artist_name, text=intro)
    print(f"    [LLM] {artist_name}: calling LLM API ({len(intro)} chars)...")
    response = _call_llm(prompt)

    if not response:
        print(f"    [LLM] {artist_name}: no API key available or all providers failed")
        return None

    # Parse JSON
    try:
        triples = json.loads(response)
        if not isinstance(triples, list):
            print(f"    [LLM] {artist_name}: response is not a JSON array")
            return None
    except json.JSONDecodeError as e:
        print(f"    [LLM] {artist_name}: failed to parse JSON: {e}")
        print(f"    [LLM] Response was: {response[:200]}...")
        return None

    # Save cache
    with open(extraction_path, "w") as f:
        json.dump(triples, f, indent=2)
    print(f"    [LLM] {artist_name}: extracted {len(triples)} triples")

    return triples


def extract_all(artists, force=False, delay=2.0):
    """Extract triples for all artists. Skips those already cached.

    Args:
        artists: list of artist names
        force: if True, re-extract even if cache exists
        delay: seconds to wait between API calls (rate limiting)
    """
    extracted = 0
    cached = 0
    failed = 0

    for artist in artists:
        safe = safe_uri(artist)
        extraction_path = os.path.join(TEXT_DIR, f"llm_extraction_{safe}.json")

        if os.path.exists(extraction_path) and not force:
            cached += 1
            continue

        result = extract_triples(artist, force=force)
        if result is not None:
            extracted += 1
            time.sleep(delay)  # Rate limiting
        else:
            failed += 1

    print(f"\n  [LLM] Extraction complete: {extracted} new, {cached} cached, {failed} failed")
    return extracted


if __name__ == "__main__":
    from config import ARTISTS
    print("LLM Triple Extraction")
    print("=" * 60)
    print(f"Artists: {len(ARTISTS)}")
    print(f"Set GEMINI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY to enable\n")
    extract_all(ARTISTS)
