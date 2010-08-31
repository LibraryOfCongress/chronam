from django import template
from django.template.defaultfilters import stringfilter

from rfc3339 import rfc3339

from chronam.utils import url



register = template.Library()

@register.filter(name='rfc3339')
def rfc3339_filter(d):
    return rfc3339(d)

def pack_url(value, default='-'):
    return url.pack_url_path(value, default)

register.filter('pack_url', pack_url)

