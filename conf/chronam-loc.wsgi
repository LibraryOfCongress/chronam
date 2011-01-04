import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'chronam_loc.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

