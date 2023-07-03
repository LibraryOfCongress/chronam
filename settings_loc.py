from settings_template import *

INSTALLED_APPS = (
    "chronam.loc",
    "lc",
) + INSTALLED_APPS


BASE_CRUMBS = [{"label": "Chronicling America", "href": "/"}]

THUMBNAIL_WIDTH = 200
SEARCH_RESULTS_PER_PAGE = 20

DEBUG = False

IS_PRODUCTION = True
ADOBE_ANALYTICS_URL = "https://assets.adobedtm.com/f94f5647937d/624e2240e90d/launch-0610ec681aff.min.js"
SHARETOOL_URL = "https://cdn.loc.gov/sites/chronicling-america.js"

CTS_USERNAME = "username"
CTS_PASSWORD = "password"
CTS_PROJECT_ID = "ndnp"
CTS_QUEUE = "ndnpingestqueue"
CTS_SERVICE_TYPE = "ingest.NdnpIngest.ingest"
CTS_URL = "https://cts.loc.gov/transfer/"
