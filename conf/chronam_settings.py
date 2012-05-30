import os

from settings_default import *

SECRET_KEY = 'px2@!q2(m5alb$0=)h@u*80mmf9cd-nn**^y4j2j&+_8h^n_0f'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'chronam',
        }
    }

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SHARETOOL_URL = "http://cdn.loc.gov/share/sites/dUcuwr5p/share-jquery-min.js"

OMNITURE_SCRIPT = "http://www.loc.gov:8081/global/s_code.js"
DEFAULT_TTL_SECONDS = 60 * 60 * 24
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24
FEED_TTL_SECONDS = 60 * 60 * 24 * 7

MEMORIOUS_REPOSITORIES = {"default": "/opt/chronam/data/memorious"}
MEMORIOUS_DEBUG = True
SOLR = "http://localhost:8083/solr"

DOCUMENT_ROOT = "/opt/chronam/static"

if os.uname()[1] == "sun11":
    STORAGE = '/batches'
else:
    STORAGE = "/vol/ndnp_staging_02/"

BIB_STORAGE = '/opt/chronam/data/bib'
ESSAY_STORAGE = '/opt/chronam/data/ndnp-essays/essays'

USE_TIFF = False
