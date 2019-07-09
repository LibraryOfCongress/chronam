from django.conf import settings

from chronam.core.forms import _fulltext_range


def extra_request_info(request):
    """
    Add some extra useful stuff into the RequestContext.
    """
    fulltext_range = _fulltext_range()
    return {
        "site_title": "Chronicling America",
        "omniture_url": getattr(settings, "OMNITURE_SCRIPT", None),
        "sharetool_url": getattr(settings, "SHARETOOL_URL", None),
        "SENTRY_PUBLIC_DSN": getattr(settings, "SENTRY_PUBLIC_DSN", None),
        'ENVIRONMENT': getattr(
            settings, 'ENVIRONMENT', 'production' if settings.IS_PRODUCTION else 'testing'
        ),
        'RELEASE': getattr(settings, 'RELEASE', 'unknown'),
        "fulltext_startdate": fulltext_range[0],
        "fulltext_enddate": fulltext_range[1],
    }
