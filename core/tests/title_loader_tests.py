from django.test import TestCase
import os

from lxml import etree

import openoni.core
from openoni.core.models import Title
from openoni.core.title_loader import TitleLoader


def abs_filename(rel_filename):
    abs_filename = os.path.join(
        os.path.dirname(openoni.core.__file__),
        rel_filename)
    return abs_filename


class TitleLoaderTests(TestCase):
    fixtures = ['languages.json', 'countries.json']

    def setUp(self):
        # wipe the slate clean
        Title.objects.all().delete()
        # load a title
        loader = TitleLoader()
        titlexml = os.path.join(os.path.dirname(openoni.core.__file__),
            'test-data', 'title.xml')
        loader.load_file(titlexml)

    def test_title(self):
        t = Title.objects.get(lccn='sn83030846')
        self.assertEqual(t.name, 'The living issue.')
        self.assertEqual(t.name_normal, 'living issue.')
        self.assertEqual(t.lccn, 'sn83030846')
        self.assertEqual(t.place_of_publication, 'Albany, N.Y.')
        self.assertEqual(t.publisher, 'The Living Issue Co.')
        self.assertEqual(t.frequency, 'Weekly')
        self.assertEqual(t.oclc, '9688987')
        self.assertEqual(t.start_year, '1873')
        self.assertEqual(t.end_year, '1887')
        # ordering of attributes and namespace prefixes isn't predictable
        # so lets just check that we can parse the xml and get the leader
        rec = etree.fromstring(t.marc.xml)
        self.assertTrue(rec != None)
        self.assertEqual(rec.find('.//leader').text,
                         '00000cas a22000007a 4500')
        self.assertEqual(t.country.code, 'nyu')
        self.assertEqual(t.country.name, 'New York')
        self.assertEqual(t.country.region, 'North America')

    def test_places(self):
        t = Title.objects.get(lccn='sn83030846')
        places = list(t.places.all())
        self.assertEqual(len(places), 6)
        self.assertEqual(places[0].name, 'Maine--Cumberland--Portland')
        self.assertEqual(places[0].country, 'United States')
        self.assertEqual(places[0].state, 'Maine')
        self.assertEqual(places[0].county, 'Cumberland')
        self.assertEqual(places[0].city, 'Portland')
        self.assertEqual(places[5].name, 'New York--Otsego--Cooperstown')
        self.assertEqual(places[5].country, 'United States')
        self.assertEqual(places[5].state, 'New York')
        self.assertEqual(places[5].county, 'Otsego')
        self.assertEqual(places[5].city, 'Cooperstown')

    def test_publication_dates(self):
        t = Title.objects.get(lccn='sn83030846')
        pubdates = list(t.publication_dates.all())
        self.assertEqual(len(pubdates), 2)
        self.assertEqual(pubdates[0].text, 'Began in 1873.')
        self.assertEqual(pubdates[1].text, 'Ceased in Mar. 1887.')

    def test_subjects(self):
        t = Title.objects.get(lccn='sn83030846')
        # test different types and first and last
        subjects = list(t.subjects.all())
        self.assertEqual(len(subjects), 8)
        self.assertEqual(subjects[0].heading, 'Albany (N.Y.)--Newspapers.')
        self.assertEqual(subjects[0].type, 'g')  # for topic
        self.assertEqual(subjects[2].heading, 'Hartford (Conn.)--Newspapers.')
        self.assertEqual(subjects[2].type, 'g')
        self.assertEqual(subjects[7].heading, 'Utica (N.Y.)--Newspapers.')
        self.assertEqual(subjects[7].type, 'g')

    def test_notes(self):
        t = Title.objects.get(lccn='sn83030846')
        notes = list(t.notes.all())
        self.assertEqual(len(notes), 5)
        self.assertEqual(notes[0].text,
            'Description based on: Vol. 1, no. 8 (Apr. 12, 1873).')

    def test_preceeding_title_links(self):
        t = Title.objects.get(lccn='sn83030846')
        links = list(t.preceeding_title_links.all())
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].name, 'Commonwealth (New Haven, Conn.)')
        self.assertEqual(links[0].lccn, 'sn84020072')
        self.assertEqual(links[0].oclc, '10316704')
        self.assertEqual(links[1].name, 'Town and country (Providence, R.I.)')
        self.assertEqual(links[1].lccn, 'sn83021237')
        self.assertEqual(links[1].oclc, None)

    def test_alt_titles(self):
        t = Title.objects.get(lccn='sn83030846')
        alt_titles = list(t.alt_titles.all())
        self.assertEqual(len(alt_titles), 1)
        self.assertEqual(alt_titles[0].name, 'Living issue. Prohibition')

    def test_succeeding_titles(self):
        t = Title.objects.get(lccn='sn83030846')
        links = list(t.succeeding_title_links.all())
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0].name,
            'Living issue and the new republic')
        self.assertEqual(links[0].lccn, 'sn89071335')
        self.assertEqual(links[0].oclc, None)
        self.assertEqual(links[2].name,
            'State temperance journal (Middletown, Conn.)')
        self.assertEqual(links[2].lccn, 'sn92051309')
        self.assertEqual(links[2].oclc, '26109972')

    def test_marc_html(self):
        t = Title.objects.get(lccn='sn83030846')
        html = t.marc.html
        self.assertTrue('<td>00000cas a22000007a 4500</td>' in html)
        self.assertTrue('<td>9688987</td>' in html)
        self.assertTrue('<span class="marc-subfield-value">NPU</span>' in html)

    def test_language(self):
        t = Title.objects.get(lccn='sn83030846')
        langs = list(t.languages.all())
        self.assertEqual(len(langs), 1)
        self.assertEqual(langs[0].name, 'English')

    def test_urls(self):
        t = Title.objects.get(lccn='sn83030846')
        urls = list(t.urls.all())
        self.assertEqual(len(urls), 0)

    def test_solr_doc(self):
        t = Title.objects.get(lccn='sn83030846')
        solr = t.solr_doc
        self.assertEqual(solr['place_of_publication'], u'Albany, N.Y.')
        self.assertEqual(solr['publisher'], u'The Living Issue Co.')
        self.assertEqual(solr['start_year'], 1873)
        self.assertEqual(solr['essay'], [])
        self.assertEqual(solr['title'], u'The living issue.')
        self.assertEqual(solr['lccn'], u'sn83030846')
        self.assertEqual(solr['end_year'], 1887)
        self.assertEqual(solr['type'], 'title')
        self.assertEqual(solr['id'], '/lccn/sn83030846/')
        self.assertEqual(solr['frequency'], 'Weekly')
        self.assertTrue('Cumberland' in solr['county'])
        self.assertTrue('Lancaster' in solr['county'])
        self.assertTrue('Albany' in solr['county'])
        self.assertTrue('New York' in solr['county'])
        self.assertTrue('Oneida' in solr['county'])
        self.assertTrue('Otsego' in solr['county'])
        self.assertTrue(u'English' in solr['language'])
        self.assertTrue('Description based on: Vol. 1, no. 8 (Apr. 12, 1873).' in solr['note'])
        self.assertTrue('Published as: Living issue. Prohibition, <Dec. 17, 1874>.' in solr['note'])
        self.assertTrue('Published at New York, N.Y., <1874>-1879; at Portland, Me., 1879-<1880>; at Cooperstown, N.Y., <1881-1882>; at Utica, N.Y., <1883>-Jan. 27, 1887; at Lincoln, Neb., <Feb. 1887>-' in solr['note'])
        self.assertTrue('Living issue. Prohibition' in solr['alt_title'])
        self.assertEqual('New York', solr['country'])

    def test_oclc_num(self):
        t = TitleLoader()
        t.load_file(abs_filename('./test-data/sn86069873.xml'))
        t = Title.objects.get(lccn='sn86069873')
        self.assertEqual(t.oclc, '13528482')

    def test_vague_dates(self):
        loader = TitleLoader()
        filename = abs_filename('./test-data/bib-with-vague-dates.xml')
        loader.load_file(filename)
        t = Title.objects.get(lccn='00062183')
        self.assertEqual(t.start_year_int, 1900)
        self.assertEqual(t.end_year_int, 1999)

    def test_etitle(self):
        # we shouldn't load in [electronic resource] records for 
        # chronicling america titles, since they muddle up search results
        # https://rdc.lctl.gov/trac/ndnp/ticket/375
        loader = TitleLoader()
        loader.load_file(abs_filename('./test-data/etitle.xml'))
        self.assertRaises(Title.DoesNotExist, Title.objects.get,
                          lccn='2008264012')

    def test_delete(self):
        loader = TitleLoader()
        loader.load_file(abs_filename('./test-data/title-delete.xml'))
        self.assertEqual(loader.records_deleted, 1)
        self.assertEqual(loader.records_processed, 2)
        self.assertRaises(Title.DoesNotExist, Title.objects.get,
                          lccn='sn83030846')

    def test_rda_place_of_publication(self):
        loader = TitleLoader()
        loader.load_file(abs_filename('./test-data/rda.xml'))
        self.assertEqual(loader.records_processed, 1)
        t = Title.objects.get(lccn='sn84022687')
        self.assertEqual(t.place_of_publication, 'Montpelier, Vt.')
