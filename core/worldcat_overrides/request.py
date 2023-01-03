import urllib2
import urllib

from worldcat.request.search import SRURequest

# SRURequestV2 class was created to replace the existing SRURequest class in WorldCat that has an incorrect API URL which is causing 
# breakage with our pull_titles.py script.  This class is a copy of the existing SRURequest class with the exception of the api_url()
# method which has been updated to use the correct API URL.  This class should be removed once the WorldCat API is fixed.
# http_get is also overidden to include User-Agent in request to prevent OCLC API from missclassifying our requests as spam.
class SRURequestV2(SRURequest):
    def api_url(self):
        # Updated URL to use the correct API URL
        self.url = 'https://worldcat.org/webservices/catalog/search/worldcat/sru'

    def http_get(self):
        """HTTP Get method for all WorldCatRequests."""
        self.api_url()
        _query_url = '%s?%s' % (self.url, urllib.urlencode(self.args))
        # Added User-Agent to request to prevent OCLC API from missclassifying our requests as spam.
        request = urllib2.Request(_query_url, headers={'User-Agent' : "ChroniclingAmerica +https://github.com/LibraryOfCongress/chronam"})
        self.response = urllib2.urlopen(request).read()
