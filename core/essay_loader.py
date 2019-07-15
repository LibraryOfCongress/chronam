# -*- coding: utf-8 -*-

import calendar
import datetime
import io
import logging
import re
import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from django.core import management

from chronam.core.index import index_title
from chronam.core.models import Awardee, Essay, Title

LOGGER = logging.getLogger(__name__)


def fetch_feed(feed_url, timeout=120):
    """
    feedparse does not have network timeout support and the upstream
    maintainer recommends using a dedicated network client instead — see
    https://github.com/kurtmckee/feedparser/pull/80#issuecomment-449543486 –
    so we'll load the feed using requests and pass the response to feedparser.

    120 seconds was selected based on the default response time of ~45 seconds(!)
    """
    LOGGER.debug("Fetching feed %s", feed_url)

    response = requests.get(feed_url, timeout=timeout)
    response.raise_for_status()

    LOGGER.debug("Parsing feed %s", feed_url)
    feed_bytes = io.BytesIO(response.content)
    feed = feedparser.parse(feed_bytes)

    LOGGER.info("Loaded %d entries from %s", len(feed.entries), feed_url)

    return feed


def load_essays(feed_url, index=True):
    feed = fetch_feed(feed_url)

    for e in feed.entries:
        url = e.links[0]['href']
        t = calendar.timegm(e.modified_parsed)
        modified = datetime.datetime.fromtimestamp(t)

        q = Essay.objects.filter(essay_editor_url=url)
        if q.count() == 0:
            LOGGER.info("found a new essay: %s", url)
            load_essay(url, index)
        elif q.filter(modified__lt=modified).count() > 0:
            LOGGER.info("found updated essay: %s", url)
            purge_essay(url, index)
            load_essay(url, index)
        else:
            LOGGER.info("essay already up to date: %s", url)


def load_essay(essay_url, index=True):
    """
    Load an essay from an RDFa HTML document.
    """
    # extract metadata from the html
    LOGGER.info("loading essay %s", essay_url)

    # create the essay instance
    url_parts = urlparse.urlparse(essay_url)
    essay_id = url_parts[2].split("/")[2]

    r = requests.get(essay_url)
    doc = BeautifulSoup(r.text, 'html.parser')

    essay = Essay(id=essay_id)
    essay.title = doc.title.text.strip()
    essay.created = doc.find_all(property="dcterms:created")[0]['content']
    essay.modified = doc.find_all(property="dcterms:modified")[0]['content']
    essay.creator = _lookup_awardee(doc.find_all(property="dcterms:creator")[0]['content'])
    description = doc.find_all(property="dcterms:description")[0]
    description = ''.join(map(str, description.contents))
    essay.html = description
    essay.essay_editor_url = essay_url
    essay.save()  # so we can assign titles

    # attach any titles that the essay is about
    for title_uri in doc.find_all(property="dcterms:subject"):
        lccn = _lccn_from_title_uri(title_uri['content'])

        # load titles from web if not available
        try:
            title = Title.objects.get(lccn=lccn)
        except Title.DoesNotExist:
            management.call_command(
                "load_titles", "https://chroniclingamerica.loc.gov/lccn/%s/marc.xml" % lccn
            )
            title = Title.objects.get(lccn=lccn)

        # attach the title to the essay
        essay.titles.add(title)

        # index the title in solr if necessary
        if index:
            index_title(title)

    LOGGER.info("loaded essay: %s", essay_url)
    return essay


def purge_essay(essay_url, index=True):
    """
    Purge an essay from the database.
    """
    try:
        essay = Essay.objects.get(essay_editor_url=essay_url)
        titles = list(essay.titles.all())
        essay.delete()
        LOGGER.info("deleted essay %s", essay_url)

        # reindex titles
        if index:
            for title in titles:
                index_title(title)

    except Essay.DoesNotExist:
        raise Exception("No such essay loaded from %s" % essay_url)


def _essay_id(essay_uri):
    return int(re.search(r'/essay/(\d+)/', essay_uri).group(1))


def _lccn_from_title_uri(title_uri):
    m = re.search('/lccn/(.+)#title', title_uri)
    lccn = m.group(1)
    return lccn


def _lookup_awardee(awardee_uri):
    m = re.search('/awardees/(.+)#awardee', awardee_uri)
    if not m:
        raise Exception("Wrong awardee URI: %s" % awardee_uri)
    code = m.group(1)

    try:
        awardee = Awardee.objects.get(org_code=code)
    except Awardee.DoesNotExist:
        raise Exception("Unknown awardee with organization code: %s" % code)

    return awardee
