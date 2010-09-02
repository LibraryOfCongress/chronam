import os
import datetime

from django.test import TestCase
from django.conf import settings

import chronam.core
from chronam.core.essay_loader import load_essay, purge_essay
from chronam.core.models import Essay, Title

class EssayLoaderTests(TestCase):
    fixtures = ['countries.json', 'essay_titles.json']

    def test_essay_storage(self):
        self.assertTrue(os.path.isdir(settings.ESSAY_STORAGE))
        self.assertTrue(not settings.ESSAY_STORAGE.endswith('/'))
        self.assertTrue(len(os.listdir(settings.ESSAY_STORAGE)) >= 189)

    def test_load_essay(self):
        e = load_essay('00003.html', index=False)
        self.assertTrue(isinstance(e, Essay))

        # is it in the db now?
        essays = Essay.objects.all()
        self.assertEqual(len(essays), 1)

        # get an essay
        title = Title.objects.get(lccn='sn83027091')
        essay = title.essays.all()[0]

        self.assertEqual(essay.title, 'Colored American')
        self.assertEqual(essay.created, datetime.datetime(2007, 1, 19, 9, 0))
        self.assertEqual(essay.url, '/essays/3/')
        self.assertEqual(essay.filename, '00003.html')
        self.assertEqual(essay.creator.name, 'Library of Congress, Washington, DC')
        self.assertTrue('<a href="http://chroniclingamerica.loc.gov/lccn/sn82016211"><cite>Indianapolis Freeman</cite></a>' in essay.html)

    def test_purge_essay(self):
        self.assertEqual(Essay.objects.all().count(), 0)
        num_titles = Title.objects.all().count()

        load_essay('00001.html', index=False)
        self.assertEqual(Essay.objects.all().count(), 1)

        # purge it
        purge_essay('00001.html', index=False)
        self.assertEqual(Essay.objects.all().count(), 0)

        # same amount of titles (none should be deleted)
        self.assertEqual(Title.objects.all().count(), num_titles)
