# Music History & Heritage Knowledge Graph

**Knowledge Engineering CW2** — King's College London, April 2026

An automated knowledge graph construction system for the Music History domain, covering 58 primary artists from medieval (Hildegard von Bingen, ~1150) to modern (BTS, Kendrick Lamar, 2020s).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Build the KG (uses cached data, ~35 seconds)
cd pipeline && python build_kg.py

# Run all 20 SPARQL queries
cd queries && python run_all_queries.py
```

To enable LLM text extraction for new artists:
```bash
cp .env.example .env
# Add your API key (Gemini, Groq, or Anthropic)
```

## Submission Deliverables

| Deliverable | Location |
|---|---|
| **TTL file** (42,554 triples) | `ontology/music_history_kg.ttl` |
| **Meeting minutes** (3 meetings) | `docs/minutes/` |
| **Report** | `docs/report.tex` |
| **Completion analysis** | `docs/completion_analysis.tex` |
| **Prompts log** (43 prompts) | `docs/prompts_log.tex` |

## Repository Structure

```
ontology/
  music_history_kg.ttl          # Final KG (42,554 triples)

pipeline/
  build_kg.py                   # Main pipeline orchestrator (15 steps)
  config.py                     # Artist list, blacklists, overrides
  ontology_header.py            # OWL declarations + extensions
  llm_extraction.py             # Automated LLM text extraction (Gemini API)
  ingest_rag_results.py         # RAG completion ingestion
  utils.py                      # Genre/instrument normalisation
  sources/                      # Data source fetchers
    musicbrainz.py              #   MusicBrainz API (primary hub)
    discogs.py                  #   Discogs API (genre hierarchy)
    wikidata.py                 #   Wikidata SPARQL (awards, instruments, labels)
    wikipedia.py                #   Wikipedia MediaWiki API (narrative text)
  mapping/
    structured.py               # JSON → RDF mapping + validation (22 rules)
    text.py                     # LLM extraction → RDF with entity linking
    r2rml_musicbrainz.ttl       # R2RML mapping document (Week 8)
  sparql_anything/              # SPARQL Anything CONSTRUCT queries (Week 8)
  eval_*.py                     # 5 evaluation scripts
  notebooks/                    # 7 experiment notebooks
  data/                         # Cached API responses + LLM extractions

queries/
  cq01.rq — cq20.rq            # 20 SPARQL queries (one per CQ)
  run_all_queries.py            # Query runner (20/20 pass)
  test_all_queries.py           # Comprehensive test suite

docs/
  report.tex                    # KG report (LaTeX)
  completion_analysis.tex       # Completion analysis (LaTeX)
  prompts_log.tex               # Prompts log (LaTeX)
  kg_reference_guide.md         # KG reference for query writing
  minutes/                      # 3 meeting minutes
  rag_responses/                # 10 RAG completion JSON files
  eval_*_results.json           # Evaluation results
```

## Key Statistics

- **42,554 triples** across 1,332 artist entities
- **4 data sources**: MusicBrainz, Discogs, Wikidata, Wikipedia
- **58 primary artists** spanning 20+ genres, 20+ countries, medieval to modern
- **897 text-extracted triples** via automated LLM API (Google Gemini)
- **20/20 SPARQL queries** pass against the KG
- **22 structural validation rules** (zero hardcoded fixes)
- **21 OWL2 property features**: symmetric, transitive, irreflexive, asymmetric, inverse, disjoint
- **4 defined/asserted classes**: AwardWinningArtist (52), CollaboratingArtist (118), ProducerArtist (10), InternationalCollaborator (11)

## Team

| Role | Members |
|---|---|
| Domain expert | Sofia Davis, Davyd Shtepa |
| Modelling experts | William Caulton, Mert Yerlikaya |
| Requirements & pipeline | Lucas Perez Reis Lobo, Yutaka Shibata |
