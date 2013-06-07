'''
Demo of an implementation of the pymarc library found here:
http://pypi.python.org/pypi/pymarc/

What does this script do?
This script returns a list of sample values for a directory of marc records. 
You could a adjust to return all if needed.

To run this file: python extract_cntry_from_worldcatrecs.py $path_to_bib_folder $FIELD $SUBFIELD
Example: python extract_marc_values.py /vol/ndnp/chronam/bib/holdings/ 852 a


This also useds: Chronam
Found here: http://github.com/LibraryOfCongress/chronam
'''


import glob
import operator
import os
import sys

from random import choice
from pymarc import map_xml
from django.db.models import Count

from chronam.core.models import Country
from chronam.core.title_loader import _extract as extract

# FOLDER should be the location of the marcxml files.
SOURCE = sys.argv[1]
FIELD = sys.argv[2]

try:
    SUBFIELD = sys.argv[3]
except IndexError:
    SUBFIELD = None

values = []

def parse_record(record, field=FIELD, subfield=SUBFIELD):
    value = extract(record, field, subfield)
    if value:
        rec_id = extract(record, '010', 'a')
        if not rec_id:
            rec_id = extract(record, '004')
        values.append((rec_id, value))

if __name__ == '__main__':
    if os.path.isdir(SOURCE):
        marc_xml_dir = os.listdir(SOURCE)
        for xml_file in marc_xml_dir:
            marc_file = os.path.join(SOURCE, xml_file)
            map_xml(parse_record, open(marc_file, 'r'))
    else:
        map_xml(parse_record, open(SOURCE, 'r'))

    # all values
    #for value in values:
    #    print str(value[0]), ',',value[1]

    total = len(values)

    #Get a sample of 50 random values for that field
    for i in range(50):
        try:
            random_value = choice(values) 
            values.remove(random_value)
            print ','.join([random_value[0], random_value[1]])
        except IndexError:
            continue

    print "TOTAL # OF RECORDS: %s" % total 
    

