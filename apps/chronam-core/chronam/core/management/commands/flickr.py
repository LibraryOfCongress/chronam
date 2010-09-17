import json
import urllib
import logging

from urlparse import urlparse

from django.core.management.base import BaseCommand
from django.conf import settings

from chronam.core.management.commands import configure_logging
from chronam.core.models import Page, FlickrUrl

configure_logging("chronam_flickr.config", "chronam_flickr.log")
_log = logging.getLogger(__name__)

class Command(BaseCommand):
    args = '<flickr_key>'
    help = 'load links for content that has been pushed to flickr.'

    def handle(self, key, **options):
        _log.debug("looking for chronam page content on flickr")
        create_count = 0

        for flickr_url, chronam_url in flickr_chronam_links(key):
            _log.info("found flickr/chronam link: %s, %s" % 
                         (flickr_url, chronam_url))

            # use the page url to locate the Page model
            path = urlparse(chronam_url).path
            page = Page.lookup(path)
            if not page:
                _log.error("page for %s not found" % chronam_url)
                continue

            # create the FlickrUrl attached to the apprpriate page
            f, created = FlickrUrl.objects.get_or_create(value=flickr_url, 
                                                         page=page)
            if created:
                create_count += 1
                f.save()
                _log.info("updated page (%s) with flickr url (%s)" % 
                          (page, flickr_url))
            else:
                _log.info("already knew about %s" % flickr_url)

        _log.info("created %s flickr urls" % create_count)
    

def newspaper_photo_ids(key):
    """
    Fetches JSON info for all the images in the Flickr newspaper set.
    """
    u = 'http://api.flickr.com/services/rest/?method=flickr.photosets.getPhotos&api_key=%s&photoset_id=72157619452486566&format=json&nojsoncallback=1' % key
    photos = json.loads(urllib.urlopen(u).read())
    for photo in photos['photoset']['photo']:
        yield photo


def flickr_url(photo_id):
    return 'http://www.flickr.com/photos/library_of_congress/%s' % photo_id


def chronam_url(photo_id, key):
    """
    Looks at complete information for a Flickr image, and tries to find
    the first chroniclingamerica.loc.gov identifier in the machine tags.
    """
    u = 'http://api.flickr.com/services/rest/?method=flickr.photos.getInfo&api_key=%s&photo_id=%s&format=json&nojsoncallback=1' % (key, photo_id)
    j = json.loads(urllib.urlopen(u).read())
    for tag in j['photo']['tags']['tag']:
        if 'chroniclingamerica.loc.gov' in tag['raw']:
            return tag['raw'].replace('dc:identifier=', '')
    return None


def flickr_chronam_links(key):
    """
    A generator that returns a tuple of flickr urls, and their corresponding
    chroniclingamerica.loc.gov page url.
    """

    for photo in newspaper_photo_ids(key):
        yield flickr_url(photo['id']), chronam_url(photo['id'], key)

