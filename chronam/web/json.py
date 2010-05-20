import simplejson as json
from chronam.utils.rfc3339 import rfc3339

def batch_to_json(batch, serialize=True):
    b = {}
    b['name'] = batch.name
    b['ingested'] = rfc3339(batch.created)
    b['page_count'] = batch.page_count
    b['lccns'] = batch.lccns()
    b['awardee'] = batch.awardee.name
    if serialize:
        return json.dumps(b)
    else:
        return b

