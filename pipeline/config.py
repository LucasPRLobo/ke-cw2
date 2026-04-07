
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
        # Classical / Baroque / Romantic
        "Ludwig van Beethoven",
        "Wolfgang Amadeus Mozart",
        "Johann Sebastian Bach",
        "Pyotr Ilyich Tchaikovsky",
        "Antonio Vivaldi",
        "Frédéric Chopin",
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
        "Luiz Gonzaga",
        "Dominguinhos",
        "Hermeto Pascoal",
        # African
        "Fela Kuti",
        "Miriam Makeba",
        "Youssou N'Dour",
        # Cuban / Latin
        "Buena Vista Social Club",
        "Celia Cruz",
        # Spanish
        "Julio Iglesias",
        "Alejandro Sanz",
        # Early Rock / Blues (influence origins)
        "Chuck Berry",
        "Muddy Waters",
        "Elvis Presley",
        # Hip-hop
        "Tupac Shakur",
        "Kendrick Lamar",
        # Band members (cross-references)
        "Freddie Mercury",
        "John Lennon",
        # Cape Verdean
        "Cesária Évora",
        # Indian
        "Ravi Shankar",
        # Medieval / Renaissance
        "Hildegard von Bingen",
        # Opera
        "Giuseppe Verdi",
        # Country (expansion)
        "Dolly Parton",
        # Electronic (expansion)
        "Jean-Michel Jarre",
        # K-pop / East Asian
        "BTS",
        # Flamenco
        "Paco de Lucía",
        # Arabic / Middle Eastern
        "Umm Kulthum",
        # Jazz (expansion)
        "Duke Ellington",
        "Nina Simone",
        # Punk
        "Ramones",
        # Cross-country collaborators
        "Frank Sinatra",
        "Yoko Ono",
        "Peter Gabriel",
        "Paul Simon",
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
SCHEMA_URI = "https://schema.org/"
# CIDOC-CRM removed — Schema.org chosen as second ontology (see report for justification)                                                                                                                                                                       
                                                                                                                                                                                                        
# --- API Settings ---                                                                                                                                                                                   
USER_AGENT = "KE-CW2-MusicHistory/0.1 (lucas@example.com)"
MB_RATE_LIMIT = 1.1      # seconds between MusicBrainz requests                                                                                                                                          
DISCOGS_RATE_LIMIT = 3    # seconds between Discogs requests
                                                                                                                                                                                                        
# --- Cache ---                                                                                                                                                                                          
CACHE_DIR_STRUCTURED = "data/structured"                                                                                                                                                                 
CACHE_DIR_TEXT = "data/text"                                                                                                                                                                             
                                                                                                                                                                                                        
