import os
import logging
import datetime

from lxml import etree
from django.conf import settings

from chronam.core.batch_loader import ns
from chronam.web.index import index_title
from chronam.core.models import Essay, Title


_logger = logging.getLogger(__name__)


class EssayLoader:

    def __init__(self):
        self.missing = []
        self.creates = []
        self.deletes = []

    def load(self, batch_dir, index=True):
        """
        Loads encyclopedia entries from a batch.
        """
        for essay, titles in self._get_entries(batch_dir):
            # sanity check to make  sure we haven't seen an essay for this 
            # title with the exact same timestamp (this can happen if
            # an essay is accidentally placed in two essay batches)
            # TODO: if we had a unique identifier for an essay this would be 
            # cleaner
            seen_before = False
            for title in titles:
               if title.essays.filter(created=essay.created).count() != 0:
                    _logger.error("already seen essay %s:%s " %\
                            (title.lccn, essay.created))
                    seen_before = True
            if seen_before:
                continue

            # persist the essay
            essay.save()
            essay.titles = titles
            essay.save()

            # index titles if needed
            if index:
                for title in titles:
                    index_title(title)

            # keep track of lccns that we created essays for 
            self.creates.extend([title.lccn for title in titles])

            _logger.info("added essay to titles: %s" % (titles))

    def purge(self, batch_dir, index=True):
        """
        Purges encyclopedia entries in a batch from the database.
        """
        for essay, titles in self._get_entries(batch_dir):
            essays = Essay.objects.filter(created=essay.created,
                    titles__in=titles)
            num_essays = len(essays)
            if num_essays == 1:
                _logger.info("purging essay: %s" % essays[0])
                essays[0].delete()
                self.deletes.extend([t.lccn for t in titles])
            elif num_essays == 0:
                logging.error("unable to find essay to delete")
            else:
                logging.error("found too many essays to delete")

    def _get_entries(self, batch_dir):
        """
        A generator that looks through an essay batch and returns
        an Essay and its associated Titles for each essay in the batch.
        The Essay and Title objects are not persisted.
        """
        batch_xml = os.path.join(batch_dir, 'batch_1.xml')
        doc = etree.parse(batch_xml)
        for entry in doc.xpath('.//ndnp:encyclopediaEntry', namespaces=ns):
            entry_file = os.path.join(batch_dir, entry.text)
            _logger.info("parsing essay xml file: %s" % entry_file)

            doc = etree.parse(entry_file)
            mets_file = entry_file.replace(settings.ESSAY_STORAGE + '/', '')

            # grab the create time which is important for creating 
            # unique URIs when there are multiple essays for a title
            try: 
                created = doc.xpath('string(//mets:metsHdr/@CREATEDATE)', 
                                    namespaces=ns)
                created = datetime.datetime.strptime(created, '%Y-%m-%dT%H:%M:%S')
            except Exception, e:
                _logger.error("no CREATEDATE in %s: %s" % entry_file, e)
                return

            for div in doc.xpath('.//mets:structMap/mets:div', namespaces=ns):
                if div.attrib.get('TYPE', '') != 'np:encyclopediaEntry':
                    continue

                dmdid = div.attrib.get('DMDID', None)

                # get the html
                fileid = div.xpath('.//mets:fptr', namespaces=ns)[0].attrib['FILEID']
                html = self._extract_html(doc, fileid)

                # get the titles that the essay is attached to
                titles = []
                for id in doc.xpath('.//mets:dmdSec[@ID="%s"]//mods:identifier[@type="lccn"]' % dmdid, namespaces=ns):
                    lccn = id.xpath('string()')
                    _logger.info("found essay for lccn: %s" % lccn)

                    # look for the title
                    try:
                        title = Title.objects.get(lccn=lccn)
                        titles.append(title)
                    except Title.DoesNotExist, e:
                        _logger.error("no title record for %s" % lccn)
                        self.missing.append(lccn)
                        continue
                if len(titles) > 0:
                    essay = Essay(html=html, created=created, 
                            mets_file=mets_file)
                    yield essay, titles

    def _extract_html(self, doc, fileid):
        html = doc.xpath('.//mets:file[@ID="%s"]//xhtml:html' % fileid,
                namespaces=ns)[0]
        # rewrite info:lccn/* uris to be relative lccn/* urls
        for a in html.xpath('.//xhtml:a', namespaces=ns):
            if a.attrib.get('href', '').startswith('info:lccn'):
                url = a.attrib.get('href').replace('info:lccn/', '/lccn/')
                a.attrib['href'] = url
        return etree.tostring(html)
