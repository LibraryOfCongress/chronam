from settings_template import *

INSTALLED_APPS = (
    'chronam.loc',
    'lc',
) + INSTALLED_APPS


BASE_CRUMBS = [
    {'label': 'The Library of Congress', 'href': 'http://www.loc.gov/'},
    {'label':'Chronicling America', 'href': '/'}
]

THUMBNAIL_WIDTH = 200
SEARCH_RESULTS_PER_PAGE = 20
