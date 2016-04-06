import os, sys

os.environ['CELERY_LOADER'] = 'django'
os.environ['DJANGO_SETTINGS_MODULE'] = "chronam.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

