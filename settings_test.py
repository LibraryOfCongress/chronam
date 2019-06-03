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

ESSAYS_FEED = "http://essyedtrrvlt01.loctest.gov/feed/"

# Use different storage pathes to avoid interference with the actual storage for the web app
# some tests purge batch and deletes data (such as word coordinates)
BIB_STORAGE = os.path.join(STORAGE, "test_bib")
OCR_DUMP_STORAGE = os.path.join(STORAGE, "test_ocr")
COORD_STORAGE = os.path.join(STORAGE, "test_word_coordinates")
TEMP_TEST_DATA = os.path.join(STORAGE, "temp_test_data")
DATA_DIR = os.path.join(DIRNAME, "data")
BATCH_STORAGE = os.path.join(DATA_DIR, "batches")

# DO NOT CHECK-IN WORLDCAT_KEY TO REPO
from settings import WORLDCAT_KEY
