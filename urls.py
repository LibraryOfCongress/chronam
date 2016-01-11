import os

from django.conf.urls import patterns, url, include
from django.conf import settings
from django.utils import cache
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from openoni.core.views import home, image, search

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'


def cache_page(function, ttl):
    def decorated_function(*args, **kwargs):
        request = args[0]
        response = function(*args, **kwargs)
        cache.patch_response_headers(response, ttl)
        cache.patch_cache_control(response, public=True)
        return response
    return decorated_function

urlpatterns = patterns(
    'openoni.core.views',

    url(r'^$',
        cache_page(home.home, settings.DEFAULT_TTL_SECONDS),
        name="openoni_home"),
    url(r'^(?P<date>\d{4}-\d{2}-\d{2})/$', 
        cache_page(home.home, settings.DEFAULT_TTL_SECONDS),
        name="openoni_home_date"),
    url(r'^frontpages/(?P<date>\d{4}-\d{1,2}-\d{1,2}).json$',
        cache_page(home.frontpages, settings.DEFAULT_TTL_SECONDS),
        name="openoni_frontpages_date_json"),

    url(r'^tabs$',
        cache_page(home.tabs, settings.DEFAULT_TTL_SECONDS),
        name="openoni_tabs"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/thumbnail.jpg$',
        cache_page(image.thumbnail, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_page_thumbnail"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/medium.jpg$',
        cache_page(image.medium, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_page_medium"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024_from_0,0_to_6504,8192.jpg
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+).jpg$',
        cache_page(image.page_image_tile, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_page_image_tile"),

    # example: /tiles/batch_dlc_jamaica_ver01/data/sn83030214/00175042143/1903051701/0299.jp2/image_813x1024_from_0,0_to_6504,8192.jpg
    url(r'^images/tiles/(?P<path>.+)/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+).jpg$',
        cache_page(image.image_tile, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_image_tile"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024.jpg
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/image_(?P<width>\d+)x(?P<height>\d+).jpg$',
        cache_page(image.page_image, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_page_image"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/coordinates/
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/coordinates/$',
        cache_page(image.coordinates, settings.PAGE_IMAGE_TTL_SECONDS),
        name="openoni_page_coordinates"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/coordinates/;words=corn+peas+cigars
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/coordinates/;words=(?P<words>.+)$',
        cache_page(image.coordinates, settings.DEFAULT_TTL_SECONDS),
        name="openoni_page_coordinates_words"),
        
)

urlpatterns += patterns(
    'openoni.core.views',

    # TODO: url(r'^.*[A-Z]+.*$', 'lowercase', name="openoni_lowercase"),

    url(r'^about/$', 'about', name="openoni_about"),

    url(r'^help/$', 'help', name="openoni_help"),

    # explainOCR.html
    url(r'^ocr/$', 'ocr', name="openoni_ocr"),

    # recommended topics
    url(r'^recommended-topics/$', 'recommended_topics', name="recommended_topics"),

    # topic page
    url(r'^recommended-topics/(?P<topic_id>\d+)/$', 'openoni_topic', name="openoni_topic"),

    # API docs
    url(r'^about/api/$', 'about_api', name="openoni_about_api"),

    # example: /lccn/sn85066387
    url(r'^lccn/(?P<lccn>\w+)/$', 'title', 
        name="openoni_title"),

    # example: /lccn/sn85066387/issues/
    url(r'^lccn/(?P<lccn>\w+)/issues/$', 'issues', name="openoni_issues"),

    # example: /lccn/sn85066387/issues/1900
    url(r'^lccn/(?P<lccn>\w+)/issues/(?P<year>\d{4})/$', 
        'issues', name="openoni_issues_for_year"),

    # example: /lccn/sn85066387/issues/first_pages
    url(r'^lccn/(?P<lccn>\w+)/issues/first_pages/$', 'issues_first_pages', 
        name="openoni_issues_first_pages"),

    # example: /lccn/sn85066387/issues/first_pages/3
    url(r'^lccn/(?P<lccn>\w+)/issues/first_pages/(?P<page_number>\d+)/$', 
        'issues_first_pages', name="openoni_issues_first_pages_page_number"),

    # example: /lccn/sn85066387/marc
    url(r'^lccn/(?P<lccn>\w+)/marc/$', 'title_marc', 
        name="openoni_title_marc"),

    # example: /lccn/sn85066387/feed/
    url(r'^lccn/(?P<lccn>\w+)/feed/$', 'title_atom', 
        name='openoni_title_atom'),

    # example: /lccn/sn85066387/feed/10
    url(r'^lccn/(?P<lccn>\w+)/feed/(?P<page_number>\w+)$', 'title_atom',
        name='openoni_title_atom_page'),

    # example: /lccn/sn85066387/marc.xml
    url(r'^lccn/(?P<lccn>\w+)/marc.xml$', 'title_marcxml',
        name="openoni_title_marcxml"),

    # example: /lccn/sn85066387/holdings
    url(r'^lccn/(?P<lccn>\w+)/holdings/$', 'title_holdings',
        name="openoni_title_holdings"),

    # example: /essays/
    url(r'^essays/$', 'essays', name='openoni_essays'),

    # example: /essays/1/
    url(r'^essays/(?P<essay_id>\d+)/$', 'essay', name='openoni_essay'),

    # TOD0: remove this some suitable time after 08/2010 since it
    # permanently redirects to new essay id based URL
    # example: /lccn/sn85066387/essay
    url(r'^lccn/(?P<lccn>\w+)/essays/$', 'title_essays', 
        name="openoni_title_essays"),

    # example: /lccn/sn85066387/1907-03-17/ed-1
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/$',
        'issue_pages', name="openoni_issue_pages"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/1
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/(?P<page_number>\d+)/$', 
        'issue_pages', name="openoni_issue_pages_page_number"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/$',
        'page', name="openoni_page"),
        
    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4.pdf
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).pdf$',
        'page_pdf', name="openoni_page_pdf"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4.jp2
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).jp2$',
        'page_jp2', name="openoni_page_jp2"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr.xml
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr.xml$',
        'page_ocr_xml', name="openoni_page_ocr_xml"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr.txt
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr.txt$',
        'page_ocr_txt', name="openoni_page_ocr_txt"),
        
    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/;words=
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/;words=(?P<words>.+)$',
        'page', name="openoni_page_words"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/print/image_813x1024_from_0,0_to_6504,8192
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/print/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+)/$',
    'page_print', name="openoni_page_print"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr/
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr/$',
        'page_ocr', name="openoni_page_ocr"),

    url(r'^newspapers/$', 'newspapers', name='openoni_newspapers'),
    url(r'^newspapers/feed/$', 'newspapers_atom', name='openoni_newspapers_atom'),

    url(r'^newspapers.(?P<format>csv)$', 'newspapers',
        name='openoni_newspapers_format'),
    url(r'^newspapers.(?P<format>txt)$', 'newspapers', 
        name='openoni_newspapers_format'),
    url(r'^newspapers.(?P<format>json)$', 'newspapers', 
        name='openoni_newspapers_format'),

    url(r'^newspapers/(?P<state>[^/;]+)/$', 'newspapers', 
        name='openoni_newspapers_state'),
    url(r'^newspapers/(?P<state>[^/;]+)\.(?P<format>json)$', 'newspapers', 
        name='openoni_newspapers_json'),

    url('search/pages/opensearch.xml', 'search_pages_opensearch',
        name='openoni_search_pages_opensearch'),
    url(r'^search/pages/results/$', 'search_pages_results',
        name='openoni_search_pages_results'),
    url(r'^search/pages/results/(?P<view_type>list)/$', 'search_pages_results',
        name='openoni_search_pages_results_list'),

    url('search/titles/opensearch.xml', 'search_titles_opensearch',
        name='openoni_search_titles_opensearch'),
    url(r'^search/titles/$', 'search_titles', 
        name="openoni_search_titles"),
    url(r'^search/titles/results/$', 'search_titles_results', 
        name='openoni_search_titles_results'),
    url(r'^suggest/titles/$', 'suggest_titles',
        name='openoni_suggest_titles'),

    url(r'^search/pages/navigation/$', search.search_pages_navigation,
        name='openoni_search_pages_navigation'),

    url(r'^search/advanced/$', search.search_advanced,
        name='openoni_search_advanced'),

    url(r'^events/$', 'events', name='openoni_events'),
    url(r'^events\.csv$', 'events_csv', name='openoni_events_csv'),
    url(r'^events/(?P<page_number>\d+)/$', 'events',
        name='openoni_events_page'),
    url(r'^events/feed/$', 'events_atom', name='openoni_events_atom'),
    url(r'^events/feed/(?P<page_number>\d+)/$', 'events_atom',
        name='openoni_events_atom_page'),
    url(r'^event/(?P<event_id>.+)/$', 'event', name='openoni_event'),
    url(r'^awardees/$', 'awardees', name='openoni_awardees'),
    url(r'^awardees.json$', 'awardees_json', name='openoni_awardees_json'),

    # example: /titles
    url(r'^titles/$', 'titles', name='openoni_titles'),

    # example: /titles;page=5
    url(r'^titles/;page=(?P<page_number>\d+)$', 'titles', 
            name='openoni_titles_page'),

    # example: /titles;start=F
    url(r'^titles/;start=(?P<start>\w)$', 'titles', name='openoni_titles_start'),

    # example: /titles;start=F;page=5
    url(r'^titles/;start=(?P<start>\w);page=(?P<page_number>\d+)$', 
        'titles', name='openoni_titles_start_page'),

    # example: /titles/places/pennsylvania
    url(r'^titles/places/(?P<state>[^/;]+)/$', 'titles_in_state', 
        name='openoni_state'),

    # example: /titles/places/pennsylvania;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/;page=(?P<page_number>\d+)$',
        'titles_in_state', name='openoni_state_page_number'), 

    # example: /titles/places/pennsylvania;page=1;order=title
    url(r'^titles/places/(?P<state>[^;]+)/;page=(?P<page_number>\d+);(?P<order>\w+)$', 
        'titles_in_state', name='openoni_state_page_number'), 

    # example /titles/places/pennsylvania/allegheny
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/$', 
        'titles_in_county', name='openoni_county'),

    # example /titles/places/pennsylvania/allegheny;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/;page=(?P<page_number>\d+)$', 
        'titles_in_county', name='openoni_county_page_number'),

    # example: /titles/places/pennsylvania/allegheny/pittsburgh
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/(?P<city>[^/;]+)/$', 
        'titles_in_city', name='openoni_city'),

    # example: /titles/places/pennsylvania/allegheny/pittsburgh;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/]+)/(?P<city>[^/;]+)/;page=(?P<page_number>\d+)$', 
        'titles_in_city', name='openoni_city_page_number'),

    # example: # /titles/places/pennsylvania/allegheny/pittsburgh;page=1;order=title
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/(?P<city>[^/;]+)/;page=(?P<page_number>\d+);(?P<order>\w+)$', 
        'titles_in_city', name='openoni_city_page_number'),

    # example: /states
    url(r'^states/$', 'states', name='openoni_states'),

    # example: /states_counties/
    url(r'^states_counties/$', 'states_counties', name='openoni_states_counties'),

    # example: /states.json
    url(r'^states\.(?P<format>json)$', 'states', name='openoni_states_json'),

    # example: /counties/pennsylvania
    url(r'^counties/(?P<state>[^/;]+)/$', 'counties_in_state', name='openoni_counties_in_state'),

    # example: /counties/pennsylvania.json
    url(r'^counties/(?P<state>[^/;]+)\.(?P<format>json)$', 'counties_in_state', name='openoni_counties_in_state_json'),

    # example: /cities/pennsylvania/allegheny
    url(r'^cities/(?P<state>[^/;]+)/(?P<county>[^/]+)/$', 'cities_in_county', name='openoni_cities_in_county'),

    # example: /cities/pennsylvania/allegheny.json
    url(r'^cities/(?P<state>[^/;]+)/(?P<county>[^/]+)\.(?P<format>json)$', 'cities_in_county', name='openoni_cities_in_county_json'),

    # example: /cities/pennsylvania
    url(r'^cities/(?P<state>[^/;]+)/$', 'cities_in_state', name='openoni_cities_in_state'),

    # example: /cities/pennsylvania.json
    url(r'^cities/(?P<state>[^/;]+)\.(?P<format>json)$', 'cities_in_state', name='openoni_cities_in_state_json'),

    # example: /institutions
    url(r'^institutions/$', 'institutions', name='openoni_institutions'),
    
    # example: /institutions;page=5
    url(r'^institutions/;page=(?P<page_number>\d+)$', 'institutions', 
        name='openoni_institutions_page_number'),

    # example: /institutions/cuy
    url(r'^institutions/(?P<code>[^/]+)/$', 'institution',
        name='openoni_institution'),

    # example: /institutions/cuy/titles
    url(r'^institutions/(?P<code>[^/]+)/titles/$', 'institution_titles',
        name='openoni_institution_titles'),

    # example: /institutions/cuy/titles/5/
    url(r'^institutions/(?P<code>[^/]+)/titles/(?P<page_number>\d+)/$', 
        'institution_titles', name='openoni_institution_titles_page_number'),

    # awardee
    url(r'^awardees/(?P<institution_code>\w+)/$', 'awardee', 
        name='openoni_awardee'),
    url(r'^awardees/(?P<institution_code>\w+).json$', 'awardee_json', name='openoni_awardee_json'),


    url(r'^status', 'status', name='openoni_stats'),

)

