import json

from django.test import TestCase


class ApiTests(TestCase):
    """Tests the current API. Note URLs are hardwired instead of dynamic
    using names from urls.py to help notice when we break our contract with
    clients outside of LC.
    """

    fixtures = ['countries.json', 'titles.json',
                'awardee.json', 'batch.json', 'issue.json',
                'page.json']

    def test_newspaper_json(self):
        r = self.client.get("/newspapers.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(len(j['newspapers']), 1)
        self.assertEqual(j['newspapers'][0]['lccn'], 'sn83030214')
        self.assertEqual(j['newspapers'][0]['state'], 'New York')
        self.assertEqual(j['newspapers'][0]['title'], 'New-York tribune.')
        self.assertTrue(j['newspapers'][0]['url'].endswith('/lccn/sn83030214.json'))

    def test_title_json(self):
        r = self.client.get("/lccn/sn83030214.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(j['place_of_publication'], 'New York [N.Y.]')
        self.assertEqual(j['lccn'], 'sn83030214')
        self.assertEqual(j['start_year'], '1866')
        self.assertEqual(j['place'][0], 'New York--Brooklyn--New York City')
        self.assertEqual(j['name'], 'New-York tribune.')
        self.assertTrue(j['url'].endswith('/lccn/sn83030214.json'))
        self.assertEqual(j['subject'][0], 'New York (N.Y.)--Newspapers.')
        self.assertEqual(j['issues'][0]['date_issued'], '1898-01-01')

    def test_issue_json(self):
        r = self.client.get("/lccn/sn83030214/1898-01-01/ed-1.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertTrue(j['url'].endswith('/lccn/sn83030214/1898-01-01/ed-1.json'))
        self.assertTrue(j['title']['url'].endswith('/lccn/sn83030214.json'))
        self.assertEqual(j['title']['name'], 'New-York tribune.')
        self.assertEqual(j['date_issued'], '1898-01-01')
        self.assertEqual(j['volume'], '83')
        self.assertEqual(j['number'], '32')
        self.assertEqual(j['edition'], 1)
        self.assertEqual(j['pages'][0]['sequence'], 1)
        self.assertTrue(j['pages'][0]['url'].endswith('/lccn/sn83030214/1898-01-01/ed-1/seq-1.json'))

    def test_page_json(self):
        r = self.client.get("/lccn/sn83030214/1898-01-01/ed-1/seq-1.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertTrue(j['jp2'].endswith('/lccn/sn83030214/1898-01-01/ed-1/seq-1.jp2'))
        self.assertTrue(j['ocr'].endswith('/lccn/sn83030214/1898-01-01/ed-1/seq-1/ocr.xml'))
        self.assertTrue(j['pdf'].endswith('/lccn/sn83030214/1898-01-01/ed-1/seq-1.pdf'))
        self.assertTrue(j['text'].endswith('/lccn/sn83030214/1898-01-01/ed-1/seq-1/ocr.txt'))
        self.assertEqual(j['sequence'], 1)
        self.assertEqual(j['title']['name'], 'New-York tribune.')
        self.assertTrue(j['title']['url'].endswith('/lccn/sn83030214.json'))
        self.assertTrue(j['issue']['date_issued'], '1898-01-01')
        self.assertTrue(j['issue']['url'].endswith('/lccn/sn83030214/1898-01-01/ed-1.json'))

    def test_batch_json(self):
        r = self.client.get("/batches/batch_curiv_ahwahnee_ver01.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(j['name'], 'batch_curiv_ahwahnee_ver01')
        self.assertEqual(j['page_count'], 1)
        self.assertEqual(j['awardee']['name'], 'University of California, Riverside')
        self.assertTrue(j['awardee']['url'].endswith('/awardees/curiv.json'))
        self.assertEqual(j['lccns'], ['sn83030214'])
        self.assertTrue(j['ingested'].startswith('2009-03-26T20:59:28'))
        self.assertEqual(j['issues'][0]['date_issued'], '1898-01-01')
        self.assertTrue(j['issues'][0]['url'].endswith('/lccn/sn83030214/1898-01-01/ed-1.json'))
        self.assertEqual(j['issues'][0]['title']['name'], 'New-York tribune.')
        self.assertTrue(j['issues'][0]['title']['url'].endswith('/lccn/sn83030214.json'))

    def test_awardee_json(self):
        r = self.client.get("/awardees/curiv.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(j['name'], 'University of California, Riverside')
        self.assertTrue(j['url'].endswith('/awardees/curiv.json'))
        self.assertTrue(j['batches'][0]['url'].endswith('/batches/batch_curiv_ahwahnee_ver01.json'))
        self.assertEqual(j['batches'][0]['name'], 'batch_curiv_ahwahnee_ver01')

    def test_batches_json(self):
        r = self.client.get("/batches.json")
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(len(j['batches']), 1)
        b = j['batches'][0]
        self.assertEqual(b['name'], 'batch_curiv_ahwahnee_ver01')
        self.assertTrue(b['url'].endswith('/batches/batch_curiv_ahwahnee_ver01.json'))
        self.assertEqual(b['page_count'], 1)
        self.assertEqual(b['lccns'], ['sn83030214'])
        self.assertEqual(b['awardee']['name'], 'University of California, Riverside')
        self.assertTrue(b['awardee']['url'].endswith('/awardees/curiv.json'))

        self.assertTrue(b['ingested'].startswith('2009-03-26T20:59:28'))

    # TODO: test conneg on JSON views
    # TODO: test RDF views?
