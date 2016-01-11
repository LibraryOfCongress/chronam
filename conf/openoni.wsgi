import os, sys

os.environ['CELERY_LOADER'] = 'django'
os.environ['DJANGO_SETTINGS_MODULE'] = 'openoni.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