# --- Genre Filtering ---                                                                                                                                                                                
# Genre blacklist — expanded based on RAG evaluation findings (P19-P23)
# Categories: nationality tags, role tags, decade tags, non-genre content types,
#             production modes, song formats, radio formats
GENRE_BLACKLIST = {
    # Nationality tags
    "british", "uk", "american", "english", "german", "french",
    "nigerian", "brazilian", "jamaican", "african",
    # Role/occupation tags (not genres)
    "actors", "arrangers", "composers", "singer-songwriters",
    "male vocalists", "female vocalists",
    # Decade tags
    "80s", "70s", "60s", "90s", "00s",
    # Non-genre content types (RAG finding P21: data artifacts)
    "interview", "spoken word", "audiobook", "field recording",
    # Production modes, not genres (RAG finding P21)
    "acoustic", "a]cappella", "lo-fi",
    # Song formats, not genres (RAG finding P21)
    "ballad", "compilation", "remix",
    # Radio formats, not musical genres (RAG finding P21, P22)
    "classic rock",
    # Discogs non-music / media categories (not genres)
    "soundtrack", "score", "promotional", "theme", "music video",
    "non-music", "dialogue", "comedy", "health-fitness",
    "public broadcast", "public service announcement", "radioplay", "therapy",
    # Nationality/geography tags (not genres) — from Wikidata P136
    "austrian", "polish", "italian", "european", "indian", "russian",
    # Occupations/descriptors/instruments (not genres)
    "composer", "beholder", "glorious", "pianist", "flute", "sitar",
    # Animation/TV (Wikidata P136 artefacts)
    "clay animation", "puppetoon animation", "telenovela",
    # Video game / film / TV categories (Wikidata P136 doesn't distinguish media types)
    "4x", "arcade", "fighting game", "role-playing video game",
    "action-adventure game", "adventure video game", "god game",
    "life simulation game", "real-time strategy", "biological simulation video game",
    "cyberpunk video game", "space trading and combat game",
    "action film", "adventure film", "comedy film", "crime film",
    "documentary film", "drama film", "fantasy film", "horror film",
    "romance film", "science fiction film", "thriller film", "western film",
    "biographical film", "musical film", "concert film", "film soundtrack",
    "film score", "film noir", "art film", "blaxploitation film",
    "children's film", "christmas film", "coming-of-age film",
    "crime thriller film", "crime drama film", "disaster film",
    "dystopian film", "ghost film", "heist film", "historical film",
    "historical drama", "independent film", "lgbtq-related film",
    "live-action/animated film", "music documentary film", "opera film",
    "parody film", "period drama film", "post-apocalyptic film",
    "prison film", "road movie", "romantic comedy", "romantic comedy film",
    "science fiction comedy", "spy film", "superhero film",
    "supernatural film", "supernatural horror film", "suspense film",
    "teen film", "trial film", "boxing film", "flashback film",
    "film based on a novel", "film based on literature", "comedy drama",
    "adventure science fiction", "adventure anime and manga",
    "comedy television program", "comedy television series",
    "lgbt-related television series",
    # Non-music categories that slipped through Wikidata P136 / NER
    "first-person shooter", "political magazine show", "neo-noir",
    "conceptual art", "cyberpunk", "rockumentary", "musical comedy",
    # Vague/non-genre tags
    "popular", "seattle", "vanguard", "fluxus", "western", "boy group",
    "light", "conscious", "gangsta", "orchestra",
    # Country names as genres (Wikidata P136 artefacts)
    "united states", "united kingdom",
}                                           
                                                                                                                                                                                                        
# Minimum tag count to include a MusicBrainz tag as a genre
MIN_TAG_COUNT = 3

# --- Award Blacklist ---
# Wikidata P166 returns ALL awards; filter out non-music awards.
# Pattern-based: any award whose lowercased name contains a keyword is excluded.
AWARD_BLACKLIST_KEYWORDS = [
    # Military
    "campaign medal", "victory medal", "military",
    # Honorary degrees
    "honorary doctor", "honorary degree", "honorary doctorate",
    # Humanitarian
    "humanitarian award",
    # Film/TV acting (not music)
    "best supporting actor", "best actor", "best actress",
    "screen actors guild", "cecil b. demille",
    # Science / non-arts
    "science fiction and fantasy hall of fame",
    "stephen hawking medal", "hawking medal",
    # Citizenship
    "honorary citizen",
    # Specific non-music awards
    "tony award", "saturn award",
]
# Exact-match blacklist for awards that can't be caught by keywords
AWARD_BLACKLIST_EXACT = {
    "emmy award", "primetime emmy award", "golden globe awards",
}

# --- Artist Search Overrides ---
# For artists where MusicBrainz search returns the wrong result,
# provide the correct MBID directly
ARTIST_MBID_OVERRIDES = {
    "Bob Marley": "ed2ac1e9-d51d-4eff-a2c2-85e81abd6360",                # Bob Marley (Person), not Bob Dylan
    "Pyotr Ilyich Tchaikovsky": "9ddd7abc-9e1b-471d-8031-583bc6bc8be9",  # Tchaikovsky the composer (Cyrillic name in MB)
    "Quincy Jones": "5803c81e-739a-4057-9a5c-cf84e55db630",              # Quincy Jones (Person)
    "Rick Rubin": "07aebfa0-55d6-47e0-a284-12330e3eae0d",                # Rick Rubin (producer)
    "George Martin": "26fa8b67-6c7f-406c-ad64-a1d070092df2",             # George Martin (Beatles producer)
    "Umm Kulthum": "0a354a70-b879-4697-ad9b-60bfe2bd1d63",               # أم كلثوم (Egyptian singer), not "UMM" (electronic project)
}

# --- Tools ---
# PySPARQL Anything (Python wrapper — auto-downloads jar on first use)
# Requires Java 21+ installed
SPARQL_ANYTHING_QUERIES = "pipeline/sparql_anything/"     
                                            