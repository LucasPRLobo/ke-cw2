import sys                                  
import os                               
from SPARQLWrapper import SPARQLWrapper, JSON
                                                                                                                                                                                                        
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT                                                                                                                                                                            
from utils import cache_load, cache_save                                                                                                                                                                 
                                        
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"                                                                                                                                                  
                                                                                                                                                                                                        
def _query(sparql_str):                                                                                                                                                                                  
    """Run a SPARQL query against Wikidata."""            
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)                                                                                                                                                            
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)  
    sparql.setQuery(sparql_str)
    sparql.setReturnFormat(JSON)                                                                                                                                                                         
    return sparql.query().convert()

                                                                                                                                                                                                 
def fetch_artist(wikidata_id, artist_name):
    """Fetch structured facts from Wikidata via SPARQL.                                                                                                                                                  
                                                                                                                                                                                                        
    Args:
        wikidata_id: Wikidata Q-ID (e.g., "Q5383" from MusicBrainz url-rels)                                                                                                                             
        artist_name: for caching and logging              
                                        
    Returns dict with keys:
        - wikidata_id                                                                                                                                                                                    
        - genres, instruments, awards, labels, influences, occupations
        - birth_place, birth_date, death_date, country                                                                                                                                                   
        - wikipedia_title (English Wikipedia article title)
        - compositions (for classical composers)                                                                                                                                                         
    """                                                                                                                                                                                                  
    if wikidata_id is None:                                                                                                                                                                              
        print(f"  [WD] {artist_name}: no Wikidata ID")                                                                                                                                                   
        return None                                                                                                                                                                                      
                                                                                                                                                                                                        
    # Check cache                                                                                                                                                                                        
    cached = cache_load("wikidata", artist_name)          
    if cached:
        print(f"  [WD] {artist_name}: loaded from cache")                                                                                                                                                
        return cached
                                                                                                                                                                                                        
    # Batch query: fetch all properties in a single SPARQL query
    # Uses UNION to avoid cartesian products between multi-valued properties
    batch_query = f"""
    SELECT ?prop ?valueLabel WHERE {{
      VALUES ?prop {{
        wdt:P136 wdt:P1303 wdt:P166 wdt:P264
        wdt:P737 wdt:P106 wdt:P27 wdt:P19
      }}
      wd:{wikidata_id} ?prop ?value .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

    # Property ID to name mapping
    prop_map = {
        "http://www.wikidata.org/prop/direct/P136": "genres",
        "http://www.wikidata.org/prop/direct/P1303": "instruments",
        "http://www.wikidata.org/prop/direct/P166": "awards",
        "http://www.wikidata.org/prop/direct/P264": "labels",
        "http://www.wikidata.org/prop/direct/P737": "influences",
        "http://www.wikidata.org/prop/direct/P106": "occupations",
        "http://www.wikidata.org/prop/direct/P27": "country",
        "http://www.wikidata.org/prop/direct/P19": "birth_place",
    }

    from collections import defaultdict
    prop_values = defaultdict(list)

    try:
        batch_results = _query(batch_query)
        for r in batch_results["results"]["bindings"]:
            prop_uri = r["prop"]["value"]
            value = r["valueLabel"]["value"]
            if not value.startswith("Q"):
                prop_name = prop_map.get(prop_uri, prop_uri)
                prop_values[prop_name].append(value)
    except Exception:
        pass

    genres = prop_values.get("genres", [])
    instruments = prop_values.get("instruments", [])
    awards = prop_values.get("awards", [])
    labels = prop_values.get("labels", [])
    influences = prop_values.get("influences", [])
    occupations = prop_values.get("occupations", [])
    country = prop_values.get("country", [])
    birth_place = prop_values.get("birth_place", [])

    # Dates need separate query (literals, not entities)
    def _get_literal(prop_id):
        q = f"""
        SELECT ?value WHERE {{
          wd:{wikidata_id} wdt:{prop_id} ?value .
        }}
        LIMIT 1
        """
        try:
            results = _query(q)
            bindings = results["results"]["bindings"]
            if bindings:
                return bindings[0]["value"]["value"]
        except Exception:
            pass
        return None

    birth_date = _get_literal("P569")
    death_date = _get_literal("P570")

    # Query for Wikipedia title via sitelinks
    wikipedia_title = None                                                                                                                                                                               
    try:                                                  
        import requests                                                                                                                                                                                  
        wd_resp = requests.get(         
            f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json",                                                                                                                      
            headers={"User-Agent": USER_AGENT}                                                                                                                                                           
        )                               
        if wd_resp.status_code == 200:                                                                                                                                                                   
            entity = wd_resp.json()["entities"][wikidata_id]                                                                                                                                             
            sitelinks = entity.get("sitelinks", {})
            enwiki = sitelinks.get("enwiki", {})                                                                                                                                                         
            wikipedia_title = enwiki.get("title")         
    except Exception:                                                                                                                                                                                    
        pass
                                                                                                                                                                                                        
    # Query for compositions (classical composers — P86 = composer)
    comp_query = f"""                                                                                                                                                                                    
    SELECT ?workLabel ?genreLabel ?date WHERE {{          
    ?work wdt:P86 wd:{wikidata_id} .                                                                                                                                                                   
    OPTIONAL {{ ?work wdt:P136 ?genre . }}
    OPTIONAL {{ ?work wdt:P577 ?date . }}                                                                                                                                                              
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}                                                                                                                               
    }}                                      
    LIMIT 30                                                                                                                                                                                             
    """                                                   
                                                                                                                                                                                                        
    compositions = []                                     
    try:                                                                                                                                                                                                 
        comp_results = _query(comp_query)                 
        for r in comp_results["results"]["bindings"]:
            title = r["workLabel"]["value"] 
            if not title.startswith("Q"):  # Skip unresolved Q-IDs
                compositions.append({       
                    "title": title,                                                                                                                                                                      
                    "genre": r.get("genreLabel", {}).get("value"),
                    "date": r.get("date", {}).get("value", "")[:10],                                                                                                                                     
                })                                        
    except Exception:                                                                                                                                                                                    
        pass                                                                                                                                                                                             

    result = {
        "wikidata_id": wikidata_id,
        "genres": genres,
        "instruments": instruments,
        "awards": awards,
        "labels": labels,
        "influences": influences,
        "occupations": occupations,
        "country": country[0] if country else None,
        "birth_place": birth_place[0] if birth_place else None,
        "birth_date": birth_date[:10] if birth_date else None,
        "death_date": death_date[:10] if death_date else None,
        "wikipedia_title": wikipedia_title,
        "compositions": compositions,
    }                                                                                                                                                                                                    
                                                        
    cache_save("wikidata", artist_name, result)                                                                                                                                                          
    genres_n = len(result["genres"])                      
    awards_n = len(result["awards"])
    comps_n = len(result["compositions"])                                                                                                                                                                
    print(f"  [WD] {artist_name}: fetched ({wikidata_id}, {genres_n} genres, {awards_n} awards, {comps_n} compositions)")
    return result                            