"""Generate formal OWL ontology declarations for the Music History KG.

Declares all classes, properties, and extensions of Music Ontology + Schema.org.
Merges contributions from modelling experts (William Caulton, Mert Yerlikaya)
with the pipeline team's property declarations.

Uses stubs instead of owl:imports to avoid reasoner failures when external
ontologies are not reachable (Schema.org has no clean OWL import URI).

This header is added to the RDF graph before serialisation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD, OWL, FOAF

from config import NAMESPACE_URI, MUSIC_ONTOLOGY_URI, SCHEMA_URI

MO = Namespace(MUSIC_ONTOLOGY_URI)
MH = Namespace(NAMESPACE_URI)
SCHEMA = Namespace(SCHEMA_URI)
DC = Namespace("http://purl.org/dc/elements/1.1/")


def add_ontology_header(g):
    """Add formal OWL ontology declarations to the graph."""

    # ============================================================
    # ONTOLOGY DECLARATION
    # ============================================================
    ontology_uri = URIRef(NAMESPACE_URI)
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, RDFS.label, Literal("Music History & Heritage Knowledge Graph")))
    g.add((ontology_uri, RDFS.comment, Literal(
        "An ontology for representing music history, extending the Music Ontology "
        "and Schema.org. Covers artists, compositions, albums, genres, instruments, "
        "awards, and record labels across all eras from medieval to modern."
    )))

    # ============================================================
    # 1. EXTERNAL CLASS & PROPERTY STUBS
    #    Declared locally so the reasoner can process the file
    #    without needing live imports of full external ontologies.
    # ============================================================

    # --- Music Ontology (mo) stubs ---
    mo_classes = {
        MO.MusicArtist: "A person or group making music.",
        MO.SoloMusicArtist: "An individual musician.",
        MO.MusicGroup: "A band or musical ensemble.",
        MO.MusicalWork: "An abstract musical composition (FRBR Work level).",
        MO.Record: "An album or record release.",
        MO.Release: "A specific release of a record.",
        MO.Track: "A track on a record.",
        MO.Signal: "An audio recording or signal.",
        MO.Label: "A record label.",
        MO.Genre: "A music genre.",
        MO.Instrument: "A musical instrument.",
        MO.Performance: "A live performance event.",
    }
    for cls, comment in mo_classes.items():
        g.add((cls, RDF.type, OWL.Class))
        g.add((cls, RDFS.comment, Literal(f"[Music Ontology] {comment}")))

    mo_obj_props = {
        MO.collaborated_with: "Links two artists who collaborated.",
        MO.instrument: "Links a performance or artist to an instrument.",
        MO.genre: "Links an artist, work, or track to a genre.",
        MO.composer: "Links a musical work to its composer.",
        MO.performer: "Links a track or signal to its performer.",
        MO.producer: "Links a record to its producer.",
        MO.member: "Links a music group to its members.",
        MO.member_of: "Links an artist to a group they are a member of.",
        MO.track: "Links a record to its tracks.",
        MO.publisher: "Links a record to its record label.",
    }
    for prop, comment in mo_obj_props.items():
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((prop, RDFS.comment, Literal(f"[Music Ontology] {comment}")))

    g.add((MO.release_date, RDF.type, OWL.DatatypeProperty))
    g.add((MO.release_date, RDFS.comment, Literal("[Music Ontology] Release date of a record.")))

    # --- Schema.org stubs ---
    schema_classes = {
        SCHEMA.MusicGroup: "A musical group (e.g., a band).",
        SCHEMA.MusicAlbum: "A music album.",
        SCHEMA.MusicRecording: "A music recording (track).",
        SCHEMA.MusicComposition: "A musical composition.",
        SCHEMA.Award: "An award or prize.",
        SCHEMA.Country: "A country.",
    }
    for cls, comment in schema_classes.items():
        g.add((cls, RDF.type, OWL.Class))
        g.add((cls, RDFS.comment, Literal(f"[Schema.org] {comment}")))

    schema_obj_props = {
        SCHEMA.affiliation: "An organisation that this person is affiliated with.",
        SCHEMA.nationality: "Nationality of a person.",
        SCHEMA.award: "An award won by or for this item.",
        SCHEMA.genre: "Genre of the creative work or group.",
        SCHEMA.recordLabel: "The record label for a music release.",
    }
    for prop, comment in schema_obj_props.items():
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((prop, RDFS.comment, Literal(f"[Schema.org] {comment}")))

    schema_dt_props = {
        SCHEMA.datePublished: "Date of first publication.",
        SCHEMA.birthDate: "Date of birth.",
        SCHEMA.deathDate: "Date of death.",
        SCHEMA.gender: "Gender of a person.",
    }
    for prop, comment in schema_dt_props.items():
        g.add((prop, RDF.type, OWL.DatatypeProperty))
        g.add((prop, RDFS.comment, Literal(f"[Schema.org] {comment}")))

    # --- Dublin Core and FOAF stubs (used in instance data) ---
    g.add((DC.title, RDF.type, OWL.DatatypeProperty))
    g.add((DC.title, RDFS.comment, Literal("[Dublin Core] Title of a resource.")))
    g.add((FOAF.name, RDF.type, OWL.DatatypeProperty))
    g.add((FOAF.name, RDFS.comment, Literal("[FOAF] Name of a person or agent.")))

    # ============================================================
    # 2. EXTENSIONS OF MUSIC ONTOLOGY (2 subclasses + 2 subproperties)
    # ============================================================

    # Subclass 1: IndependentLabel — a label without major label funding
    g.add((MH.IndependentLabel, RDF.type, OWL.Class))
    g.add((MH.IndependentLabel, RDFS.subClassOf, MO.Label))
    g.add((MH.IndependentLabel, RDFS.label, Literal("Independent Label")))
    g.add((MH.IndependentLabel, RDFS.comment, Literal(
        "A record label that operates without the funding of major record labels."
    )))

    # Subclass 2: CoverRecording — a recording by someone other than the original composer
    g.add((MH.CoverRecording, RDF.type, OWL.Class))
    g.add((MH.CoverRecording, RDFS.subClassOf, MO.Signal))
    g.add((MH.CoverRecording, RDFS.label, Literal("Cover Recording")))
    g.add((MH.CoverRecording, RDFS.comment, Literal(
        "An audio recording of a composition made by an artist who is not the original composer."
    )))

    # Subproperty 1: internationalCollaboration — collaboration across countries
    g.add((MH.internationalCollaboration, RDF.type, OWL.ObjectProperty))
    g.add((MH.internationalCollaboration, RDFS.subPropertyOf, MO.collaborated_with))
    g.add((MH.internationalCollaboration, RDFS.label, Literal("international collaboration")))
    g.add((MH.internationalCollaboration, RDFS.comment, Literal(
        "A collaboration between two artists who originate from different countries."
    )))

    # Subproperty 2: primaryInstrument — the lead instrument
    g.add((MH.primaryInstrument, RDF.type, OWL.ObjectProperty))
    g.add((MH.primaryInstrument, RDFS.subPropertyOf, MO.instrument))
    g.add((MH.primaryInstrument, RDFS.label, Literal("primary instrument")))
    g.add((MH.primaryInstrument, RDFS.comment, Literal(
        "The lead or most prominent instrument used in a track or by an artist."
    )))

    # ============================================================
    # 3. EXTENSIONS OF SCHEMA.ORG (2 subclasses + 2 subproperties)
    # ============================================================

    # Subclass 1: MultinationalBand — members from multiple countries
    g.add((MH.MultinationalBand, RDF.type, OWL.Class))
    g.add((MH.MultinationalBand, RDFS.subClassOf, SCHEMA.MusicGroup))
    g.add((MH.MultinationalBand, RDFS.label, Literal("Multinational Band")))
    g.add((MH.MultinationalBand, RDFS.comment, Literal(
        "A music group whose members originate from more than one distinct country."
    )))

    # Subclass 2: MusicAward — award specific to music industry
    g.add((MH.MusicAward, RDF.type, OWL.Class))
    g.add((MH.MusicAward, RDFS.subClassOf, SCHEMA.Award))
    g.add((MH.MusicAward, RDFS.label, Literal("Music Award")))
    g.add((MH.MusicAward, RDFS.comment, Literal(
        "An award given specifically for achievements in the music industry "
        "(e.g., Grammy, Brit Award, Rock and Roll Hall of Fame)."
    )))

    # Subproperty 1: signedTo — specialises schema:affiliation for artist-label relationship
    g.add((MH.signedTo, RDF.type, OWL.ObjectProperty))
    g.add((MH.signedTo, RDFS.subPropertyOf, SCHEMA.affiliation))
    g.add((MH.signedTo, RDFS.label, Literal("signed to")))
    g.add((MH.signedTo, RDFS.comment, Literal(
        "Links an artist or band to the record label they are contracted with."
    )))
    g.add((MH.signedTo, RDFS.domain, MO.MusicArtist))
    g.add((MH.signedTo, RDFS.range, MO.Label))

    # Subproperty 2: countryOfOrigin — specialises schema:nationality
    g.add((MH.countryOfOrigin, RDF.type, OWL.ObjectProperty))
    g.add((MH.countryOfOrigin, RDFS.subPropertyOf, SCHEMA.nationality))
    g.add((MH.countryOfOrigin, RDFS.label, Literal("country of origin")))
    g.add((MH.countryOfOrigin, RDFS.comment, Literal(
        "Links an artist, member, or band to their country of origin or formation."
    )))
    g.add((MH.countryOfOrigin, RDFS.domain, MO.MusicArtist))
    g.add((MH.countryOfOrigin, RDFS.range, SCHEMA.Country))

    # ============================================================
    # 4. CUSTOM CLASSES
    # ============================================================

    # Artist role classes — modelling note:
    # These represent roles/functions, not rigid types. An artist can be
    # both a Composer and a Musician simultaneously. We model these as
    # subclasses for simplicity in SPARQL queries, but acknowledge this
    # is a modelling trade-off (see CW1 feedback: "denote roles, not types").
    # The defined classes (AwardWinningArtist, ProducerArtist) in section 4b
    # demonstrate the preferred approach: inferring roles from behaviour.
    g.add((MH.Composer, RDF.type, OWL.Class))
    g.add((MH.Composer, RDFS.subClassOf, MO.MusicArtist))
    g.add((MH.Composer, RDFS.label, Literal("Composer")))
    g.add((MH.Composer, RDFS.comment, Literal(
        "A person who writes or composes musical works. "
        "Modelled as a subclass for query convenience; "
        "see ProducerArtist defined class for inference-based role assignment."
    )))

    g.add((MH.Producer, RDF.type, OWL.Class))
    g.add((MH.Producer, RDFS.subClassOf, MO.MusicArtist))
    g.add((MH.Producer, RDFS.label, Literal("Producer")))
    g.add((MH.Producer, RDFS.comment, Literal(
        "A person who oversees and directs the recording and production of music. "
        "See ProducerArtist defined class for reasoner-inferred assignment."
    )))

    g.add((MH.Musician, RDF.type, OWL.Class))
    g.add((MH.Musician, RDFS.subClassOf, MO.MusicArtist))
    g.add((MH.Musician, RDFS.label, Literal("Musician")))
    g.add((MH.Musician, RDFS.comment, Literal(
        "A person who performs music, typically as an instrumentalist or vocalist."
    )))

    # Era — for decade/period-based queries
    g.add((MH.Era, RDF.type, OWL.Class))
    g.add((MH.Era, RDFS.label, Literal("Era")))
    g.add((MH.Era, RDFS.comment, Literal(
        "A named historical period in music history (e.g., Baroque, Classical, Jazz Age, Rock Era)."
    )))

    # Other custom classes
    g.add((MH.Country, RDF.type, OWL.Class))
    g.add((MH.Country, RDFS.subClassOf, SCHEMA.Country))
    g.add((MH.Country, RDFS.label, Literal("Country")))
    g.add((MH.Country, RDFS.comment, Literal("A country or nation, used for artist origin and geographic analysis.")))

    g.add((MH.Award, RDF.type, OWL.Class))
    g.add((MH.Award, RDFS.subClassOf, SCHEMA.Award))
    g.add((MH.Award, RDFS.label, Literal("Award")))
    g.add((MH.Award, RDFS.comment, Literal("A music award or recognition (e.g., Grammy, Rock and Roll Hall of Fame).")))

    g.add((MH.RecordLabel, RDF.type, OWL.Class))
    g.add((MH.RecordLabel, RDFS.subClassOf, MO.Label))
    g.add((MH.RecordLabel, RDFS.label, Literal("Record Label")))
    g.add((MH.RecordLabel, RDFS.comment, Literal("A record label or music publishing company.")))

    g.add((MH.MusicalWork, RDF.type, OWL.Class))
    g.add((MH.MusicalWork, RDFS.subClassOf, MO.MusicalWork))
    g.add((MH.MusicalWork, RDFS.label, Literal("Musical Work")))
    g.add((MH.MusicalWork, RDFS.comment, Literal(
        "A musical composition, independent of any recording. "
        "Covers classical compositions that predate recordings."
    )))

    g.add((MH.Persona, RDF.type, OWL.Class))
    g.add((MH.Persona, RDFS.label, Literal("Persona")))
    g.add((MH.Persona, RDFS.comment, Literal("A stage persona or alter ego adopted by an artist (e.g., Ziggy Stardust).")))

    g.add((MH.AlbumGroup, RDF.type, OWL.Class))
    g.add((MH.AlbumGroup, RDFS.label, Literal("Album Group")))
    g.add((MH.AlbumGroup, RDFS.comment, Literal("A named grouping of albums (e.g., Berlin Trilogy).")))

    g.add((MH.Organisation, RDF.type, OWL.Class))
    g.add((MH.Organisation, RDFS.label, Literal("Organisation")))
    g.add((MH.Organisation, RDFS.comment, Literal("An organisation founded by or associated with an artist.")))

    # ============================================================
    # 4b. DEFINED CLASSES (with necessary & sufficient conditions)
    #     These use owl:equivalentClass so a reasoner can infer
    #     class membership from instance data.
    # ============================================================

    # Defined Class 1: AwardWinningArtist
    # An artist who has won at least one award.
    # Necessary & sufficient: MusicArtist AND (wonAward some MusicAward)
    award_winning_restriction = BNode()
    g.add((award_winning_restriction, RDF.type, OWL.Restriction))
    g.add((award_winning_restriction, OWL.onProperty, MH.wonAward))
    g.add((award_winning_restriction, OWL.someValuesFrom, MH.MusicAward))

    award_winning_intersection = BNode()
    g.add((award_winning_intersection, RDF.type, OWL.Class))
    award_winning_list = BNode()
    award_winning_rest = BNode()
    g.add((award_winning_list, RDF.first, MO.MusicArtist))
    g.add((award_winning_list, RDF.rest, award_winning_rest))
    g.add((award_winning_rest, RDF.first, award_winning_restriction))
    g.add((award_winning_rest, RDF.rest, RDF.nil))
    g.add((award_winning_intersection, OWL.intersectionOf, award_winning_list))

    g.add((MH.AwardWinningArtist, RDF.type, OWL.Class))
    g.add((MH.AwardWinningArtist, OWL.equivalentClass, award_winning_intersection))
    g.add((MH.AwardWinningArtist, RDFS.label, Literal("Award-Winning Artist")))
    g.add((MH.AwardWinningArtist, RDFS.comment, Literal(
        "Defined class: a MusicArtist who has won at least one MusicAward. "
        "Inferred by a reasoner from wonAward triples."
    )))

    # Defined Class 2: InternationalCollaborator
    # An artist who has collaborated with artists from different countries.
    # Necessary & sufficient: MusicArtist AND (collaboratedWith some MusicArtist)
    collab_restriction = BNode()
    g.add((collab_restriction, RDF.type, OWL.Restriction))
    g.add((collab_restriction, OWL.onProperty, MH.collaboratedWith))
    g.add((collab_restriction, OWL.someValuesFrom, MO.MusicArtist))

    collab_intersection = BNode()
    g.add((collab_intersection, RDF.type, OWL.Class))
    collab_list = BNode()
    collab_rest = BNode()
    g.add((collab_list, RDF.first, MO.MusicArtist))
    g.add((collab_list, RDF.rest, collab_rest))
    g.add((collab_rest, RDF.first, collab_restriction))
    g.add((collab_rest, RDF.rest, RDF.nil))
    g.add((collab_intersection, OWL.intersectionOf, collab_list))

    g.add((MH.InternationalCollaborator, RDF.type, OWL.Class))
    g.add((MH.InternationalCollaborator, OWL.equivalentClass, collab_intersection))
    g.add((MH.InternationalCollaborator, RDFS.label, Literal("International Collaborator")))
    g.add((MH.InternationalCollaborator, RDFS.comment, Literal(
        "Defined class: a MusicArtist who has collaborated with at least one other MusicArtist. "
        "Inferred by a reasoner from collaboratedWith triples."
    )))

    # Defined Class 3: ProducerArtist
    # An artist who has produced at least one release.
    # Necessary & sufficient: MusicArtist AND (produced some Release)
    prod_restriction = BNode()
    g.add((prod_restriction, RDF.type, OWL.Restriction))
    g.add((prod_restriction, OWL.onProperty, MH.produced))
    g.add((prod_restriction, OWL.someValuesFrom, MO.Release))

    prod_intersection = BNode()
    g.add((prod_intersection, RDF.type, OWL.Class))
    prod_list = BNode()
    prod_rest = BNode()
    g.add((prod_list, RDF.first, MO.MusicArtist))
    g.add((prod_list, RDF.rest, prod_rest))
    g.add((prod_rest, RDF.first, prod_restriction))
    g.add((prod_rest, RDF.rest, RDF.nil))
    g.add((prod_intersection, OWL.intersectionOf, prod_list))

    g.add((MH.ProducerArtist, RDF.type, OWL.Class))
    g.add((MH.ProducerArtist, OWL.equivalentClass, prod_intersection))
    g.add((MH.ProducerArtist, RDFS.label, Literal("Producer Artist")))
    g.add((MH.ProducerArtist, RDFS.comment, Literal(
        "Defined class: a MusicArtist who has produced at least one Release. "
        "Inferred by a reasoner from produced triples. "
        "Note: this addresses the CW1 feedback about roles vs types — "
        "ProducerArtist is defined by what the artist does, not by assertion."
    )))

    # ============================================================
    # 5. CUSTOM OBJECT PROPERTIES
    # ============================================================

    properties = [
        (MH.released, "released", "Links an artist to an album they released.",
         MO.MusicArtist, MO.Release),
        (MH.hasTrack, "has track", "Links an album to its tracks.",
         MO.Release, MO.Track),
        (MH.wonAward, "won award", "Links an artist to a music award they received.",
         MO.MusicArtist, MH.MusicAward),
        (MH.influencedBy, "influenced by", "Links an artist to another artist who influenced their work or style.",
         MO.MusicArtist, MO.MusicArtist),
        (MH.collaboratedWith, "collaborated with", "Links two artists who collaborated.",
         MO.MusicArtist, MO.MusicArtist),
        (MH.playsInstrument, "plays instrument", "Links an artist to an instrument they play.",
         MO.MusicArtist, MO.Instrument),
        (MH.composed, "composed", "Links a composer to a musical work they composed.",
         MO.MusicArtist, MH.MusicalWork),
        (MH.subgenreOf, "subgenre of", "Links a subgenre to its parent genre.",
         MO.Genre, MO.Genre),
        (MH.alterEgo, "alter ego", "Links an artist to a stage persona.",
         MO.MusicArtist, MH.Persona),
        (MH.albumGrouping, "album grouping", "Links an album to a named album group.",
         MO.Release, MH.AlbumGroup),
        (MH.hasMember, "has member", "Links a group to a member artist.",
         MO.MusicGroup, MO.SoloMusicArtist),
        (MH.produced, "produced", "Links a producer to a work they produced.",
         MO.MusicArtist, MO.Release),
        (MH.producedBy, "produced by", "Links an album to its producer.",
         MO.Release, MO.MusicArtist),
        (MH.hasMusicalPeriod, "has musical period", "Links an artist to a historical musical period.",
         MO.MusicArtist, MH.Era),
        (MH.pioneerOf, "pioneer of", "Links an artist to a genre they pioneered.",
         MO.MusicArtist, MO.Genre),
        (MH.founded, "founded", "Links an artist to an organisation they founded.",
         MO.MusicArtist, MH.Organisation),
        (MH.covers, "covers", "Links a cover recording to the original musical work.",
         MH.CoverRecording, MO.MusicalWork),
        (MH.activeIn, "active in", "Links an artist to a country where they were professionally active.",
         MO.MusicArtist, SCHEMA.Country),
        (MH.activeDuring, "active during", "Links an artist to the historical era during which they were active.",
         MO.MusicArtist, MH.Era),
        (MH.hasEra, "has era", "Links a musical work to the historical era in which it was composed.",
         MO.MusicalWork, MH.Era),
    ]

    for prop_uri, label, comment, domain, range_cls in properties:
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.label, Literal(label)))
        g.add((prop_uri, RDFS.comment, Literal(comment)))
        g.add((prop_uri, RDFS.domain, domain))
        g.add((prop_uri, RDFS.range, range_cls))

    # ============================================================
    # 6. DATATYPE PROPERTY DECLARATIONS
    # ============================================================

    dt_properties = [
        (MH.releaseDate, "release date", "The date an album was released.",
         MO.Release),
        (MH.compositionDate, "composition date",
         "The date a musical work was composed, distinct from recording or release date.",
         MH.MusicalWork),
        (MH.realName, "real name", "The birth name or legal name of an artist.",
         MO.SoloMusicArtist),
        (MH.duration, "duration", "The duration of a track in milliseconds.",
         MO.Track),
        (MH.birthPlace, "birth place", "The city or area where an artist was born.",
         MO.SoloMusicArtist),
    ]

    for prop_uri, label, comment, domain in dt_properties:
        g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
        g.add((prop_uri, RDFS.label, Literal(label)))
        g.add((prop_uri, RDFS.comment, Literal(comment)))
        g.add((prop_uri, RDFS.domain, domain))

    return g


if __name__ == "__main__":
    g = Graph()
    g.bind("mh", MH)
    g.bind("mo", MO)
    g.bind("owl", OWL)
    g.bind("schema", SCHEMA)
    g.bind("dc", DC)
    g.bind("foaf", FOAF)

    add_ontology_header(g)
    print(f"Ontology header: {len(g)} triples")
    g.serialize(destination="../ontology/ontology_header.ttl", format="turtle")
    print("Saved to ontology/ontology_header.ttl")
