import os

from django.conf import settings
from django.db import connection
from django.test import TestCase

from chronam.core.batch_loader import Batch, BatchLoader
from chronam.core.index import get_page_text
from chronam.core.models import Title
from chronam.core.utils.utils import _get_tip


class BrowseTests(TestCase):
    """
    Tests related to core/views/browse.py
    """

    fixtures = ["countries.json", "languages.json", "awardee.json"]

    def test_words_redirect(self):
        """
        the url /lccn/sn85066387/1907-03-17/ed-1/seq-4/;words=foo
        should redirect to /lccn/sn85066387/1907-03-17/ed-1/seq-4/#words=foo
        """
        r = self.client.get("/lccn/sn83045396/1911-09-17/ed-1/seq-12/;words=foo")
        self.assertEquals(r.status_code, 302)
        self.assertIn("/lccn/sn83045396/1911-09-17/ed-1/seq-12/#words=foo", r.url)

    def test_query_preserved(self):
        """
        query parameters should be preserved for page
        ex: /lccn/sn85066387/1907-03-17/ed-1/seq-4/;words=foo?bar=ham
        should redirect to /lccn/sn85066387/1907-03-17/ed-1/seq-4/?bar=ham#words=foo
        This is needed so that campaign codes work properly
        """
        r = self.client.get("/lccn/sn83045396/1911-09-17/ed-1/seq-12/;words=foo?bar=ham")
        self.assertEquals(r.status_code, 302)
        self.assertIn("/lccn/sn83045396/1911-09-17/ed-1/seq-12/?bar=ham#words=foo", r.url)

    def test_full_text_deleted(self):
        # 'sanity' check that 'text' column is removed
        with connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM core_languagetext")
            rows = cursor.fetchall()
            for row in rows:
                if row[0] == "text":
                    self.fail("core_languagetext.text should not exist. " "Did you run the migrations?")

    def test_getting_text_from_solr_utah(self):
        """
        tests get_page_text() with batch batch_uuml_thys_ver01.
        First creates a page object 'page' with _get_tip()
        then uses it as an argument to get_page_text()
        """
        batch_dir = os.path.join(settings.BATCH_STORAGE, "batch_uuml_thys_ver01")
        self.assertTrue(os.path.isdir(batch_dir))
        loader = BatchLoader(process_ocr=True)
        batch = loader.load_batch(batch_dir)
        self.assertEqual(batch.name, "batch_uuml_thys_ver01")
        title, issue, page = _get_tip("sn83045396", "1911-09-17", 1, 1)
        text = get_page_text(page)
        self.assertIn("Uc nice at tlio slate fair track", text[0])
        self.assertIn("PAGES FIVE CENTS", text[0])
        self.assertIn("gBter ho had left the grounds that", text[0])

        # purge the batch and make sure it's gone from the db
        loader.purge_batch("batch_uuml_thys_ver01")
        self.assertEqual(Batch.objects.all().count(), 0)
        self.assertEqual(Title.objects.get(lccn="sn83045396").has_issues, False)

    def test_getting_text_from_solr_slovenia(self):
        """
        tests get_page_text() with batch batch_iune_oriole_ver01.
        First creates a page object 'page' with _get_tip()
        then uses it as an argument to get_page_text()
        """
        batch_dir = os.path.join(settings.BATCH_STORAGE, "batch_iune_oriole_ver01")
        self.assertTrue(os.path.isdir(batch_dir))
        loader = BatchLoader(process_ocr=True)
        batch = loader.load_batch(batch_dir)
        self.assertEqual(batch.name, "batch_iune_oriole_ver01")
        title, issue, page = _get_tip("sn83045377", "1906-03-01", 1, 1)
        text = get_page_text(page)
        self.assertIn("Od Mizo in dale", text[0])
        self.assertIn("To je preecj inoettii tobak! Marsi", text[0])

        # purge the batch and make sure it's gone from the db
        loader.purge_batch("batch_iune_oriole_ver01")
        self.assertEqual(Batch.objects.all().count(), 0)
        self.assertEqual(Title.objects.get(lccn="sn83045377").has_issues, False)
