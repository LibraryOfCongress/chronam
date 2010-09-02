from chronam.settings_global import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'chronam',
        'USER': 'chronam',
        'PASSWORD': 'pick_one',
        'HOST': '/tmp/mysql_public1.sock',
        'PORT': '3306',
        }
    }

STORAGE = '/batches'
BIB_STORAGE = '/ndnp/public1/data/bib/data'
ESSAY_STORAGE = '/ndnp/public1/data/ndnp-essays/essays'
