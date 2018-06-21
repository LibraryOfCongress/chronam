import calendar
import datetime
import feedparser
import logging
import re
import requests
import urlparse

from bs4 import BeautifulSoup

from django.core import management

from chronam.core.index import index_title
from chronam.core.models import Essay, Title, Awardee

LOGGER = logging.getLogger(__name__)


def load_essays(feed_url, index=True):
    LOGGER.info("loading feed %s" % feed_url)
    feed = feedparser.parse(feed_url)
    LOGGER.info("got %s entries" % len(feed.entries))
    for e in feed.entries:
        url = e.links[0]['href']
        t = calendar.timegm(e.modified_parsed)
        modified = datetime.datetime.fromtimestamp(t)

        q = Essay.objects.filter(essay_editor_url=url)
        if q.count() == 0:
            LOGGER.info("found a new essay: %s" % url)
            load_essay(url, index)
        elif q.filter(modified__lt=modified).count() > 0:
            LOGGER.info("found updated essay: %s" % url)
            purge_essay(url, index)
            load_essay(url, index)
        else:
            LOGGER.info("essay already up to date: %s" % url)


def load_essay(essay_url, index=True):
    """
    Load an essay from an RDFa HTML document.
    """
    # extract metadata from the html
    LOGGER.info("loading essay %s" % essay_url)

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
        except Exception:  # FIXME: this should only handle expected exceptions
            management.call_command('load_titles', 'http://chroniclingamerica.loc.gov/lccn/%s/marc.xml' % lccn)
            title = Title.objects.get(lccn=lccn)

        # attach the title to the essay
        essay.titles.add(title)

        # index the title in solr if necessary
        if index:
            index_title(title)

    LOGGER.info("loaded essay: %s" % essay_url)
    return essay


def purge_essay(essay_url, index=True):
    """
    Purge an essay from the database.
    """
    try:
        essay = Essay.objects.get(essay_editor_url=essay_url)
        titles = list(essay.titles.all())
        essay.delete()
        LOGGER.info("deleted essay %s" % essay_url)

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
