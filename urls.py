import os

from django.conf.urls import url, include
from django.conf import settings
from django.utils import cache
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

import chronam.core.views as views

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

urlpatterns = [

    url(r'^$',
        cache_page(views.home.home, settings.DEFAULT_TTL_SECONDS),
        name="chronam_home"),

    url(r'^(?P<date>\d{4}-\d{2}-\d{2})/$', 
        cache_page(views.home.home, settings.DEFAULT_TTL_SECONDS),
        name="chronam_home_date"),

    url(r'^frontpages/(?P<date>\d{4}-\d{1,2}-\d{1,2}).json$',
        cache_page(views.home.frontpages, settings.DEFAULT_TTL_SECONDS),
        name="chronam_frontpages_date_json"),

    url(r'^tabs$',
        cache_page(views.home.tabs, settings.DEFAULT_TTL_SECONDS),
        name="chronam_tabs"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/thumbnail.jpg$',
        cache_page(views.image.thumbnail, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_page_thumbnail"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/medium.jpg$',
        cache_page(views.image.medium, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_page_medium"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024_from_0,0_to_6504,8192.jpg
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+).jpg$',
        cache_page(views.image.page_image_tile, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_page_image_tile"),

    # example: /tiles/batch_dlc_jamaica_ver01/data/sn83030214/00175042143/1903051701/0299.jp2/image_813x1024_from_0,0_to_6504,8192.jpg
    url(r'^images/tiles/(?P<path>.+)/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+).jpg$',
        cache_page(views.image.image_tile, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_image_tile"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024.jpg
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/image_(?P<width>\d+)x(?P<height>\d+).jpg$',
        cache_page(views.image.page_image, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_page_image"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/coordinates/
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/coordinates/$',
        cache_page(views.image.coordinates, settings.PAGE_IMAGE_TTL_SECONDS),
        name="chronam_page_coordinates"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/coordinates/;words=corn+peas+cigars
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/coordinates/;words=(?P<words>.+)$',
        cache_page(views.image.coordinates, settings.DEFAULT_TTL_SECONDS),
        name="chronam_page_coordinates_words"),
]

urlpatterns += [

    url(r'^about/$', 
        views.about, 
        name="chronam_about"),

    url(r'^help/$', 
        views.help, 
        name="chronam_help"),

    # explainOCR.html
    url(r'^ocr/$', 
        views.ocr, 
        name="chronam_ocr"),

    # recommended topics
    url(r'^recommended-topics/$', 
        views.recommended_topics, 
        name="recommended_topics"),

    # topic page
    url(r'^recommended-topics/(?P<topic_id>\d+)/$', 
        views.chronam_topic, 
        name="chronam_topic"),

    # API docs
    url(r'^about/api/$', 
        views.about_api, 
        name="chronam_about_api"),

    # example: /lccn/sn85066387
    url(r'^lccn/(?P<lccn>\w+)/$', 
        views.title, 
        name="chronam_title"),

    # example: /lccn/sn85066387/issues/
    url(r'^lccn/(?P<lccn>\w+)/issues/$', 
        views.issues, 
        name="chronam_issues"),

    # example: /lccn/sn85066387/issues/1900
    url(r'^lccn/(?P<lccn>\w+)/issues/(?P<year>\d{4})/$', 
        views.issues, 
        name="chronam_issues_for_year"),

    # example: /lccn/sn85066387/issues/first_pages
    url(r'^lccn/(?P<lccn>\w+)/issues/first_pages/$', 
        views.issues_first_pages, 
        name="chronam_issues_first_pages"),

    # example: /lccn/sn85066387/issues/first_pages/3
    url(r'^lccn/(?P<lccn>\w+)/issues/first_pages/(?P<page_number>\d+)/$', 
        views.issues_first_pages, 
        name="chronam_issues_first_pages_page_number"),

    # example: /lccn/sn85066387/marc
    url(r'^lccn/(?P<lccn>\w+)/marc/$', 
        views.title_marc, 
        name="chronam_title_marc"),

    # example: /lccn/sn85066387/feed/
    url(r'^lccn/(?P<lccn>\w+)/feed/$', 
        views.title_atom, 
        name='chronam_title_atom'),

    # example: /lccn/sn85066387/feed/10
    url(r'^lccn/(?P<lccn>\w+)/feed/(?P<page_number>\w+)$', 
        views.title_atom,
        name='chronam_title_atom_page'),

    # example: /lccn/sn85066387/marc.xml
    url(r'^lccn/(?P<lccn>\w+)/marc.xml$', 
        views.title_marcxml,
        name="chronam_title_marcxml"),

    # example: /lccn/sn85066387/holdings
    url(r'^lccn/(?P<lccn>\w+)/holdings/$', 
        views.title_holdings,
        name="chronam_title_holdings"),

    # example: /essays/
    url(r'^essays/$', 
        views.essays, 
        name='chronam_essays'),

    # example: /essays/1/
    url(r'^essays/(?P<essay_id>\d+)/$', 
        views.essay, 
        name='chronam_essay'),

    # TOD0: remove this some suitable time after 08/2010 since it
    # permanently redirects to new essay id based URL
    # example: /lccn/sn85066387/essay
    url(r'^lccn/(?P<lccn>\w+)/essays/$', 
        views.title_essays, 
        name="chronam_title_essays"),

    # example: /lccn/sn85066387/1907-03-17/ed-1
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/$',
        views.issue_pages, 
        name="chronam_issue_pages"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/1
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/(?P<page_number>\d+)/$', 
        views.issue_pages, 
        name="chronam_issue_pages_page_number"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/$',
        views.page, 
        name="chronam_page"),
        
    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4.pdf
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).pdf$',
        views.page_pdf, 
        name="chronam_page_pdf"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4.jp2
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).jp2$',
        views.page_jp2, 
        name="chronam_page_jp2"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr.xml
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr.xml$',
        views.page_ocr_xml, 
        name="chronam_page_ocr_xml"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr.txt
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr.txt$',
        views.page_ocr_txt, 
        name="chronam_page_ocr_txt"),
        
    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/;words=
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/;words=(?P<words>.+)$',
        views.page, 
        name="chronam_page_words"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/print/image_813x1024_from_0,0_to_6504,8192
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/print/image_(?P<width>\d+)x(?P<height>\d+)_from_(?P<x1>\d+),(?P<y1>\d+)_to_(?P<x2>\d+),(?P<y2>\d+)/$',
        views.page_print, 
        name="chronam_page_print"),

    # example: /lccn/sn85066387/1907-03-17/ed-1/seq-4/ocr/
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)/ocr/$',
        views.page_ocr, 
        name="chronam_page_ocr"),

    url(r'^newspapers/$', 
        views.newspapers, 
        name='chronam_newspapers'),

    url(r'^newspapers/feed/$', 
        views.newspapers_atom, 
        name='chronam_newspapers_atom'),

    url(r'^newspapers.(?P<format>csv)$', 
        views.newspapers,
        name='chronam_newspapers_format'),

    url(r'^newspapers.(?P<format>txt)$', 
        views.newspapers, 
        name='chronam_newspapers_format'),

    url(r'^newspapers.(?P<format>json)$', 
        views.newspapers, 
        name='chronam_newspapers_format'),

    url(r'^newspapers/(?P<state>[^/;]+)/$', 
        views.newspapers, 
        name='chronam_newspapers_state'),

    url(r'^newspapers/(?P<state>[^/;]+)\.(?P<format>json)$', 
        views.newspapers, 
        name='chronam_newspapers_json'),

    url('search/pages/opensearch.xml', 
        views.search_pages_opensearch,
        name='chronam_search_pages_opensearch'),

    url(r'^search/pages/results/$', 
        views.search_pages_results,
        name='chronam_search_pages_results'),

    url(r'^search/pages/results/(?P<view_type>list)/$', 
        views.search_pages_results,
        name='chronam_search_pages_results_list'),

    url('search/titles/opensearch.xml', 
        views.search_titles_opensearch,
        name='chronam_search_titles_opensearch'),

    url(r'^search/titles/$', 
        views.search_titles, 
        name="chronam_search_titles"),

    url(r'^search/titles/results/$', 
        views.search_titles_results, 
        name='chronam_search_titles_results'),

    url(r'^suggest/titles/$', 
        views.suggest_titles,
        name='chronam_suggest_titles'),

    url(r'^search/pages/navigation/$', 
        views.search_pages_navigation,
        name='chronam_search_pages_navigation'),

    url(r'^search/advanced/$', 
        views.search_advanced,
        name='chronam_search_advanced'),

    url(r'^events/$', 
        views.events, 
        name='chronam_events'),

    url(r'^events\.csv$', 
        views.events_csv, 
        name='chronam_events_csv'),

    url(r'^events/(?P<page_number>\d+)/$', 
        views.events,
        name='chronam_events_page'),

    url(r'^events/feed/$', 
        views.events_atom, 
        name='chronam_events_atom'),

    url(r'^events/feed/(?P<page_number>\d+)/$', 
        views.events_atom,
        name='chronam_events_atom_page'),

    url(r'^event/(?P<event_id>.+)/$', 
        views.event, 
        name='chronam_event'),

    url(r'^awardees/$', 
        views.awardees, 
        name='chronam_awardees'),

    url(r'^awardees.json$', 
        views.awardees_json, 
        name='chronam_awardees_json'),

    # example: /titles
    url(r'^titles/$', 
        views.titles, 
        name='chronam_titles'),

    # example: /titles;page=5
    url(r'^titles/;page=(?P<page_number>\d+)$', 
        views.titles, 
        name='chronam_titles_page'),

    # example: /titles;start=F
    url(r'^titles/;start=(?P<start>\w)$', 
        views.titles, 
        name='chronam_titles_start'),

    # example: /titles;start=F;page=5
    url(r'^titles/;start=(?P<start>\w);page=(?P<page_number>\d+)$', 
        views.titles, 
        name='chronam_titles_start_page'),

    # example: /titles/places/pennsylvania
    url(r'^titles/places/(?P<state>[^/;]+)/$', 
        views.titles_in_state, 
        name='chronam_state'),

    # example: /titles/places/pennsylvania;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/;page=(?P<page_number>\d+)$',
        views.titles_in_state, 
        name='chronam_state_page_number'), 

    # example: /titles/places/pennsylvania;page=1;order=title
    url(r'^titles/places/(?P<state>[^;]+)/;page=(?P<page_number>\d+);(?P<order>\w+)$', 
        views.titles_in_state, 
        name='chronam_state_page_number'), 

    # example /titles/places/pennsylvania/allegheny
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/$', 
        views.titles_in_county, 
        name='chronam_county'),

    # example /titles/places/pennsylvania/allegheny;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/;page=(?P<page_number>\d+)$', 
        views.titles_in_county, 
        name='chronam_county_page_number'),

    # example: /titles/places/pennsylvania/allegheny/pittsburgh
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/(?P<city>[^/;]+)/$', 
        views.titles_in_city, 
        name='chronam_city'),

    # example: /titles/places/pennsylvania/allegheny/pittsburgh;page=1
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/]+)/(?P<city>[^/;]+)/;page=(?P<page_number>\d+)$', 
        views.titles_in_city, 
        name='chronam_city_page_number'),

    # example: # /titles/places/pennsylvania/allegheny/pittsburgh;page=1;order=title
    url(r'^titles/places/(?P<state>[^/;]+)/(?P<county>[^/;]+)/(?P<city>[^/;]+)/;page=(?P<page_number>\d+);(?P<order>\w+)$', 
        views.titles_in_city, 
        name='chronam_city_page_number'),

    # example: /states
    url(r'^states/$', 
        views.states, 
        name='chronam_states'),

    # example: /states_counties/
    url(r'^states_counties/$', 
        views.states_counties, 
        name='chronam_states_counties'),

    # example: /states.json
    url(r'^states\.(?P<format>json)$', 
        views.states, 
        name='chronam_states_json'),

    # example: /counties/pennsylvania
    url(r'^counties/(?P<state>[^/;]+)/$', 
        views.counties_in_state, 
        name='chronam_counties_in_state'),

    # example: /counties/pennsylvania.json
    url(r'^counties/(?P<state>[^/;]+)\.(?P<format>json)$', 
        views.counties_in_state, 
        name='chronam_counties_in_state_json'),

    # example: /cities/pennsylvania/allegheny
    url(r'^cities/(?P<state>[^/;]+)/(?P<county>[^/]+)/$', 
        views.cities_in_county, 
        name='chronam_cities_in_county'),

    # example: /cities/pennsylvania/allegheny.json
    url(r'^cities/(?P<state>[^/;]+)/(?P<county>[^/]+)\.(?P<format>json)$', 
        views.cities_in_county, 
        name='chronam_cities_in_county_json'),

    # example: /cities/pennsylvania
    url(r'^cities/(?P<state>[^/;]+)/$', 
        views.cities_in_state, 
        name='chronam_cities_in_state'),

    # example: /cities/pennsylvania.json
    url(r'^cities/(?P<state>[^/;]+)\.(?P<format>json)$', 
        views.cities_in_state, 
        name='chronam_cities_in_state_json'),

    # example: /institutions
    url(r'^institutions/$', 
        views.institutions, 
        name='chronam_institutions'),
    
    # example: /institutions;page=5
    url(r'^institutions/;page=(?P<page_number>\d+)$', 
        views.institutions, 
        name='chronam_institutions_page_number'),

    # example: /institutions/cuy
    url(r'^institutions/(?P<code>[^/]+)/$', 
        views.institution,
        name='chronam_institution'),

    # example: /institutions/cuy/titles
    url(r'^institutions/(?P<code>[^/]+)/titles/$', 
        views.institution_titles,
        name='chronam_institution_titles'),

    # example: /institutions/cuy/titles/5/
    url(r'^institutions/(?P<code>[^/]+)/titles/(?P<page_number>\d+)/$', 
        views.institution_titles, 
        name='chronam_institution_titles_page_number'),

    # awardee
    url(r'^awardees/(?P<institution_code>\w+)/$', 
        views.awardee, 
        name='chronam_awardee'),

    url(r'^awardees/(?P<institution_code>\w+)/$', 
        views.awardee, 
        name='chronam_awardee'),

    url(r'^awardees/(?P<institution_code>\w+).json$', 
        views.awardee_json, 
        name='chronam_awardee_json'),


    url(r'^status', 
        views.status, 
        name='chronam_stats'),
]

