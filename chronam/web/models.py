import os
import re
import datetime
import textwrap

try:
    import simplejson as json
except ImportError:
    import json

from lxml import etree

from django.db import models 
from django.db.models import permalink
from django.utils import datetime_safe
from django.conf import settings

from chronam.utils import pack_url_path


class Awardee(models.Model):
    org_code = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    @property 
    def batch_count(self):
        return Batch.objects.filter(awardee__org_code=self.org_code).count()

    @property
    def page_count(self):
        return Page.objects.filter(issue__batch__awardee__org_code=self.org_code).count()

    @property
    @permalink
    def url(self):
        return ('chronam_awardee', (), {'institution_code': self.org_code})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#awardee'

    class Meta:
        db_table = 'awardees'
    class Admin:
        pass


class Batch(models.Model):
    name = models.CharField(max_length=250, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    validated_batch_file = models.CharField(max_length=100)
    awardee = models.ForeignKey('Awardee', related_name='batches', null=True)
    released = models.DateTimeField(null=True)

    @property
    def path(self):
        """Absolute path of batch directory"""
        return os.path.join(settings.STORAGE, self.awardee.org_code, 
                            self.name, "data")

    @property
    def full_name(self):
        if self.awardee is None:
            return "%s" % self.name
        else:
            return "%s (%s)" % (self.name, self.awardee.name)

    @property
    def validated_batch_file_path(self):
        return os.path.join(self.path, self.validated_batch_file)

    @property 
    def validated_batch_file_relative_path(self):
        return os.path.join(self.awardee.org_code, self.name, 
                            "data", self.validated_batch_file)

    @property
    def bag_relative_path(self):
        return os.path.join(self.awardee.org_code, self.name, "")

    @property 
    def page_count(self):
        return Page.objects.filter(issue__batch__name=self.name).count()

    @property
    @permalink
    def url(self):
        return ('chronam_batch', (), {'batch_name': self.name})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#batch'

    def lccns(self):
        # TODO: rewrite me
        l = {}
        for issue in self.issues.all():
            l[issue.title_id] = 1
        return l.keys()
 
    def __unicode__(self):
        return self.full_name

    class Meta:
        db_table = 'batches'
        verbose_name_plural = 'batches'
    class Admin:
        pass


class LoadBatchEvent(models.Model):
    # intentionally not a Foreign Key to batches
    # so that batches can be purged while preserving the event history
    batch_name = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True)

    def get_batch(self):
        """
        get_batch looks up the Batch which an event is associated with
        in the case of purged batches it's quite possible that the 
        batch no longer exists, in which case this method returns None
        """
        try:
            return Batch.objects.get(name=self.batch_name) 
        except Title.DoesNotExist:
            return None 

    def __unicode__(self):
        return self.batch_name

    class Meta:
        db_table = 'load_batch_events'
        verbose_name_plural = 'load_batch_events'
    class Admin:
        pass


