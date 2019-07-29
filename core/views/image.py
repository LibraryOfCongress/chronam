from __future__ import absolute_import

import gzip
import logging
import os.path
import urllib2
import urlparse
from cStringIO import StringIO

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseServerError

from chronam.core import models
from chronam.core.decorator import cors
from chronam.core.utils.utils import add_cache_tag, get_page

LOGGER = logging.getLogger(__name__)

if settings.USE_TIFF:
    LOGGER.info("Configured to use TIFFs. Set USE_TIFF=False if you want to use the JPEG2000s.")
    from PIL import Image
else:
    import NativeImaging

    for backend in ("aware", "graphicsmagick"):
        try:
            Image = NativeImaging.get_image_class(backend)
            LOGGER.info("Using NativeImage backend '%s'", backend)
            break
        except ImportError as e:
            LOGGER.info("NativeImage backend '%s' not available.", backend)
    else:
        raise Exception("No suitable NativeImage backend found.")


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
    except IOError as e:
        e.message += " (while trying to open %s)" % url
        raise e
    im = Image.open(stream)
    return im


def _get_resized_image(page, width):
    im = _get_image(page)
    actual_width, actual_height = im.size
    height = int(round(width / float(actual_width) * float(actual_height)))
    im = im.resize((width, height), Image.ANTIALIAS)
    return im


def thumbnail(request, lccn, date, edition, sequence):
    page = get_page(lccn, date, edition, sequence)
    try:
        im = _get_resized_image(page, settings.THUMBNAIL_WIDTH)
    except IOError as e:
        return HttpResponseServerError("Unable to create thumbnail: %s" % e)
    response = HttpResponse(content_type="image/jpeg")
    im.save(response, "JPEG")
    return add_cache_tag(response, "lccn=%s" % lccn)


def medium(request, lccn, date, edition, sequence):
    page = get_page(lccn, date, edition, sequence)
    try:
        im = _get_resized_image(page, settings.THUMBNAIL_MEDIUM_WIDTH)
    except IOError as e:
        return HttpResponseServerError("Unable to create thumbnail: %s" % e)
    response = HttpResponse(content_type="image/jpeg")
    im.save(response, "JPEG")
    return add_cache_tag(response, "lccn=%s" % lccn)


def page_image(request, lccn, date, edition, sequence, width, height):
    page = get_page(lccn, date, edition, sequence)
    return page_image_tile(
        request, lccn, date, edition, sequence, width, height, 0, 0, page.jp2_width, page.jp2_length
    )


def page_image_tile(request, lccn, date, edition, sequence, width, height, x1, y1, x2, y2):
    page = get_page(lccn, date, edition, sequence)
    if "download" in request.GET and request.GET["download"]:
        response = HttpResponse(content_type="binary/octet-stream")
    else:
        response = HttpResponse(content_type="image/jpeg")

    width, height = int(width), int(height)
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    try:
        im = _get_image(page)
    except IOError as e:
        return HttpResponseServerError("Unable to create image tile: %s" % e)

    width = min(width, (x2 - x1))
    height = min(height, (y2 - y1))

    c = im.crop((x1, y1, x2, y2))
    f = c.resize((width, height))
    f.save(response, "JPEG")
    return add_cache_tag(response, "lccn=%s" % lccn)


def image_tile(request, path, width, height, x1, y1, x2, y2):
    if "download" in request.GET and request.GET["download"]:
        response = HttpResponse(content_type="binary/octet-stream")
    else:
        response = HttpResponse(content_type="image/jpeg")

    width, height = int(width), int(height)
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    try:
        p = os.path.join(settings.BATCH_STORAGE, path)
        im = Image.open(p)
    except IOError as e:
        return HttpResponseServerError("Unable to create image tile: %s" % e)
    c = im.crop((x1, y1, x2, y2))
    f = c.resize((width, height))
    f.save(response, "JPEG")
    return response


@cors
def coordinates(request, lccn, date, edition, sequence, words=None):
    url_parts = {"lccn": lccn, "date": date, "edition": edition, "sequence": sequence}

    file_path = models.coordinates_path(url_parts)

    try:
        with gzip.open(file_path, "rb") as i:
            response = HttpResponse(i.read(), content_type="application/json")
            return add_cache_tag(response, "lccn=%s" % lccn)
    except IOError:
        LOGGER.warning("Word coordinates file %s does not exist", file_path)
        raise Http404
