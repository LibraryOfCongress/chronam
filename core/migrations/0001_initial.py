# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Awardee'
        db.create_table('core_awardee', (
            ('org_code', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Awardee'])

        # Adding model 'Batch'
        db.create_table('core_batch', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('validated_batch_file', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('awardee', self.gf('django.db.models.fields.related.ForeignKey')(related_name='batches', null=True, to=orm['core.Awardee'])),
            ('released', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=4096, null=True)),
        ))
        db.send_create_signal('core', ['Batch'])

        # Adding model 'LoadBatchEvent'
        db.create_table('core_loadbatchevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('batch_name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('core', ['LoadBatchEvent'])

        # Adding model 'Title'
        db.create_table('core_title', (
            ('lccn', self.gf('django.db.models.fields.CharField')(max_length=25, primary_key=True)),
            ('lccn_orig', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('name_normal', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('place_of_publication', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('frequency', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('frequency_date', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('oclc', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, db_index=True)),
            ('issn', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('start_year', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('end_year', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Country'])),
            ('version', self.gf('django.db.models.fields.DateTimeField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('has_issues', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('core', ['Title'])

        # Adding model 'AltTitle'
        db.create_table('core_alttitle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='alt_titles', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['AltTitle'])

        # Adding model 'MARC'
        db.create_table('core_marc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('title', self.gf('django.db.models.fields.related.OneToOneField')(related_name='marc', unique=True, to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['MARC'])

        # Adding model 'Issue'
        db.create_table('core_issue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_issued', self.gf('django.db.models.fields.DateField')(db_index=True)),
            ('volume', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('edition', self.gf('django.db.models.fields.IntegerField')()),
            ('edition_label', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='issues', to=orm['core.Title'])),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='issues', to=orm['core.Batch'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Issue'])

        # Adding model 'Page'
        db.create_table('core_page', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sequence', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('section_label', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('tiff_filename', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('jp2_filename', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('jp2_width', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('jp2_length', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('pdf_filename', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('ocr_filename', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('issue', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pages', to=orm['core.Issue'])),
            ('reel', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pages', null=True, to=orm['core.Reel'])),
            ('indexed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Page'])

        # Adding model 'LanguageText'
        db.create_table('core_languagetext', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Language'], null=True)),
            ('ocr', self.gf('django.db.models.fields.related.ForeignKey')(related_name='language_texts', to=orm['core.OCR'])),
        ))
        db.send_create_signal('core', ['LanguageText'])

        # Adding model 'OCR'
        db.create_table('core_ocr', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('word_coordinates_json', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('page', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ocr', unique=True, null=True, to=orm['core.Page'])),
        ))
        db.send_create_signal('core', ['OCR'])

        # Adding model 'PublicationDate'
        db.create_table('core_publicationdate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('titles', self.gf('django.db.models.fields.related.ForeignKey')(related_name='publication_dates', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['PublicationDate'])

        # Adding model 'Place'
        db.create_table('core_place', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, primary_key=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('county', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('dbpedia', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('geonames', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True)),
        ))
        db.send_create_signal('core', ['Place'])

        # Adding M2M table for field titles on 'Place'
        db.create_table('core_place_titles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('place', models.ForeignKey(orm['core.place'], null=False)),
            ('title', models.ForeignKey(orm['core.title'], null=False))
        ))
        db.create_unique('core_place_titles', ['place_id', 'title_id'])

        # Adding model 'Subject'
        db.create_table('core_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('heading', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('core', ['Subject'])

        # Adding M2M table for field titles on 'Subject'
        db.create_table('core_subject_titles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('subject', models.ForeignKey(orm['core.subject'], null=False)),
            ('title', models.ForeignKey(orm['core.title'], null=False))
        ))
        db.create_unique('core_subject_titles', ['subject_id', 'title_id'])

        # Adding model 'Note'
        db.create_table('core_note', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notes', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['Note'])

        # Adding model 'PageNote'
        db.create_table('core_pagenote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notes', to=orm['core.Page'])),
        ))
        db.send_create_signal('core', ['PageNote'])

        # Adding model 'IssueNote'
        db.create_table('core_issuenote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('issue', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notes', to=orm['core.Issue'])),
        ))
        db.send_create_signal('core', ['IssueNote'])

        # Adding model 'Essay'
        db.create_table('core_essay', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')()),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='essays', to=orm['core.Awardee'])),
            ('essay_editor_url', self.gf('django.db.models.fields.TextField')()),
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('loaded', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Essay'])

        # Adding M2M table for field titles on 'Essay'
        db.create_table('core_essay_titles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('essay', models.ForeignKey(orm['core.essay'], null=False)),
            ('title', models.ForeignKey(orm['core.title'], null=False))
        ))
        db.create_unique('core_essay_titles', ['essay_id', 'title_id'])

        # Adding model 'Holding'
        db.create_table('core_holding', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=25, null=True)),
            ('institution', self.gf('django.db.models.fields.related.ForeignKey')(related_name='holdings', to=orm['core.Institution'])),
            ('last_updated', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='holdings', to=orm['core.Title'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Holding'])

        # Adding model 'SucceedingTitleLink'
        db.create_table('core_succeedingtitlelink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('lccn', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('oclc', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='succeeding_title_links', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['SucceedingTitleLink'])

        # Adding model 'PreceedingTitleLink'
        db.create_table('core_preceedingtitlelink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('lccn', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('oclc', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='preceeding_title_links', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['PreceedingTitleLink'])

        # Adding model 'RelatedTitleLink'
        db.create_table('core_relatedtitlelink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, null=True)),
            ('lccn', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('oclc', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_title_links', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['RelatedTitleLink'])

        # Adding model 'Ethnicity'
        db.create_table('core_ethnicity', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
        ))
        db.send_create_signal('core', ['Ethnicity'])

        # Adding model 'EthnicitySynonym'
        db.create_table('core_ethnicitysynonym', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('synonym', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('ethnicity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='synonyms', to=orm['core.Ethnicity'])),
        ))
        db.send_create_signal('core', ['EthnicitySynonym'])

        # Adding model 'Language'
        db.create_table('core_language', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('lingvoj', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
        ))
        db.send_create_signal('core', ['Language'])

        # Adding M2M table for field titles on 'Language'
        db.create_table('core_language_titles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('language', models.ForeignKey(orm['core.language'], null=False)),
            ('title', models.ForeignKey(orm['core.title'], null=False))
        ))
        db.create_unique('core_language_titles', ['language_id', 'title_id'])

        # Adding model 'Country'
        db.create_table('core_country', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('core', ['Country'])

        # Adding model 'LaborPress'
        db.create_table('core_laborpress', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
        ))
        db.send_create_signal('core', ['LaborPress'])

        # Adding model 'MaterialType'
        db.create_table('core_materialtype', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
        ))
        db.send_create_signal('core', ['MaterialType'])

        # Adding model 'Institution'
        db.create_table('core_institution', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('address1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('address2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['Institution'])

        # Adding model 'PhysicalDescription'
        db.create_table('core_physicaldescription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dates_of_publication', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['PhysicalDescription'])

        # Adding model 'Url'
        db.create_table('core_url', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('title', self.gf('django.db.models.fields.related.ForeignKey')(related_name='urls', to=orm['core.Title'])),
        ))
        db.send_create_signal('core', ['Url'])

        # Adding model 'FlickrUrl'
        db.create_table('core_flickrurl', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='flickr_urls', to=orm['core.Page'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['FlickrUrl'])

        # Adding model 'Reel'
        db.create_table('core_reel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reels', to=orm['core.Batch'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('implicit', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Reel'])

        # Adding model 'OcrDump'
        db.create_table('core_ocrdump', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sequence', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('sha1', self.gf('django.db.models.fields.TextField')()),
            ('size', self.gf('django.db.models.fields.BigIntegerField')()),
            ('batch', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ocr_dump', unique=True, to=orm['core.Batch'])),
        ))
        db.send_create_signal('core', ['OcrDump'])


    def backwards(self, orm):
        # Deleting model 'Awardee'
        db.delete_table('core_awardee')

        # Deleting model 'Batch'
        db.delete_table('core_batch')

        # Deleting model 'LoadBatchEvent'
        db.delete_table('core_loadbatchevent')

        # Deleting model 'Title'
        db.delete_table('core_title')

        # Deleting model 'AltTitle'
        db.delete_table('core_alttitle')

        # Deleting model 'MARC'
        db.delete_table('core_marc')

        # Deleting model 'Issue'
        db.delete_table('core_issue')

        # Deleting model 'Page'
        db.delete_table('core_page')

        # Deleting model 'LanguageText'
        db.delete_table('core_languagetext')

        # Deleting model 'OCR'
        db.delete_table('core_ocr')

        # Deleting model 'PublicationDate'
        db.delete_table('core_publicationdate')

        # Deleting model 'Place'
        db.delete_table('core_place')

        # Removing M2M table for field titles on 'Place'
        db.delete_table('core_place_titles')

        # Deleting model 'Subject'
        db.delete_table('core_subject')

        # Removing M2M table for field titles on 'Subject'
        db.delete_table('core_subject_titles')

        # Deleting model 'Note'
        db.delete_table('core_note')

        # Deleting model 'PageNote'
        db.delete_table('core_pagenote')

        # Deleting model 'IssueNote'
        db.delete_table('core_issuenote')

        # Deleting model 'Essay'
        db.delete_table('core_essay')

        # Removing M2M table for field titles on 'Essay'
        db.delete_table('core_essay_titles')

        # Deleting model 'Holding'
        db.delete_table('core_holding')

        # Deleting model 'SucceedingTitleLink'
        db.delete_table('core_succeedingtitlelink')

        # Deleting model 'PreceedingTitleLink'
        db.delete_table('core_preceedingtitlelink')

        # Deleting model 'RelatedTitleLink'
        db.delete_table('core_relatedtitlelink')

        # Deleting model 'Ethnicity'
        db.delete_table('core_ethnicity')

        # Deleting model 'EthnicitySynonym'
        db.delete_table('core_ethnicitysynonym')

        # Deleting model 'Language'
        db.delete_table('core_language')

        # Removing M2M table for field titles on 'Language'
        db.delete_table('core_language_titles')

        # Deleting model 'Country'
        db.delete_table('core_country')

        # Deleting model 'LaborPress'
        db.delete_table('core_laborpress')

        # Deleting model 'MaterialType'
        db.delete_table('core_materialtype')

        # Deleting model 'Institution'
        db.delete_table('core_institution')

        # Deleting model 'PhysicalDescription'
        db.delete_table('core_physicaldescription')

        # Deleting model 'Url'
        db.delete_table('core_url')

        # Deleting model 'FlickrUrl'
        db.delete_table('core_flickrurl')

        # Deleting model 'Reel'
        db.delete_table('core_reel')

        # Deleting model 'OcrDump'
        db.delete_table('core_ocrdump')


    models = {
        'core.alttitle': {
            'Meta': {'ordering': "['name']", 'object_name': 'AltTitle'},
            'date': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alt_titles'", 'to': "orm['core.Title']"})
        },
        'core.awardee': {
            'Meta': {'object_name': 'Awardee'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'org_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        },
        'core.batch': {
            'Meta': {'object_name': 'Batch'},
            'awardee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batches'", 'null': 'True', 'to': "orm['core.Awardee']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'}),
            'released': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'validated_batch_file': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.essay': {
            'Meta': {'ordering': "['title']", 'object_name': 'Essay'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'essays'", 'to': "orm['core.Awardee']"}),
            'essay_editor_url': ('django.db.models.fields.TextField', [], {}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'essays'", 'symmetrical': 'False', 'to': "orm['core.Title']"})
        },
        'core.ethnicity': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Ethnicity'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        'core.ethnicitysynonym': {
            'Meta': {'ordering': "('synonym',)", 'object_name': 'EthnicitySynonym'},
            'ethnicity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'synonyms'", 'to': "orm['core.Ethnicity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'core.flickrurl': {
            'Meta': {'object_name': 'FlickrUrl'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flickr_urls'", 'to': "orm['core.Page']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'core.holding': {
            'Meta': {'ordering': "('institution',)", 'object_name': 'Holding'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'holdings'", 'to': "orm['core.Institution']"}),
            'last_updated': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'holdings'", 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True'})
        },
        'core.institution': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Institution'},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'})
        },
        'core.issue': {
            'Meta': {'ordering': "('date_issued',)", 'object_name': 'Issue'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_issued': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'edition': ('django.db.models.fields.IntegerField', [], {}),
            'edition_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': "orm['core.Title']"}),
            'volume': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        'core.issuenote': {
            'Meta': {'ordering': "('text',)", 'object_name': 'IssueNote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': "orm['core.Issue']"}),
            'label': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'core.laborpress': {
            'Meta': {'ordering': "('name',)", 'object_name': 'LaborPress'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        'core.language': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'primary_key': 'True'}),
            'lingvoj': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'languages'", 'symmetrical': 'False', 'to': "orm['core.Title']"})
        },
        'core.languagetext': {
            'Meta': {'object_name': 'LanguageText'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Language']", 'null': 'True'}),
            'ocr': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'language_texts'", 'to': "orm['core.OCR']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'core.loadbatchevent': {
            'Meta': {'object_name': 'LoadBatchEvent'},
            'batch_name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'core.marc': {
            'Meta': {'object_name': 'MARC'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'marc'", 'unique': 'True', 'to': "orm['core.Title']"}),
            'xml': ('django.db.models.fields.TextField', [], {})
        },
        'core.materialtype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MaterialType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        'core.note': {
            'Meta': {'ordering': "('text',)", 'object_name': 'Note'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'core.ocr': {
            'Meta': {'object_name': 'OCR'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr'", 'unique': 'True', 'null': 'True', 'to': "orm['core.Page']"}),
            'word_coordinates_json': ('django.db.models.fields.TextField', [], {})
        },
        'core.ocrdump': {
            'Meta': {'object_name': 'OcrDump'},
            'batch': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr_dump'", 'unique': 'True', 'to': "orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'sha1': ('django.db.models.fields.TextField', [], {}),
            'size': ('django.db.models.fields.BigIntegerField', [], {})
        },
        'core.page': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Page'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indexed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': "orm['core.Issue']"}),
            'jp2_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'jp2_length': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'jp2_width': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ocr_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'pdf_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'reel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'null': 'True', 'to': "orm['core.Reel']"}),
            'section_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tiff_filename': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'core.pagenote': {
            'Meta': {'ordering': "('text',)", 'object_name': 'PageNote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.TextField', [], {}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': "orm['core.Page']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'core.physicaldescription': {
            'Meta': {'ordering': "('type',)", 'object_name': 'PhysicalDescription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dates_of_publication'", 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'core.place': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Place'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'county': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'dbpedia': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'geonames': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'places'", 'symmetrical': 'False', 'to': "orm['core.Title']"})
        },
        'core.preceedingtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PreceedingTitleLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'preceeding_title_links'", 'to': "orm['core.Title']"})
        },
        'core.publicationdate': {
            'Meta': {'ordering': "['text']", 'object_name': 'PublicationDate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'titles': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'publication_dates'", 'to': "orm['core.Title']"})
        },
        'core.reel': {
            'Meta': {'object_name': 'Reel'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reels'", 'to': "orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'implicit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'core.relatedtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'RelatedTitleLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_title_links'", 'to': "orm['core.Title']"})
        },
        'core.subject': {
            'Meta': {'ordering': "('heading',)", 'object_name': 'Subject'},
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subjects'", 'symmetrical': 'False', 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'core.succeedingtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'SucceedingTitleLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'succeeding_title_links'", 'to': "orm['core.Title']"})
        },
        'core.title': {
            'Meta': {'ordering': "['name_normal']", 'object_name': 'Title'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Country']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'end_year': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'frequency_date': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'has_issues': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'issn': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '25', 'primary_key': 'True'}),
            'lccn_orig': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'name_normal': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'db_index': 'True'}),
            'place_of_publication': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'start_year': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'version': ('django.db.models.fields.DateTimeField', [], {})
        },
        'core.url': {
            'Meta': {'object_name': 'Url'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['core']