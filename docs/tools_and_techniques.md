# Tools and Techniques Reference

A reference of all techniques, tools, and libraries covered in the course (Weeks 7–11) and how they apply to each phase of our CW2 project.

---

## 1. Text-to-KG Pipeline (Week 7)

### NLP Foundations
- **Text pre-processing**: tokenization, lowercasing, stopword removal, stemming/lemmatization, punctuation removal
- **NLP task types**: sequence classification, sequence labelling (NER, PoS tagging), sequence-to-sequence (translation, summarisation)

### Named Entity Recognition (NER)

Four tools compared in class, in order of capability:

| Tool | Strengths | Weaknesses | Labels |
|---|---|---|---|
| **NLTK** | Simple, educational | Fragments multi-word entities, limited labels | GPE, ORGANIZATION, PERSON |
| **SpaCy** | Industrial-strength, multi-word spans, dates/money | Less semantic richness than LLMs | ORG, GPE, PERSON, DATE, CARDINAL, MONEY |
| **BERT** (Hugging Face `pipeline("ner")`) | High accuracy, confidence scores, BIO tagging | Subword tokenization needs `aggregation_strategy="simple"` | B-ORG, I-ORG, B-LOC, B-PER, etc. |
| **ChatGPT/LLM prompting** | Richest semantic types, flexible, zero-shot | Non-deterministic, prompt-dependent | Any user-defined types |

### Classic NLP-to-KG Pipeline (step-by-step)
1. **Pre-processing** — tokenization, PoS tagging, dependency parsing, word sense disambiguation
2. **Named Entity Recognition** — extract entities (people, places, organisations, dates)
3. **Entity Linking** — resolve surface forms to canonical KG identifiers (e.g., "Rapa Nui" → Easter Island)
4. **Relation Extraction** — extract binary triples (subject → predicate → object) and n-ary relations

### LLM-Based KG Construction (chained prompting)
An alternative to the classic pipeline — use LLMs for all steps via sequential prompts:
1. **Coreference Resolution** — "If 'John Doe' is mentioned and later referred to as 'he,' always use 'John Doe'"
2. **NER** — "Extract all people, places, and organizations. Label 'Steve Jobs' as 'Person' and 'Apple' as 'Company'"
3. **Entity Disambiguation** — "Ensure that 'Paris, France' and 'Paris, Texas' are treated as separate entities"
4. **Relation Extraction** — "Extract relationships like 'Steve Jobs co-founded Apple' and label it as 'co-founder'"

### Key References
- **COMET** (Bosselut et al., 2019) — commonsense KG construction via transformers
- **BertNet** (Hao et al., 2022) — automatic KG construction using weighted prompt sets
- **LLMKE** (Zhang et al., 2023, KCL) — LLM-based KG engineering on Wikidata, F1=0.701
- **Semi-automatic KG construction** (Kommineni et al., 2024) — 6-stage LLM pipeline with human checkpoints

### Applies to CW2
- **Phase 4 (Mappings)**: extract triples from Wikipedia articles using SpaCy/BERT NER + LLM relation extraction
- **Phase 7 (Evaluation)**: precision/recall/F1 for entity and relation extraction quality

### Libraries
```
spacy, transformers (hugging face), nltk, scikit-learn, gensim, snorkel
```

---

## 2. Database-to-KG Pipeline (Week 8)

### Mapping Languages

| Language | Standard | Input Sources | Key Feature |
|---|---|---|---|
| **R2RML** | W3C Recommendation (2012) | Relational databases (SQL) | Declarative triple maps from tables to RDF |
| **RML** | Community (rml.io) | Any structured format (JSON, CSV, XML, SQL) | Extends R2RML to non-relational sources |
| **SPARQL Anything** | Research tool (Asprino et al., 2023) | JSON, CSV, XML, HTML, XLSX, etc. | Overloads SPARQL SERVICE to query any file directly |

### R2RML Core Pattern
```turtle
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix ex: <http://example.org/> .

<#TriplesMap> rr:logicalTable [
    rr:tableName "TableName"
] ;
rr:subjectMap [
    rr:template "http://example.org/{PrimaryKey}" ;
    rr:class ex:ClassName
] ;
rr:predicateObjectMap [
    rr:predicate ex:propertyName ;
    rr:objectMap [ rr:column "ColumnName" ]
] .
```

