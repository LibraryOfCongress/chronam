# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TopicPages'
        db.create_table(u'core_topicpages', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Page'], null=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Topic'])),
            ('query_params', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'core', ['TopicPages'])

        # Adding model 'Topic'
        db.create_table(u'core_topic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.TopicCategory'])),
            ('topic_start_year', self.gf('django.db.models.fields.IntegerField')()),
            ('topic_end_year', self.gf('django.db.models.fields.IntegerField')()),
            ('suggested_search_terms', self.gf('django.db.models.fields.TextField')()),
            ('intro_text', self.gf('django.db.models.fields.TextField')()),
            ('important_dates', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'core', ['Topic'])

        # Adding model 'TopicCategory'
        db.create_table(u'core_topiccategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('date_synced', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['TopicCategory'])

        db.execute('ALTER TABLE core_topicpages CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;')
        db.execute('ALTER TABLE core_topic CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;')
        db.execute('ALTER TABLE core_topiccategory CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;')

    def backwards(self, orm):
        # Deleting model 'TopicPages'
        db.delete_table(u'core_topicpages')

        # Deleting model 'Topic'
        db.delete_table(u'core_topic')

        # Deleting model 'TopicCategory'
        db.delete_table(u'core_topiccategory')


    models = {
        u'core.alttitle': {
            'Meta': {'ordering': "['name']", 'object_name': 'AltTitle'},
            'date': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alt_titles'", 'to': u"orm['core.Title']"})
        },
        u'core.awardee': {
            'Meta': {'object_name': 'Awardee'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'org_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        },
        u'core.batch': {
            'Meta': {'object_name': 'Batch'},
            'awardee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'batches'", 'null': 'True', 'to': u"orm['core.Awardee']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'}),
            'released': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'sitemap_indexed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'validated_batch_file': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.essay': {
            'Meta': {'ordering': "['title']", 'object_name': 'Essay'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'essays'", 'to': u"orm['core.Awardee']"}),
            'essay_editor_url': ('django.db.models.fields.TextField', [], {}),
            'html': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'essays'", 'symmetrical': 'False', 'to': u"orm['core.Title']"})
        },
        u'core.ethnicity': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Ethnicity'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        u'core.ethnicitysynonym': {
            'Meta': {'ordering': "('synonym',)", 'object_name': 'EthnicitySynonym'},
            'ethnicity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'synonyms'", 'to': u"orm['core.Ethnicity']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'synonym': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'core.flickrurl': {
            'Meta': {'object_name': 'FlickrUrl'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flickr_urls'", 'to': u"orm['core.Page']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'core.holding': {
            'Meta': {'ordering': "('institution',)", 'object_name': 'Holding'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'holdings'", 'to': u"orm['core.Institution']"}),
            'last_updated': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'holdings'", 'to': u"orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True'})
        },
        u'core.institution': {
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
        u'core.issue': {
            'Meta': {'ordering': "('date_issued',)", 'object_name': 'Issue'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': u"orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_issued': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'edition': ('django.db.models.fields.IntegerField', [], {}),
            'edition_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'issues'", 'to': u"orm['core.Title']"}),
            'volume': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'core.issuenote': {
            'Meta': {'ordering': "('text',)", 'object_name': 'IssueNote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': u"orm['core.Issue']"}),
            'label': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'core.laborpress': {
            'Meta': {'ordering': "('name',)", 'object_name': 'LaborPress'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        u'core.language': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'primary_key': 'True'}),
            'lingvoj': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'languages'", 'symmetrical': 'False', 'to': u"orm['core.Title']"})
        },
        u'core.languagetext': {
            'Meta': {'object_name': 'LanguageText'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Language']", 'null': 'True'}),
            'ocr': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'language_texts'", 'to': u"orm['core.OCR']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'core.loadbatchevent': {
            'Meta': {'object_name': 'LoadBatchEvent'},
            'batch_name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        u'core.marc': {
            'Meta': {'object_name': 'MARC'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'marc'", 'unique': 'True', 'to': u"orm['core.Title']"}),
            'xml': ('django.db.models.fields.TextField', [], {})
        },
        u'core.materialtype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MaterialType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        },
        u'core.note': {
            'Meta': {'ordering': "('text',)", 'object_name': 'Note'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': u"orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        u'core.ocr': {
            'Meta': {'object_name': 'OCR'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr'", 'unique': 'True', 'null': 'True', 'to': u"orm['core.Page']"})
        },
        u'core.ocrdump': {
            'Meta': {'object_name': 'OcrDump'},
            'batch': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr_dump'", 'unique': 'True', 'to': u"orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sha1': ('django.db.models.fields.TextField', [], {}),
            'size': ('django.db.models.fields.BigIntegerField', [], {})
        },
        u'core.page': {
            'Meta': {'ordering': "('sequence',)", 'object_name': 'Page'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indexed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['core.Issue']"}),
            'jp2_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'jp2_length': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'jp2_width': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ocr_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'pdf_filename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'reel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'null': 'True', 'to': u"orm['core.Reel']"}),
            'section_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tiff_filename': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'core.pagenote': {
            'Meta': {'ordering': "('text',)", 'object_name': 'PageNote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.TextField', [], {}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': u"orm['core.Page']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'core.physicaldescription': {
            'Meta': {'ordering': "('type',)", 'object_name': 'PhysicalDescription'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dates_of_publication'", 'to': u"orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        u'core.place': {
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
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'places'", 'symmetrical': 'False', 'to': u"orm['core.Title']"})
        },
        u'core.preceedingtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PreceedingTitleLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'preceeding_title_links'", 'to': u"orm['core.Title']"})
        },
        u'core.publicationdate': {
            'Meta': {'ordering': "['text']", 'object_name': 'PublicationDate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'titles': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'publication_dates'", 'to': u"orm['core.Title']"})
        },
        u'core.reel': {
            'Meta': {'object_name': 'Reel'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reels'", 'to': u"orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'implicit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'core.relatedtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'RelatedTitleLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_title_links'", 'to': u"orm['core.Title']"})
        },
        u'core.subject': {
            'Meta': {'ordering': "('heading',)", 'object_name': 'Subject'},
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'titles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'subjects'", 'symmetrical': 'False', 'to': u"orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        u'core.succeedingtitlelink': {
            'Meta': {'ordering': "('name',)", 'object_name': 'SucceedingTitleLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'succeeding_title_links'", 'to': u"orm['core.Title']"})
        },
        u'core.title': {
            'Meta': {'ordering': "['name_normal']", 'object_name': 'Title'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Country']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'end_year': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'frequency_date': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'has_issues': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'issn': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'lccn': ('django.db.models.fields.CharField', [], {'max_length': '25', 'primary_key': 'True'}),
            'lccn_orig': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'name_normal': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'oclc': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'db_index': 'True'}),
            'place_of_publication': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True'}),
            'sitemap_indexed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'start_year': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'uri': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True'}),
            'version': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'core.topic': {
            'Meta': {'object_name': 'Topic'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.TopicCategory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'important_dates': ('django.db.models.fields.TextField', [], {}),
            'intro_text': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'suggested_search_terms': ('django.db.models.fields.TextField', [], {}),
            'topic_end_year': ('django.db.models.fields.IntegerField', [], {}),
            'topic_start_year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'core.topiccategory': {
            'Meta': {'object_name': 'TopicCategory'},
            'date_synced': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'core.topicpages': {
            'Meta': {'object_name': 'TopicPages'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Page']", 'null': 'True'}),
            'query_params': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Topic']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'core.url': {
            'Meta': {'object_name': 'Url'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': u"orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['core']
