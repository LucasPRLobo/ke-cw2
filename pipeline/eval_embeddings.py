"""KG Embeddings & Link Prediction using PyKEEN.                                                                                                                                                         
                                                        
Course technique from Week 9: Train TransE/RotatE on our KG,                                                                                                                                             
evaluate with MRR and Hits@K, predict missing triples.
"""                                                                                                                                                                                                      
import sys                                                
import os                                                                                                                                                                                                
import json                                               

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                                                                                                                                           

from rdflib import Graph                                                                                                                                                                                 
from pykeen.triples import TriplesFactory                 
from pykeen.pipeline import pipeline
from pykeen.predict import predict_target                                                                                                                                                                
import torch
import numpy as np



def load_triples_from_ttl(ttl_path):
    """Convert our .ttl to PyKEEN-compatible triples."""                                                                                                                                                 
    g = Graph()                                                                                                                                                                                          
    g.parse(ttl_path, format="turtle")
                                                                                                                                                                                                        
    triples = []                                          
    # Filter to meaningful triples (skip labels, types, titles for cleaner embeddings)                                                                                                                   
    skip_predicates = {                                                                                                                                                                                  
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",                                                                                                                                               
        "http://xmlns.com/foaf/0.1/name",                 
        "http://purl.org/dc/elements/1.1/title",                                                                                                                                                         
        "https://schema.org/gender",                      
    }                                                                                                                                                                                                    
                                                                                                                                                                                                        
    for s, p, o in g:
        p_str = str(p)                                                                                                                                                                                   
        # Skip metadata predicates and literal objects    
        if p_str in skip_predicates:                                                                                                                                                                     
            continue
        # Only include triples where both subject and object are URIs                                                                                                                                    
        if hasattr(o, 'toPython') and isinstance(o.toPython(), str) and str(o).startswith("http"):                                                                                                       
            triples.append((str(s), p_str, str(o)))                                                                                                                                                      
                                                                                                                                                                                                        
    print(f"Extracted {len(triples)} entity-relation-entity triples from {len(g)} total triples")                                                                                                        
    return triples                                                                                                                                                                                       
                                                                                                                                                                                                        
                                                        
def create_triples_factory(triples):
    """Create PyKEEN TriplesFactory from list of (h, r, t) tuples."""
    import numpy as np                                                                                                                                                                                   
    arr = np.array(triples, dtype=str)                                                                                                                                                                   
    tf = TriplesFactory.from_labeled_triples(arr)                                                                                                                                                        
    return tf       


def train_and_evaluate(tf, model_name="TransE", epochs=50, embedding_dim=64):
    """Train a KG embedding model and evaluate."""                                                                                                                                                       
    print(f"\n{'='*60}")                                  
    print(f"Training {model_name} (dim={embedding_dim}, epochs={epochs})")                                                                                                                               
    print(f"{'='*60}")
                                                                                                                                                                                                        
    # Split into train/test                               
    training, testing = tf.split([0.8, 0.2], random_state=42)                                                                                                                                            
                                                                                                                                                                                                        
    print(f"  Training triples: {training.num_triples}")                                                                                                                                                 
    print(f"  Testing triples: {testing.num_triples}")                                                                                                                                                   
    print(f"  Entities: {tf.num_entities}")                                                                                                                                                              
    print(f"  Relations: {tf.num_relations}")             

    # Train using PyKEEN pipeline (same pattern as Week 9 lab)                                                                                                                                           
    result = pipeline(
        training=training,                                                                                                                                                                               
        testing=testing,                                  
        model=model_name,
        model_kwargs=dict(embedding_dim=embedding_dim),
        optimizer_kwargs=dict(lr=1.0e-2),                                                                                                                                                                
        training_kwargs=dict(num_epochs=epochs, use_tqdm_batch=False),                                                                                                                                   
        training_loop="sLCWA",                                                                                                                                                                           
        negative_sampler="BasicNegativeSampler",                                                                                                                                                         
        evaluator="RankBasedEvaluator",                                                                                                                                                                  
        random_seed=42,                                                                                                                                                                                  
    )                                                     
                                                                                                                                                                                                        
    # Extract metrics                                                                                                                                                                                    
    metrics = result.metric_results.to_dict()
    mrr = metrics.get("both", {}).get("realistic", {}).get("inverse_harmonic_mean_rank", 0)                                                                                                              
    hits_1 = metrics.get("both", {}).get("realistic", {}).get("hits_at_1", 0)                                                                                                                            
    hits_3 = metrics.get("both", {}).get("realistic", {}).get("hits_at_3", 0)                                                                                                                            
    hits_10 = metrics.get("both", {}).get("realistic", {}).get("hits_at_10", 0)                                                                                                                          
                                                                                                                                                                                                        
    print(f"\n  Results:")                                                                                                                                                                               
    print(f"    MRR:      {mrr:.4f}")                     
    print(f"    Hits@1:   {hits_1:.4f}")                                                                                                                                                                 
    print(f"    Hits@3:   {hits_3:.4f}")                  
    print(f"    Hits@10:  {hits_10:.4f}")                                                                                                                                                                

    return result, {                                                                                                                                                                                     
        "model": model_name,                              
        "embedding_dim": embedding_dim,                                                                                                                                                                  
        "epochs": epochs,
        "training_triples": training.num_triples,                                                                                                                                                        
        "testing_triples": testing.num_triples,           
        "entities": tf.num_entities,                                                                                                                                                                     
        "relations": tf.num_relations,
        "mrr": round(mrr, 4),                                                                                                                                                                            
        "hits_at_1": round(hits_1, 4),                    
        "hits_at_3": round(hits_3, 4),                                                                                                                                                                   
        "hits_at_10": round(hits_10, 4),
    }                                                                                                                                                                                                    
                                                        
                                                                                                                                                                                                        
