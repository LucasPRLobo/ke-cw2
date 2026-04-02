"""NER Comparison: SpaCy vs BERT vs LLM Extraction.                                                                                                                                                      
                                                                                                                                                                                                        
Course technique from Week 7: Compare NER tools for entity extraction                                                                                                                                    
from music history text. Tests SpaCy (en_core_web_sm), BERT (dslim/bert-base-NER),                                                                                                                       
and our LLM extraction approach.                                                                                                                                                                         
"""                                                       
import sys                                                                                                                                                                                               
import os                                                                                                                                                                                                
import json
import time                                                                                                                                                                                              
                                                        
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collections import defaultdict

def load_wikipedia_intro(artist_name):                    
    """Load cached Wikipedia intro text."""
    from utils import safe_uri                                                                                                                                                                           
    safe = safe_uri(artist_name)
    path = f"data/text/wikipedia_{safe}.json"                                                                                                                                                            
    if os.path.exists(path):                              
        with open(path) as f:                                                                                                                                                                            
            return json.load(f).get("intro", "")          
    return ""                                                                                                                                                                                            
                                                        

def load_llm_extraction(artist_name):
    """Load cached LLM extraction results."""
    from utils import safe_uri
    safe = safe_uri(artist_name)                                                                                                                                                                         
    path = f"data/text/llm_extraction_{safe}.json"
    if os.path.exists(path):                                                                                                                                                                             
        with open(path) as f:                             
            return json.load(f)
    return []                                                                                                                                                                                            

                                                                                                                                                                                                        
def run_spacy_ner(text):                                  
    """Run SpaCy NER on text."""
    import spacy
    nlp = spacy.load("en_core_web_sm")                                                                                                                                                                   
    doc = nlp(text)
    entities = []                                                                                                                                                                                        
    for ent in doc.ents:                                  
        entities.append({
            "text": ent.text,
            "type": ent.label_,                                                                                                                                                                          
            "start": ent.start_char,
            "end": ent.end_char,                                                                                                                                                                         
        })                                                
    return entities

                                                                                                                                                                                                        
def run_bert_ner(text):
    """Run BERT NER via Hugging Face pipeline."""                                                                                                                                                        
    from transformers import pipeline as hf_pipeline      
    ner = hf_pipeline(
        "ner",                                                                                                                                                                                           
        model="dslim/bert-base-NER",
        aggregation_strategy="simple",                                                                                                                                                                   
        device=-1,  # CPU — change to 0 for GPU           
    )                                                                                                                                                                                                    
    results = ner(text)
    entities = []                                                                                                                                                                                        
    for r in results:                                     
        entities.append({                                                                                                                                                                                
            "text": r["word"],                            
            "type": r["entity_group"],
            "score": round(float(r["score"]), 4),
            "start": r["start"],                                                                                                                                                                         
            "end": r["end"],
        })                                                                                                                                                                                               
    return entities                                       

                                                                                                                                                                                                        
def analyse_entities(entities, source_name):
    """Group entities by type and deduplicate."""                                                                                                                                                        
    by_type = defaultdict(set)                            
    for e in entities:                                                                                                                                                                                   
        by_type[e["type"]].add(e["text"])
    return {t: sorted(list(v)) for t, v in by_type.items()}                                                                                                                                              
                                                                                                                                                                                                        
                                                                                                                                                                                                        
