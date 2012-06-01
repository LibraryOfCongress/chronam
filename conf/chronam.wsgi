import os, sys

sys.path.append("/opt")

os.environ['CELERY_LOADER'] = 'django'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

