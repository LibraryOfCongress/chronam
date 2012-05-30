from django.conf import settings
from chronam.core.decorator import cache_page
from django.shortcuts import render_to_response
from django.template import RequestContext

@cache_page(settings.DEFAULT_TTL_SECONDS)
def about(request):
    page_title = "About Chronicling America"
    return render_to_response('about.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def about_api(request):
    page_title = "About the Site and API"
    return render_to_response('about_api.html', dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def help(request):
    page_title = "Help"
    return render_to_response('help.html', dictionary=locals(),
                              context_instance=RequestContext(request))