def predict_missing_links(result, tf, relation, head_label=None, tail_label=None, top_k=10):
    """Predict missing links for a given relation."""                                                                                                                                                    
    model = result.model                                  
                                                                                                                                                                                                        
    print(f"\n{'='*60}")
    print(f"Link Prediction: {relation.split('/')[-1]}")                                                                                                                                                 
    print(f"{'='*60}")                                    
                                                                                                                                                                                                        
    if head_label:
        # Predict tail given head + relation                                                                                                                                                             
        print(f"  Head: {head_label}")                    
        print(f"  Relation: {relation.split('/')[-1]}")                                                                                                                                                  
        print(f"  Predicting: tail (top {top_k})")
                                                                                                                                                                                                        
        try:                                              
            predictions = predict_target(                                                                                                                                                                
                model=model,                              
                head=head_label,
                relation=relation,                                                                                                                                                                       
                triples_factory=tf,
            )                                                                                                                                                                                            
            df = predictions.df                           
            print(f"\n  Top {top_k} predicted tails:")                                                                                                                                                   
            for i, row in df.head(top_k).iterrows():
                entity = row["tail_label"]                                                                                                                                                               
                score = row["score"]                                                                                                                                                                     
                # Clean up URI for display
                display = entity.split("/")[-1].replace("%20", " ").replace("_", " ")                                                                                                                    
                print(f"    {i+1:2d}. {display:50s} (score: {score:.4f})")
            return df.head(top_k).to_dict("records")                                                                                                                                                     
        except Exception as e:                                                                                                                                                                           
            print(f"  Error: {e}")                                                                                                                                                                       
            return []                                                                                                                                                                                    
                                                                                                                                                                                                        
    elif tail_label:
        # Predict head given relation + tail                                                                                                                                                             
        print(f"  Tail: {tail_label}")                    
        print(f"  Relation: {relation.split('/')[-1]}")
        print(f"  Predicting: head (top {top_k})")
                                                                                                                                                                                                        
        try:
            predictions = predict_target(                                                                                                                                                                
                model=model,                              
                tail=tail_label,
                relation=relation,
                triples_factory=tf,
            )
            df = predictions.df                                                                                                                                                                          
            print(f"\n  Top {top_k} predicted heads:")
            for i, row in df.head(top_k).iterrows():                                                                                                                                                     
                entity = row["head_label"]                
                score = row["score"]
                display = entity.split("/")[-1].replace("%20", " ").replace("_", " ")
                print(f"    {i+1:2d}. {display:50s} (score: {score:.4f})")                                                                                                                               
            return df.head(top_k).to_dict("records")
        except Exception as e:                                                                                                                                                                           
            print(f"  Error: {e}")                        
            return []                                                                                                                                                                                    
                                                        

