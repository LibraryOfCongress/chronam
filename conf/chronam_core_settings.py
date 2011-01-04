import os

from chronam.core.settings_default import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'pick_one',
        }
    }

SOLR = 'http://localhost:8080/solr'

DOCUMENT_ROOT = "/ndnp/chronam/static"

if os.uname()[1]=="sun11":
    STORAGE = '/batches'
else:
    STORAGE = '/vol/ndnp/chronam/batches/'

BIB_STORAGE = '/ndnp/chronam/data/bib/data'
ESSAY_STORAGE = '/ndnp/chronam/data/ndnp-essays/essays'

