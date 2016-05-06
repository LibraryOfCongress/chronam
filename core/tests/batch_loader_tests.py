from datetime import date
import os

from django.test import TestCase
from django.conf import settings

import chronam.core
from chronam.core.batch_loader import BatchLoader
from chronam.core.models import Title
from chronam.core.models import Batch


class BatchLoaderTest(TestCase):
    fixtures = ['countries.json', 'languages.json', 'awardee.json']

    def test_load_batch(self):
        batch_dir = os.path.join(settings.BATCH_STORAGE, 'batch_uuml_thys_ver01')
        self.assertTrue(os.path.isdir(batch_dir))
        loader = BatchLoader(process_ocr=False)
        batch = loader.load_batch(batch_dir)
        self.assertTrue(isinstance(batch, Batch))
        self.assertEqual(batch.name, 'batch_uuml_thys_ver01')
        self.assertEqual(len(batch.issues.all()), 2)

        title = Title.objects.get(lccn = 'sn83045396')
        self.assertTrue(title.has_issues)

        issue = batch.issues.all()[0]
        self.assertEqual(issue.volume, '83')
        self.assertEqual(issue.number, '156')
        self.assertEqual(issue.edition, 1)
        self.assertEqual(issue.title.lccn, 'sn83045396')
        self.assertEqual(date.strftime(issue.date_issued, '%Y-%m-%d'), 
            '1911-09-17')
        self.assertEqual(len(issue.pages.all()), 56)

        page = issue.pages.all()[0]
        self.assertEqual(page.sequence, 1)
        self.assertEqual(page.url, u'/lccn/sn83045396/1911-09-17/ed-1/seq-1/')

        note = page.notes.all()[1]
        self.assertEqual(note.type, "agencyResponsibleForReproduction")
        self.assertEqual(note.text, "uuml")

        self.assertEqual(page.sequence, 1)
        self.assertEqual(page.tiff_filename, 'sn83045396/print/1911091701/0001.tif')
        self.assertEqual(page.jp2_filename, 'sn83045396/print/1911091701/0001.jp2')
        self.assertEqual(page.jp2_length, 8736)
        self.assertEqual(page.jp2_width, 6544)
        self.assertEqual(page.ocr_filename, 'sn83045396/print/1911091701/0001.xml')
        self.assertEqual(page.pdf_filename, 'sn83045396/print/1911091701/0001.pdf')

        # extract ocr data just for this page
        loader.process_ocr(page, index=False)
        self.assertTrue(page.ocr != None)
        self.assertTrue(len(page.ocr.text) > 0)

        p = Title.objects.get(lccn='sn83045396').issues.all()[0].pages.all()[0]
        self.assertTrue(p.ocr != None)

        # check that the solr_doc looks legit
        solr_doc = page.solr_doc
        self.assertEqual(solr_doc['id'], '/lccn/sn83045396/1911-09-17/ed-1/seq-1/')
        self.assertEqual(solr_doc['type'], 'page')
        self.assertEqual(solr_doc['sequence'], 1)
        self.assertEqual(solr_doc['lccn'], 'sn83045396')
        self.assertEqual(solr_doc['title'], 'The Salt Lake tribune.')
        self.assertEqual(solr_doc['date'], '19110917')
        self.assertEqual(solr_doc['batch'], 'batch_uuml_thys_ver01')
        self.assertEqual(solr_doc['subject'], [
            u'Salt Lake City (Utah)--Newspapers.', 
            u'Utah--Salt Lake City.--fast--(OCoLC)fst01205314'])
        self.assertEqual(solr_doc['place'], [
            u'Utah--Salt Lake--Salt Lake City'])
        self.assertEqual(solr_doc['note'], [
            u'Archived issues are available in digital format as part of the Library of Congress Chronicling America online collection.', 
            u'Continues the numbering of: Salt Lake daily tribune.', 
            u'Other eds.: Salt Lake tribune (Salt Lake City, Utah : Idaho ed.), 1954-1973, and: Salt Lake tribune (Salt Lake City, Utah : Metropolitan ed.), 1960-1972, and: Salt Lake tribune (Salt Lake City, Utah : State ed.), 1954-1974.', 
            u'Publisher varies.', 
            u'Semiweekly ed.: Salt Lake semi-weekly tribune, 1894-1902.', 
            u'Weekly ed.: Salt Lake weekly tribune (Salt Lake City, Utah : 1902), 1902-< >.'])
        self.assertTrue(not solr_doc.has_key('essay'))

        f = os.path.join(os.path.dirname(chronam.core.__file__), 'test-data', 
            'uuml_thys_ocr.txt')
        self.assertEqual(solr_doc['ocr_eng'], file(f).read().decode('utf-8'))


        # purge the batch and make sure it's gone from the db
        loader.purge_batch('batch_uuml_thys_ver01')
        self.assertEqual(Batch.objects.all().count(), 0)
        self.assertEqual(Title.objects.get(lccn='sn83045396').has_issues, False)
