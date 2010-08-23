from django.test import TestCase

try:
    import simplejson as json
except ImportError:
    import json

from chronam.web.json_helper import batch_to_json
from chronam.core import models as m

class JsonTests(TestCase):
    fixtures = ['batch.json']

    def test_speedups(self):
        # simplejson needs to have c bits comiled to be fast enough
        self.assertTrue(json._speedups)

    def test_batch(self):
        b = m.Batch.objects.get(name='batch_curiv_ahwahnee_ver01')
        j = batch_to_json(b)
        x = json.loads(j)
        self.assertEqual(x['name'], 'batch_curiv_ahwahnee_ver01')


