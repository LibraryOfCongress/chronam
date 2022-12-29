import urllib2
import urllib
from exceptions import StopIteration

from worldcat.exceptions import APIKeyError, APIKeyNotSpecifiedError, \
                                EmptyQueryError, EmptyRecordNumberError, \
                                InvalidArgumentError, ExtractError
from worldcat.request.search import SearchAPIRequest
from worldcat.util.extract import extract_elements


# SRURequestV2 class was created to replace the existing SRURequest class in WorldCat that has an incorrect API URL which is causing 
# breakage with our pull_titles.py script.  This class is a copy of the existing SRURequest class with the exception of the api_url()
# method which has been updated to use the correct API URL.  This class should be removed once the WorldCat API is fixed.
# http_get is also overidden to include User-Agent in request to prevent OCLC API from missclassifying our requests as spam.
class SRURequestV2(SearchAPIRequest):
    """request.search.NewSRURequest: queries search API using SRU
    SRURequests should be used when fielded searching is desired.
    """

    def __init__(self, **kwargs):
        """Constructor method for WorldCatRequests."""
        SearchAPIRequest.__init__(self, **kwargs)

    def __iter__(self):
        return self

    def api_url(self):
        # Updated URL to use the correct API URL
        self.url = 'http://worldcat.org/webservices/catalog/search/worldcat/sru'

    def next(self):
        _i = extract_elements(self.response,
                element='{http://www.loc.gov/zing/srw/}nextRecordPosition')
        if len(_i) != 0:
            if _i[0].text is not None:
                self.args['startRecord'] = int(_i[0].text)
            else:
                raise StopIteration
        else:
            raise StopIteration

    def subclass_validator(self, quiet=False):
        """Validator method for SRURequests."""
        if 'query' not in self.args:
            if quiet == True:
                return False
            else:
                raise EmptyQueryError
        else:
            return True

    def http_get(self):
        """HTTP Get method for all WorldCatRequests."""
        self.api_url()
        _query_url = '%s?%s' % (self.url, urllib.urlencode(self.args))
        # Added User-Agent to request to prevent OCLC API from missclassifying our requests as spam.
        request = urllib2.Request(_query_url, headers={'User-Agent' : "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2)"})
        self.response = urllib2.urlopen(request).read()
