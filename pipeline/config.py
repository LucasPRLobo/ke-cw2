
ARTISTS = [
        # Rock                                                                                                                                                                                               
        "David Bowie",                                        
        "The Beatles",                                                                                                                                                                                       
        "Led Zeppelin",
        "Nirvana",                                                                                                                                                                                           
        "Queen",                                              
        # Jazz                                                                                                                                                                                               
        "Miles Davis",                                        
        "John Coltrane",
        # Classical                             
        "Ludwig van Beethoven",             
        "Wolfgang Amadeus Mozart",
        "Johann Sebastian Bach",                                                                                                                                                                             
        "Pyotr Ilyich Tchaikovsky",
        # Pop                                                                                                                                                                                                
        "Michael Jackson",                                    
        # Soul / R&B
        "Aretha Franklin",                                                                                                                                                                                   
        # Electronic
        "Kraftwerk",                                                                                                                                                                                         
        "Daft Punk",                                          
        "Brian Eno",                        
        # Folk
        "Bob Dylan",                                                                                                                                                                                         
        # Country
        "Johnny Cash",                                                                                                                                                                                       
        # Reggae                                              
        "Bob Marley",
        # Brazilian                             
        "Antônio Carlos Jobim",             
        # African
        "Fela Kuti",                                                                                                                                                                                         
        "Miriam Makeba",
        # Producers                                                                                                                                                                                          
        "Rick Rubin",                                         
        "Quincy Jones",        
        "George Martin",
]


# --- Namespaces ---
NAMESPACE_URI = "http://example.org/music-history/"                                                                                                                                                      
MUSICBRAINZ_ARTIST_URI = "http://musicbrainz.org/artist/" 
MUSICBRAINZ_RELEASE_URI = "http://musicbrainz.org/release/"
MUSICBRAINZ_RECORDING_URI = "http://musicbrainz.org/recording/"
MUSIC_ONTOLOGY_URI = "http://purl.org/ontology/mo/"
CIDOC_CRM_URI = "http://www.cidoc-crm.org/cidoc-crm/"                                                                                                                                                    
SCHEMA_URI = "https://schema.org/"                                                                                                                                                                       
                                                                                                                                                                                                        
# --- API Settings ---                                                                                                                                                                                   
USER_AGENT = "KE-CW2-MusicHistory/0.1 (lucas@example.com)"
MB_RATE_LIMIT = 1.1      # seconds between MusicBrainz requests                                                                                                                                          
DISCOGS_RATE_LIMIT = 3    # seconds between Discogs requests
                                                                                                                                                                                                        
# --- Cache ---                                                                                                                                                                                          
CACHE_DIR_STRUCTURED = "data/structured"                                                                                                                                                                 
CACHE_DIR_TEXT = "data/text"                                                                                                                                                                             
                                                                                                                                                                                                        
# --- Genre Filtering ---                                                                                                                                                                                
GENRE_BLACKLIST = {                                       
    "british", "uk", "american", "english", "german", "french",
    "nigerian", "brazilian", "jamaican", "african",                                                                                                                                                      
    "actors", "arrangers", "composers", "singer-songwriters",
    "male vocalists", "female vocalists",                                                                                                                                                                
    "80s", "70s", "60s", "90s", "00s",                                                                                                                                                                   
}                                           
                                                                                                                                                                                                        
# Minimum tag count to include a MusicBrainz tag as a genre
MIN_TAG_COUNT = 3        

# --- Tools ---
# PySPARQL Anything (Python wrapper — auto-downloads jar on first use)
# Requires Java 21+ installed
SPARQL_ANYTHING_QUERIES = "pipeline/sparql_anything/"     
                                            