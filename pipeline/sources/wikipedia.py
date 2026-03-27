import requests                             
import sys                                                                                                                                                                                               
import os
                                                                                                                                                                                                        
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT                                                                                                                                                                            
from utils import cache_load, cache_save                  
                                                                                                                                                                                                        
WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": USER_AGENT}                                                                                                                                                                     
                                                                                                                                                                                                        
                                        
def _wiki_get(params):                                                                                                                                                                                   
    """Make a Wikipedia API request."""                                                                                                                                                                  
    params["format"] = "json"               
    resp = requests.get(WIKI_API, params=params, headers=HEADERS)                                                                                                                                        
    resp.raise_for_status()                               
    return resp.json()                                                                                                                                                                                   

                                                                                                                                                                                                        
def fetch_artist(wikipedia_title, artist_name):           
    """Fetch Wikipedia article text and categories.
                                                                                                                                                                                                        
    Args:                               
        wikipedia_title: exact Wikipedia article title (from Wikidata sitelinks)                                                                                                                         
        artist_name: for caching and logging                                                                                                                                                             
                                        
    Returns dict with keys:                                                                                                                                                                              
        - title, page_id                                                                                                                                                                                 
        - intro: first section text (plain text)
        - full_text: complete article text (plain text)                                                                                                                                                  
        - sections: list of {name, level, index}          
        - categories: list of category names                                                                                                                                                             
    """                                                                                                                                                                                                  
    if wikipedia_title is None:
        print(f"  [WP] {artist_name}: no Wikipedia title")                                                                                                                                               
        return None                                       
                                                                                                                                                                                                        
    # Check cache                                                                                                                                                                                        
    cached = cache_load("wikipedia", artist_name, subdir="text")
    if cached:                                                                                                                                                                                           
        print(f"  [WP] {artist_name}: loaded from cache") 
        return cached                                                                                                                                                                                    
                                                                                                                                                                                                        
    # Fetch intro text
    intro_result = _wiki_get({                                                                                                                                                                           
        "action": "query",                                
        "titles": wikipedia_title,      
        "prop": "extracts",
        "explaintext": True,                                                                                                                                                                             
        "exintro": True,
        "exlimit": 1,                                                                                                                                                                                    
    })                                                    
    intro_page = list(intro_result["query"]["pages"].values())[0]
    intro_text = intro_page.get("extract", "")                                                                                                                                                           
                                        
    # Fetch full text                                                                                                                                                                                    
    full_result = _wiki_get({                                                                                                                                                                            
        "action": "query",
        "titles": wikipedia_title,                                                                                                                                                                       
        "prop": "extracts",                               
        "explaintext": True,            
        "exlimit": 1,
    })                                                                                                                                                                                                   
    full_page = list(full_result["query"]["pages"].values())[0]
    full_text = full_page.get("extract", "")                                                                                                                                                             
                                                        
    # Fetch sections                    
    sections = []
    try:                                                                                                                                                                                                 
        sections_result = _wiki_get({
            "action": "parse",                                                                                                                                                                           
            "page": wikipedia_title,                      
            "prop": "sections",         
        })
        for s in sections_result["parse"]["sections"]:                                                                                                                                                   
            sections.append({
                "name": s["line"],                                                                                                                                                                       
                "level": int(s["toclevel"]),              
                "index": s["index"],        
            })                          
    except Exception:
        pass                                                                                                                                                                                             

    # Fetch categories                                                                                                                                                                                   
    cat_result = _wiki_get({                              
        "action": "query",                  
        "titles": wikipedia_title,      
        "prop": "categories",
        "cllimit": 50,                                                                                                                                                                                   
    })
    cat_page = list(cat_result["query"]["pages"].values())[0]                                                                                                                                            
    categories = [                                        
        c["title"].replace("Category:", "")
        for c in cat_page.get("categories", [])
    ]                                                                                                                                                                                                    

    result = {                                                                                                                                                                                           
        "title": intro_page.get("title", wikipedia_title),
        "page_id": intro_page.get("pageid"),                                                                                                                                                             
        "intro": intro_text,                              
        "full_text": full_text,
        "sections": sections,                                                                                                                                                                            
        "categories": categories,
    }                                                                                                                                                                                                    
                                                        
    cache_save("wikipedia", artist_name, result, subdir="text")
    print(f"  [WP] {artist_name}: fetched ('{wikipedia_title}', {len(intro_text)} intro chars, {len(full_text)} full chars, {len(sections)} sections)")
    return result                     