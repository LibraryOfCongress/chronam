from datetime import datetime

from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef, RDF, RDFS
from rfc3339 import rfc3339

DC = Namespace('http://purl.org/dc/elements/1.1/')
ORE = Namespace('http://www.openarchives.org/ore/terms/')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
RDA = Namespace('http://rdvocab.info/elements/')
XSD = Namespace('http://www.w3.org/2001/XMLSchema#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
EXIF = Namespace('http://www.w3.org/2003/12/exif/ns#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
FRBR = Namespace('http://purl.org/vocab/frbr/core#')
NDNP = Namespace('http://chroniclingamerica.loc.gov/terms#')
DCTERMS = Namespace('http://purl.org/dc/terms/')

def title_to_graph(t, g=None, include_issues=True):
    if not g:
        g = make_graph()

    uri = abstract_uri(t)
    g.add((uri, RDF.type, BIBO['Newspaper']))
    g.add((uri, DCTERMS['title'], Literal(t.name)))
    g.add((uri, RDA['placeOfPublication'], Literal(t.place_of_publication)))

    for subject in t.subjects.all():
        g.add((uri, DC['subject'], Literal(subject.heading)))
    for language in t.languages.all():
        if language.lingvoj:
            g.add((uri, DCTERMS['language'], URIRef(language.lingvoj)))
    if t.publisher and t.publisher != 's.n.':
        g.add((uri, DC['publisher'], Literal(t.publisher)))
    for essay in t.essays.all():
        g.add((uri, DCTERMS['description'], URIRef(essay.url)))
    if include_issues:
        for issue in t.issues.all():
            g.add((uri, ORE['aggregates'], abstract_uri(issue)))
    for url in t.urls.all():
        g.add((uri, RDFS.seeAlso, URIRef(url.value)))
    for place in t.places.all():
        if place.dbpedia:
            g.add((uri, DCTERMS['coverage'], URIRef(place.dbpedia)))
        if place.geonames:
            g.add((uri, DCTERMS['coverage'], URIRef(place.geonames)))
    for title in t.succeeding_titles():
        g.add((uri, FRBR.successor, abstract_uri(title)))
    for title in t.preceeding_titles():
        g.add((uri, FRBR.successorOf, abstract_uri(title)))
    for title in t.related_titles():
        g.add((uri, DCTERMS.relation, abstract_uri(title)))

    if t.start_year and t.end_year:
        start, end = t.start_year, t.end_year
        if end == 'current':
            end = 'unknown'
        if start == '????':
            start = 'unknown'
        g.add((uri, DCTERMS['date'], Literal('%s/%s' % (start, end),
            datatype=URIRef('http://www.loc.gov/standards/datetime#edt'))))

    g.add((uri, DCTERMS.hasFormat, URIRef(t.marc.url)))
    g.add((uri, RDFS.seeAlso, URIRef('http://lccn.loc.gov/%s' % t.lccn)))
    g.add((uri, OWL['sameAs'], URIRef('info:lccn/%s' % t.lccn)))

    if t.oclc:
        g.add((uri, RDFS.seeAlso, 
               URIRef('http://www.worldcat.org/oclc/%s' % t.oclc)))
        g.add((uri, OWL['sameAs'], URIRef('info:oclcnum/%s' % t.oclc)))
    if t.issn:
        g.add((uri, OWL['sameAs'], URIRef('urn:issn:%s' % t.issn)))

    add_rem(g, uri, rdf_uri(t))

    return g

def issue_to_graph(i, g=None):
    if not g:
        g = make_graph()

    uri = abstract_uri(i)
    g.add((uri, RDF.type, BIBO['Issue']))
    g.add((uri, DCTERMS['title'], Literal('%s - %s' % (i.title.display_name,
        i.date_issued)))) 
    g.add((uri, DCTERMS['issued'], Literal(i.date_issued, datatype=XSD.date)))
    g.add((uri, ORE['isAggregatedBy'], abstract_uri(i.title)))
    g.add((uri, ORE['isAggregatedBy'], abstract_uri(i.batch)))
    for page in i.pages.all():
        g.add((uri, ORE['aggregates'], abstract_uri(page)))
    
    add_rem(g, uri, rdf_uri(i))

    return g

def page_to_graph(p, g=None):
    if not g:
        g = make_graph()

    uri = abstract_uri(p)
    g.add((uri, RDF.type, NDNP['Page']))
    g.add((uri, NDNP['sequence'], Literal(p.sequence)))
    g.add((uri, ORE['isAggregatedBy'], abstract_uri(p.issue)))

    jp2_uri = URIRef(p.jp2_url)
    g.add((uri, ORE['aggregates'], jp2_uri))
    g.add((jp2_uri, DC['format'], Literal('image/jp2')))
    g.add((jp2_uri, EXIF['width'], Literal(p.jp2_width)))
    g.add((jp2_uri, EXIF['height'], Literal(p.jp2_length)))

    ocr_uri = URIRef(p.ocr_url)
    g.add((uri, ORE.aggregates, ocr_uri))
    g.add((ocr_uri, DC['format'], Literal('text/xml')))
   
    pdf_uri = URIRef(p.pdf_url)
    g.add((uri, ORE.aggregates, pdf_uri))
    g.add((pdf_uri, DC['format'], Literal('application/pdf')))

    txt_uri = URIRef(p.txt_url)
    g.add((uri, ORE.aggregates, txt_uri))
    g.add((txt_uri, DC['format'], Literal('text/plain')))

    thumb_uri = URIRef(p.thumb_url)
    g.add((uri, ORE.aggregates, thumb_uri))
    g.add((uri, FOAF.depiction, thumb_uri))
    g.add((thumb_uri, DC['format'], Literal('image/jpeg')))
    g.add((uri, DCTERMS['issued'], Literal(p.issue.date_issued, 
                                           datatype=XSD.date)))
    g.add((uri, DCTERMS['title'], Literal('%s - %s - %s' % 
        (p.issue.title.display_name, p.issue.date_issued, p.sequence))))

    for flickr_url in p.flickr_urls.all():
        g.add((uri, ORE.aggregates, flickr_url.value))

    if p.number:
        g.add((uri, NDNP['number'], Literal(p.number)))
    if p.section_label:
        g.add((uri, NDNP['section'], Literal(p.section_label)))

    add_rem(g, uri, rdf_uri(p))

    return g

def titles_to_graph(titles):
    g = make_graph()
    for title in titles:
        g = title_to_graph(title, g, include_issues=False)
    return g

def batch_to_graph(b):
    g = make_graph()
    uri = abstract_uri(b)

    g.add((uri, RDF.type, NDNP['Batch']))
    g.add((uri, DCTERMS['created'], Literal(rfc3339(b.created), 
                                            datatype=XSD.dateTime)))
    g.add((uri, DCTERMS['title'], Literal(b.name)))
    g.add((uri, DCTERMS['creator'], abstract_uri(b.awardee)))
    g.add((uri, NDNP['bag'], URIRef('/data/batches/' + b.name)))
    for issue in b.issues.all():
        g.add((uri, ORE['aggregates'], abstract_uri(issue)))
    add_rem(g, uri, rdf_uri(b))

    return g

def awardee_to_graph(a):
    g = make_graph()
    uri = abstract_uri(a)
    g.add((uri, RDF.type, NDNP['Awardee']))
    g.add((uri, FOAF['name'], Literal(a.name)))
    for batch in a.batches.all():
        g.add((abstract_uri(batch), DCTERMS['creator'], uri))
    g.add((uri, RDFS.isDefinedBy, rdf_uri(a)))
    for essay in a.essays.all():
        g.add((URIRef(essay.url), DCTERMS['creator'], uri))
        g.add((URIRef(essay.url), RDF['type'], NDNP['Essay']))
    if a.org_code == 'dlc':
        # important for resource maps that reference loc as dc:creator
        g.add((uri, FOAF['mbox'], Literal('help@loc.gov')))
        g.add((uri, OWL['sameAs'], 
            URIRef("http://dbpedia.org/resource/Library_of_Congress")))
    return g

def make_graph():
    g = ConjunctiveGraph()
    g.bind('dc', DC)
    g.bind('ore', ORE)
    g.bind('owl', OWL)
    g.bind('rda', RDA)
    g.bind('bibo', BIBO)
    g.bind('exif', EXIF)
    g.bind('foaf', FOAF)
    g.bind('frbr', FRBR)
    g.bind('ndnp', NDNP)
    g.bind('dcterms', DCTERMS)
    return g

def abstract_uri(m):
    return URIRef(m.abstract_url)

def rdf_uri(m):
    return URIRef(m.url.rstrip('/') + '.rdf')

def add_rem(g, uri_a, uri_r):
    """
    adds assertions about the aggregate resource (uri_a) and the
    the resource map (uri_r) that describes it using the oai-ore vocabulary
    http://www.openarchives.org/ore/1.0/datamodel.html
    """
    g.add((uri_a, ORE['isDescribedBy'], uri_r))
    g.add((uri_r, RDF.type, ORE['ResourceMap']))
    g.add((uri_r, ORE['describes'], uri_a))
    g.add((uri_r, DCTERMS['creator'], URIRef('http://chroniclingamerica.loc.gov/awardees/dlc#awardee')))

    # TODO: would be nice if created and modified were more real somehow
    # so oai-ore bots would know when resources needed to be harvested...
    t = rfc3339(datetime.now())
    g.add((uri_r, DCTERMS['created'], Literal(t, datatype=XSD.dateTime)))
    g.add((uri_r, DCTERMS['modified'], Literal(t, datatype=XSD.dateTime)))

    return g