# linked-data rdf/atom/json views

urlpatterns += [

    # newspapers
    url(r'^newspapers.rdf$', 
        views.newspapers_rdf, 
        name="chronam_newspapers_dot_rdf"),

    url(r'^newspapers$', 
        views.newspapers_rdf, 
        name="chronam_newspapers_rdf"),

    # title
    url(r'^lccn/(?P<lccn>\w+).rdf$', 
        views.title_rdf, 
        name='chronam_title_dot_rdf'),

    url(r'^lccn/(?P<lccn>\w+)$', 
        views.title_rdf, 
        name='chronam_title_rdf'),

    url(r'^lccn/(?P<lccn>\w+).json', 
        views.title_json, 
        name='chronam_title_dot_json'),

    # issue
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+).rdf$', 
        views.issue_pages_rdf, 
        name='chronam_issue_pages_dot_rdf'),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+).json$', 
        views.issue_pages_json, 
        name='chronam_issue_pages_dot_json'),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)$', 
        views.issue_pages_rdf, 
        name='chronam_issue_pages_rdf'),

    # page
    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).rdf$', 
        views.page_rdf, 
        name="chronam_page_dot_rdf"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+).json$', 
        views.page_json, 
        name="chronam_page_dot_json"),

    url(r'^lccn/(?P<lccn>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/ed-(?P<edition>\d+)/seq-(?P<sequence>\d+)$', 
        views.page_rdf, 
        name="chronam_page_rdf"),

    # awardee
    url(r'^awardees/(?P<institution_code>\w+).rdf$', 
        views.awardee_rdf, 
        name='chronam_awardee_dot_rdf'),

    url(r'^awardees/(?P<institution_code>\w+)$', 
        views.awardee_rdf, 
        name='chronam_awardee_rdf'),

    # ndnp vocabulary
    url(r'^terms/.*$', 
        views.terms, 
        name='chronam_terms'),

    # flickr report
    url(r'^flickr/$', 
        views.pages_on_flickr, 
        name='chronam_pages_on_flickr'),

    # batch summary
    url(r'^batches/summary/$', 
        views.batch_summary, 
        name='chronam_batch_summary'),

    url(r'^batches/summary.(?P<format>txt)$', 
        views.batch_summary, 
        name='chronam_batch_summary_txt'),

    # batch view
    url(r'^batches/$', 
        views.batches, 
        name='chronam_batches'),

    url(r'^batches/;page=(?P<page_number>\d+)$', 
        views.batches, 
        name='chronam_batches_page'),

    url(r'^batches/feed/$', 
        views.batches_atom, 
        name='chronam_batches_atom'),

    url(r'^batches/feed/(?P<page_number>\d+)/$', 
        views.batches_atom,
        name='chronam_batches_atom_page'), 

    url(r'^batches\.json$', 
        views.batches_json, 
        name='chronam_batches_json'),

    url(r'^batches\.csv$', 
        views.batches_csv, 
        name='chronam_batches_csv'),

    url(r'^batches/(?P<page_number>\d+).json$', 
        views.batches_json,
        name='chronam_batches_json_page'),

    url(r'^batches/(?P<batch_name>.+)/$', 
        views.batch, 
        name='chronam_batch'),

    url(r'^batches/(?P<batch_name>.+).rdf$', 
        views.batch_rdf, 
        name='chronam_batch_dot_rdf'),

    url(r'^batches/(?P<batch_name>.+)\.json$', 
        views.batch_json, 
        name='chronam_batch_dot_json'),

    url(r'^batches/(?P<batch_name>.+)$', 
        views.batch_rdf, 
        name='chronam_batch_rdf'),

    # reels 
    url(r'^reels/$', 
        views.reels, 
        name='chronam_reels'),

    url(r'^reels/;page=(?P<page_number>\d+)$', 
        views.reels, 
        name='chronam_reels_page'),

    url(r'^reel/(?P<reel_number>\w+)/$', 
        views.reel, 
        name='chronam_reel'),
 
    # languages 
    url(r'^languages/$', 
        views.languages, 
        name='chronam_languages'),

    url(r'^languages/(?P<language>.+)/batches/$', 
        views.language_batches,
        name='chronam_language_batches'),

    url(r'^languages/(?P<language>.+)/batches/;page=(?P<page_number>\d+)$', 
        views.language_batches,
        name='chronam_language_batches_page_number'),

    url(r'^languages/(?P<language>.+)/titles/$', 
        views.language_titles,
        name='chronam_language_titles'),

    url(r'^languages/(?P<language>.+)/titles/;page=(?P<page_number>\d+)$', 
        views.language_titles,
        name='chronam_language_titles_page_number'),

    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/(?P<title>.+)/$', 
        views.language_pages,
        name='chronam_language_title_pages'),

    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/(?P<title>.+)/;page=(?P<page_number>\d+)$', 
        views.language_pages,
        name='chronam_language_title_pages_page_number'),

    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/$', 
        views.language_pages,
        name='chronam_language_batch_pages'),

    url(r'^languages/(?P<language>.+)/(?P<batch>.+)/;page=(?P<page_number>\d+)$', 
        views.language_pages,
        name='chronam_language_batch_pages_page_number'),

    # reports 
    url(r'^reports/$', 
        views.reports, 
        name='chronam_reports'),

    # ocr data
    url(r'^ocr/feed/$', 
        views.ocr_atom, 
        name='chronam_ocr_atom'),

    url(r'^ocr.json$', 
        views.ocr_json, 
        name='chronam_ocr_json'),   
]

_ROOT = os.path.abspath(os.path.dirname(__file__))
_MEDIA_ROOT = os.path.join(_ROOT, 'media')

# these are static files that will normally be served up by apache
# in production deployments before django ever sees the request
# but are useful when running in development environments

urlpatterns += [
    url(r'^data/(?P<path>.*)$', 
        serve, 
        {'document_root': _MEDIA_ROOT}, 
        name="chronam_data_files"),

    url(r'^(?P<path>sitemap.*)$', 
        serve,
        {'document_root': _MEDIA_ROOT + '/sitemaps'},
        name="chronam_sitemaps"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
