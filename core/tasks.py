import logging
import minicts
import os
import requests

from celery.decorators import task

from django.conf import settings
from django.core import management
from django.core.cache import cache

from chronam.core import cts
from chronam.core.models import Batch, OcrDump
from chronam.core.batch_loader import BatchLoader

_logger = logging.getLogger(__name__)

@task
def load_page_in_cache(url):
    try:
        _logger.debug("Requesting page [%s]" % url)
        r = requests.get(url)
        _logger.debug("status %s" % r.status_code)
        r.raise_for_status() #throw an error if status is not OK
    except Exception, e:
        _logger.exception("Unable to request page [%s]: %s" % (url, e))

@task
def process_coordinates(batch_dir):
    try:
        batch_loader = BatchLoader()
        batch_loader.process_coordinates(batch_dir)
        _logger.info("processed batch %s", batch_dir)
    except Exception, e:
        _logger.exception("unable to process batch %s" % batch_dir)

@task
def load_batch(batch_dir, service_request=None, process_coordinates=True):
    try:
        batch_loader = BatchLoader(process_coordinates=process_coordinates)
        batch = batch_loader.load_batch(batch_dir)
        _logger.info("loaded batch %s", batch)
        if service_request:
            _logger.info("marking service request as complete")
            service_request.complete()

    except Exception, e:
        _logger.exception("unable to load batch %s" % batch_dir)
        if service_request:
            _logger.info("marking service request as failed")
            service_request.fail(str(e))

@task
def load_essays():
    try:
       management.call_command('load_essays')
    except:
        _logger.error("Unable to load essays")

@task
def purge_batch(batch, service_request=None):
    try:
        optimize = not settings.IS_PRODUCTION
        management.call_command('purge_batch', batch, optimize=optimize)
        if service_request:
            service_request.complete()
    except Exception, e:
        _logger.exception("unable to purge batch: %s" % e)
        if service_request:
            service_request.fail(str(e))

@task
def poll_purge():
    cts = minicts.CTS(settings.CTS_URL,
                      settings.CTS_USERNAME,
                      settings.CTS_PASSWORD)

    queue = settings.CTS_QUEUE
    purge_service_type = "purge.NdnpPurge.purge"
    while True:
        req = cts.next_service_request(queue, purge_service_type)
        if req == None:
            _logger.info("no purge service requests")
            break

        _logger.info('got purge service request: %s' % req.url)
        bag_instance_key = req.data['requestParameters']['baginstancekey']
        bag_instance = cts.get_bag_instance(bag_instance_key)
        batch_name = os.path.basename(bag_instance.data['filepath'])
        _logger.info('purging %s' % batch_name)

        # if the batch isn't there no need to purge
        try:
            if Batch.objects.filter(name=batch_name).count() == 0:
                _logger.info('no need to purge %s ; it is not loaded' % batch_name)
                _logger.info('batch %s purged' % batch_name)
            else:
                purge_batch(batch_name, req)
        except Exception, e:
            _logger.exception("purge of %s failed", batch_name)
            req.fail("purge of %s failed: %s" % (batch_name, e))


@task
def poll_cts():
    if settings.MAX_BATCHES != 0 \
            and Batch.objects.all().count() >= settings.MAX_BATCHES:
        _logger.debug("not loading more than %s batches", settings.MAX_BATCHES)
        return None

    c = cts.CTS(settings.CTS_USERNAME,
                  settings.CTS_PASSWORD,
                  settings.CTS_URL)

    # 'ndnpstagingingestqueue', 'ingest.NdnpIngest.ingest'
    sr = c.next_service_request(settings.CTS_QUEUE,
                                settings.CTS_SERVICE_TYPE)

    # no service request? whew, we're done.
    if not sr:
        _logger.debug("no service requests")
        return

    # determine the location of the bag on the filesystem
    _logger.info("got service request: %s", sr)
    bag_instance_id = sr.data['requestParameters']['baginstancekey']
    bag = c.get_bag_instance(bag_instance_id)
    bag_dir = bag.data['filepath']

    try:
        _logger.info("loading %s" % bag_dir)
        return load_batch.delay(bag_dir, sr)

    except Exception, e:
        _logger.exception("loading batch failed!")
        sr.fail(str(e))

@task
def delete_django_cache():
    _logger.info("deleting newspaper_info")
    cache.delete('newspaper_info')

    _logger.info("deleting titles_states")
    cache.delete('titles_states')

@task
def dump_ocr(batch_name):
    batch = Batch.objects.get(name=batch_name)
    try:
        if batch.ocr_dump:
            _logger.info("ocr already generated for %s", batch)
        return
    except OcrDump.DoesNotExist:
        # as expected
        pass

    _logger.info("starting to dump ocr for %s", batch)
    dump = OcrDump.new_from_batch(batch)
    _logger.info("created ocr dump %s for %s", dump, batch)
