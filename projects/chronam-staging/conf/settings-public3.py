import os
# Django settings for chronam project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

MASTER = False
REPLICANT = (not MASTER)

ADMINS = (
    # ('NDNP Dev', 'ndnp-dev@rdc.lctl.gov'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'chronam'             # Or path to database file if using sqlite3.
DATABASE_USER = 'chronam'             # Not used with sqlite3.
DATABASE_PASSWORD = 'pick_one'         # Not used with sqlite3.
DATABASE_HOST = '/tmp/mysql_public3.sock'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = '3302'             # Set to empty string for default. Not used with sqlite3.
DATABASE_OPTIONS = { 'unix_socket': '/tmp/mysql_public3.sock' }


# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3&f-6xj^w^g)bj0mlxv$qw_=ebb_o0k)bk2s#o&b8%5-7*up5l'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
)

ROOT_URLCONF = 'chronam.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.humanize',
    'chronam.web',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'chronam.web.context_processors.extra_request_info',
)

STORAGE = '/batches'
BIB_STORAGE = '/ndnp/public3/data/bib/data'
ESSAY_STORAGE = '/ndnp/public3/data/essays'

_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(_ROOT, 'static')
THUMBNAIL_WIDTH = 200

SOLR = 'http://localhost:8086/solr'

if MASTER:
    OMNITURE_SCRIPT = "http://www.loc.gov:8081/global/s_code.js"
    DEFAULT_TTL_SECONDS = 1
    PAGE_IMAGE_TTL_SECONDS = 1
else:
    OMNITURE_SCRIPT = "http://www.loc.gov/global/s_code.js"
    DEFAULT_TTL_SECONDS = 86400
    PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2 # 2 weeks
