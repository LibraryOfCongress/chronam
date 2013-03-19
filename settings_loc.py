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

OMNITURE_SCRIPT = "http://cdn.loc.gov/js/global/s_code.js"
SHARETOOL_URL = "http://cdn.loc.gov/sites/chronicling-america.js"