class Title(models.Model):
    lccn = models.CharField(primary_key=True, max_length=25)
    lccn_orig = models.CharField(max_length=25)
    name = models.CharField(max_length=250)
    name_normal = models.CharField(max_length=250)
    edition = models.CharField(null=True, max_length=250)
    place_of_publication = models.CharField(null=True, max_length=250)
    publisher = models.CharField(null=True, max_length=250)
    frequency = models.CharField(null=True, max_length=250)
    frequency_date = models.CharField(null=True, max_length=250)
    oclc = models.CharField(null=True, max_length=25, db_index=True)
    issn = models.CharField(null=True, max_length=15)
    start_year = models.CharField(max_length=10)
    end_year = models.CharField(max_length=10)
    country = models.ForeignKey('Country')
    marc = models.OneToOneField('MARC')
    version = models.DateTimeField() # http://www.loc.gov/marc/bibliographic/bd005.html
    created = models.DateTimeField(auto_now_add=True)

    @property
    @permalink
    def url(self):
        return ('chronam_title', (), {'lccn': self.lccn})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#title'

    def has_issues(self):
        return Issue.objects.filter(title=self).count() > 0

    def has_essays(self):
        return self.essays.count() > 0

    @property
    def first_issue(self):
        try:
            return self.issues.order_by("date_issued")[0]
        except IndexError, e:
            return None

    @property
    def last_issue(self):
        try:
            return self.issues.order_by("-date_issued")[0]
        except IndexError, e:
            return None

    @property
    def last_issue_released(self):
        try:
            return self.issues.order_by("-batch__released")[0]
        except IndexError, e:
            return None

    @property 
    def solr_doc(self):
        doc = {
                'id': self.url,
                'type': 'title',
                'title': self.name,
                'title_normal': self.name_normal,
                'lccn': self.lccn,
                'edition': self.edition,
                'place_of_publication': self.place_of_publication,
                'frequency': self.frequency,
                'publisher': self.publisher,
                'start_year': self.start_year_int,
                'end_year': self.end_year_int,
                'language': [l.name for l in self.languages.all()],
                'alt_title': [t.name for t in self.alt_titles.all()],
                'subject': [s.heading for s in self.subjects.all()],
                'note': [n.text for n in self.notes.all()],
                'city': [p.city for p in self.places.all()],
                'county': [p.county for p in self.places.all()],
                'country': self.country.name,
                'state': [p.state for p in self.places.all()],
                'place': [p.name for p in self.places.all()],
                'holding_type': [h.type for h in self.holdings.all()],
                'url': [u.value for u in self.urls.all()],
                'essay': [e.html for e in self.essays.all()],
              }

        return doc

    def has_non_english_language(self):
        for language in self.languages.all():
            if language.code != 'eng':
                return True
        return False

    # TODO: if we took two passes through the title data during title
    # loading we could link up the Title objects explictly with each 
    # other. This would be 'doing the right thing' from a rdbms perspective
    #
    # For the time being we just extract and store the links, with their 
    # associated oclc and lccn numbers, and figure out which ones 
    # we can find at runtime using the preceeding_titles, succeeding_titles,
    # and related_titles helper methods.

    def preceeding_titles(self):
        """uses the preceeding_title_links to look up referenced
        titles, and returns them as a list.
        """
        return self._lookup_title_links(self.preceeding_title_links.all())

    def succeeding_titles(self):
        """uses the succeeding_title_links to look up referenced 
        titles, and returns them as a list
        """
        return self._lookup_title_links(self.succeeding_title_links.all())

    def related_titles(self):
        """uses the related_title_links to look up referenced
        titles, and returns them as a list
        """
        return self._lookup_title_links(self.related_title_links.all())

    @property
    def start_year_int(self):
        if self.start_year == 'current':
            return 0
        return int(re.sub(r'[?u]', '0', self.start_year))

    @property
    def end_year_int(self):
        if self.end_year == 'current':
            return 9999
        return int(re.sub(r'[?u]', '9', self.end_year))

    def _lookup_title_links(self, links):
        titles = []
        # a title link may have a lccn and/or a oclc number
        for link in links:
            # first look by lccn 
            if link.lccn:
                try:
                    t = Title.objects.get(lccn=link.lccn)
                    titles.append(t)
                    continue
                except Title.DoesNotExist:
                    pass # oh well, we tried
            
            # look by OCLC number
            if link.oclc:
                try:
                    t = Title.objects.get(oclc="ocm" + link.oclc)
                    titles.append(t)
                except:
                    pass # oh well, we tried again

        return titles

    def __unicode__(self):
        # TODO: should edition info go in here if present?
        return u'%s (%s) %s-%s' % (self.name, self.place_of_publication, 
                                   self.start_year, self.end_year)
       

    class Meta:
        db_table = 'titles'
        ordering = ['name_normal']

    class Admin:
        list_display = ('name', 'lccn', 'oclc', 'start_year', 'end_year')
        ordering = ['name_normal']


class AltTitle(models.Model):
    name = models.CharField(max_length=250)
    date = models.CharField(max_length=250, null=True)
    title = models.ForeignKey('Title', related_name='alt_titles')

    class Meta:
        db_table = 'alt_titles'
        ordering = ['name']


