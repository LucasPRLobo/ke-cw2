import musicbrainzngs                                                                                                                                                                                    
import time                                               
import sys                              
import os
                                                                                                                                                                                                        
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, MB_RATE_LIMIT                                                                                                                                                             
from utils import cache_load, cache_save                  
                                                                                                                                                                                                        
musicbrainzngs.set_useragent(*USER_AGENT.split("/", 1)[0:1], "0.1", "test@example.com")

def fetch_artist(artist_name):                                                                                                                                                                           
    """Fetch full artist data from MusicBrainz.                                                                                                                                                          
                                                                                                                                                                                                        
    Returns dict with keys:                               
        - mbid, name, type, country, gender, life_span, begin_area
        - tags: list of {name, count}                                                                                                                                                                    
        - artist_rels: list of {type, direction, target_name, target_mbid, attributes, begin, end}
        - url_rels: list of {type, target} — includes Discogs, Wikidata links                                                                                                                            
        - release_groups: list of {id, title, type, first_release_date}                                                                                                                                  
    """                                                                                                                                                                                                  
    # Check cache                                                                                                                                                                                        
    cached = cache_load("musicbrainz", artist_name)                                                                                                                                                      
    if cached:                                                                                                                                                                                           
        print(f"  [MB] {artist_name}: loaded from cache") 
        return cached                                                                                                                                                                                    
                                                        
    # Search for artist                                                                                                                                                                                  
    time.sleep(MB_RATE_LIMIT)                                                                                                                                                                            
    search = musicbrainzngs.search_artists(artist=artist_name, limit=1)
    if not search["artist-list"]:                                                                                                                                                                        
        print(f"  [MB] {artist_name}: NOT FOUND")         
        return None                                                                                                                                                                                      
                                            
    mbid = search["artist-list"][0]["id"]                                                                                                                                                                
                                                        
    # Fetch full detail                                                                                                                                                                                  
    time.sleep(MB_RATE_LIMIT)                             
    detail = musicbrainzngs.get_artist_by_id(                                                                                                                                                            
        mbid, includes=["tags", "url-rels", "artist-rels"]
    )["artist"]                             
                                        
    # Fetch release groups (deduplicated albums)                                                                                                                                                         
    time.sleep(MB_RATE_LIMIT)                                                                                                                                                                            
    rg_result = musicbrainzngs.browse_release_groups(                                                                                                                                                    
        artist=mbid, release_type=["album"], limit=25                                                                                                                                                    
    )                                                     
                                        
    # Build clean result dict                                                                                                                                                                            
    life_span = detail.get("life-span", {})                                                                                                                                                              
    result = {                                                                                                                                                                                           
        "mbid": mbid,                                                                                                                                                                                    
        "name": detail["name"],                           
        "type": detail.get("type", "Unknown"),                                                                                                                                                           
        "country": detail.get("country"),
        "gender": detail.get("gender"),                                                                                                                                                                  
        "life_span": {                                    
            "begin": life_span.get("begin"),
            "end": life_span.get("end"),                                                                                                                                                                 
            "ended": life_span.get("ended", "false"),
        },                                                                                                                                                                                               
        "area": detail.get("area", {}).get("name"),       
        "begin_area": detail.get("begin-area", {}).get("name"),
        "tags": [                                                                                                                                                                                        
            {"name": t["name"], "count": t.get("count", 0)}
            for t in detail.get("tag-list", [])                                                                                                                                                          
        ],                                                
        "artist_rels": [                                                                                                                                                                                 
            {                                                                                                                                                                                            
                "type": r.get("type"),
                "direction": r.get("direction"),                                                                                                                                                         
                "target_name": r.get("artist", {}).get("name"),
                "target_mbid": r.get("artist", {}).get("id"),
                "attributes": r.get("attribute-list", []),
                "begin": r.get("begin"),                                                                                                                                                                 
                "end": r.get("end"),
            }                                                                                                                                                                                            
            for r in detail.get("artist-relation-list", [])
        ],                                                                                                                                                                                               
        "url_rels": [                                     
            {"type": r["type"], "target": r["target"]}
            for r in detail.get("url-relation-list", [])                                                                                                                                                 
        ],                                  
        "release_groups": [                                                                                                                                                                              
            {                                             
                "id": rg["id"],                                                                                                                                                                          
                "title": rg["title"],
                "type": rg.get("type"),                                                                                                                                                                  
                "first_release_date": rg.get("first-release-date"),
            }                               
            for rg in rg_result.get("release-group-list", [])
        ],
    }                                                                                                                                                                                                    

    # Extract cross-reference IDs for other sources                                                                                                                                                      
    for url_rel in result["url_rels"]:                    
        if url_rel["type"] == "discogs":    
            try:                                                                                                                                                                                         
                result["discogs_id"] = int(url_rel["target"].rstrip("/").split("/")[-1])
            except ValueError:                                                                                                                                                                           
                pass                                      
        elif url_rel["type"] == "wikidata":                                                                                                                                                              
            result["wikidata_id"] = url_rel["target"].rstrip("/").split("/")[-1]                                                                                                                         
                                            
    # Cache and return                                                                                                                                                                                   
    cache_save("musicbrainz", artist_name, result)        
    print(f"  [MB] {artist_name}: fetched ({mbid})")                                                                                                                                                     
    return result                           
                                    