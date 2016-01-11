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

STATIC_URL = '/media/'
STATIC_ROOT = os.path.join(DIRNAME, '.static-media')

MEDIA_ROOT = ''
MEDIA_URL = ''
#ADMIN_MEDIA_PREFIX = '/media/'

ROOT_URLCONF = 'openoni.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'openoni',
        'USER': 'openoni',
        'PASSWORD': 'openoni',
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
    'openoni.core.context_processors.get_search_form',
    'openoni.core.context_processors.extra_request_info',
    'openoni.core.context_processors.newspaper_info',
)

TEMPLATE_DIRS = (
    os.path.join(DIRNAME, 'templates'),
)

INSTALLED_APPS = (
    'south',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'djcelery',
    'djkombu',

    'openoni.core',
)

BROKER_TRANSPORT = "django"

THUMBNAIL_WIDTH = 200

DEFAULT_TTL_SECONDS = 86400  # 1 day
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
API_TTL_SECONDS = 60 * 60  # 1 hour

MEMORIOUS_REPOSITORIES = {"default": '/opt/openoni/'}

MEMORIOUS_DEBUG = True
USE_TIFF = False

SOUTH_TESTS_MIGRATE = False
ESSAYS_FEED = "http://ndnp-essays.rdc.lctl.gov/feed/"
CACHE_BACKEND = 'file:///var/tmp/django_cache?timeout=100'

IS_PRODUCTION = False
CTS_USERNAME = 'openoni'
CTS_PASSWORD = 'openoni'
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

DOCUMENT_ROOT = "/opt/openoni/static"

STORAGE = '/var/lib/jenkins/jobs/openoni/openoni/data/'
STORAGE_URL = '/data/'
BATCH_STORAGE = os.path.join(STORAGE, "batches")
BIB_STORAGE = os.path.join(STORAGE, "bib")
OCR_DUMP_STORAGE = os.path.join(STORAGE, "ocr")
COORD_STORAGE = os.path.join(STORAGE, "word_coordinates")
TEMP_TEST_DATA = os.path.join(STORAGE, "temp_test_data")

BASE_CRUMBS = [{'label':'Home', 'href': '/'}]
