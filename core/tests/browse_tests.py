import os

from django.test import TestCase
from django.db import connection
from django.conf import settings

from chronam.core.index import get_page_text
from chronam.core.utils.utils import _get_tip
from chronam.core.batch_loader import BatchLoader, Batch
from chronam.core.models import Title


class BrowseTests(TestCase):
    """
    Tests related to core/views/browse.py
    """
    fixtures = ['countries.json', 'languages.json', 'awardee.json']

    def test_full_text_deleted(self):
        #'sanity' check that 'text' column is removed
        with connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM core_languagetext")
            rows = cursor.fetchall()
            for row in rows:
                if row[0] == 'text':
                    self.fail("core_languagetext.text should not exist. "
                              "Did you run the migrations?")

    def test_getting_text_from_solr_utah(self):
        """
        tests get_page_text() with batch batch_uuml_thys_ver01.
        First creates a page object 'page' with _get_tip()
        then uses it as an argument to get_page_text()
        """
        batch_dir = os.path.join(settings.BATCH_STORAGE, 'batch_uuml_thys_ver01')
        self.assertTrue(os.path.isdir(batch_dir))
        loader = BatchLoader(process_ocr=False)
        batch = loader.load_batch(batch_dir)
        self.assertEqual(batch.name, 'batch_uuml_thys_ver01')
        title, issue, page = _get_tip('sn83045396', '1911-09-17', 1, 1)
        text = get_page_text(page)
        self.assertIn("Uc nice at tlio slate fair track", text[0])
        self.assertIn("PAGES FIVE CENTS", text[0])
        self.assertIn('gBter ho had left the grounds that', text[0])

        # purge the batch and make sure it's gone from the db
        loader.purge_batch('batch_uuml_thys_ver01')
        self.assertEqual(Batch.objects.all().count(), 0)
        self.assertEqual(Title.objects.get(lccn='sn83045396').has_issues, False)

    def test_getting_text_from_solr_slovenia(self):
        """
        tests get_page_text() with batch batch_iune_oriole_ver01.
        First creates a page object 'page' with _get_tip()
        then uses it as an argument to get_page_text()
        """
        batch_dir = os.path.join(settings.BATCH_STORAGE, 'batch_iune_oriole_ver01')
        self.assertTrue(os.path.isdir(batch_dir))
        loader = BatchLoader(process_ocr=False)
        batch = loader.load_batch(batch_dir)
        self.assertEqual(batch.name, 'batch_iune_oriole_ver01')
        title, issue, page = _get_tip('sn83045377', '1906-03-01', 1, 1)
        text = get_page_text(page)
        self.assertIn("Od Mizo in dale", text[0])
        self.assertIn("To je preecj inoettii tobak! Marsi", text[0])

        # purge the batch and make sure it's gone from the db
        loader.purge_batch('batch_iune_oriole_ver01')
        self.assertEqual(Batch.objects.all().count(), 0)
        self.assertEqual(Title.objects.get(lccn='sn83045377').has_issues, False)