Key constructs:
- `rr:logicalTable` / `rr:tableName` — source table
- `rr:subjectMap` with `rr:template` — URI generation from row values using `{Column}` placeholders
- `rr:class` — assign RDF class
- `rr:predicateObjectMap` — map columns to RDF properties
- `rr:parentTriplesMap` + `rr:joinCondition` — cross-table joins (foreign key → RDF link)

### SPARQL Anything Pattern
```sparql
PREFIX fx: <http://sparql.xyz/facade-x/ns/>

CONSTRUCT {
    ?entity a <http://example.org/Class> ;
            <http://example.org/property> ?value .
}
WHERE {
    SERVICE <x-sparql-anything:location=data.json> {
        ?entity fx:properties ?props .
        ?props fx:propertyName "fieldName" ;
               fx:propertyValue ?value .
    }
}
```

Run via: `java -jar sparql-anything.jar --query=query.sparql --output=output.ttl`

### Facade-X Data Model
SPARQL Anything represents any source as RDF using a minimal model:
- Root node typed `fx:root`
- Nested content via `rdf:_1`, `rdf:_2`, etc. (positional properties)
- Works uniformly across JSON, CSV, XML, XLSX

### Key Concepts
- **5-Star Linked Data** (Berners-Lee): OL → RE → OF → URI → LOD
- **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
- **Materialisation vs Virtual KGs (OBDA)**: generate-and-store RDF vs query-rewrite at runtime
- **Primary keys → URIs, Foreign keys → RDF object properties**

### Applies to CW2
- **Phase 4 (Mappings)**: map MusicBrainz/Discogs JSON to RDF triples
- Options: SPARQL Anything on saved JSON files, or rdflib in Python with R2RML-style logic
- **Phase 7 (Evaluation)**: benchmark performance of mapping pipeline

### Libraries/Tools
```
SPARQL Anything (Java jar), Apache Jena ARQ, rdflib (Python), R2RML processors
```

---

## 3. KG Embeddings (Week 9)

### Embedding Models

| Model | Type | Space | Scoring | Handles N-to-M? |
|---|---|---|---|---|
| **TransE** | Translational distance | Euclidean | `\|\|h + r - t\|\|` | No |
| **TransH** | Translational (hyperplane) | Euclidean | Project to relation hyperplane, then translate | Yes |
| **TransR** | Translational (relation space) | Euclidean | `\|\|hM_r + r - tM_r\|\|` | Yes |
| **RotatE** | Rotation | Complex | `h * r = t` (Hadamard in complex space) | Yes |
| **RESCAL** | Semantic matching | Euclidean | `h^T * W_r * t` | Yes |
| **ConvE** | DNN (CNN) | Euclidean | Stack h,r → CNN → score vs t | Yes |
| **R-GCN** | GNN | Euclidean | Multi-relational message passing | Yes |
| **RDF2Vec** | Random walks + Word2Vec | Euclidean | Walk sequences → Skip-gram/CBOW | N/A |

### Training Concepts
- **Negative sampling**: corrupt true triples by replacing head or tail with random entities
- **LCWA vs sLCWA**: all corruptions vs sampled corruptions
- **Loss functions**: pointwise (BCE, softplus), pairwise (hinge, logistic), setwise (cross-entropy)

### PyKEEN Pipeline (from Week 9 lab)
```python
from pykeen.datasets import CoDExMedium
from pykeen.pipeline import pipeline

result = pipeline(
    dataset=dataset,
    model='TransE',
    model_kwargs=dict(embedding_dim=50),
    optimizer_kwargs=dict(lr=1.0e-2),
    training_kwargs=dict(num_epochs=20),
    training_loop='sLCWA',
    negative_sampler='BasicNegativeSampler',
    evaluator='RankBasedEvaluator'
)
mrr = result.get_metric('mrr')
hits_at_10 = result.get_metric('hits@k')
```

