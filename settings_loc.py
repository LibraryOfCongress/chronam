from settings_template import *

INSTALLED_APPS = (
    'chronam.loc',
    'lc',
) + INSTALLED_APPS


BASE_CRUMBS = [
    {'label':'Chronicling America', 'href': '/'}
]

THUMBNAIL_WIDTH = 200
SEARCH_RESULTS_PER_PAGE = 20


OMNITURE_SCRIPT = "//cdn.loc.gov/js/global/metrics/sc/s_code.js"
SHARETOOL_URL = "//cdn.loc.gov/sites/chronicling-america.js"

