"""Test structured mapping for David Bowie."""
from sources.musicbrainz import fetch_artist as mb_fetch                                                                                                                                                 
from sources.discogs import fetch_artist as dc_fetch                                                                                                                                                     
from sources.wikidata import fetch_artist as wd_fetch                                                                                                                                                    
from mapping.structured import create_graph, map_artist                                                                                                                                                  
                                                                                                                                                                                                        
# Fetch data (will use cache if available)                                                                                                                                                               
mb = mb_fetch("David Bowie")                                                                                                                                                                             
dc = dc_fetch(mb.get("discogs_id"), "David Bowie")                                                                                                                                                       
wd = wd_fetch(mb.get("wikidata_id"), "David Bowie")                                                                                                                                                      

# Map to RDF                                                                                                                                                                                             
g = create_graph()
map_artist(g, mb, dc, wd)                                                                                                                                                                                
                
print(f"\nTriples generated: {len(g)}")                                                                                                                                                                  

# Save                                                                                                                                                                                                   
output = "../ontology/test_mapping.ttl"
g.serialize(destination=output, format="turtle")                                                                                                                                                         
print(f"Saved to {output}")
                                                                                                                                                                                                        
# Quick SPARQL tests                                                                                                                                                                                     
print("\n--- SPARQL Tests ---")
                                                                                                                                                                                                        
# Test 1: Genres
q1 = """
PREFIX mo: <http://purl.org/ontology/mo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>                                                                                                                                                     
SELECT ?genre WHERE {
    ?artist rdfs:label "David Bowie" .                                                                                                                                                                   
    ?artist mo:genre ?g .
    ?g rdfs:label ?genre .                                                                                                                                                                               
}                                                                                                                                                                                                        
"""
genres = [str(row.genre) for row in g.query(q1)]                                                                                                                                                         
print(f"Genres ({len(genres)}): {genres[:8]}")
                                                                                                                                                                                                        
# Test 2: Awards
q2 = """                                                                                                                                                                                                 
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>                                                                                                                                                     
SELECT ?award WHERE {                                                                                                                                                                                    
    ?artist rdfs:label "David Bowie" .                                                                                                                                                                   
    ?artist mh:wonAward ?a .                                                                                                                                                                             
    ?a rdfs:label ?award .
}
"""
awards = [str(row.award) for row in g.query(q2)]                                                                                                                                                         
print(f"Awards ({len(awards)}): {awards[:5]}")
                                                                                                                                                                                                        
# Test 3: Instruments
q3 = """
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>                                                                                                                                                     
SELECT ?instrument WHERE {
    ?artist rdfs:label "David Bowie" .                                                                                                                                                                   
    ?artist mh:playsInstrument ?i .
    ?i rdfs:label ?instrument .                                                                                                                                                                          
}
"""                                                                                                                                                                                                      
instruments = [str(row.instrument) for row in g.query(q3)]
print(f"Instruments ({len(instruments)}): {instruments}")
                                                                                                                                                                                                        
# Test 4: Labels
q4 = """                                                                                                                                                                                                 
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label WHERE {
    ?artist rdfs:label "David Bowie" .
    ?artist mh:signedTo ?l .                                                                                                                                                                             
    ?l rdfs:label ?label .
}                                                                                                                                                                                                        
"""             
labels = [str(row.label) for row in g.query(q4)]
print(f"Labels ({len(labels)}): {labels[:5]}")                                                                                                                                                           

# Test 5: Influences                                                                                                                                                                                     
q5 = """        
PREFIX mh: <http://example.org/music-history/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name WHERE {                                                                                                                                                                                     
    ?artist rdfs:label "David Bowie" .
    ?artist mh:influencedBy ?inf .                                                                                                                                                                       
    ?inf rdfs:label ?name .                                                                                                                                                                              
}
"""                                                                                                                                                                                                      
influences = [str(row.name) for row in g.query(q5)]
print(f"Influences ({len(influences)}): {influences}")

# Test 6: Subgenres                                                                                                                                                                                      
q6 = """
PREFIX mh: <http://example.org/music-history/>                                                                                                                                                           
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?style ?genre WHERE {
    ?s mh:subgenreOf ?g .                                                                                                                                                                                
    ?s rdfs:label ?style .
    ?g rdfs:label ?genre .                                                                                                                                                                               
}                                                                                                                                                                                                        
"""
subgenres = [(str(row.style), str(row.genre)) for row in g.query(q6)]                                                                                                                                    
print(f"Subgenres ({len(subgenres)}): {subgenres}")
                                                                                                                                                                                                        
# Test 7: Albums
q7 = """                                                                                                                                                                                                 
PREFIX mh: <http://example.org/music-history/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?title WHERE {                                                                                                                                                                                    
    ?artist rdfs:label "David Bowie" .
    ?artist mh:released ?album .                                                                                                                                                                         
    ?album dc:title ?title .                                                                                                                                                                             
}
"""                                                                                                                                                                                                      
albums = [str(row.title) for row in g.query(q7)]
print(f"Albums ({len(albums)}): {albums[:5]}")