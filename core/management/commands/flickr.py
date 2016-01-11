import re
import json
import urllib
import logging

from urlparse import urlparse

from django.core.management.base import BaseCommand

from openoni.core.management.commands import configure_logging
from openoni.core.models import Page, FlickrUrl

configure_logging("openoni_flickr.config", "openoni_flickr.log")
_log = logging.getLogger(__name__)

class Command(BaseCommand):
    args = '<flickr_key>'
    help = 'load links for content that has been pushed to flickr.'

    def handle(self, key, **options):
        _log.debug("looking for openoni page content on flickr")
        create_count = 0

        for flickr_url, openoni_url in flickr_openoni_links(key):
            _log.info("found flickr/openoni link: %s, %s" % 
                         (flickr_url, openoni_url))

            # use the page url to locate the Page model
            path = urlparse(openoni_url).path
            page = Page.lookup(path)
            if not page:
                _log.error("page for %s not found" % openoni_url)
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
    

def photos_in_set(key, set_id):
    """A generator for all the photos in a set. 
    """
    u = 'http://api.flickr.com/services/rest/?method=flickr.photosets.getPhotos&api_key=%s&photoset_id=%s&format=json&nojsoncallback=1' % (key, set_id)
    photos = json.loads(urllib.urlopen(u).read())
    for p in photos['photoset']['photo']:
        yield photo(key, p['id'])


def photo(key, photo_id):
    """Return JSON for a given photo.
    """
    u = 'http://api.flickr.com/services/rest/?method=flickr.photos.getInfo&api_key=%s&photo_id=%s&format=json&nojsoncallback=1' % (key, photo_id)
    return json.loads(urllib.urlopen(u).read())


def flickr_url(photo):
    for url in photo['photo']['urls']['url']:
        if url['type'] == 'photopage':
            return url['_content']
    return None


def openoni_url(photo):
    """Tries to find a openoni link in the photo metadata
    """
    # libraryofcongress photos are uploaded with a machinetag
    for tag in photo['photo']['tags']['tag']:
        if 'chroniclingamerica.loc.gov' in tag['raw']:
            return tag['raw'].replace('dc:identifier=', '')
   
    # some other photos might have a link in the textual description
    m = re.search('"(http://chroniclingamerica.loc.gov/.+?)"',
    photo['photo']['description']['_content'])
    if m:
        return m.group(1)

    return None


def flickr_openoni_links(key):
    """
    A generator that returns a tuple of flickr urls, and their corresponding
    chroniclingamerica.loc.gov page url.
    """
    # these are two flickr sets that have known openoni content
    for set_id in [72157600479553448, 72157619452486566]:
        for photo in photos_in_set(key, set_id):
            openoni = openoni_url(photo)
            # not all photos in set will have a link to openoni
            if openoni:
                yield flickr_url(photo), openoni
