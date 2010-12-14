import os
import re
import logging

from django.conf import settings
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

from chronam.core.index import index_title
from chronam.core.models import Essay, Title, Awardee

_logger = logging.getLogger(__name__)

DC = Namespace('http://purl.org/dc/terms/')
NDNP = Namespace('http://chroniclingamerica.loc.gov/terms#')


def load_essay(essay_file, index=True):
    """
    Load an essay from a file.
    """
    # make sure the essay file hasn't been loaded before
    if Essay.objects.filter(filename=essay_file).count() > 0:
        raise Exception("Essay file %s already loaded, try purging it first")

    # figure out the id for the essay
    path = os.path.join(settings.ESSAY_STORAGE, essay_file)

    # extract metadata from the html
    g = Graph()
    g.parse(path, format='rdfa')

    # determine the essay uri
    essay_uri = _essay_uri(essay_file)

    # create the essay instance 
    essay_id = _essay_id(essay_uri)

    essay = Essay(id=essay_id)
    essay.title = unicode(g.value(essay_uri, DC.title)).strip()
    essay.created = g.value(essay_uri, DC.created).toPython()
    essay.creator = _lookup_awardee((g.value(essay_uri, DC.creator)))
    essay.html = unicode(g.value(essay_uri, DC.description))
    essay.filename = essay_file
    essay.save() # so we can assign titles

    # attach any titles that the essay is about
    for title_uri in g.objects(essay_uri, DC.subject):
        lccn = _lccn_from_title_uri(title_uri)
        try:
            title = Title.objects.get(lccn=lccn)
            essay.titles.add(title)

            # index the title in solr if necessary
            if index:
                index_title(title)

        except Title.DoesNotExist, e:
            raise Exception("title with lccn=%s is not loaded" % lccn)

    _logger.info("loaded essay: %s" % essay.id)
    return essay

    
def purge_essay(essay_file, index=True):
    """
    Purge an essay from the database.
    """
    try:
        essay = Essay.objects.get(filename=essay_file)
        titles = list(essay.titles.all())
        essay.delete()
        _logger.info("deleted essay %s" % essay_file)
        
        # reindex titles
        if index:
            for title in titles:
                index_title(title)

    except Essay.DoesNotExist:
        raise Exception("No such essay loaded with filename=%s" % essay_file)


def _essay_uri(html_file):
    path, ext = os.path.splitext(os.path.basename(html_file))
    path = int(path) # i.e. turn 00012 into 12
    return URIRef('http://chroniclingamerica.loc.gov/essays/%s/' % path)

def _essay_id(essay_uri):
    return int(re.search(r'/essays/(\d+)/', essay_uri).group(1))

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
