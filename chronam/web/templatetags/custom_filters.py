from django import template
from django.template.defaultfilters import stringfilter

import chronam.utils
from chronam.utils.rfc3339 import rfc3339

register = template.Library()

@register.filter(name='rfc3339')
def rfc3339_filter(d):
    return rfc3339(d)

@stringfilter
def pack_url(value):
    return chronam.utils.pack_url_path(value)

register.filter('pack_url', pack_url)