class MARC(models.Model):
    xml = models.TextField()

    @property
    def html(self):
        """
        Convert MARCXML to a human readable HTML table, with CSS
        classes for styling.
        """
        doc = etree.fromstring(self.xml)
        table = etree.Element('table')
        table.attrib['class'] = 'marc-record'

        # leader
        tr = etree.SubElement(table, 'tr')
        tr.attrib['class'] = 'marc-leader'
        etree.SubElement(tr, 'td').text = 'LDR'
        etree.SubElement(tr, 'td')
        etree.SubElement(tr, 'td').text = doc.find('.//leader').text

        # control fields
        for control_field in doc.findall('.//controlfield'):
            tr = etree.SubElement(table, 'tr')
            etree.SubElement(tr, 'td').text = control_field.attrib['tag']
            etree.SubElement(tr, 'td')
            etree.SubElement(tr, 'td').text = control_field.text

        # fields
        for field in doc.findall('.//datafield'):
            tr = etree.SubElement(table, 'tr')
            etree.SubElement(tr, 'td').text = field.attrib['tag']
            indicators = etree.SubElement(tr, 'td')
            indicators.attrib['class'] = 'marc-field-indicators'
            indicators.text = field.attrib['ind1']
            indicators.text += field.attrib['ind2']

            # subfields
            td = etree.SubElement(tr, 'td')
            for subfield in field.findall('.//subfield'):
                code = etree.SubElement(td, 'span')
                code.attrib['class'] = 'marc-subfield-code'
                code.text = '$%s' % subfield.attrib['code']
                value = etree.SubElement(td, 'span')
                value.attrib['class'] = 'marc-subfield-value'

                if field.attrib['tag'] == '856' \
                    and subfield.attrib['code'] == 'u':
                    a = etree.SubElement(value, 'a')
                    a.attrib['href'] = subfield.text
                    a.text = ' '.join(textwrap.wrap(subfield.text, 45))
                else:
                    value.text = ' '.join(textwrap.wrap(subfield.text, 45))

        return etree.tostring(table, pretty_print=True)

    @property
    @permalink
    def url(self):
        return ('chronam_title_marcxml', (), {'lccn': self.title.lccn})
 
    class Meta: 
        db_table = 'marc'
    class Admin:
        pass


class Issue(models.Model):
    date_issued = models.DateField(db_index=True)
    volume = models.CharField(null=True, max_length=50)
    number = models.CharField(max_length=50)
    edition = models.IntegerField()
    edition_label = models.CharField(max_length=100)
    title = models.ForeignKey('Title', related_name='issues')
    batch = models.ForeignKey('Batch', related_name='issues')
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s [%s]" % (self.title.name, self.date_issued)
    
    @property
    @permalink
    def url(self):
        date = self.date_issued
        return ('chronam_issue_pages', (), 
                {'lccn': self.title.lccn,
                 'date': "%04i-%02i-%02i" % (date.year, date.month, date.day),
                 'edition': self.edition})

    @property 
    def abstract_url(self):
        return self.url.rstrip('/') + '#issue'
    
    @property
    def first_page(self):
        try:
            return self.pages.all()[0]
        except Exception, e:
            return None

    @property
    def _previous(self):
        """return the previous issue to this one (including 'duplicates')."""
        try:
            previous_issue = self.get_previous_by_date_issued(title=self.title)
        except Issue.DoesNotExist, e:
            previous_issue = None
        return previous_issue

    @property
    def _next(self):
        """return the next issue to this one (including 'duplicates')."""
        try:
            next_issue = self.get_next_by_date_issued(title=self.title)
        except Issue.DoesNotExist, e:
            next_issue = None
        return next_issue

    @property
    def previous(self):
        """return the previous issue to this one (skipping over 'duplicates')"""
        previous_issue = self._previous
        while previous_issue is not None and previous_issue.date_issued==self.date_issued and previous_issue.edition==self.edition:
            previous_issue = previous_issue._previous
        return previous_issue
    
    @property
    def next(self):
        """return the next issue to this one (skipping over 'duplicates')"""
        next_issue = self._next
        while next_issue is not None and next_issue.date_issued==self.date_issued and next_issue.edition==self.edition:
            next_issue = next_issue._next
        return next_issue
    
    class Meta: 
        db_table = 'issues'
        ordering = ('date_issued',)
    class Admin:
        pass


