from django.conf.urls.defaults import patterns, url, include


urlpatterns = patterns(
    '',

    (r'^', include('chronam.web.urls')),

)
