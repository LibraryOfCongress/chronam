# Django settings for chronam project.
import os
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
ADMIN_MEDIA_PREFIX = '/media/'
OMNITURE_SCRIPT = ""
STORAGE = ""

ROOT_URLCONF = 'chronam.urls'

BIB_STORAGE = '/opt/chronam/data/bib'
ESSAY_STORAGE = '/opt/chronam/data/ndnp-essays/essays'

DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
    }
}
# Make this unique, and don't share it with anybody.
SECRET_KEY = '123'

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

OMNITURE_SCRIPT = ""
DEFAULT_TTL_SECONDS = 86400  # 1 day
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
API_TTL_SECONDS = 60 * 60  # 1 hour


def abs_path(path):
    import os
    _root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(_root, path)

MEMORIOUS_REPOSITORIES = {
    "default": abs_path("..")
    }

MEMORIOUS_DEBUG = False

SOLR = "http://localhost:8986/solr"

USE_TIFF = True

SOUTH_TESTS_MIGRATE = False
ESSAYS_FEED = "http://ndnp-essays.rdc.lctl.gov/feed/"
IS_PRODUCTION = False
MAX_BATCHES = 8

CACHE_BACKEND = 'file:///var/tmp/django_cache?timeout=100'

IS_PRODUCTION = False
CTS_USERNAME = None
CTS_PASSWORD = None
CTS_PROJECT_ID = None
CTS_QUEUE = None
CTS_SERVICE_TYPE = None
CTS_URL = None

import djcelery
djcelery.setup_loader()
