from django.test import TestCase
import simplejson

from chronam.web.json import batch_to_json
from chronam.web import models as m

class JsonTests(TestCase):
    fixtures = ['batch.json']

    def test_speedups(self):
        # simplejson needs to have c bits comiled to be fast enough
        self.assertTrue(simplejson._speedups)

    def test_batch(self):
        b = m.Batch.objects.get(name='batch_curiv_ahwahnee_ver01')
        j = batch_to_json(b)
        x = simplejson.loads(j)
        self.assertEqual(x['name'], 'batch_curiv_ahwahnee_ver01')


