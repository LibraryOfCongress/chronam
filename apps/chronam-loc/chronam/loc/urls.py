from django.conf.urls.defaults import patterns, url
from django.conf import settings

from chronam.loc import views


urlpatterns = patterns(
    'chronam.loc.views',

    url(r'^$', views.home, name="home"),

)
