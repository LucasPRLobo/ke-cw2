import requests
import time                                                                                                                                                                                              
import sys                              
import os                                                                                                                                                                                                
                                                                                                                                                                                                        
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, DISCOGS_RATE_LIMIT                                                                                                                                                        
from utils import cache_load, cache_save                  
                                                                                                                                                                                                        
DISCOGS_BASE = "https://api.discogs.com"
HEADERS = {"User-Agent": USER_AGENT}        


                                                                                                                                                                                                        
def _discogs_get(endpoint, params=None):                  
    """Make a Discogs API request with rate limiting."""                                                                                                                                                 
    url = f"{DISCOGS_BASE}{endpoint}"       
    resp = requests.get(url, headers=HEADERS, params=params)                                                                                                                                             
    if resp.status_code == 429:                           
        print("  [DC] Rate limited, waiting 60s...")                                                                                                                                                     
        time.sleep(60)                      
        resp = requests.get(url, headers=HEADERS, params=params)                                                                                                                                         
    resp.raise_for_status()                               
    return resp.json()                                                                                                                                                                                   
                                                        
                                                                                                                                                                                                        
def fetch_artist(discogs_id, artist_name):                
    """Fetch artist data from Discogs.
                                                                                                                                                                                                        
    Args:
        discogs_id: numeric Discogs artist ID (from MusicBrainz url-rels)                                                                                                                                
        artist_name: for caching and logging              
                                            
    Returns dict with keys:             
        - id, name, realname, profile                                                                                                                                                                    
        - members: list of {name, id, active}                                                                                                                                                            
        - groups: list of {name, id, active}                                                                                                                                                             
        - genres: set of broad genres across releases                                                                                                                                                    
        - styles: set of sub-genres across releases                                                                                                                                                      
        - genre_style_pairs: list of {genre, style} for subgenreOf mapping                                                                                                                               
    """                                                                                                                                                                                                  
    if discogs_id is None:                                                                                                                                                                               
        print(f"  [DC] {artist_name}: no Discogs ID")     
        return None                                                                                                                                                                                      
                                                                                                                                                                                                        
    # Check cache                                                                                                                                                                                        
    cached = cache_load("discogs", artist_name)                                                                                                                                                          
    if cached:                                            
        print(f"  [DC] {artist_name}: loaded from cache")                                                                                                                                                
        return cached
                                                                                                                                                                                                        
    # Fetch artist profile
    time.sleep(DISCOGS_RATE_LIMIT)
    try:
        artist = _discogs_get(f"/artists/{discogs_id}")
    except Exception as e:
        print(f"  [DC] {artist_name}: failed to fetch artist ({e})")
        return None

    # Fetch releases for genre/style data
    time.sleep(DISCOGS_RATE_LIMIT)
    try:
        releases = _discogs_get(f"/artists/{discogs_id}/releases", params={"per_page": 10})
    except Exception as e:
        print(f"  [DC] {artist_name}: failed to fetch releases ({e})")
        releases = {"releases": []}
                                                                                                                                                                                                        
    # Collect genres and styles from releases             
    all_genres = set()                                                                                                                                                                                   
    all_styles = set()                                                                                                                                                                                   
    genre_style_pairs = []              
                                                                                                                                                                                                        
    for rel in releases.get("releases", [])[:5]:                                                                                                                                                         
        rel_id = rel["id"]
        rel_type = rel.get("type", "release")                                                                                                                                                            
        time.sleep(DISCOGS_RATE_LIMIT)                    
                                            
        try:                                                                                                                                                                                             
            if rel_type == "master":
                detail = _discogs_get(f"/masters/{rel_id}")                                                                                                                                              
            else:                                         
                detail = _discogs_get(f"/releases/{rel_id}")                                                                                                                                             
                                                        
            genres = detail.get("genres", [])
            styles = detail.get("styles", [])                                                                                                                                                            
            all_genres.update(genres)
            all_styles.update(styles)                                                                                                                                                                    
                                                        
            for g in genres:
                for s in styles:                                                                                                                                                                         
                    genre_style_pairs.append({"genre": g, "style": s})
        except Exception as e:                                                                                                                                                                           
            print(f"  [DC] Error fetching release {rel_id}: {e}")

    result = {                                                                                                                                                                                           
        "id": discogs_id,
        "name": artist.get("name"),                                                                                                                                                                      
        "realname": artist.get("realname"),               
        "profile": artist.get("profile", ""),
        "members": [
            {"name": m["name"], "id": m["id"], "active": m.get("active")}                                                                                                                                
            for m in artist.get("members", [])
        ],                                                                                                                                                                                               
        "groups": [                                       
            {"name": g["name"], "id": g["id"], "active": g.get("active")}                                                                                                                                
            for g in artist.get("groups", [])
        ],                                                                                                                                                                                               
        "genres": sorted(all_genres),                     
        "styles": sorted(all_styles),                                                                                                                                                                    
        "genre_style_pairs": genre_style_pairs,
    }                                                                                                                                                                                                    
                                                        
    cache_save("discogs", artist_name, result)
    print(f"  [DC] {artist_name}: fetched (ID: {discogs_id}, {len(all_genres)} genres, {len(all_styles)} styles)")                                                                                       
    return result                           
                                               