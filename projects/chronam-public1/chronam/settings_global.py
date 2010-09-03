# Base Django settings for chronam project.
import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

MASTER = True

ADMINS = (
    # ('NDNP Dev', 'ndnp-dev@rdc.lctl.gov'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'chronam',
        'HOST': '',
        'PORT': '',
        }
    }

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
_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(_ROOT, 'static')

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
)

INSTALLED_APPS = (
    'django.contrib.humanize',
    'chronam.core',
    'chronam.web',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'chronam.web.context_processors.extra_request_info',
)

THUMBNAIL_WIDTH = 200

SOLR = 'http://localhost:8083/solr'

OMNITURE_SCRIPT = "http://www.loc.gov/global/s_code.js"
DEFAULT_TTL_SECONDS = 86400
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