if __name__ == "__main__":
    print("=" * 60)
    print("KG EMBEDDINGS — Week 9 Course Technique")                                                                                                                                                     
    print("=" * 60)
                                                                                                                                                                                                        
    # Step 1: Load triples                                
    triples = load_triples_from_ttl("../ontology/music_history_kg.ttl")                                                                                                                                  
    tf = create_triples_factory(triples)                                                                                                                                                                 

    # Step 2: Train TransE (matching Week 9 lab)                                                                                                                                                         
    result_transe, metrics_transe = train_and_evaluate(   
        tf, model_name="TransE", epochs=200, embedding_dim=128                                                                                                                                             
    )                                                                                                                                                                                                    

    # Step 3: Train RotatE for comparison                                                                                                                                                                
    result_rotate, metrics_rotate = train_and_evaluate(   
        tf, model_name="RotatE", epochs=200, embedding_dim=64
    )                                                                                                                                                                                                    

    # Step 3b: Train CompGCN (GNN-based, matching Week 9 lab)
    # CompGCN requires inverse triples and uses LCWA training loop
    print(f"\n{'='*60}")
    print(f"Training CompGCN (dim=64, epochs=200)")
    print(f"{'='*60}")

    # Rebuild triples factory with inverse triples for CompGCN
    arr_gcn = np.array(triples, dtype=str)
    tf_gcn = TriplesFactory.from_labeled_triples(arr_gcn, create_inverse_triples=True)
    training_gcn, testing_gcn = tf_gcn.split([0.8, 0.2], random_state=42)

    print(f"  Training triples: {training_gcn.num_triples}")
    print(f"  Testing triples: {testing_gcn.num_triples}")
    print(f"  Entities: {tf_gcn.num_entities}")
    print(f"  Relations: {tf_gcn.num_relations} (including inverse)")

    try:
        result_gcn_pipeline = pipeline(
            training=training_gcn,
            testing=testing_gcn,
            model="CompGCN",
            model_kwargs=dict(embedding_dim=64),
            optimizer_kwargs=dict(lr=1.0e-3),
            training_kwargs=dict(num_epochs=200, use_tqdm_batch=False),
            training_loop="LCWA",
            evaluator="RankBasedEvaluator",
            random_seed=42,
        )
        gcn_metrics = result_gcn_pipeline.metric_results.to_dict()
        metrics_gcn = {
            "model": "CompGCN",
            "embedding_dim": 64,
            "epochs": 200,
            "training_triples": training_gcn.num_triples,
            "testing_triples": testing_gcn.num_triples,
            "entities": tf_gcn.num_entities,
            "relations": tf_gcn.num_relations,
            "mrr": round(gcn_metrics.get("both", {}).get("realistic", {}).get("inverse_harmonic_mean_rank", 0), 4),
            "hits_at_1": round(gcn_metrics.get("both", {}).get("realistic", {}).get("hits_at_1", 0), 4),
            "hits_at_3": round(gcn_metrics.get("both", {}).get("realistic", {}).get("hits_at_3", 0), 4),
            "hits_at_10": round(gcn_metrics.get("both", {}).get("realistic", {}).get("hits_at_10", 0), 4),
        }
        print(f"\n  Results:")
        print(f"    MRR:      {metrics_gcn['mrr']:.4f}")
        print(f"    Hits@1:   {metrics_gcn['hits_at_1']:.4f}")
        print(f"    Hits@3:   {metrics_gcn['hits_at_3']:.4f}")
        print(f"    Hits@10:  {metrics_gcn['hits_at_10']:.4f}")
    except Exception as e:
        import traceback
        print(f"  CompGCN error: {e}")
        traceback.print_exc()
        metrics_gcn = {"mrr": 0, "hits_at_1": 0, "hits_at_3": 0, "hits_at_10": 0}

    # Step 4: Link prediction — predict missing influences                                                                                                                                               
    # Who might have influenced David Bowie (beyond what's in the KG)?
    bowie_uri = "http://musicbrainz.org/artist/5441c29d-3602-4898-b1a1-b77fa23b8e50"                                                                                                                     
    influence_rel = "http://example.org/music-history/influencedBy"                                                                                                                                      
                                                                                                                                                                                                        
    predictions_influence = predict_missing_links(                                                                                                                                                       
        result_transe, tf,                                                                                                                                                                               
        relation=influence_rel,                                                                                                                                                                          
        head_label=bowie_uri,
        top_k=10                                                                                                                                                                                         
    )                                                     

    # Who might have collaborated with Quincy Jones?                                                                                                                                                     
    quincy_uri = "http://musicbrainz.org/artist/5803c81e-739a-4057-9a5c-cf84e55db630"
    collab_rel = "http://example.org/music-history/collaboratedWith"                                                                                                                                     
                                                        
    predictions_collab = predict_missing_links(                                                                                                                                                          
        result_transe, tf,                                
        relation=collab_rel,                                                                                                                                                                             
        head_label=quincy_uri,
        top_k=10                                                                                                                                                                                         
    )                                                     

    # Step 5: Model comparison summary
    print(f"\n{'='*60}")
    print("MODEL COMPARISON")
    print(f"{'='*60}")
    print(f"{'Metric':<15s} {'TransE':>10s} {'RotatE':>10s} {'CompGCN':>10s}")
    print("-" * 50)
    for metric in ["mrr", "hits_at_1", "hits_at_3", "hits_at_10"]:
        t = metrics_transe[metric]
        r = metrics_rotate[metric]
        gc = metrics_gcn.get(metric, 0)
        best = max(t, r, gc)
        print(f"  {metric:<13s} {t:>10.4f} {r:>10.4f} {gc:>10.4f}  {'T' if t == best else 'R' if r == best else 'G'}")

    # Save results
    all_results = {
        "transe": metrics_transe,
        "rotate": metrics_rotate,
        "compgcn": metrics_gcn,
        "predictions_influence": predictions_influence,
        "predictions_collab": predictions_collab,
    }                                                     

    output_path = "../docs/eval_embeddings_results.json"                                                                                                                                                 
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)                                                                                                                                                 
    print(f"\nResults saved to {output_path}")