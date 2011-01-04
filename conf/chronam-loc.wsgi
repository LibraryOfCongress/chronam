import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'chronam_loc_settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

