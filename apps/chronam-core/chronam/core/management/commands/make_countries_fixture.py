from xml.etree import ElementTree

import urllib
try:
    import simplejson as json
except ImportError:
    import json

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "loads MARC Country list XML from the web, and dumps JSON fixture to stdout"

    def handle(self, *args, **options):
        uri = 'http://www.loc.gov/standards/codelists/countries.xml'
        xml = urllib.urlopen(uri)
        doc = ElementTree.parse(xml)
        countries = []

        for country in doc.findall('.//{info:lc/xmlns/codelist-v1}country'):
            name = country.findtext('./{info:lc/xmlns/codelist-v1}name')
            code = country.findtext('./{info:lc/xmlns/codelist-v1}code')
            region = country.findtext('./{info:lc/xmlns/codelist-v1}region')
            countries.append({'pk': code, 'model': 'core.countries', 
                              'fields': {'name': name, 'region': region}})

        print json.dumps(countries, indent=2)

