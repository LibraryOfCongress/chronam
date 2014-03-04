import os
import os.path
import re
import json
import time
import hashlib
import logging
import tarfile
import textwrap
import urlparse
from cStringIO import StringIO

from rfc3339 import rfc3339
from lxml import etree
from urllib import url2pathname

from django.db import models
from django.db.models import permalink, Q
from django.conf import settings

from chronam.core.utils import strftime

from django.core import urlresolvers


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
    @permalink
    def json_url(self):
        return ('chronam_awardee_json', (), {'institution_code': self.org_code})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#awardee'

    def json(self, host="chroniclingamerica.loc.gov", serialize=True):
        j = {
            "name": self.name,
            "url": 'http://' + host + self.json_url
        }
        if serialize:
            return json.dumps(j, indent=2)
        return j

    def __unicode__(self):
        return self.name


class Batch(models.Model):
    name = models.CharField(max_length=250, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    validated_batch_file = models.CharField(max_length=100)
    awardee = models.ForeignKey('Awardee', related_name='batches', null=True)
    released = models.DateTimeField(null=True)
    source = models.CharField(max_length=4096, null=True)
    sitemap_indexed = models.DateTimeField(auto_now_add=False, null=True)

    @classmethod
    def viewable_batches(klass):
        if settings.IS_PRODUCTION:
            batches = Batch.objects.filter(released__isnull=False)
        else:
            batches = Batch.objects.all()
        return batches.order_by("-released")

    @property
    def storage_url(self):
        """Absolute path of batch directory"""
        source = self.source
        if source:
            u = urlparse.urljoin(source, "data/")
        else:
            u = urlparse.urljoin("file:", self.path)
        return u

    @property
    def path(self):
        """Absolute path of batch directory"""
        return os.path.join(settings.BATCH_STORAGE, self.name, "data/")

    @property
    def full_name(self):
        if self.awardee is None:
            return "%s" % self.name
        else:
            return "%s (%s)" % (self.name, self.awardee.name)

    @property
    def validated_batch_url(self):
        return urlparse.urljoin(self.storage_url, self.validated_batch_file)

    @property
    def page_count(self):
        return Page.objects.filter(issue__batch__name=self.name).count()

    @property
    @permalink
    def url(self):
        return ('chronam_batch', (), {'batch_name': self.name})

    @property
    @permalink
    def json_url(self):
        return ('chronam_batch_dot_json', (), {'batch_name': self.name})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#batch'

    def lccns(self):
        # TODO: rewrite me
        l = {}
        for issue in self.issues.all():
            l[issue.title_id] = 1
        return l.keys()

    def delete(self, *args, **kwargs):
        # manually delete any OcrDump associated with this batch
        # since a Batch.delete doesn't seem to trigger a OcrDump.delete
        # and we need OcrDump.delete to clean up the filesystem
        try:
            self.ocr_dump.delete()
        except OcrDump.DoesNotExist:
            logging.warn("no OcrDump to delete for %s", self)
        super(Batch, self).delete(*args, **kwargs)

    def json(self, include_issues=True, serialize=True, host="chroniclingamerica.loc.gov"):
        b = {}
        b['name'] = self.name
        b['ingested'] = rfc3339(self.created)
        b['page_count'] = self.page_count
        b['lccns'] = self.lccns()
        b['awardee'] = {
            "name": self.awardee.name,
            "url": "http://" + host + self.awardee.json_url
        }
        b['url'] = "http://" + host + self.json_url
        if include_issues:
            b['issues'] = []
            for issue in self.issues.all():
                i = {
                    "title": {
                        "name": issue.title.display_name,
                        "url": "http://" + host + issue.title.json_url,
                    },
                    "date_issued": strftime(issue.date_issued, "%Y-%m-%d"),
                    "url": "http://" + host + issue.json_url
                }
                b['issues'].append(i)
        if serialize:
            return json.dumps(b)
        else:
            return b

    def __unicode__(self):
        return self.full_name


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
    medium = models.CharField(null=True, max_length=50, help_text="245$h field")
    oclc = models.CharField(null=True, max_length=25, db_index=True)
    issn = models.CharField(null=True, max_length=15)
    start_year = models.CharField(max_length=10)
    end_year = models.CharField(max_length=10)
    country = models.ForeignKey('Country')
    version = models.DateTimeField()  # http://www.loc.gov/marc/bibliographic/bd005.html
    created = models.DateTimeField(auto_now_add=True)
    has_issues = models.BooleanField(default=False, db_index=True)
    uri = models.URLField(null=True, max_length=500, help_text="856$u")
    sitemap_indexed = models.DateTimeField(auto_now_add=False, null=True)

    @property
    @permalink
    def url(self):
        return ('chronam_title', (), {'lccn': self.lccn})

    @property
    @permalink
    def json_url(self):
        return ('chronam_title_dot_json', (), {'lccn': self.lccn})

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#title'

    @property
    def display_name(self):
        if self.medium:
            return ' '.join([self.name, self.medium])
        else:
            return self.name

    @property
    def first_issue(self):
        try:
            return self.issues.order_by("date_issued")[0]
        except IndexError:
            return None

    def has_essays(self):
        return self.essays.count() > 0

    @property
    def first_essay(self):
        try:
            return self.essays.all()[0]
        except IndexError:
            return None

    @property
    def last_issue(self):
        try:
            return self.issues.order_by("-date_issued")[0]
        except IndexError:
            return None

    @property
    def last_issue_released(self):
        try:
            return self.issues.order_by("-batch__released")[0]
        except IndexError:
            return None

    @property
    def holding_types(self):
        # This was added to take into consideration the 856$u field
        # values when electronic resource (online resource) is selected in search.
        ht = [h.type for h in self.holdings.all()]
        if self.uri and not 'Online Resource' in ht:
            ht.append('Online Resource')
        return ht

    @property
    def solr_doc(self):
        doc = {
            'id': self.url,
            'type': 'title',
            'title': self.display_name,
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
            'holding_type': self.holding_types,
            'url': [u.value for u in self.urls.all()],
            'essay': [e.html for e in self.essays.all()],
        }

        return doc

    def json(self, serialize=True, host="chroniclingamerica.loc.gov"):
        j = {
            "url": "http://" + host + self.json_url,
            "lccn": self.lccn,
            "name": self.display_name,
            "place_of_publication": self.place_of_publication,
            "publisher": self.publisher,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "subject": [s.heading for s in self.subjects.all()],
            "place": [p.name for p in self.places.all()],
            "issues": [{
                "url": "http://" + host + i.json_url,
                "date_issued": strftime(i.date_issued, "%Y-%m-%d")
            } for i in self.issues.all()]
        }

        if serialize:
            return json.dumps(j, indent=2)
        return j

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
                    pass  # oh well, we tried

            # look by OCLC number
            if link.oclc:
                try:
                    t = Title.objects.get(oclc="ocm" + link.oclc)
                    titles.append(t)
                except:
                    pass  # oh well, we tried again

        return titles

    def __unicode__(self):
        # TODO: should edition info go in here if present?
        return u'%s (%s) %s-%s' % (self.display_name, self.place_of_publication,
                                   self.start_year, self.end_year)

    class Meta:
        ordering = ['name_normal']


class AltTitle(models.Model):
    name = models.CharField(max_length=250)
    date = models.CharField(max_length=250, null=True)
    title = models.ForeignKey('Title', related_name='alt_titles')

    class Meta:
        ordering = ['name']


class MARC(models.Model):
    xml = models.TextField()
    title = models.OneToOneField('Title', related_name='marc')

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

                if field.attrib['tag'] == '856' and subfield.attrib['code'] == 'u':
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
        return "%s [%s]" % (self.title.display_name, self.date_issued)

    @property
    @permalink
    def url(self):
        date = self.date_issued
        return ('chronam_issue_pages', (),
                {'lccn': self.title.lccn,
                 'date': "%04i-%02i-%02i" % (date.year, date.month, date.day),
                 'edition': self.edition})

    @property
    @permalink
    def json_url(self):
        date = self.date_issued
        return ('chronam_issue_pages_dot_json', (),
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
        except Exception:
            return None

    @property
    def first_page_with_image(self):
        for page in self.pages.all():
            if page.jp2_filename:
                return page
        return None

    @property
    def _previous(self):
        """return the previous issue to this one (including 'duplicates')."""
        try:
            previous_issue = self.get_previous_by_date_issued(title=self.title)
        except Issue.DoesNotExist:
            previous_issue = None
        return previous_issue

    @property
    def _next(self):
        """return the next issue to this one (including 'duplicates')."""
        try:
            next_issue = self.get_next_by_date_issued(title=self.title)
        except Issue.DoesNotExist:
            next_issue = None
        return next_issue

    @property
    def previous(self):
        """return the previous issue to this one (skipping over 'duplicates')"""
        previous_issue = self._previous
        while previous_issue is not None and previous_issue.date_issued == self.date_issued and previous_issue.edition == self.edition:
            previous_issue = previous_issue._previous
        return previous_issue

    @property
    def next(self):
        """return the next issue to this one (skipping over 'duplicates')"""
        next_issue = self._next
        while next_issue is not None and next_issue.date_issued == self.date_issued and next_issue.edition == self.edition:
            next_issue = next_issue._next
        return next_issue

    def save(self, *args, **kwargs):
        """override the default save behavior to populate has_issues on title.
        this is an intentional denormalization to speed up some queries.
        """
        self.title.has_issues = True
        self.title.save()
        super(Issue, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """override the default delete behavior to make sure has_issues is
        set to False when the last issue is deleted.
        """
        super(Issue, self).delete(*args, **kwargs)
        if self.title.issues.all().count() == 0:
            self.title.has_issues = False
            self.title.save()

    def json(self, serialize=True, include_pages=True, host='chroniclingamerica.loc.gov'):
        j = {
            'url': 'http://' + host + self.json_url,
            'date_issued': strftime(self.date_issued, "%Y-%m-%d"),
            'volume': self.volume,
            'number': self.number,
            'edition': self.edition,
            'title': {"name": self.title.display_name, "url": 'http://' + host + self.title.json_url},
            'batch': {"name": self.batch.name, "url": 'http://' + host + self.batch.json_url},
        }

        j['pages'] = [{
            "url": "http://" + host + p.json_url,
            "sequence": p.sequence
        } for p in self.pages.all()]

        if serialize:
            return json.dumps(j, indent=2)
        return j

    class Meta:
        ordering = ('date_issued',)


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

    def json(self, serialize=True, host="chroniclingamerica.loc.gov"):
        j = {
            "sequence": self.sequence,
            "issue": {
                "date_issued": strftime(self.issue.date_issued, "%Y-%m-%d"),
                "url": "http://" + host + self.issue.json_url},
            "jp2": "http://" + host + self.jp2_url,
            "ocr": "http://" + host + self.ocr_url,
            "text": "http://" + host + self.txt_url,
            "pdf": "http://" + host + self.pdf_url,
            "title": {
                "name": self.issue.title.display_name,
                "url": "http://" + host + self.issue.title.json_url}
        }
        if serialize:
            return json.dumps(j, indent=2)
        return j

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

    @property
    def noteAboutReproduction(self):
        try:
            return self.notes.filter(type="noteAboutReproduction")[0]
        except IndexError:
            return ""

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
    @permalink
    def json_url(self):
        return ('chronam_page_dot_json', (), self._url_parts())

    @property
    def abstract_url(self):
        return self.url.rstrip('/') + '#page'

    @property
    @permalink
    def thumb_url(self):
        return ('chronam_page_thumbnail', (), self._url_parts())

    @property
    @permalink
    def medium_url(self):
        return ('chronam_page_medium', (), self._url_parts())

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
        month, day, year  = '%02i'%date.month, '%02i'%date.day, '%04i'%date.year
        date = ''.join([year, month, day])
        # start with basic title data
        doc = self.issue.title.solr_doc
        # no real need to repeat this stuff in pages
        del doc['essay']
        del doc['url']
        del doc['holding_type']
        doc.update({
            'id': self.url,
            'type': 'page',
            'batch': self.issue.batch.name,
            'date': date,
            'month': month,
            'year': year,
            'day': day,
            'page': self.number,
            'sequence': self.sequence,
            'section_label': self.section_label,
            'edition_label': self.issue.edition_label,
        })
        try:
            ocr_texts = self.ocr.language_texts.select_related().values('language__code', 'text')
        except OCR.DoesNotExist:
            ocr_texts = None
        for ocr_text in ocr_texts:
            # make sure Solr is configured to handle the language and if it's
            # not just treat it as English
            lang = ocr_text['language__code']
            if lang not in settings.SOLR_LANGUAGES:
                lang = "eng"
            doc['ocr_%s' % lang] = ocr_text['text']
        return doc

    def previous(self):
        """
        return the previous page to this one.
        """
        previous_page = None
        pages = list(self.issue.pages.all().order_by("-sequence"))
        i = pages.index(self)
        if i >= 0:
            i += 1
            if i < len(pages):
                previous_page = pages[i]
        return previous_page

    def next(self):
        """
        return the next page to this one.
        """
        next_page = None
        pages = list(self.issue.pages.all().order_by("sequence"))
        i = pages.index(self)
        if i >= 0:
            i += 1
            if i < len(pages):
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
        parts.append(strftime(self.issue.date_issued, '%B %d, %Y'))
        if self.issue.edition_label:
            parts.append(self.issue.edition_label)
        if self.section_label:
            parts.append(self.section_label)
        parts.append('Image %s' % self.sequence)
        return u', '.join(parts)

    class Meta:
        ordering = ('sequence',)

    class Admin:
        pass


class LanguageText(models.Model):
    text = models.TextField()
    language = models.ForeignKey('Language', null=True)
    ocr = models.ForeignKey('OCR', related_name="language_texts")


class OCR(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    page = models.OneToOneField('Page', null=True, related_name='ocr')

    @property
    def text(self):
        return (' '.join([obj.text for obj in self.language_texts.all()]))


class PublicationDate(models.Model):
    text = models.CharField(max_length=500)
    titles = models.ForeignKey('Title', related_name='publication_dates')

    class Meta:
        ordering = ['text']


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

    def __unicode__(self):
        return u"%s, %s, %s" % (self.city, self.county, self.state)

    class Meta:
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
        ordering = ('heading',)


class Note(models.Model):
    text = models.TextField()
    type = models.CharField(max_length=3)
    title = models.ForeignKey('Title', related_name='notes')

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ('text',)


class PageNote(models.Model):
    label = models.TextField()
    text = models.TextField()
    type = models.CharField(max_length=50)
    page = models.ForeignKey('Page', related_name='notes')

    def __unicode__(self):
        return u"type: %s label: %s text: %s" % (self.type, self.label, self.text)

    class Meta:
        ordering = ('text',)


class IssueNote(models.Model):
    label = models.TextField()
    text = models.TextField()
    type = models.CharField(max_length=50)
    issue = models.ForeignKey('Issue', related_name='notes')

    def __unicode__(self):
        return u"type: %s label: %s text: %s" % (self.type, self.label, self.text)

    class Meta:
        ordering = ('text',)


class Essay(models.Model):
    title = models.TextField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    creator = models.ForeignKey('Awardee', related_name='essays')
    essay_editor_url = models.TextField()
    html = models.TextField()
    loaded = models.DateTimeField(auto_now_add=True)
    titles = models.ManyToManyField('Title', related_name='essays')

    def first_title(self):
        return self.titles.all()[0]

    @property
    @permalink
    def url(self):
        return ('chronam_essay', (), {'essay_id': self.id})

    class Meta:
        ordering = ['title']


class Holding(models.Model):
    description = models.TextField(null=True)
    type = models.CharField(null=True, max_length=25)
    institution = models.ForeignKey('Institution', related_name='holdings')
    last_updated = models.CharField(null=True, max_length=10)
    title = models.ForeignKey('Title', related_name='holdings')
    created = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, help_text="852$z")

    def description_as_list(self):
        desc_list = []
        desc_txt = self.description
        # To protect the records that start w/ things like "s="
        # We pull those out first & remove those from the desc_txt
        # Sample record: 's=<1959:6:2-1962:11:15> <1966:11:23-12:29>'
        for d in desc_txt.split():
            try:
                if d[1] == '=' and d.endswith('>'):
                    desc_list.append(d)
                    desc_txt = desc_txt.replace(d, '')
            except IndexError:
                continue

        l = re.findall(r'<.+?>', desc_txt)
        if l:
            [desc_list.append(d) for d in l]

        if desc_list:
            return desc_list
        else:
            return [self.description]

    def __unicode__(self):
        return u"%s - %s - %s" % (self.institution.name, self.type, self.description)

    class Meta:
        ordering = ('institution',)


class SucceedingTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='succeeding_title_links')

    class Meta:
        ordering = ('name',)


class PreceedingTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='preceeding_title_links')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.lccn)

    class Meta:
        ordering = ('name',)


