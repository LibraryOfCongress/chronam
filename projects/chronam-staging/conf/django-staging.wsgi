import os, sys

sys.path.append('/ndnp/staging/chronam/projects/chronam-staging')

os.environ['DJANGO_SETTINGS_MODULE'] = 'chronam.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

