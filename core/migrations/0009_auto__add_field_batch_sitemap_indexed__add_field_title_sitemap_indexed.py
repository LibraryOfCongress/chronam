# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Batch.sitemap_indexed'
        db.add_column('core_batch', 'sitemap_indexed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'Title.sitemap_indexed'
        db.add_column('core_title', 'sitemap_indexed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Batch.sitemap_indexed'
        db.delete_column('core_batch', 'sitemap_indexed')

        # Deleting field 'Title.sitemap_indexed'
        db.delete_column('core_title', 'sitemap_indexed')


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
            'sitemap_indexed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
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
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'holdings'", 'to': "orm['core.Institution']"}),
            'last_updated': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
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
            'page': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr'", 'unique': 'True', 'null': 'True', 'to': "orm['core.Page']"})
        },
        'core.ocrdump': {
            'Meta': {'object_name': 'OcrDump'},
            'batch': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ocr_dump'", 'unique': 'True', 'to': "orm['core.Batch']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        'core.url': {
            'Meta': {'object_name': 'Url'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['core.Title']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['core']