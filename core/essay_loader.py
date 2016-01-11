import re
import calendar
import logging
import datetime

import feedparser

from django.core import management
from rdflib import Graph, Namespace, URIRef

from openoni.core.index import index_title
from openoni.core.models import Essay, Title, Awardee


DC = Namespace('http://purl.org/dc/terms/')
NDNP = Namespace('http://chroniclingamerica.loc.gov/terms#')


def load_essays(feed_url, index=True):
    logging.info("loading feed %s" % feed_url)
    feed = feedparser.parse(feed_url)
    logging.info("got %s entries" % len(feed.entries))
    for e in feed.entries:
        url = e.links[0]['href']
        t = calendar.timegm(e.modified_parsed)
        modified = datetime.datetime.fromtimestamp(t)

        q = Essay.objects.filter(essay_editor_url=url)
        if q.count() == 0:
            logging.info("found a new essay: %s" % url)
            load_essay(url, index)
        elif q.filter(modified__lt=modified).count() > 0:
            logging.info("found updated essay: %s" % url)
            purge_essay(url, index)
            load_essay(url, index)
        else:
            logging.info("essay already up to date: %s" % url)


def load_essay(essay_url, index=True):
    """
    Load an essay from an RDFa HTML document.
    """
    # extract metadata from the html
    logging.info("loading essay %s" % essay_url)
    g = Graph()
    g.parse(essay_url, format='rdfa')

    # create the essay instance
    essay_uri = URIRef(essay_url)
    essay_id = _essay_id(essay_uri)
    modified = g.value(essay_uri, DC.modified).toPython()

    essay = Essay(id=essay_id)
    essay.title = unicode(g.value(essay_uri, DC.title)).strip()
    essay.created = g.value(essay_uri, DC.created).toPython()
    essay.modified = g.value(essay_uri, DC.modified).toPython()
    essay.creator = _lookup_awardee((g.value(essay_uri, DC.creator)))
    essay.html = unicode(g.value(essay_uri, DC.description))
    essay.essay_editor_url = essay_url
    essay.save()  # so we can assign titles

    # attach any titles that the essay is about
    for title_uri in g.objects(essay_uri, DC.subject):
        lccn = _lccn_from_title_uri(title_uri)

        # load titles from web if not available
        try:
            title = Title.objects.get(lccn=lccn)
        except Exception, e:
            management.call_command('load_titles', 'http://chroniclingamerica.loc.gov/lccn/%s/marc.xml' % lccn)
            title = Title.objects.get(lccn=lccn)

        # attach the title to the essay
        essay.titles.add(title)

        # index the title in solr if necessary
        if index:
            index_title(title)

    logging.info("loaded essay: %s" % essay_url)
    return essay


def purge_essay(essay_url, index=True):
    """
    Purge an essay from the database.
    """
    try:
        essay = Essay.objects.get(essay_editor_url=essay_url)
        titles = list(essay.titles.all())
        essay.delete()
        logging.info("deleted essay %s" % essay_url)

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
