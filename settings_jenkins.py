import os

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
#ADMIN_MEDIA_PREFIX = '/media/'

ROOT_URLCONF = 'chronam.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'chronam',
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
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'chronam.core.context_processors.get_search_form',
    'chronam.core.context_processors.extra_request_info',
    'chronam.core.context_processors.newspaper_info',
)

TEMPLATE_DIRS = (
    os.path.join(DIRNAME, 'templates'),
)

INSTALLED_APPS = (
    'south',
    'django.contrib.humanize',
    'django_memorious',
    'djcelery',
    'djkombu',

    'chronam.core',
)

BROKER_TRANSPORT = "django"

THUMBNAIL_WIDTH = 200

DEFAULT_TTL_SECONDS = 86400  # 1 day
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
API_TTL_SECONDS = 60 * 60  # 1 hour

MEMORIOUS_REPOSITORIES = {"default": '/opt/chronam/'}

MEMORIOUS_DEBUG = True
USE_TIFF = False

SOUTH_TESTS_MIGRATE = False
ESSAYS_FEED = "http://ndnp-essays.rdc.lctl.gov/feed/"
CACHE_BACKEND = 'file:///var/tmp/django_cache?timeout=100'

IS_PRODUCTION = False
CTS_USERNAME = 'chronam'
CTS_PASSWORD = 'chronam'
CTS_PROJECT_ID = 'ndnp'
CTS_QUEUE = 'ndnpingestqueue'
CTS_SERVICE_TYPE = 'ingest.NdnpIngest.ingest'
CTS_URL = "https://cts.loc.gov/transfer/"

MAX_BATCHES = 0

SHARETOOL_URL = "http://cdn.loc.gov/share/sites/dUcuwr5p/share-jquery-min.js"
OMNITURE_SCRIPT = "http://www.loc.gov:8081/global/s_code.js"

DEFAULT_TTL_SECONDS = 60 * 60 * 24
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24
FEED_TTL_SECONDS = 60 * 60 * 24 * 7

SOLR = "http://localhost:8080/solr"
SOLR_LANGUAGES = ("eng", "fre", "ger", "ita", "spa")

DOCUMENT_ROOT = "/opt/chronam/static"

STORAGE = '/var/lib/jenkins/jobs/chronam/chronam/data/'
STORAGE_URL = '/data/'
BATCH_STORAGE = os.path.join(STORAGE, "batches")
BIB_STORAGE = os.path.join(STORAGE, "bib")
OCR_DUMP_STORAGE = os.path.join(STORAGE, "ocr")
