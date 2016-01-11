import os
import csv 
import codecs

from django.core.management.base import BaseCommand

from openoni.core.management.commands import configure_logging
from openoni.core.models import Institution

configure_logging("load_intitutions_logging.config", 
                  "load_institutions_%s.log" % os.getpid())

"""
Simple command to load institution data obtained from the MySQL database 
running in the MARC Standards office.

"oid","orgName","altname1","altname2","altname3","altname4","orgCode","lowercode","isilCode","obsoleteOrgCode","createDate","modifiedDate","address1","address2","address3","city","stateID","zip","countryID","ID","cname","prefix","searchable"
22035,"3Com Corporation Technical Library","","","","","CStcTCC","cstctcc","US-CStcTCC","","1995-10-19 00:00:00","1995-10-19 00:00:00","5400 Bayfront Plaza","","","Santa Clara",5,"95052",210,210,"United States","US","yes"
"""

class Command(BaseCommand):
    help = 'loads institution csv data into Institution table'
    args = '<institution_csv_file>'

    def handle(self, csv_file, *args, **options):
        for row in unicode_csv_reader(codecs.open(csv_file, encoding='utf-8')): 
            if row[20] != 'United States':
                continue
            i = Institution()
            i.code = row[7].upper()
            i.name = row[1]
            i.address1 = row[12]
            i.address2 = row[13]
            i.city = row[15]
            i.state = "MD" # XXX: use real state! row[16]
            i.zip = row[17]
            i.save()

# some hoops to get csv reader to emit unicode
# http://www.python.org/doc/2.5.2/lib/csv-examples.html

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_encoder(unicode_csv_data), 
                                         dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
