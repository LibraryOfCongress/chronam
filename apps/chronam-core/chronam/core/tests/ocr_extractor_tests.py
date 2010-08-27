from os.path import dirname, join

from django.test import TestCase

from chronam.core.ocr_extractor import ocr_extractor


class OcrExtractorTests(TestCase):

    def test_extractor(self):
        dir = join(dirname(dirname(__file__)), 'test-data')
        ocr_file = join(dir, 'ocr.xml')
        text, coords = ocr_extractor(ocr_file)
        expected_text = file(join(dir, 'ocr.txt')).read().decode('utf-8')
        self.assertEqual(text, expected_text)
        self.assertEqual(len(coords.keys()), 2196)
        self.assertEqual(len(coords['place']), 3)
        # Craft. should be normalized to Craft
        # since Solr's highlighting will not include
        # trailing punctuation in highlighted text
        self.assertTrue(coords.has_key('Craft'))
        self.assertTrue(not coords.has_key('Craft.'))