### Evaluation Metrics
- **MRR** (Mean Reciprocal Rank) — average of 1/rank for correct predictions
- **Hits@K** (K=1, 3, 10) — percentage of correct entities in top K predictions

### Embedding Visualisation
```python
from torch.utils.tensorboard import SummaryWriter

entity_embeddings = model.entity_representations[0]().detach().cpu()
writer = SummaryWriter("embeddings")
writer.add_embedding(entity_embeddings, tag='Entities', metadata=entity_labels)
```

### Applies to CW2
- **Phase 6 (KG Completion)**: train embeddings on your KG, use link prediction to find missing triples
- **Phase 7 (Evaluation)**: MRR and Hits@K as quantitative quality metrics

### Libraries
```
pykeen, torch, tensorboard, tensorflow (visualisation), pyrdf2vec
```

---

## 4. KG Completion (Week 10)

### Completeness Metrics (Zaveri et al., 2015)

| Metric | What it measures | Formula intuition |
|---|---|---|
| **CM1 — Schema completeness** | Classes/properties represented vs total in ontology | Are all ontology concepts populated? |
| **CM2 — Property completeness** | Values present for a property vs expected total | Are entity properties filled in? |
| **CM3 — Population completeness** | Real-world objects represented vs total that exist | Are all real-world entities in the KG? |
| **CM4 — Interlinking completeness** | Instances interlinked vs total instances | Are entities connected to external KGs? |

### Completion Techniques

**Statistical methods:**
- Outlier detection (histograms, scatter plots)
- Averaging (replace missing values with mean)
- Imputation (sophisticated missing value replacement)

**ML-based:**
- KG embeddings + link prediction (TransE, RotatE — see Week 9)
- **OntoZSL** (Geng et al., WWW 2021) — zero-shot learning using ontological schema (rdfs:subClassOf, rdfs:domain, rdfs:range) to infer unseen relations
- **RMPI** (Geng et al., ICDE 2023) — fully inductive completion using GNN relational message passing, handles unseen entities AND relations

**LLM-based:**
- Treat LLMs as implicit knowledge bases (Petroni et al., 2019)
- Three prompting strategies: question prompting, triple completion prompting, retrieval-augmented context
- GPT-4 with improved disambiguation + context achieves F1=0.665 on Wikidata (Zhang et al., 2023)

### Knowledge Gaps Framework
- **Knowledge equity**: biases in what is included/excluded in KGs
- **Gap dimensions**: demographic, geographic, linguistic, temporal
- **Content gaps vs user needs**: contribution metrics, ROI ratios (pageviews per contribution)

### Applies to CW2
- **Phase 6 (KG Completion)**: use CM1-CM4 to identify 5 ontology gaps + 5 instance gaps; use link prediction or LLM prompting to resolve them
- **Phase 7 (Evaluation)**: CM1-CM4 as quantitative completeness metrics

---

## 5. RAG — Retrieval Augmented Generation (Week 11)

### RAG Architecture (5-step pipeline)
1. User submits a query
2. Retrieval engine searches external resources
3. Results returned
4. Augmented prompt = original query + retrieved context
5. LLM generates the response

### Two Ways to Combine RAG with Knowledge Graphs

**Option 1: KG as SPARQL-based retrieval source**
- Run SPARQL queries against your KG
- Verbalise returned triples into natural language
- Inject into LLM prompt as context
- LLM generates answer

**Option 2: KG as vector-embedded retrieval source**
- Encode entire KG as embeddings
- Encode query as text embeddings
- Retrieve nearest KG facts via vector similarity
- Feed to LLM reader

### KG-Enriched Prompt Engineering (Brate et al., 2022)
Example:
- **Non-enriched**: "Die Hard is of the genre \<mask\>."
- **Pipeline**: entity recognition → entity linking (→ wd:Q105598) → retrieve KG properties (title, director, cast)
- **Enriched**: "Die Hard is a movie, starring Bruce Willis, directed by John McTiernan, is of the genre \<mask\>."
- **Result**: "action"

### QALD (Question Answering over Linked Data)
- Natural language questions → SPARQL queries → RDF results
- Dataset: Wikidata (multilingual: EN, DE, RU, ZH)
- Format: JSON with question text, SPARQL query, and result bindings

