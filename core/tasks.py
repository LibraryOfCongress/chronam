import logging

from celery.decorators import task

from django.conf import settings
from django.core import management
from django.core.cache import cache

from chronam.core import cts 
from chronam.core.models import Batch
from chronam.core.batch_loader import BatchLoader

logger = logging.getLogger(__name__)


@task
def load_batch(batch_dir, service_request=None):
    try:
        batch_loader = BatchLoader()
        batch = batch_loader.load_batch(batch_dir)
        logger.info("loaded batch %s", batch)
        if service_request:
            logger.info("marking service request as complete")
            service_request.complete()

    except Exception, e:
        logger.exception("unable to load batch %s" % batch_dir)
        if service_request:
            logginer.info("marking service request as failed")
            service_request.fail(str(e))


@task
def purge_batch(batch):
    # TODO: if we ever get service requests to purge batches we might want
    # to have purge_batch take a service request.
    try:
        batch_loader = BatchLoader()
        batch_loader.purge_batch(batch)
    except Exception, e:
        logger.exception("unable to purge batch: %s" % e)


@task 
def poll_cts():
    if settings.MAX_BATCHES != 0 \
            and Batch.objects.all().count() >= settings.MAX_BATCHES:
        logger.debug("not loading more than %s batches", settings.MAX_BATCHES)
        return None

    c = cts.CTS(settings.CTS_USERNAME, 
                  settings.CTS_PASSWORD,
                  settings.CTS_URL)

    # 'ndnpstagingingestqueue', 'ingest.NdnpIngest.ingest'
    sr = c.next_service_request(settings.CTS_QUEUE, 
                                settings.CTS_SERVICE_TYPE)

    # no service request? whew, we're done.
    if not sr: 
        logger.debug("no service requests")
        return 

    # determine the location of the bag on the filesystem
    logger.info("got service request: %s", sr)
    bag_instance_id = sr.data['requestParameters']['baginstancekey']
    bag = c.get_bag_instance(bag_instance_id)
    bag_dir = bag.data['filepath']

    try:
        logger.info("loading %s" % bag_dir)
        return load_batch.delay(bag_dir, sr)

    except Exception, e:
        logger.exception("loading batch failed!")
        sr.fail(str(e))

@task
def delete_django_cache():
    logger.info("deleting newspaper_info")
    cache.delete('newspaper_info')

    logger.info("deleting titles_states")
    cache.delete('titles_states')
