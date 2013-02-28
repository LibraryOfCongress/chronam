import os
import logging
import subprocess

def abs_path(path):
    import os
    _root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(_root, path)

DIRNAME = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
)

MANAGERS = ADMINS

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

MEDIA_ROOT = ''
MEDIA_URL = ''

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

STATIC_URL = '/media/'
STATIC_ROOT = os.path.join(DIRNAME, '.static-media')

ROOT_URLCONF = 'chronam.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'pick_one',
        }
    }

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'px2@!q2(m5alb$0=)h@u*80mmf9cd-nn**^y4j2j&+_8h^n_0f'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'chronam.core.middleware.TooBusyMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'chronam.core.context_processors.extra_request_info',
    'chronam.core.context_processors.newspaper_info',
)

TEMPLATE_DIRS = (
    os.path.join(DIRNAME, 'templates'),
)

INSTALLED_APPS = (
    # 'lc',
    # 'chronam.loc',
    'south',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'djcelery',
    'djkombu',

    'chronam.core',
)

BROKER_TRANSPORT = "django"

THUMBNAIL_WIDTH = 360

DEFAULT_TTL_SECONDS = 86400  # 1 day
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
API_TTL_SECONDS = 60 * 60  # 1 hour
FEED_TTL_SECONDS = 60 * 60 * 24 * 7

USE_TIFF = False

SOUTH_TESTS_MIGRATE = False
ESSAYS_FEED = "http://ndnp-essays.rdc.lctl.gov/feed/"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 100,
    }
}

IS_PRODUCTION = False
CTS_USERNAME = 'username'
CTS_PASSWORD = 'password'
CTS_PROJECT_ID = 'ndnp'
CTS_QUEUE = 'ndnpingestqueue'
CTS_SERVICE_TYPE = 'ingest.NdnpIngest.ingest'
CTS_URL = "https://cts.loc.gov/transfer/"

MAX_BATCHES = 0

import multiprocessing
#TOO_BUSY_LOAD_AVERAGE = 1.5 * multiprocessing.cpu_count()
TOO_BUSY_LOAD_AVERAGE = 64 

SOLR = "http://localhost:8080/solr"
SOLR_LANGUAGES = ("eng", "fre", "spa")

DOCUMENT_ROOT = "/opt/chronam/static"

STORAGE = '/opt/chronam/data/'
STORAGE_URL = '/data/'
BATCH_STORAGE = os.path.join(STORAGE, "batches")
BIB_STORAGE = os.path.join(STORAGE, "bib")
OCR_DUMP_STORAGE = os.path.join(STORAGE, "ocr")
COORD_STORAGE = os.path.join(STORAGE, "word_coordinates")


BASE_CRUMBS = [{'label':'Home', 'href': '/'}]
