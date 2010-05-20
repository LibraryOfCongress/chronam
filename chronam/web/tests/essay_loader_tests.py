import os
import datetime

from django.test import TestCase

import chronam.web
from chronam.web.essay_loader import EssayLoader
from chronam.web.models import Essay, Title
from chronam import settings

class EssayLoaderTests(TestCase):
    fixtures = ['essay_titles.json']

    def test_essay_storage(self):
        self.assertTrue(os.path.isdir(settings.ESSAY_STORAGE))
        self.assertTrue(not settings.ESSAY_STORAGE.endswith('/'))

    def test_load_essay_batch(self):
        loader = EssayLoader()
        batch_dir = os.path.join(settings.ESSAY_STORAGE, 
                                 'batch_encyclopedia_20071031_arcturus')
        loader.load(batch_dir, index=False)

        # see if we loaded as many as we thought
        self.assertEqual(len(loader.creates), 12)

        # are they in the db
        essays = Essay.objects.all()
        self.assertEqual(len(essays), 12)

        # get an essay
        title = Title.objects.get(lccn='sn83027091')
        essay = title.essays.all()[0]

        # is the created correct?
        self.assertEqual(essay.created, datetime.datetime(2007, 1, 19, 9, 0))

        # is the url ok?
        self.assertEqual(essay.url, '/lccn/sn83027091/essays/20070119090000/')

        # is the mets file populated?
        self.assertEqual(essay.mets_file, 'batch_encyclopedia_20071031_arcturus/encyclopedia/sn83027091_1.xml')

        # compare the html
        essay_file = os.path.join(os.path.dirname(chronam.web.__file__), 
            'test-data', 'essay.html')
        expected_essay_html = file(essay_file).read().decode('utf-8')
        self.assertEqual(essay.html, expected_essay_html)

        div = essay.div
        self.assertTrue('xhtml' not in div)
        self.assertTrue('<a href="/lccn/sn82016211"><cite>Indianapolis Freeman</cite></a>' in div)

    def test_purge_essay_batch(self):
        self.assertEqual(Essay.objects.all().count(), 0)
        num_titles = Title.objects.all().count()

        # load a batch of essays
        loader = EssayLoader()
        batch_dir = os.path.join(settings.ESSAY_STORAGE, 
                                 'batch_encyclopedia_20071031_arcturus')
        loader.load(batch_dir, index=False)
        self.assertEqual(Essay.objects.all().count(), 12)

        # purge the batch
        loader.purge(batch_dir, index=False)
        self.assertEqual(Essay.objects.all().count(), 0)

        # same amount of titles (none deleted)
        self.assertEqual(Title.objects.all().count(), num_titles)

    def test_essay_delete(self):
        loader = EssayLoader()
        batch_dir = os.path.join(settings.ESSAY_STORAGE, 
                                 'batch_encyclopedia_20071031_arcturus')
        loader.load(batch_dir, index=False)

        title = Title.objects.get(lccn='sn83027091')

        essays = title.essays.all()
        self.assertEqual(len(essays), 1)
        
        essay = essays[0]
        essay.delete()

        # delete of the essay shouldn't delete the title it is attached to
        self.assertTrue(Title.objects.get(lccn='sn83027091'))

    def test_multiple_titles(self):
        loader = EssayLoader()
        batch_dir = os.path.join(settings.ESSAY_STORAGE, 
                                 'batch_encyclopedia_20070808_barnard')
        loader.load(batch_dir, index=False)
        title = Title.objects.get(lccn='sn82016351')
        essay = title.essays.all()[0]

        titles = essay.titles.order_by('lccn')
        self.assertEqual(len(titles), 3)
        self.assertEqual(titles[0].lccn, 'sn82016351')
        self.assertEqual(titles[1].lccn, 'sn82016352')
        self.assertEqual(titles[2].lccn, 'sn82016353')

    def test_load_dupe(self):
        loader = EssayLoader()

        batch_dir = os.path.join(settings.ESSAY_STORAGE,
                                 'batch_encyclopedia_20070808_barnard')
        loader.load(batch_dir, index=False)
        title = Title.objects.get(lccn='sn86069325')
        self.assertTrue(title.has_essays())
        self.assertEqual(len(title.essays.all()), 1)

        loader = EssayLoader()
        batch_dir = os.path.join(settings.ESSAY_STORAGE,
                                 'batch_encyclopedia_20071031_barnard')
        loader.load(batch_dir, index=False)
        title = Title.objects.get(lccn='sn86069325')
        self.assertTrue(title.has_essays())
        self.assertEqual(len(title.essays.all()), 1)

