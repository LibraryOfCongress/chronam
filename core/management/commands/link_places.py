from __future__ import absolute_import

import logging
import urllib2

from django.db import reset_queries
from rdflib import ConjunctiveGraph, Namespace, URIRef

from chronam.core import models

from . import LoggingCommand

try:
    import simplejson as json
except ImportError:
    import json


LOGGER = logging.getLogger(__name__)

geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
owl = Namespace('http://www.w3.org/2002/07/owl#')
dbpedia = Namespace('http://dbpedia.org/ontology/')


class Command(LoggingCommand):
    def handle(self, **options):
        LOGGER.debug("linking places")
        for place in models.Place.objects.filter(dbpedia__isnull=True):
            if not place.city or not place.state:
                continue

            # formulate a dbpedia place uri
            path = urllib2.quote('%s,_%s' % (_clean(place.city), _clean(place.state)))
            url = URIRef('http://dbpedia.org/resource/%s' % path)

            # attempt to get a graph from it
            graph = ConjunctiveGraph()
            try:
                LOGGER.debug("looking up %s" % url)
                graph.load(url)
            except urllib2.HTTPError as e:
                LOGGER.error(e)

            # if we've got more than 3 assertions extract some stuff from
            # the graph and save back some info to the db, would be nice
            # to have a triple store underneath where we could persist
            # all the facts eh?

            if len(graph) >= 3:
                place.dbpedia = url
                place.latitude = graph.value(url, geo['lat'])
                place.longitude = graph.value(url, geo['long'])
                for object in graph.objects(URIRef(url), owl['sameAs']):
                    if object.startswith('http://sws.geonames.org'):
                        place.geonames = object
                place.save()
                LOGGER.info("found dbpedia resource %s" % url)
            else:
                LOGGER.warn("couldn't find dbpedia resource for %s" % url)

            reset_queries()
        LOGGER.info("finished looking up places in dbpedia")

        LOGGER.info("dumping place_links.json fixture")

        # so it would be nice to use django.core.serializer here
        # but it serializes everything about the model, including
        # titles that are linked to ... and this could theoretically
        # change over time, so we only preserve the facts that have
        # been harvested from dbpedia, so they can overlay over
        # the places that have been extracted during title load

        json_src = []
        places_qs = models.Place.objects.filter(dbpedia__isnull=False)
        for p in places_qs.order_by('name'):
            json_src.append(
                {
                    'name': p.name,
                    'dbpedia': p.dbpedia,
                    'geonames': p.geonames,
                    'longitude': p.longitude,
                    'latitude': p.latitude,
                }
            )
            reset_queries()
        json.dump(json_src, open('core/fixtures/place_links.json', 'w'), indent=2)
        LOGGER.info("finished dumping place_links.json fixture")


def _clean(u):
    return u.strip().replace(' ', '_').encode('ascii', 'ignore')
