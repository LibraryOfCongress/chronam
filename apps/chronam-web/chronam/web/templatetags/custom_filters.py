from django import template
from django.template.defaultfilters import stringfilter

from chronam.utils import url
from chronam.utils.rfc3339 import rfc3339


register = template.Library()

@register.filter(name='rfc3339')
def rfc3339_filter(d):
    return rfc3339(d)

def pack_url(value, default='-'):
    return url.pack_url_path(value, default)

register.filter('pack_url', pack_url)

