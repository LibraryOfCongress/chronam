import os

def abs_path(path):
    import os
    _root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(_root, path)

DIRNAME = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

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

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(DIRNAME, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'chronam.core.context_processors.extra_request_info',
                'chronam.core.context_processors.newspaper_info',
            ],
            'debug' : DEBUG,
        },
    },
]

INSTALLED_APPS = (
    'south',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
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
COORD_STORAGE = os.path.join(STORAGE, "word_coordinates")
TEMP_TEST_DATA = os.path.join(STORAGE, "temp_test_data")

BASE_CRUMBS = [{'label':'Home', 'href': '/'}]