class RelatedTitleLink(models.Model):
    name = models.CharField(null=True, max_length=250)
    lccn = models.CharField(null=True, max_length=50)
    oclc = models.CharField(null=True, max_length=50)
    title = models.ForeignKey('Title', related_name='related_title_links')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.lccn)

    class Meta:
        ordering = ('name',)


class Ethnicity(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    @property
    def has_issues(self):
        return self.titles_with_issues().count() > 0

    def titles_with_issues(self):
        return self.titles().filter(has_issues=True)

    def titles(self):
        f = Q(subjects__heading__icontains=self.name)
        for s in self.synonyms.all():
            f |= Q(subjects__heading__icontains=s.synonym)
        return Title.objects.filter(f).distinct()

    class Meta:
        ordering = ('name',)


class EthnicitySynonym(models.Model):
    synonym = models.CharField(null=False, max_length=250)
    ethnicity = models.ForeignKey('Ethnicity', related_name='synonyms')

    class Meta:
        ordering = ('synonym',)


class Language(models.Model):
    code = models.CharField(null=False, max_length=3, primary_key=True)
    name = models.CharField(null=False, max_length=100)
    lingvoj = models.CharField(null=True, max_length=200)
    titles = models.ManyToManyField('Title', related_name='languages')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


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
        ordering = ('name',)


class LaborPress(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    class Meta:
        ordering = ('name',)


class MaterialType(models.Model):
    name = models.CharField(null=False, max_length=250, primary_key=True)

    class Meta:
        ordering = ('name',)


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
        ordering = ('name',)


class PhysicalDescription(models.Model):
    text = models.TextField()
    type = models.CharField(max_length=3)
    title = models.ForeignKey('Title', related_name='dates_of_publication')

    class Meta:
        ordering = ('type',)


class Url(models.Model):
    value = models.TextField()
    type = models.CharField(max_length=1, null=True)
    title = models.ForeignKey('Title', related_name='urls')

    def __unicode__(self):
        return self.value


class FlickrUrl(models.Model):
    value = models.TextField()
    page = models.ForeignKey('Page', related_name='flickr_urls')
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.value


class Reel(models.Model):
    number = models.CharField(max_length=50)
    batch = models.ForeignKey('Batch', related_name='reels')
    created = models.DateTimeField(auto_now_add=True)

    # not explicit mentioned in top level batch.xml
    implicit = models.BooleanField(default=False)

    def titles(self):
        return Title.objects.filter(issues__pages__reel=self).distinct()


class OcrDump(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    sha1 = models.TextField()
    size = models.BigIntegerField()
    batch = models.OneToOneField('Batch', related_name='ocr_dump')

    @classmethod
    def new_from_batch(klass, batch):
        """Does the work of creating a new OcrDump based on a Batch
        """
        dump = OcrDump(batch=batch)

        # add each page to a tar ball
        tar = tarfile.open(dump.path, "w:bz2")
        for issue in batch.issues.all():
            for page in issue.pages.filter(ocr__isnull=False):
                dump._add_page(page, tar)
        tar.close()

        dump._calculate_size()
        dump._calculate_sha1()
        dump.save()

        return dump

    @property
    def name(self):
        return self.batch.name + ".tar.bz2"

    @property
    def url(self):
        path = self.path.replace(settings.STORAGE, "/data/")
        return os.path.join(path)

    @classmethod
    def last(klass):
        dumps = OcrDump.objects.all().order_by("-sequence")
        if dumps.count() > 0:
            return dumps[0]
        return None

    @property
    def path(self):
        return os.path.join(settings.OCR_DUMP_STORAGE, self.name)

    def json(self, serialize=True, host="chroniclingamerica.loc.gov"):
        j = {
            "name": self.name,
            "created": rfc3339(self.created),
            "size": self.size,
            "sha1": self.sha1,
            "url": "http://" + host + self.url
        }
        if serialize:
            return json.dumps(i, indent=2)
        return j

    def __unicode__(self):
        return "path=%s size=%s sha1=%s" % (self.path, self.size, self.sha1)

    def _add_page(self, page, tar):
        d = page.issue.date_issued
        relative_dir = "%s/%i/%02i/%02i/ed-%i/seq-%i/" % (page.issue.title_id, d.year, d.month, d.day, page.issue.edition, page.sequence)

        # add ocr text
        txt_filename = relative_dir + "ocr.txt"
        ocr_text = page.ocr.text.encode('utf-8')
        info = tarfile.TarInfo(name=txt_filename)
        info.size = len(ocr_text)
        info.mtime = time.time()
        tar.addfile(info, StringIO(ocr_text))

        # add ocr xml
        xml_filename = relative_dir + "ocr.xml"
        info = tarfile.TarInfo(name=xml_filename)
        info.size = os.path.getsize(page.ocr_abs_filename)
        info.mtime = time.time()
        tar.addfile(info, open(page.ocr_abs_filename))

        logging.info("added %s to %s" % (page, tar.name))

    def delete(self, *args, **kwargs):
        # clean up file off of filesystem
        if os.path.isfile(self.path):
            os.remove(self.path)
        return super(OcrDump, self).delete(*args, **kwargs)

    def _calculate_size(self):
        self.size = os.path.getsize(self.path)

    def _calculate_sha1(self):
        """looks at the dump file and calculates the sha1 digest and stores it
        """
        f = open(self.path)
        sha1 = hashlib.sha1()
        while True:
            buff = f.read(2 ** 16)
            if not buff:
                break
            sha1.update(buff)
        self.sha1 = sha1.hexdigest()
        return self.sha1


def coordinates_path(url_parts):
    url = urlresolvers.reverse('chronam_page', kwargs=url_parts)
    path = url2pathname(url)
    if path.startswith("/"):
        path = path[1:]
    full_path = os.path.join(settings.COORD_STORAGE, path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return os.path.join(full_path, "coordinates.json.gz")
