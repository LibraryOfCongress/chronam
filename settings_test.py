from settings_template import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'TEST': {
            'CHARSET': "utf8",
            'COLLATION': "utf8_general_ci"
        }
    }
}

ESSAYS_FEED = "http://rdccavld04.loctest.gov/feed/"

CTS_URL = "https://transferqa.loctest.gov/transfer/"

# DO NOT CHECK-IN WORLDCAT_KEY TO REPO