class Page(models.Model):
    sequence = models.IntegerField(db_index=True)
    number = models.CharField(max_length=50)
    section_label = models.CharField(max_length=100)
    tiff_filename = models.CharField(max_length=250)
    jp2_filename = models.CharField(max_length=250, null=True)
    jp2_width = models.IntegerField(null=True)
    jp2_length = models.IntegerField(null=True)
    pdf_filename = models.CharField(max_length=250, null=True)
    ocr_filename = models.CharField(max_length=250, null=True)
    issue = models.ForeignKey('Issue', related_name='pages')
    reel = models.ForeignKey('Reel', related_name='pages', null=True)
    indexed = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)

    @property
    def jp2_abs_filename(self):
        return self._abs_path(self.jp2_filename)

    @property
    def tiff_abs_filename(self):
        return self._abs_path(self.tiff_filename)

    @property 
    def pdf_abs_filename(self):
        return self._abs_path(self.pdf_filename)

    @property
    def ocr_abs_filename(self):
        return self._abs_path(self.ocr_filename)

    def _abs_path(self, rel_path):
        if rel_path:
            return os.path.join(self.issue.batch.path, rel_path)
        else:
            return None

    def _url_parts(self):
        date = self.issue.date_issued 
        return {'lccn': self.issue.title.lccn,
                'date': "%04i-%02i-%02i" % (date.year, date.month, date.day),
                'edition': self.issue.edition,
                'sequence': self.sequence}
 
    @property
    @permalink
    def url(self):
        return ('chronam_page', (), self._url_parts())

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#page'

    @property
    @permalink
    def thumb_url(self):
        return ('chronam_page_thumbnail', (), self._url_parts())

    @property
    @permalink
    def jp2_url(self):
        return ('chronam_page_jp2', (), self._url_parts())

    @property
    @permalink
    def ocr_url(self):
        return ('chronam_page_ocr_xml', (), self._url_parts())

    @property
    @permalink
    def txt_url(self):
        return ('chronam_page_ocr_txt', (), self._url_parts())

    @property
    @permalink
    def pdf_url(self):
        return ('chronam_page_pdf', (), self._url_parts())

    @property
    def solr_doc(self):
        date = self.issue.date_issued
        date = "%4i%02i%02i" % (date.year, date.month, date.day)
        # start with basic title data 
        doc = self.issue.title.solr_doc
        # no real need to repeat this stuff in pages
        del doc['essay']
        del doc['url']
        del doc['holding_type']
        try:
            ocr_text = self.ocr.text
        except OCR.DoesNotExist:
            ocr_text = None
        doc.update({
            'id': self.url, 
            'type': 'page', 
            'batch': self.issue.batch.name,
            'date': date, 
            'page': self.number,
            'sequence': self.sequence, 
            'section_label': self.section_label,
            'edition_label': self.issue.edition_label,
            'ocr': ocr_text})
        return doc

    def previous(self):
        """
        return the previous page to this one.
        """
        previous_page = None
        pages = list(self.issue.pages.all().order_by("-sequence"))
        i = pages.index(self)
        if i>=0:
            i+=1
            if i<len(pages):
                previous_page = pages[i]
        return previous_page

    def next(self):
        """
        return the next page to this one.
        """
        next_page = None
        pages = list(self.issue.pages.all().order_by("sequence"))
        i = pages.index(self)
        if i>=0:
            i+=1
            if i<len(pages):
                next_page = pages[i]
        return next_page

    @classmethod
    def lookup(cls, page_id):
        """ 
        a quick page lookup using URL path, which happens to be what solr
        uses as its document ID.
        """

        # parse out the parts of the id
        m = re.match(r'/lccn/(.+)/(.+)/ed-(\d+)/seq-(\d+)/?', page_id)
        if not m:
            return None
        lccn, date, edition, sequence = m.groups()

        # unfortunately there can be more than one
        # default to the latest one
        q = Page.objects.filter(issue__title__lccn=lccn, 
                                    issue__date_issued=date, 
                                    issue__edition=edition, 
                                    sequence=sequence)
        pages = q.order_by('-issue__date_issued').all()
        if len(pages) == 0:
            return None
        return pages[0]

    def on_flickr(self):
        return len(self.flickr_urls.all()) > 0

    def first_flickr_url(self):
        for flickr_url in self.flickr_urls.all():
            return flickr_url.value
        return None

    def __unicode__(self):
        parts = [u'%s' % self.issue.title]
        # little hack to get django's datetime support for stftime
        # when the year is < 1900
        dt = datetime_safe.new_datetime(self.issue.date_issued)
        parts.append(dt.strftime('%B %d, %Y'))
        if self.issue.edition_label:
            parts.append(self.issue.edition_label)
        if self.section_label:
            parts.append(self.section_label)
        parts.append('Image %s' % self.sequence)
        return u', '.join(parts)

    class Meta:
        db_table = 'pages'
        ordering = ('sequence',)

    class Admin:
        pass


class OCR(models.Model):
    text = models.TextField()
    word_coordinates_json = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    page = models.OneToOneField('Page', null=True, related_name='ocr')

    def __get_word_coordinates(self):
        return json.loads(self.word_coordinates_json)
    def __set_word_coordinates(self, word_coordinates):
        self.word_coordinates_json = json.dumps(word_coordinates)
    word_coordinates = property(__get_word_coordinates, __set_word_coordinates)

    class Meta:
        db_table = 'ocr'
    class Admin:
        pass