### Applies to CW2
- **Phase 6 (KG Completion)**: use RAG to resolve identified gaps — query KG via SPARQL, verbalise triples, prompt LLM to fill missing information
- **Phase 7 (Evaluation)**: compare KG+RAG answers vs plain LLM answers to CQs

---

## 6. Evaluation Framework (across all weeks)

### Metrics by Type

| Metric | Source | What it measures | Use in CW2 |
|---|---|---|---|
| Precision / Recall / F1 | W7 | NER and relation extraction accuracy | Text pipeline quality |
| MRR | W9 | Mean reciprocal rank of correct link predictions | Embedding quality |
| Hits@K | W9 | % correct entities in top K predictions | Embedding quality |
| CM1 (Schema completeness) | W10 | Ontology coverage | Gap analysis |
| CM2 (Property completeness) | W10 | Property fill rate | Gap analysis |
| CM3 (Population completeness) | W10 | Entity coverage vs real world | Gap analysis |
| CM4 (Interlinking completeness) | W10 | Cross-KG links | Gap analysis |
| Graph connectivity | W7 | Path length, degree distribution, clustering | KG structure quality |
| Task-based (CQ answering) | W7, W11 | How well KG answers competency questions | Overall KG quality |
| KG vs LLM comparison | W11 | KG+RAG answers vs plain LLM answers | Quality justification |

### Performance Metrics
- Pipeline execution time
- Memory usage
- API call counts and rate limiting impact

### Benchmarks Referenced in Course
- Berlin SPARQL Benchmark (BSBM)
- Lehigh University Benchmark (LUBM)
- SP2Bench
- DBpedia SPARQL Benchmark
- CoDExMedium (PyKEEN)
- LM-KBC Challenge (ISWC)
- HELM (Holistic Evaluation of Language Models)

---

## 7. Libraries and Tools Summary

### Python Libraries
| Library | Purpose | Install |
|---|---|---|
| `rdflib` | RDF graph creation, Turtle serialisation, SPARQL queries | `pip install rdflib` |
| `spacy` | NER, PoS tagging, dependency parsing | `pip install spacy` |
| `transformers` | BERT/RoBERTa NER pipeline | `pip install transformers` |
| `pykeen` | KG embedding training and evaluation | `pip install pykeen` |
| `musicbrainzngs` | MusicBrainz API client | `pip install musicbrainzngs` |
| `python-discogs-client` | Discogs API client | `pip install python-discogs-client` |
| `SPARQLWrapper` | SPARQL endpoint querying (Wikidata) | `pip install SPARQLWrapper` |
| `beautifulsoup4` | HTML parsing | `pip install beautifulsoup4` |
| `requests` | HTTP API calls | `pip install requests` |
| `nltk` | Basic NLP (tokenization, stemming) | `pip install nltk` |
| `pyrdf2vec` | RDF2Vec embeddings | `pip install pyrdf2vec` |
| `torch` | PyTorch (backend for pykeen, transformers) | `pip install torch` |

### External Tools
| Tool | Purpose | How to use |
|---|---|---|
| **SPARQL Anything** | Map JSON/CSV/XML to RDF via SPARQL CONSTRUCT | `java -jar sparql-anything.jar --query=q.sparql --output=out.ttl` |
| **Protege** | Ontology editor and viewer | Desktop application |
| **GraphDB** | RDF triple store + SPARQL endpoint | Desktop/server application |
| **TensorBoard** | Embedding visualisation | `tensorboard --logdir embeddings` |

### APIs
| API | Base URL | Auth | Rate limit |
|---|---|---|---|
| **MusicBrainz** | `https://musicbrainz.org/ws/2/` | None (User-Agent required) | 1 req/sec |
| **Discogs** | `https://api.discogs.com/` | Personal access token | 60 req/min |
| **Wikipedia** | `https://en.wikipedia.org/w/api.php` | None | ~200 req/sec |
| **Wikidata SPARQL** | `https://query.wikidata.org/sparql` | None | Soft limits, 60s timeout |
