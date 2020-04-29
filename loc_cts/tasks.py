import logging
import os

import minicts
from celery.decorators import task
from django.conf import settings

from chronam.core import cts
from chronam.core.models import Batch
from chronam.core.tasks import load_batch, purge_batch

logger = logging.getLogger(__name__)


@task
def poll_purge():
    cts = minicts.CTS(settings.CTS_URL, settings.CTS_USERNAME, settings.CTS_PASSWORD)

    queue = settings.CTS_QUEUE
    purge_service_type = "purge.NdnpPurge.purge"
    while True:
        req = cts.next_service_request(queue, purge_service_type)
        if req is None:
            logger.info("no purge service requests")
            break

        logger.info('got purge service request: %s', req.url)
        bag_instance_key = req.data['requestParameters']['baginstancekey']
        bag_instance = cts.get_bag_instance(bag_instance_key)
        batch_name = os.path.basename(bag_instance.data['filepath'])
        logger.info('purging %s', batch_name)

        # if the batch isn't there no need to purge
        try:
            if Batch.objects.filter(name=batch_name).count() == 0:
                logger.info('no need to purge %s ; it is not loaded', batch_name)
                logger.info('batch %s purged', batch_name)
            else:
                purge_batch(batch_name, req)
        except Exception as e:
            logger.exception("purge of %s failed", batch_name)
            req.fail("purge of %s failed: %s" % (batch_name, e))


@task
def poll_cts():
    if settings.MAX_BATCHES != 0 and Batch.objects.all().count() >= settings.MAX_BATCHES:
        logger.debug("not loading more than %s batches", settings.MAX_BATCHES)
        return None

    c = cts.CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)

    # 'ndnpstagingingestqueue', 'ingest.NdnpIngest.ingest'
    sr = c.next_service_request(settings.CTS_QUEUE, settings.CTS_SERVICE_TYPE)

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
        logger.info("loading %s", bag_dir)
        return load_batch.delay(bag_dir, sr)

    except Exception as e:
        logger.exception("loading batch failed!")
        sr.fail(str(e))
