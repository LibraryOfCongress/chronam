from os.path import dirname, join

from django.test import TestCase

from chronam.core.ocr_extractor import ocr_extractor


class OcrExtractorTests(TestCase):
    def test_extractor(self):
        dir = join(dirname(dirname(__file__)), "test-data")
        ocr_file = join(dir, "ocr.xml")
        text, coord_info = ocr_extractor(ocr_file)
        coords = coord_info["coords"]
        expected_text = {"eng": open(join(dir, "ocr.txt")).read().decode("utf-8")}

        self.assertEqual(text, expected_text)
        self.assertEqual(len(coords.keys()), 2489)
        self.assertEqual(len(coords["place"]), 3)
