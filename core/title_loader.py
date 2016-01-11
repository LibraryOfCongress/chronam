import logging
import urlparse
import urllib2
import datetime
from re import sub
from time import time, strptime

from pymarc import map_xml, record_to_xml
from django.db import reset_queries

from openoni.core import models

_logger = logging.getLogger(__name__)


class TitleLoader(object):

    def __init__(self):
        self.records_processed = 0
        self.records_created = 0
        self.records_updated = 0
        self.records_deleted = 0
        self.missing_lccns = 0
        self.errors = 0

    def load_file(self, location, skip=0):
        location = urlparse.urljoin("file:", location)
        t0 = time()
        times = []

        def load_record(record):

            try:
                # we test to see if it is a record, b/c not
                # all values returned from OCLC are records.
                # if it is not a record, we just want to skip it.
                if record:
                    self.records_processed += 1
                    if skip > self.records_processed:
                        _logger.info("skipped %i" % self.records_processed)
                    elif record.leader[5] == 'd':
                        self.delete_bib(record)
                    elif record.leader[6] == 'a':
                        self.load_bib(record)

            except Exception, e:
                _logger.error("unable to load: %s" % e)
                _logger.exception(e)
                self.errors += 1

            seconds = time() - t0
            times.append(seconds)

            if self.records_processed % 1000 == 0:
                _logger.info("processed %sk records in %.2f seconds" %
                             (self.records_processed / 1000, seconds))

        map_xml(load_record, urllib2.urlopen(location))

    def load_bib(self, record):
        title = None

        # we must have an lccn, but it's not an error if we don't find one
        lccn_orig = _extract(record, '010', 'a')
        lccn = _normal_lccn(lccn_orig)

        if not lccn:
            #_logger.info("###### LCCN in OCLC pull, \
            #              but not in database. Missing LCCN. ######")
            #_logger.info(record)
            self.missing_lccns += 1
            return

        # newer marc xml sets pulled from OCLC do not have the 005 control
        # field. 005 is the date and time of the last transaction.
        try:
            s = _extract(record, '005')
            parts = s.split(".")
            dt = datetime.datetime(*strptime(parts[0], '%Y%m%d%H%M%S')[0:6])
        except AttributeError:
            dt = datetime.datetime.now()

        #dt.replace(microsecond=int(parts[1]))

        # it's remotely possible that a title with the LCCN already exists
        try:
            title = models.Title.objects.get(lccn=lccn)
            _logger.debug("Found another record for lccn: %s" % lccn)
            if title.version == dt:
                _logger.debug("    with the same timestamp: %s" % title.version)
                return  # skip over this record with same timestamp
            elif title.version < dt:
                _logger.debug("    with newer timestamp: %s vs %s" % (title.version, dt))
                title.version = dt
                self.records_updated += 1
            elif title.version > dt:
                _logger.debug("    with older timestamp: %s vs %s" % (title.version, dt))
                return  # skip over older record
            else:
                _logger.error("Logic error... this should be unreachable.")
        except models.Title.DoesNotExist:
            self.records_created += 1
            title = models.Title(lccn=lccn)
            title.version = dt

        # clear m2m relationships
        # these will come from the extraction
        title.subjects.clear()
        title.languages.clear()
        title.places.clear()

        # delete fk relationships
        # these will come from the extraction
        title.publication_dates.all().delete()
        title.notes.all().delete()
        title.alt_titles.all().delete()
        title.succeeding_title_links.all().delete()
        title.preceeding_title_links.all().delete()
        title.related_title_links.all().delete()
        title.urls.all().delete()

        # update title fields
        self._set_name(record, title)

        title.lccn_orig = lccn_orig
        title.oclc = self._extract_oclc(record)
        title.edition = _extract(record, '250', 'a')
        title.publisher = _extract(record, '260', 'b')
        title.frequency = _extract(record, '310', 'a')
        title.frequency_date = _extract(record, '310', 'b')
        title.uri = _extract(record, '856', 'u')

        # rda records use 265$a, fallback to 260$a
        title.place_of_publication = _extract(record, '264', 'a')
        if not title.place_of_publication:
            title.place_of_publication = _extract(record, '260', 'a')

        # rda records use 338$a, fallback to 245$h
        title.medium = _extract(record, '338', 'a')
        if not title.medium:
            title.medium = _extract(record, '245', 'h')

        title.issn = _extract(record, '022', 'a')
        f008 = record['008'].data
        title.start_year = _normal_year(f008[7:11])
        title.end_year = _normal_year(f008[11:15])
        title.country = self._extract_country(record)
        title.save()

        # update fk relationships with new values
        self._extract_languages(record, title)
        self._extract_places(record, title)
        self._extract_publication_dates(record, title)
        self._extract_subjects(record, title)
        self._extract_notes(record, title)
        self._extract_preceeding_titles(record, title)
        self._extract_succeeding_titles(record, title)
        self._extract_related_titles(record, title)
        self._extract_alt_titles(record, title)
        self._extract_urls(record, title)
        title.save()

        marc, marc_created = models.MARC.objects.get_or_create(title=title)
        marc.xml = record_to_xml(record)
        marc.save()

        # for context see: https://rdc.lctl.gov/trac/ndnp/ticket/375
        if _is_openoni_electronic_resource(title, record):
            _logger.info("deleting title record for openoni electronic resource: %s" % title)
            title.delete()

        # this is for long running processes so the query cache
        # doesn't bloat memory
        reset_queries()

        return title

    def delete_bib(self, record):
        lccn = _normal_lccn(_extract(record, '010', 'a'))
        _logger.info("trying to delete title record for %s" % lccn)
        try:
            title = models.Title.objects.get(lccn=lccn)
            # XXX: a safety to avoid deleting issue data that is
            # attached to a title
            if title.issues.count() == 0:
                _logger.info("deleting title for %s" % lccn)
                title.delete()
                self.records_deleted += 1
            else:
                _logger.warn("not deleting title %s it has issue data" % lccn)
        except models.Title.DoesNotExist:
            _logger.warn("no such title %s to delete" % lccn)
        return

    def _set_name(self, record, title):
        f245 = record['245']
        title.name = f245['a']

        # add subtitle if available
        if f245['b']:
            if not title.name.endswith(' '):
                title.name += ' '
            title.name += f245['b']

        # lowercase the normalized title
        title.name_normal = title.name.lower()

        # strip of leading The, An, A, etc if present
        if f245.indicators[1] != '0':
            title.name_normal = title.name_normal[int(f245.indicators[1]):]
        return

    def _extract_languages(self, record, title):

        def _get_langs(field):
            '''
            _get_langs sub-function is to extract/parse
            subfield values
            '''
            field_langs = []
            for code in field:
                # kinda odd, but the 041 can contain $a fraengspa
                # so theye need to be split into fra, eng, spa first
                for c in nsplit(code, 3):
                    try:
                        field_langs.append(models.Language.objects.get(code=c))
                    except models.Language.DoesNotExist:
                        _logger.error('missing language for %s' % c)
            return field_langs

        code = _extract(record, '008')[35:38]
        try:
            langs = [models.Language.objects.get(code=code)]
        except models.Language.DoesNotExist:
            langs = []
            _logger.error("Code %s, not found in language table." % code)

        subfields_to_eval = ['a', 'b']
        for f041 in record.get_fields('041'):
            for sf in subfields_to_eval:
                sf_langs = _get_langs(f041.get_subfields(sf))
                [langs.append(sf_lang) for sf_lang in sf_langs if sf_lang not in langs]

        title.languages = list(set(langs))
        return

    def _extract_places(self, record, title):
        places = []
        for field in record.get_fields('752'):
            # TODO fix this up so that it works with nulls
            country = _normal_place(field['a'])
            state = _normal_place(field['b'])
            county = _normal_place(field['c'])
            city = _normal_place(field['d'])
            name = "%s--%s--%s" % (state, county, city)
            # hack to remove --None-- when county isn't present
            name = sub('--None', '', name)
            place, created = models.Place.objects.get_or_create(name=name)
            if created:
                place.country = country
                place.state = state
                place.county = county
                place.city = city
                place.save()
            places.append(place)
        title.places = places
        return

    def _extract_publication_dates(self, record, title):
        for field in record.get_fields('362'):
            text = field['a']
            if text is None:
                continue
            pubdate, created = models.PublicationDate.objects.get_or_create(
                text=text, titles=title)
        return

    def _extract_subjects(self, record, title):
        subjects = []
        for field in record.get_fields('650', '651'):
            heading = '--'.join([v for k, v in field])
            if field.tag == '650':
                type = 't'
            else:
                type = 'g'
            # many-to-many relationship between titles and subjects
            subject, found = models.Subject.objects.get_or_create(
                heading=heading,
                type=type
            )
            subjects.append(subject)
        title.subjects = subjects
        return

    def _extract_notes(self, record, title):
        for field in record.fields:
            if field.tag.startswith('5') and field['a']:
                note, note_created = models.Note.objects.get_or_create(
                    text=field['a'],
                    type=field.tag,
                    title=title
                )
        return

    def _extract_preceeding_titles(self, record, title):
        for f in record.get_fields('780'):
            link_obj = self._unpack_link(models.PreceedingTitleLink, f)
            link, link_created = models.PreceedingTitleLink.objects.get_or_create(
                name=link_obj.name,
                lccn=link_obj.lccn,
                oclc=link_obj.oclc,
                title=title
            )
        return

    def _extract_succeeding_titles(self, record, title):
        for f in record.get_fields('785'):
            link_obj = self._unpack_link(models.SucceedingTitleLink, f)
            link, link_created = models.SucceedingTitleLink.objects.get_or_create(
                name=link_obj.name,
                lccn=link_obj.lccn,
                oclc=link_obj.oclc,
                title=title
            )
        return

    def _extract_related_titles(self, record, title):
        for f in record.get_fields('775'):
            link_obj = self._unpack_link(models.RelatedTitleLink, f)
            link, link_created = models.RelatedTitleLink.objects.get_or_create(
                name=link_obj.name,
                lccn=link_obj.lccn,
                oclc=link_obj.oclc,
                title=title
            )
        return

    def _extract_alt_titles(self, record, title):
        alt_titles = []

        for field in record.get_fields('246'):
            alt = models.AltTitle(name=field['a'])
            if field['b']:
                alt.name += field['b']
            if field['f']:
                alt.date = field['f']
            alt_titles.append(alt)

        # also add non-analytic added entries as alternate titles
        for field in record.get_fields('740'):
            if field.indicators[1] == ' ':
                alt = models.AltTitle(name=field['a'])
                alt_titles.append(alt)

        for alt_title in alt_titles:
            alt_obj, alt_created = models.AltTitle.objects.get_or_create(
                name=alt_title.name,
                date=alt_title.date,
                title=title
            )
        return

    def _extract_country(self, record):
        country_code = record['008'].data[15:18]
        country = models.Country.objects.get(code=country_code)
        return country

    def _unpack_link(self, klass, field):
        link = klass()
        link.name = field['t']
        if not link.name:
            link.name = field['a']

        for v in field.get_subfields('w'):
            if v.startswith('(DLC)'):
                link.lccn = _normal_lccn(v.replace('(DLC)', ''))
            elif v.startswith('(OCoLC)'):
                link.oclc = _normal_oclc(v.replace('(OCoLC)', ''))
        return link

    def _extract_oclc(self, record):
        # check for control number identifier of the 001 field
        cni = _extract(record, '003')

        # Strip & lower if cni is not NoneType
        if cni:
            cni = cni.strip().lower()

        # Info on codes referred to below:
        # http://www.loc.gov/marc/organizations/org-search.php
        # The first two checks are values found in older version
        # of title XML. In the third case, the XML is from
        # OCLC, but has no 003 field, so infer that None means
        # that the record has an implied 003 field.

        # dlc = DLC =  Library of Congress
        if cni == 'dlc':
            # then the 001 is LCCN, so we want to hit 035 $a.
            oclc = _extract(record, '035', 'a')

        # ocolc = OCoLC = OCLC
        # or
        # None implies that the 003 should be ocolc, but
        # it is not explicitly listed.
        elif (cni == 'ocolc') or (cni is None):
            oclc = _extract(record, '001')

        else:
            # if the script makes it here, we have a problem
            _logger.info("003 value is not handled by this load script")

        return _normal_oclc(oclc)

    def _extract_urls(self, record, title):
        for field in record.get_fields('856'):
            i2 = field.indicators[1]
            for url in field.get_subfields('u'):
                url_obj, url_created = models.Url.objects.get_or_create(
                    value=url, type=i2, title=title)
        return


