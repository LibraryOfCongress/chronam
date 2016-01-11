from django.test import TestCase
from django.conf import settings
from django.http import QueryDict as Q

from openoni.core.index import page_search, title_search, find_words, \
                              _solrize_date


class IndexTests(TestCase):
    """
    Exercise some search form -> solr query translations
    """
    fixtures = ['ethnicities.json']
    ocr_langs = ['ocr_%s' %l for l in settings.SOLR_LANGUAGES]

    def test_page_search_lccn(self):
        self.assertEqual(page_search(Q('lccn=sn83030214'))[0], 
            '+type:page +lccn:("sn83030214")')
        self.assertEqual(page_search(Q('lccn=sn83030214&lccn=sn83030215'))[0],
            '+type:page +lccn:("sn83030214" "sn83030215")')

    def test_page_search_state(self):
        self.assertEqual(page_search(Q('state=California'))[0],
            '+type:page +state:("California")')
        self.assertEqual(page_search(Q('state=California&state=New Jersey'))[0],
            '+type:page +state:("California" "New Jersey")')

    def test_page_search_year(self):
        self.assertEqual(page_search(Q('dateFilterType=year&year=1900'))[0], 
            '+type:page +year:[1900 TO 1900]')

    def test_page_search_date_range(self):
        self.assertEqual(
            page_search(Q('dateFilterType=range&date1=10/25/1901&date2=10/31/1901'))[0],
            '+type:page +date:[19011025 TO 19011031]')

    def test_page_search_ortext(self):
        q = ' OR '.join(['%s:("apples" "oranges")' % lang for lang in self.ocr_langs])
        self.assertEqual(page_search(Q('ortext=apples%20oranges'))[0], u'+type:page +((ocr:("apples" "oranges")^10000 ) OR %s )' % q)

    def test_page_search_andtext(self):
        q = ' OR '.join(['%s:(+"apples" +"oranges")' % lang for lang in self.ocr_langs])
        self.assertEqual(page_search(Q('andtext=apples%20oranges'))[0], u'+type:page +((ocr:(+"apples" +"oranges")^10000 ) OR %s )' % q)

    def test_page_search_phrase(self):
        q = ' OR '.join(['%s:"new york yankees"' % lang for lang in self.ocr_langs])
        self.assertEqual(page_search(Q('phrasetext=new%20york%20yankees'))[0], u'+type:page +((ocr:"new york yankees"^10000 ) OR %s )' % q)

    def test_page_search_proxtext(self):
        q = ' OR '.join(['%s:"apples oranges"~10' % lang for lang in self.ocr_langs])
        self.assertEqual(page_search(Q('proxtext=apples%20oranges&proxdistance=10'))[0], u'+type:page +((ocr:("apples oranges"~10)^10000 ) OR %s )' %q)
        q = ' OR '.join(['%s:"apples oranges"~5' % lang for lang in self.ocr_langs])
        self.assertEqual(page_search(Q('proxtext=apples%20oranges'))[0], u'+type:page +((ocr:("apples oranges"~5)^10000 ) OR %s )' %q)

    def test_page_search_language(self):
        self.assertEqual(page_search(Q('proxtext=apples%20oranges&language=eng'))[0], '+type:page +((ocr:("apples oranges"~5)^10000 AND ocr_eng:"apples oranges"~5 ) OR ocr_eng:"apples oranges"~5 )')

    def test_find_words(self):
        hl = "Today <em>is</em> the <em>greatest</em> day i've <em>ever</em> known\nCan't wait <em>for</em> tomorrow ..."
        self.assertEqual(find_words(hl), ['is', 'greatest', 'ever',
            'for'])

    def test_title_search(self):
        self.assertEqual(
            title_search(Q('terms=bloody'))[0], 
            '+type:title +(title:"bloody" OR essay:"bloody" OR note:"bloody" OR edition:"bloody" OR place_of_publication:"bloody" OR url:"bloody" OR publisher:"bloody")')

    def test_ethnicity_query(self):
        self.assertEqual(title_search(Q('ethnicity=Anabaptist'))[0], 
                '+type:title +(subject:"Anabaptist" OR subject:"Amish" OR subject:"Amish Mennonites" OR subject:"Mennonites" OR subject:"Pennsylvania Dutch" OR subject:"Pennsylvania Dutch.")')

    def test_solrize_date(self):
        self.assertEqual(_solrize_date('03/01/1900'), 19000301)
        self.assertEqual(_solrize_date('01/1900'), 19000101)
        self.assertEqual(_solrize_date('01/1900', is_start=False), 19000131)
        self.assertEqual(_solrize_date('1900'), 19000101)
        self.assertEqual(_solrize_date('1900', is_start=False), 19001231)
        self.assertEqual(_solrize_date('1/01/1900'), 19000101)
