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

DOCUMENT_ROOT = "/opt/chronam/static"

if os.uname()[1]=="sun11":
    STORAGE = '/batches'
else:
    STORAGE = '/opt/chronam/data/batches/'

BIB_STORAGE = '/opt/chronam/data/bib/data'
ESSAY_STORAGE = '/opt/chronam/data/ndnp-essays/essays'

