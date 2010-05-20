import re
import datetime


def solrdate_to_date(n):
    """
    convert the date number in solr docs into a nicer string
    19001225 => datetime.date(1900, 12, 25)
    """
    n = str(n)
    match = re.match(r'^(\d\d\d\d)(\d\d)(\d\d)$', n)
    if match:
        try:
            return datetime.date(int(match.group(1)), 
                                 int(match.group(2)), int(match.group(3)))
        except ValueError, ve:
            return None
    return None




