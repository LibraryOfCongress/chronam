import datetime

import feedparser

from django.test import TestCase
from django.conf import settings

from openoni.core.essay_loader import load_essay, purge_essay
from openoni.core.models import Essay, Title

class EssayLoaderTests(TestCase):
    fixtures = ['countries.json', 'essay_titles.json']

    def test_essay_feed(self):
        feed = feedparser.parse(settings.ESSAYS_FEED)
        self.assertTrue(len(feed.entries) > 0)

    def test_load_essay(self):
        e = load_essay('http://ndnp-essays.rdc.lctl.gov/essay/3/', index=False)
        self.assertTrue(isinstance(e, Essay))

        # is it in the db now?
        essays = Essay.objects.all()
        self.assertEqual(len(essays), 1)

        # get an essay
        title = Title.objects.get(lccn='sn83027091')
        essay = title.essays.all()[0]

        self.assertEqual(essay.title, 'Colored American')
        self.assertEqual(essay.created, datetime.datetime(2007, 1, 19, 9, 0))
        self.assertTrue(type(essay.modified), datetime.datetime)
        self.assertEqual(essay.url, '/essays/3/')
        self.assertEqual(essay.essay_editor_url, 'http://ndnp-essays.rdc.lctl.gov/essay/3/')
        self.assertEqual(essay.creator.name, 'Library of Congress, Washington, DC')
        self.assertTrue('<a href="http://chroniclingamerica.loc.gov/lccn/sn82016211/"><cite>Indianapolis Freeman</cite></a>' in essay.html)

    def test_purge_essay(self):
        self.assertEqual(Essay.objects.all().count(), 0)
        num_titles = Title.objects.all().count()

        load_essay('http://ndnp-essays.rdc.lctl.gov/essay/3/', index=False)
        self.assertEqual(Essay.objects.all().count(), 1)

        # purge it
        purge_essay('http://ndnp-essays.rdc.lctl.gov/essay/3/', index=False)
        self.assertEqual(Essay.objects.all().count(), 0)

        # same amount of titles (none should be deleted)
        self.assertEqual(Title.objects.all().count(), num_titles)
