from django.test import TestCase

class BrowseTests(TestCase):
    """
    Tests to ensure that caching for specific pages stays correct
    """

    #As per CHRONAM-372 make sure specific pages have specific cache times
    def test_caching_times(self):
        one_day = 86400
        two_months = 60 * 60 * 24 * 7 * 8
        never = 0
        url_cache_times = {"/#tab=tab_search": one_day,
                "/#tab=tab_advanced_search": one_day,
                "/#tab=tab_newspapers": one_day,
                "/newspapers/": one_day,
                "/essays/": one_day,
                "/awardees/": one_day,
                "/search/titles/" : one_day,
                "/batches/": never,
                "/events/": never,
                "/status": never,
                "/languages": never,
                "/titles": two_months,
                "/states": two_months,
                "/institutions/": two_months,
                "/": one_day,
                "/terms/": two_months,
                "/reports/": two_months,
                "/reels/": one_day,
                "/ocr/": one_day,
                "/about/": two_months,
                "/about/api/": two_months,
                "/help/": two_months}
        
        for url, cache_time in url_cache_times.iteritems():
            try:
                response = self.client.get(url)
                cache_header = response['Cache-Control']
                max_age = cache_header.split("=")[1]
                self.assertEqual(int(max_age), cache_time, msg="url [%s] is supposed to have cache time of [%s] but was [%s]" % (url, cache_time, max_age))
            except KeyError:
                if cache_time > 0:
                    self.assertRaises("cache_time is supposed to be [%s], but was not in the header for url [%s]" % (cache_time, url))
