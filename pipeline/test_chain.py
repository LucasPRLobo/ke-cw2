"""Test the full source fetcher chain with Miles Davis."""                                                                                                                                               
from sources.musicbrainz import fetch_artist as mb_fetch                                                                                                                                                 
from sources.discogs import fetch_artist as dc_fetch                                                                                                                                                     
from sources.wikidata import fetch_artist as wd_fetch                                                                                                                                                    
from sources.wikipedia import fetch_artist as wp_fetch                                                                                                                                                   
                                                                                                                                                                                                        
# Step 1: MusicBrainz (hub)                                                                                                                                                                              
mb = mb_fetch("Miles Davis")                              
                                                                                                                                                                                                        
# Step 2: Discogs (via MB cross-ref)
dc = dc_fetch(mb.get("discogs_id"), "Miles Davis")                                                                                                                                                       
                                                        
# Step 3: Wikidata (via MB cross-ref)   
wd = wd_fetch(mb.get("wikidata_id"), "Miles Davis")
                                                                                                                                                                                                        
# Step 4: Wikipedia (via Wikidata title)
wp = wp_fetch(wd.get("wikipedia_title"), "Miles Davis")                                                                                                                                                  
                                                        
print(f"\n=== COMBINED: Miles Davis ===")
print(f"MB:  {mb['type']}, {mb['country']}, {len(mb['tags'])} tags, {len(mb['release_groups'])} albums")
print(f"DC:  Genres: {dc['genres']}, Styles: {dc['styles']}")                                                                                                                                            
print(f"WD:  {len(wd['genres'])} genres, {len(wd['awards'])} awards, {len(wd['instruments'])} instruments")
print(f"WP:  {len(wp['intro'])} intro chars, {len(wp['sections'])} sections")                                             