# linked-data rdf/atom/json views

urlpatterns += patterns(
    'openoni.core.views',

    # newspapers
    url(r'^newspapers.rdf$', 'newspapers_rdf', name="openoni_newspapers_dot_rdf"),
    url(r'^newspapers$', 'newspapers_rdf', name="openoni_newspapers_rdf"),

    # title
    url(r'^lccn/(?P<lccn>\w+).rdf$', 'title_rdf', name='openoni_title_dot_rdf'),
    url(r'^lccn/(?P<lccn>\w+)$', 'title_rdf', name='openoni_title_rdf'),
    url(r'^lccn/(?P<lccn>\w+).json', 'title_json', name='openoni_title_dot_json'),

    # issue
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+).rdf$', 'issue_pages_rdf', name='openoni_issue_pages_dot_rdf'),
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+).json$', 'issue_pages_json', name='openoni_issue_pages_dot_json'),
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)$', 'issue_pages_rdf', name='openoni_issue_pages_rdf'),

    # page
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).rdf$', 'page_rdf', name="openoni_page_dot_rdf"),
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).json$', 'page_json', name="openoni_page_dot_json"),
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)$', 'page_rdf', name="openoni_page_rdf"),

    # awardee
    url(r'^awardees/(?P<institution_code>\w+).rdf$', 'awardee_rdf', name='openoni_awardee_dot_rdf'),
    url(r'^awardees/(?P<institution_code>\w+)$', 'awardee_rdf', name='openoni_awardee_rdf'),

    # ndnp vocabulary
    url(r'^terms/.*$', 'terms', name='openoni_terms'),

    # flickr report
    url(r'^flickr/$', 'pages_on_flickr', name='openoni_pages_on_flickr'),

    # batch summary
    url(r'^batches/summary/$', 'batch_summary', name='openoni_batch_summary'),
    url(r'^batches/summary.(?P<format>txt)$', 'batch_summary', 
        name='openoni_batch_summary_txt'),

    # batch view
    url(r'^batches/$', 'batches', name='openoni_batches'),
    url(r'^batches/;page=(?P<page_number>\d+)$', 'batches', 
        name='openoni_batches_page'),
    url(r'^batches/feed/$', 'batches_atom', name='openoni_batches_atom'),
    url(r'^batches/feed/(?P<page_number>\d+)/$','batches_atom',
        name='openoni_batches_atom_page'), 
    url(r'^batches\.json$', 'batches_json', name='openoni_batches_json'),
    url(r'^batches\.csv$', 'batches_csv', name='openoni_batches_csv'),
    url(r'^batches/(?P<page_number>\d+).json$', 'batches_json',
        name='openoni_batches_json_page'),
    url(r'^batches/(?P<batch_name>.+)/$', 'batch', name='openoni_batch'),
    url(r'^batches/(?P<batch_name>.+).rdf$', 'batch_rdf', 
        name='openoni_batch_dot_rdf'),
    url(r'^batches/(?P<batch_name>.+)\.json$', 'batch_json', 
        name='openoni_batch_dot_json'),
    url(r'^batches/(?P<batch_name>.+)$', 'batch_rdf', name='openoni_batch_rdf'),

    # reels 
    url(r'^reels/$', 'reels', name='openoni_reels'),
    url(r'^reels/;page=(?P<page_number>\d+)$', 'reels', 
        name='openoni_reels_page'),
    url(r'^reel/(?P<reel_number>\w+)/$', 'reel', name='openoni_reel'),
 
    # languages 
    url(r'^languages/$', 'languages', name='openoni_languages'),
    url(r'^languages/(?P<language>.+)/batches/$', 'language_batches',
        name='openoni_language_batches'),
    url(r'^languages/(?P<language>.+)/batches/;page=(?P<page_number>\d+)$', 'language_batches',
        name='openoni_language_batches_page_number'),
    url(r'^languages/(?P<language>.+)/titles/$', 'language_titles',
        name='openoni_language_titles'),
    url(r'^languages/(?P<language>.+)/titles/;page=(?P<page_number>\d+)$', 'language_titles',
        name='openoni_language_titles_page_number'),
    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/(?P<title>.+)/$', 'language_pages',
        name='openoni_language_title_pages'),
    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/(?P<title>.+)/;page=(?P<page_number>\d+)$', 'language_pages',
        name='openoni_language_title_pages_page_number'),
    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/$', 'language_pages',
        name='openoni_language_batch_pages'),
    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/;page=(?P<page_number>\d+)$', 'language_pages',
        name='openoni_language_batch_pages_page_number'),

    # reports 
    url(r'^reports/$', 'reports', name='openoni_reports'),

    # ocr data
    url(r'^ocr/feed/$', 'ocr_atom', name='openoni_ocr_atom'),
    url(r'^ocr.json$', 'ocr_json', name='openoni_ocr_json'),
    
)

_ROOT = os.path.abspath(os.path.dirname(__file__))
_MEDIA_ROOT = os.path.join(_ROOT, 'media')

# these are static files that will normally be served up by apache
# in production deployments before django ever sees the request
# but are useful when running in development environments

urlpatterns += patterns(
    '',

    url(r'^data/(?P<path>.*)$', 'django.views.static.serve', 
        {'document_root': _MEDIA_ROOT}, name="openoni_data_files"),

    url(r'^(?P<path>sitemap.*)$', 'django.views.static.serve',
        {'document_root': _MEDIA_ROOT + '/sitemaps'},
        name="openoni_sitemaps"),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