class PublicationDate(models.Model):
    text = models.CharField(max_length=500)
    titles = models.ForeignKey('Title', related_name='publication_dates')
    class Meta:
        db_table = 'publication_dates'
        ordering = ['text']
    class Admin:
        pass


class Place(models.Model):
    name = models.CharField(primary_key=True, max_length=100)
    city = models.CharField(null=True, max_length=100, db_index=True)
    county = models.CharField(null=True, max_length=100, db_index=True)
    state = models.CharField(null=True, max_length=100, db_index=True)
    country = models.CharField(null=True, max_length=100)
    titles = models.ManyToManyField('Title', related_name='places')
    dbpedia = models.CharField(null=True, max_length=250)
    geonames = models.CharField(null=True, max_length=250)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    @property
    def city_for_url(self):
        return pack_url_path(self.city)

    @property
    def county_for_url(self):
        return pack_url_path(self.county)

    @property
    def state_for_url(self):
        return pack_url_path(self.state)

    def __unicode__(self):
        return u"%s, %s, %s" % (self.city, self.county, self.state)

    class Meta: 
        db_table = 'places'
        ordering = ('name',)
    class Admin:
        list_display = ('name', 'state', 'county', 'city')
        ordering = ('name',)


class Subject(models.Model):
    heading = models.CharField(max_length=250)
    type = models.CharField(max_length=1)
    titles = models.ManyToManyField('Title', related_name='subjects')
    # TODO maybe split out types into different classes
    # e.g. GeographicSubject, TopicalSubject ?

    def __unicode__(self):
        return self.heading

    class Meta:
        db_table = 'subjects'
        ordering = ('heading',)
    class Admin:
        list_display = ('heading',)
        ordering = ('heading',)


class Note(models.Model):
    text = models.TextField()
    type = models.CharField(max_length=3)
    title = models.ForeignKey('Title', related_name='notes')

    def __unicode__(self):
        return self.text

    class Meta:
        db_table = 'notes'
        ordering = ('text',)

    class Admin:
        pass

class PageNote(models.Model):
    label = models.TextField()
    text = models.TextField()
    type = models.CharField(max_length=50)
    page = models.ForeignKey('Page', related_name='notes')

    def __unicode__(self):
        return u"type: %s label: %s text: %s" % (self.type, self.label, self.text)

    class Meta:
        db_table = 'page_notes'
        ordering = ('text',)

    class Admin:
        pass


class IssueNote(models.Model):
    label = models.TextField()
    text = models.TextField()
    type = models.CharField(max_length=50)
    issue = models.ForeignKey('Issue', related_name='notes')

    def __unicode__(self):
        return u"type: %s label: %s text: %s" % (self.type, self.label, self.text)

    class Meta:
        db_table = 'issue_notes'
        ordering = ('text',)

    class Admin:
        pass


class Essay(models.Model):
    html = models.TextField()
    created = models.DateTimeField()
    titles = models.ManyToManyField('Title', related_name='essays')
    mets_file = models.TextField(null=True)

    def first_title(self):
        return self.titles.all()[0]

    def get_div(self, base=None):
        """
        Extracts the contents of <body> and puts them in a <div> for
        display in another page of html. If base is specified relative
        hrefs are adjusted accordingly (currently ones starting with
        /lccn).
        """
        div = etree.Element('div')
        div.attrib['class'] = 'essay'
        doc = etree.fromstring(self.html)

        # strip all namespaces
        for elem in doc.getiterator():
            # comment elements don't have a string for tag
            if type(elem.tag) != str:
                continue
            has_ns = re.match(r'{.+}(.+)', elem.tag)
            if has_ns:
                elem.tag = has_ns.group(1)

        if base:
            for elem in doc.getiterator():
                if elem.tag=="a":
                    current = elem.attrib['href']
                    if current.startswith("/lccn"):
                        elem.attrib['href'] = base + current
                
        body = doc.find('.//body')
        for child in body.getchildren():
            div.append(child)

        return etree.tostring(div, pretty_print=True)

    @property
    def div(self):
        return self.get_div()

    @property
    @permalink
    def url(self):
        created = datetime.datetime.strftime(self.created, '%Y%m%d%H%M%S')
        return ('chronam_title_essay', (), {'lccn': self.first_title().lccn, 
                                            'created': created})

    class Meta:
        db_table = 'essays'
        ordering = ['created']


    class Admin:
        pass


