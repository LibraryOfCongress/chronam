from chronam import settings

def extra_request_info (request):
    """
    Add some extra useful stuff into the RequestContext.
    """
    return {
        'site_title': 'Chronicling America',
        'script_name': request.META['SCRIPT_NAME'],
        'omniture_url': settings.OMNITURE_SCRIPT
        }
