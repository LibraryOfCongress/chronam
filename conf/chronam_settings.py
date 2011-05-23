import os

from chronam_core_settings import *
from chronam_loc.settings_default import *


DEBUG = False
TEMPLATE_DEBUG = False

OMNITURE_SCRIPT = "http://www.loc.gov:8081/global/s_code.js"
DEFAULT_TTL_SECONDS = 60 * 60 * 24
PAGE_IMAGE_TTL_SECONDS = 60 * 60 * 24
FEED_TTL_SECONDS = 60 * 60 * 24 * 7
STORAGE = "/opt/chronam/data/batches/"

MEMORIOUS_REPOSITORIES = {"default": "/opt/chronam/data/memorious"}
MEMORIOUS_DEBUG = False
SOLR = "http://localhost:8080/solr"