class Holding(models.Model):
    description = models.TextField()
    type = models.CharField(null=True, max_length=25)
    institution = models.ForeignKey('Institution', related_name='holdings')
    last_updated = models.CharField(null=True, max_length=10) 
    title = models.ForeignKey('Title', related_name='holdings')
    created = models.DateTimeField(auto_now_add=True)

    def description_as_list(self):
        l = re.findall(r'<.+?>', self.description)
        if l: 
            return l
        return [self.description]

    def is_summary(self):
        if self.type == None:
            return True
        return False

    def __unicode__(self):
        return u"%s - %s - %s" % (self.institution.name, self.type, self.description)

    class Meta:
        db_table = 'holdings'
        ordering = ('institution',)

    class Admin:
        pass


class SucceedingTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='succeeding_title_links')

    class Meta:
        db_table = 'succeeding_title_links'
        ordering = ('name',)

    class Admin:
        pass


class PreceedingTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='preceeding_title_links')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.lccn)

    class Meta:
        db_table = 'preceeding_title_links'
        ordering = ('name',)

    class Admin:
        pass


class RelatedTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='related_title_links')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.lccn)

    class Meta:
        db_table = 'related_title_links'
        ordering = ('name',)

    class Admin:
        pass


class Ethnicity(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    class Meta:
        db_table = 'ethnicities'
        ordering = ('name',)

    class Admin:
        pass


class EthnicitySynonym(models.Model):
    synonym = models.CharField(null=False, max_length=250)
    ethnicity = models.ForeignKey('Ethnicity', related_name='synonyms')

    class Meta:
        db_table = 'ethnicity_synonyms'
        ordering = ('synonym',)


class Language(models.Model):
    code = models.CharField(null=False, max_length=3, primary_key=True)
    name = models.CharField(null=False, max_length=100)
    lingvoj = models.CharField(null=True, max_length=200)
    titles = models.ManyToManyField('Title', related_name='languages')

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'languages'
        ordering = ('name',)

    class Admin:
        pass


class Country(models.Model):
    """
    A model for capturing MARC country codes found at:
    http://www.loc.gov/marc/countries/

    It's used primarily for state information since Chronicling America
    is about the United States and the MARC country codes contains
    distinct codes for each US state. Go figure.
    """
    code = models.CharField(null=False, max_length=3, primary_key=True)
    name = models.CharField(null=False, max_length=100)
    region = models.CharField(null=False, max_length=100)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.region)

    class Meta:
        db_table = 'countries'
        ordering = ('name',)

    class Admin:
        pass


class LaborPress(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    class Meta:
        db_table = 'labor_presses'
        ordering = ('name',)

    class Admin:
        pass


class MaterialType(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    class Meta:
        db_table = 'material_types'
        ordering = ('name',)

    class Admin:
        pass


class Institution(models.Model):
    code = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(null=False, max_length=255)
    address1 = models.CharField(null=True, max_length=255)
    address2 = models.CharField(null=True, max_length=255)
    city = models.CharField(null=False, max_length=100)
    state = models.CharField(null=False, max_length=2)
    zip = models.CharField(null=True, max_length=20)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"%s, %s, %s" % (self.name, self.city, self.state)

    class Meta:
        db_table = 'institutions'
        ordering = ('name',)

    class Admin:
        pass


class PhysicalDescription(models.Model):
    text = models.TextField()
    type = models.CharField(max_length=3)
    title = models.ForeignKey('Title', related_name='dates_of_publication')

    class Meta:
        db_table = 'physical_descriptions'
        ordering = ('type',)


class Url(models.Model):
    value = models.TextField()
    type = models.CharField(max_length=1, null=True)
    title = models.ForeignKey('Title', related_name='urls')

    def __unicode__(self):
        return self.value

    class Meta:
        db_table = 'urls'

class FlickrUrl(models.Model):
    value = models.TextField()
    page = models.ForeignKey('Page', related_name='flickr_urls')
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.value

    class Meta:
        db_table = 'flickr_urls'


class Reel(models.Model):
    number = models.CharField(max_length=50)
    batch = models.ForeignKey('Batch', related_name='reels') 
    created = models.DateTimeField(auto_now_add=True)

    # not explicit mentioned in top level batch.xml
    implicit = models.BooleanField(default=False) 
    
    def titles(self):
        return Title.objects.filter(issues__pages__reel=self).distinct()