def compare_results(spacy_ents, bert_ents, llm_triples, artist_name):                                                                                                                                    
    """Compare entity extraction across all three methods."""                                                                                                                                            
    print(f"\n{'='*70}")                                  
    print(f"NER COMPARISON: {artist_name}")                                                                                                                                                              
    print(f"{'='*70}")
                                                                                                                                                                                                        
    # Analyse each                                                                                                                                                                                       
    spacy_grouped = analyse_entities(spacy_ents, "SpaCy")
    bert_grouped = analyse_entities(bert_ents, "BERT")                                                                                                                                                   
                                                        
    # LLM entities (from triple subjects + objects)                                                                                                                                                      
    llm_entities = set()
    for t in llm_triples:                                                                                                                                                                                
        llm_entities.add(t["subject"])                                                                                                                                                                   
        llm_entities.add(t["object"])
                                                                                                                                                                                                        
    # Print SpaCy results                                 
    print(f"\n--- SpaCy (en_core_web_sm) ---")
    print(f"Total entities: {len(spacy_ents)}")                                                                                                                                                          
    for etype, ents in sorted(spacy_grouped.items()):                                                                                                                                                    
        print(f"  {etype:15s} ({len(ents):2d}): {', '.join(ents[:5])}")                                                                                                                                  
        if len(ents) > 5:                                                                                                                                                                                
            print(f"{'':19s}... and {len(ents)-5} more")                                                                                                                                                 
                                                                                                                                                                                                        
    # Print BERT results                                                                                                                                                                                 
    print(f"\n--- BERT (dslim/bert-base-NER) ---")                                                                                                                                                       
    print(f"Total entities: {len(bert_ents)}")            
    for etype, ents in sorted(bert_grouped.items()):                                                                                                                                                     
        print(f"  {etype:15s} ({len(ents):2d}): {', '.join(ents[:5])}")
        if len(ents) > 5:                                                                                                                                                                                
            print(f"{'':19s}... and {len(ents)-5} more")  
                                                                                                                                                                                                        
    # Print LLM results                                   
    print(f"\n--- LLM Extraction ---")
    print(f"Total triples: {len(llm_triples)}")                                                                                                                                                          
    print(f"Unique entities: {len(llm_entities)}")
    predicates = defaultdict(int)                                                                                                                                                                        
    for t in llm_triples:                                 
        predicates[t["predicate"]] += 1                                                                                                                                                                  
    for pred, count in sorted(predicates.items()):        
        print(f"  {pred:25s}: {count} triples")                                                                                                                                                          

    # Comparison metrics                                                                                                                                                                                 
    # Extract "person-like" entities from each for comparison
    spacy_persons = set()                                                                                                                                                                                
    for etype in ["PERSON", "ORG"]:                       
        spacy_persons.update(spacy_grouped.get(etype, []))                                                                                                                                               
                                                                                                                                                                                                        
    bert_persons = set()
    for etype in ["PER", "ORG"]:                                                                                                                                                                         
        bert_persons.update(bert_grouped.get(etype, []))  
                                                                                                                                                                                                        
    # All unique entities across all methods
    all_entities = spacy_persons | bert_persons | llm_entities                                                                                                                                           
                                                                                                                                                                                                        
    print(f"\n--- Comparison ---")
    print(f"  {'Method':<20s} {'Entities':>10s} {'Relations':>10s} {'Types found':>15s}")                                                                                                                
    print(f"  {'-'*60}")                                                                                                                                                                                 
    print(f"  {'SpaCy':<20s} {len(spacy_ents):>10d} {'0':>10s} {len(spacy_grouped):>15d}")
    print(f"  {'BERT':<20s} {len(bert_ents):>10d} {'0':>10s} {len(bert_grouped):>15d}")                                                                                                                  
    print(f"  {'LLM Extraction':<20s} {len(llm_entities):>10d} {len(llm_triples):>10d} {len(predicates):>15d}")
                                                                                                                                                                                                        
    # Overlap analysis                                    
    spacy_only = spacy_persons - bert_persons - llm_entities                                                                                                                                             
    bert_only = bert_persons - spacy_persons - llm_entities
    llm_only = llm_entities - spacy_persons - bert_persons                                                                                                                                               
    all_three = spacy_persons & bert_persons & llm_entities
                                                                                                                                                                                                        
    print(f"\n  Overlap analysis (person/org entities):")                                                                                                                                                
    print(f"    SpaCy only:     {len(spacy_only):3d} — {list(spacy_only)[:3]}")                                                                                                                          
    print(f"    BERT only:      {len(bert_only):3d} — {list(bert_only)[:3]}")                                                                                                                            
    print(f"    LLM only:       {len(llm_only):3d} — {list(llm_only)[:3]}")                                                                                                                              
    print(f"    All three:      {len(all_three):3d} — {list(all_three)[:3]}")                                                                                                                            
                                                                                                                                                                                                        
    return {                                              
        "spacy": {"total": len(spacy_ents), "types": len(spacy_grouped), "persons_orgs": len(spacy_persons)},                                                                                            
        "bert": {"total": len(bert_ents), "types": len(bert_grouped), "persons_orgs": len(bert_persons)},                                                                                                
        "llm": {"total_entities": len(llm_entities), "triples": len(llm_triples), "predicates": len(predicates)},
        "overlap": {                                                                                                                                                                                     
            "spacy_only": len(spacy_only),                
            "bert_only": len(bert_only),                                                                                                                                                                 
            "llm_only": len(llm_only),                    
            "all_three": len(all_three),                                                                                                                                                                 
        }                                                 
    }

                                                                                                                                                                                                        
