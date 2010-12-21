# Base Django settings for chronam project.
import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

MASTER = False

ADMINS = (
    # ('NDNP Dev', 'ndnp-dev@rdc.lctl.gov'),
)

MANAGERS = ADMINS

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(_ROOT, 'static')
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'px2@!q2(m5alb$0=)h@u*80mmf9cd-nn**^y4j2j&+_8h^n_0f'

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

INSTALLED_APPS = INSTALLED_APPS + (
    'django.contrib.humanize',
    'chronam.web',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'chronam.web.context_processors.extra_request_info',
)

THUMBNAIL_WIDTH = 200

OMNITURE_SCRIPT = "http://www.loc.gov/global/s_code.js"
DEFAULT_TTL_SECONDS = 86400
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks
