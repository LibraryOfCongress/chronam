import os.path

from django.test import TestCase

from chronam.web.models import Title
from chronam.web.title_loader import TitleLoader
from chronam.web.holding_loader import HoldingLoader

import chronam.web

class HoldingLoaderTests(TestCase):
    fixtures = ['countries.json', 'languages.json', 'institutions.json']

    def test_holdings(self):
        # the combined title/holdings data
        marcxml = os.path.join(os.path.dirname(chronam.web.__file__), 
            'test-data', 'bib.xml')

        # first need to load the titles so we can link against them
        title_loader = TitleLoader()
        title_loader.load_file(marcxml)

        # now load the holdings from the same file
        holding_loader = HoldingLoader()
        holding_loader.load_file(marcxml)

        # fetch the title and see that holdings are attached
        t = Title.objects.get(lccn='sn83030846')
        holdings = list(t.holdings.all())
        self.assertEqual(len(holdings), 5)
        h = holdings[1]
        self.assertEqual(h.institution.name, 'Enfield Free Pub Libr')
        self.assertEqual(h.type, 'Original')
        self.assertEqual(h.description, '<1978:1:4, 3:2, 9:28-12:21> <1979:1:11, 3:29, 4:12-8:9>')
        self.assertEqual(h.description_as_list(), ['<1978:1:4, 3:2, 9:28-12:21>', '<1979:1:11, 3:29, 4:12-8:9>'])
        self.assertEqual(str(h.last_updated), '10/1991')
