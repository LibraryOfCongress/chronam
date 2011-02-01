import os

from chronam_core_settings import *
from chronam_loc.settings_default import *


DEBUG = True
TEMPLATE_DEBUG = True

OMNITURE_SCRIPT = "http://www.loc.gov:8081/global/s_code.js"
DEFAULT_TTL_SECONDS = 1
PAGE_IMAGE_TTL_SECONDS = 1
STORAGE = "/opt/chronam/data/batches/"

MEMORIOUS_REPOSITORIES = {"default": "/opt/chronam/data/memorious"}