def _extract(record, field, subfield=None):
    value = None
    try:
        if field and subfield:
            value = _clean(record[field][subfield])
        elif field:
            value = _clean(record[field].data)
    except:
        # TODO have pymarc emit missing field/subfield exception
        # which we can catch explicitly
        pass
    return value


def _clean(value):
    return sub(r'[ /:,]+$', '', value)


def _normal_place(value):
    if value is None:
        return None
    return sub(r'\.$', '', value)


def _normal_year(value):
    if value is None:
        return None
    elif value == '9999':
        return 'current'
    return sub(r'u', '?', value)


def _normal_lccn(value):
    if value is None:
        return None
    return value.replace(' ', '')


def _normal_oclc(value):
    """attempt to normalize an oclc number that can appear in a variety of
    ways in the MARC record. Important to get this right since it is how
    holdings records are attached to the title records

    See: http://info-uri.info/registry/OAIHandler?verb=GetRecord&metadataPrefix=reg&identifier=info:oclcnum/
    for information about normalizing OCLC numbers.
    """
    value = value.replace(' ', '')
    value = value.replace('(OCoLC)', '')
    value = value.lstrip('ocm')
    value = value.lstrip('0')
    return value


def _is_openoni_electronic_resource(title, record):
    # delete the Title if it is for an electronic resource
    # and it contains a link to chronicling america
    # https://rdc.lctl.gov/trac/ndnp/ticket/375
    if record['245']['h'] != '[electronic resource].':
        return False
    if len(title.issues.all()) != 0:
        return False
    for url in title.urls.all():
        if 'chroniclingamerica' in url.value:
            return True
    return False


def nsplit(s, n):
    """returns a string split up into sequences of length n
    http://mail.python.org/pipermail/python-list/2005-August/335131.html
    """
    return [s[k:k + n] for k in xrange(0, len(s), n)]


class TitleLoaderException(RuntimeError):
    pass


def load(location, bulk_load=True):
    loader = TitleLoader()

    _logger.info("loading titles from: %s" % location)

    loader.load_file(location)

    if not bulk_load:
        _logger.info("records processed: %i" % loader.records_processed)
        _logger.info("records created: %i" % loader.records_created)
        _logger.info("records updated: %i" % loader.records_updated)
        _logger.info("errors: %i" % loader.errors)
        _logger.info("missing lccns: %i" % loader.missing_lccns)

    return (loader.records_processed,
            loader.records_created,
            loader.records_updated,
            loader.errors,
            loader.missing_lccns)