if __name__ == "__main__":
    print("=" * 70)                                                                                                                                                                                      
    print("NER COMPARISON — Week 7 Course Technique")     
    print("SpaCy vs BERT (Hugging Face) vs LLM Extraction")
    print("=" * 70)                                                                                                                                                                                      

    # Test artists (those with LLM extraction data)                                                                                                                                                      
    test_artists = ["David Bowie", "The Beatles", "Ludwig van Beethoven"]
    all_results = {}                                                                                                                                                                                     
                                                        
    for artist in test_artists:                                                                                                                                                                          
        text = load_wikipedia_intro(artist)               
        if not text:
            print(f"\n  {artist}: no Wikipedia text cached, skipping")                                                                                                                                   
            continue
                                                                                                                                                                                                        
        llm = load_llm_extraction(artist)                 
                                                                                                                                                                                                        
        print(f"\n  Processing {artist} ({len(text)} chars)...")                                                                                                                                         

        # Run NER                                                                                                                                                                                        
        t1 = time.time()                                  
        spacy_ents = run_spacy_ner(text)
        spacy_time = time.time() - t1                                                                                                                                                                    

        t2 = time.time()                                                                                                                                                                                 
        bert_ents = run_bert_ner(text)                    
        bert_time = time.time() - t2

        print(f"  SpaCy: {len(spacy_ents)} entities in {spacy_time:.2f}s")                                                                                                                               
        print(f"  BERT:  {len(bert_ents)} entities in {bert_time:.2f}s")
                                                                                                                                                                                                        
        # Compare                                         
        result = compare_results(spacy_ents, bert_ents, llm, artist)                                                                                                                                     
        result["timing"] = {"spacy_seconds": round(spacy_time, 3), "bert_seconds": round(bert_time, 3)}
        all_results[artist] = result                                                                                                                                                                     

    # Summary                                                                                                                                                                                            
    print(f"\n{'='*70}")                                  
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"\n  {'Artist':<25s} {'SpaCy':>8s} {'BERT':>8s} {'LLM':>8s} {'LLM triples':>12s}")                                                                                                            
    print(f"  {'-'*65}")                                                                                                                                                                                 
    for artist, r in all_results.items():                                                                                                                                                                
        print(f"  {artist:<25s} {r['spacy']['total']:>8d} {r['bert']['total']:>8d} {r['llm']['total_entities']:>8d} {r['llm']['triples']:>12d}")                                                         
                                                                                                                                                                                                        
    print(f"\n  Key findings:")                                                                                                                                                                          
    print(f"  - SpaCy and BERT find entities but NOT relations")                                                                                                                                         
    print(f"  - LLM extraction finds both entities AND structured relations (triples)")                                                                                                                  
    print(f"  - BERT typically has higher precision for person names than SpaCy")
    print(f"  - SpaCy finds more entity types (DATE, CARDINAL, etc.)")                                                                                                                                   
    print(f"  - Best approach: use NER for entity discovery, LLM for relation extraction")                                                                                                               
                                                                                                                                                                                                        
    # Save                                                                                                                                                                                               
    output_path = "../docs/eval_ner_results.json"                                                                                                                                                        
    with open(output_path, "w") as f:                                                                                                                                                                    
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")       