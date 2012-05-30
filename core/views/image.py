import logging
import simplejson as json
import urlparse
import urllib2
from cStringIO import StringIO

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseNotFound, HttpResponseServerError

from chronam.core import models
from chronam.core.utils.utils import get_page
from chronam.core.decorator import cors


LOGGER = logging.getLogger(__name__)

if settings.USE_TIFF:
    LOGGER.info("Configured to use TIFFs. Set USE_TIFF=False if you want to use the JPEG2000s.")
    from PIL import Image
else:
    import NativeImaging
    for backend in ('aware_cext', 'aware', 'graphicsmagick'):
        try:
            Image = NativeImaging.get_image_class(backend)
            break
        except ImportError, e:
            LOGGER.info("NativeImage backend '%s' not available.")
    else:
        raise Exception("No suitable NativeImage backend found.")
    LOGGER.info("Using NativeImage backend '%s'" % backend)


def _get_image(page):
    if settings.USE_TIFF:
        filename = page.tiff_filename
    else:
        filename = page.jp2_filename
    if not filename:
        raise Http404
    batch = page.issue.batch
    url = urlparse.urljoin(batch.storage_url, filename)
    try:
        fp = urllib2.urlopen(url)
        stream = StringIO(fp.read())
    except IOError, e:
        e.message += " (while trying to open %s)" % url
        raise e
    im = Image.open(stream)
    return im


def thumbnail(request, lccn, date, edition, sequence):
    page = get_page(lccn, date, edition, sequence)
    response = HttpResponse(mimetype="image/jpeg")
    thumb_width = settings.THUMBNAIL_WIDTH
    try:
        im = _get_image(page)
    except IOError, e:
        return HttpResponseServerError("Unable to create thumbnail: %s" % e)
    width, height = im.size
    thumb_height = int(round(thumb_width / float(width) * float(height)))
    im = im.resize((thumb_width, thumb_height), Image.ANTIALIAS)
    im.save(response, "JPEG")
    return response


def page_image(request, lccn, date, edition, sequence, width, height):
    page = get_page(lccn, date, edition, sequence)
    return page_image_tile(request, lccn, date, edition, sequence,
                           width, height, 0, 0,
                           page.jp2_width, page.jp2_length)


def page_image_tile(request, lccn, date, edition, sequence,
                    width, height, x1, y1, x2, y2):
    page = get_page(lccn, date, edition, sequence)
    if 'download' in request.GET and request.GET['download']:
        response = HttpResponse(mimetype="binary/octet-stream")
    else:
        response = HttpResponse(mimetype="image/jpeg")

    width, height = int(width), int(height)
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    try:
        im = _get_image(page)
    except IOError, e:
        return HttpResponseServerError("Unable to create image tile: %s" % e)
    c = im.crop((x1, y1, x2, y2))
    f = c.resize((width, height))
    f.save(response, "JPEG")
    return response


@cors
def coordinates(request, lccn, date, edition, sequence, words=None):
    page = get_page(lccn, date, edition, sequence)
    try:
        ocr = page.ocr
    except models.OCR.DoesNotExist, e:
        ocr = None
    if ocr is None:
        r = HttpResponseNotFound()
        r.write("page has no ocr")
        return r
    if words is not None:
        word_coordinates = ocr.word_coordinates
        all_coordinates = {}
        for word in words.split("+"):
            if word:
                all_coordinates[word] = word_coordinates.get(word, [])
        return HttpResponse(json.dumps(all_coordinates),
                            mimetype='application/json')
    else:
        r = HttpResponse(mimetype='application/json')
        r.write(str(ocr.word_coordinates_json))
        return r
