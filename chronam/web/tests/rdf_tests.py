from django.test import TestCase
from chronam.web.models import Title, Page, Issue, Batch, Awardee

from chronam.web import rdf
from chronam.web.rdf import DCTERMS, ORE, NDNP

from rdflib import Literal, URIRef, RDFS, RDF

class RdfTests(TestCase):
    fixtures = ['titles.json', 'awardee.json', 'batch.json', 'issue.json',
    'page.json']

    def test_title(self):
        t = Title.objects.get(lccn='sn83030214')
        g = rdf.title_to_graph(t)
        u = URIRef('/lccn/sn83030214#title')
        self.assertEqual(g.value(u, DCTERMS['title']), 
                                 Literal('New-York tribune.'))
        self.assertEqual(g.value(u, ORE.isDescribedBy), 
                         URIRef('/lccn/sn83030214.rdf'))

    def test_issue(self):
        i = Issue.objects.get(id=1)
        g = rdf.issue_to_graph(i)
        u = URIRef('/lccn/sn83030214/1898-01-01/ed-1#issue')
        self.assertEqual(g.value(u, DCTERMS['issued']), Literal('1898-01-01', datatype=URIRef('http://www.w3.org/2001/XMLSchema#date')))
        self.assertEqual(g.value(u, ORE.isDescribedBy),
                URIRef('/lccn/sn83030214/1898-01-01/ed-1.rdf'))

    def test_page(self):
        p = Page.objects.get(id=1)
        g = rdf.page_to_graph(p)
        u = URIRef('/lccn/sn83030214/1898-01-01/ed-1/seq-1#page')
        parts = list(g.objects(u, ORE['aggregates']))
        self.assertEqual(len(parts), 5)
        self.assertTrue(URIRef('/lccn/sn83030214/1898-01-01/ed-1/seq-1.pdf') 
                        in parts)
        self.assertEqual(g.value(u, ORE.isDescribedBy), 
                         URIRef('/lccn/sn83030214/1898-01-01/ed-1/seq-1.rdf'))

    def test_batch(self):
        b = Batch.objects.get(name='batch_curiv_ahwahnee_ver01')
        g = rdf.batch_to_graph(b)
        u = URIRef('/batches/batch_curiv_ahwahnee_ver01#batch')
        self.assertEqual(g.value(u, RDF.type), NDNP['Batch'])

    def test_awardee(self):
        a = Awardee.objects.get(org_code='curiv')
        g = rdf.awardee_to_graph(a)
        u = URIRef('/awardees/curiv#awardee')
        self.assertEqual(g.value(u, RDF.type), NDNP['Awardee'])
