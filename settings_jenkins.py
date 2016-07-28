from settings_template import *

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'chronam',
        }
    }

ESSAYS_FEED = "http://rdccavld04.loctest.gov/feed/"

IS_PRODUCTION = False

CTS_URL = "https://transferqa.loctest.gov/transfer/"

SOLR = "http://localhost:8080/solr"


STORAGE = '/var/lib/jenkins/jobs/chronam/chronam/data/'
BATCH_STORAGE = os.path.join(STORAGE, "batches")
BIB_STORAGE = os.path.join(STORAGE, "bib")
OCR_DUMP_STORAGE = os.path.join(STORAGE, "ocr")
COORD_STORAGE = os.path.join(STORAGE, "word_coordinates")
