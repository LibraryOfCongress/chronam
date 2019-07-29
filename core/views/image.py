from __future__ import absolute_import

import gzip
import logging
import os.path
import urllib2
import urlparse
from cStringIO import StringIO
from functools import wraps

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


def add_lccn_cache_tag(view_function):
    @wraps(view_function)
    def inner(request, lccn, *args, **kwargs):
        return add_cache_tag(view_function(request, lccn, *args, **kwargs), "lccn=%s" % lccn)

    return inner


@add_lccn_cache_tag
def thumbnail(request, lccn, date, edition, sequence):
    page = get_page(lccn, date, edition, sequence)
    try:
        im = _get_resized_image(page, settings.THUMBNAIL_WIDTH)
    except IOError as e:
        return HttpResponseServerError("Unable to create thumbnail: %s" % e)
    response = HttpResponse(content_type="image/jpeg")
    im.save(response, "JPEG")
    return response


@add_lccn_cache_tag
def medium(request, lccn, date, edition, sequence):
    page = get_page(lccn, date, edition, sequence)
    try:
        im = _get_resized_image(page, settings.THUMBNAIL_MEDIUM_WIDTH)
    except IOError as e:
        return HttpResponseServerError("Unable to create thumbnail: %s" % e)
    response = HttpResponse(content_type="image/jpeg")
    im.save(response, "JPEG")
    return response


@add_lccn_cache_tag
def page_image(request, lccn, date, edition, sequence, width, height):
    page = get_page(lccn, date, edition, sequence)
    return page_image_tile(
        request, lccn, date, edition, sequence, width, height, 0, 0, page.jp2_width, page.jp2_length
    )


@add_lccn_cache_tag
def page_image_tile(request, lccn, date, edition, sequence, width, height, x1, y1, x2, y2):
    page = get_page(lccn, date, edition, sequence)
    width, height = map(int, (width, height))
    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

    try:
        return serve_image_tile(request, _get_image(page), width, height, x1, y1, x2, y2)
    except EnvironmentError as e:
        logging.exception("Unable to create image tile for %s", page)
        return HttpResponseServerError("Unable to create image tile: %s" % e)


def image_tile(request, path, width, height, x1, y1, x2, y2):
    width, height = map(int, (width, height))
    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

    try:
        p = os.path.join(settings.BATCH_STORAGE, path)
        im = Image.open(p)
        return serve_image_tile(request, im, width, height, x1, y1, x2, y2)
    except EnvironmentError as e:
        logging.exception("Unable to create image tile for %s", path)
        return HttpResponseServerError("Unable to create image tile: %s" % e)


def serve_image_tile(request, image, width, height, x1, y1, x2, y2):
    response = HttpResponse(content_type="image/jpeg")
    if request.GET.get("download"):
        response["Content-Disposition"] = "attachment"

    width = min(width, (x2 - x1))
    height = min(height, (y2 - y1))

    c = image.crop((x1, y1, x2, y2))
    f = c.resize((width, height))
    f.save(response, "JPEG")
    return response


@cors
@add_lccn_cache_tag
def coordinates(request, lccn, date, edition, sequence, words=None):
    url_parts = {"lccn": lccn, "date": date, "edition": edition, "sequence": sequence}

    file_path = models.coordinates_path(url_parts)

    try:
        with gzip.open(file_path, "rb") as i:
            return HttpResponse(i.read(), content_type="application/json")
    except IOError:
        LOGGER.warning("Word coordinates file %s does not exist", file_path)
        raise Http404
