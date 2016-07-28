# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AltTitle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
                ('date', models.CharField(max_length=250, null=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Awardee',
            fields=[
                ('org_code', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('name', models.CharField(max_length=250, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('validated_batch_file', models.CharField(max_length=100)),
                ('released', models.DateTimeField(null=True)),
                ('source', models.CharField(max_length=4096, null=True)),
                ('sitemap_indexed', models.DateTimeField(null=True)),
                ('awardee', models.ForeignKey(related_name='batches', to='core.Awardee', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('region', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Essay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('created', models.DateTimeField()),
                ('modified', models.DateTimeField()),
                ('essay_editor_url', models.TextField()),
                ('html', models.TextField()),
                ('loaded', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(related_name='essays', to='core.Awardee')),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Ethnicity',
            fields=[
                ('name', models.CharField(max_length=250, serialize=False, primary_key=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='EthnicitySynonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('synonym', models.CharField(max_length=250)),
                ('ethnicity', models.ForeignKey(related_name='synonyms', to='core.Ethnicity')),
            ],
            options={
                'ordering': ('synonym',),
            },
        ),
        migrations.CreateModel(
            name='FlickrUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Holding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(null=True)),
                ('type', models.CharField(max_length=25, null=True)),
                ('last_updated', models.CharField(max_length=10, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(help_text=b'852$z', null=True)),
            ],
            options={
                'ordering': ('institution',),
            },
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('code', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('address1', models.CharField(max_length=255, null=True)),
                ('address2', models.CharField(max_length=255, null=True)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=2)),
                ('zip', models.CharField(max_length=20, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_issued', models.DateField(db_index=True)),
                ('volume', models.CharField(max_length=50, null=True)),
                ('number', models.CharField(max_length=50)),
                ('edition', models.IntegerField()),
                ('edition_label', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(related_name='issues', to='core.Batch')),
            ],
            options={
                'ordering': ('date_issued',),
            },
        ),
        migrations.CreateModel(
            name='IssueNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField()),
                ('text', models.TextField()),
                ('type', models.CharField(max_length=50)),
                ('issue', models.ForeignKey(related_name='notes', to='core.Issue')),
            ],
            options={
                'ordering': ('text',),
            },
        ),
        migrations.CreateModel(
            name='LaborPress',
            fields=[
                ('name', models.CharField(max_length=250, serialize=False, primary_key=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('code', models.CharField(max_length=3, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('lingvoj', models.CharField(max_length=200, null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='LanguageText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField()),
                ('language', models.ForeignKey(to='core.Language', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LoadBatchEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('batch_name', models.CharField(max_length=250)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MARC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MaterialType',
            fields=[
                ('name', models.CharField(max_length=250, serialize=False, primary_key=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField()),
                ('type', models.CharField(max_length=3)),
            ],
            options={
                'ordering': ('text',),
            },
        ),
        migrations.CreateModel(
            name='OCR',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='OcrDump',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('sha1', models.TextField()),
                ('size', models.BigIntegerField()),
                ('batch', models.OneToOneField(related_name='ocr_dump', to='core.Batch')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sequence', models.IntegerField(db_index=True)),
                ('number', models.CharField(max_length=50)),
                ('section_label', models.CharField(max_length=100)),
                ('tiff_filename', models.CharField(max_length=250)),
                ('jp2_filename', models.CharField(max_length=250, null=True)),
                ('jp2_width', models.IntegerField(null=True)),
                ('jp2_length', models.IntegerField(null=True)),
                ('pdf_filename', models.CharField(max_length=250, null=True)),
                ('ocr_filename', models.CharField(max_length=250, null=True)),
                ('indexed', models.BooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('issue', models.ForeignKey(related_name='pages', to='core.Issue')),
            ],
            options={
                'ordering': ('sequence',),
            },
        ),
        migrations.CreateModel(
            name='PageNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField()),
                ('text', models.TextField()),
                ('type', models.CharField(max_length=50)),
                ('page', models.ForeignKey(related_name='notes', to='core.Page')),
            ],
            options={
                'ordering': ('text',),
            },
        ),
        migrations.CreateModel(
            name='PhysicalDescription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField()),
                ('type', models.CharField(max_length=3)),
            ],
            options={
                'ordering': ('type',),
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('name', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('city', models.CharField(max_length=100, null=True, db_index=True)),
                ('county', models.CharField(max_length=100, null=True, db_index=True)),
                ('state', models.CharField(max_length=100, null=True, db_index=True)),
                ('country', models.CharField(max_length=100, null=True)),
                ('dbpedia', models.CharField(max_length=250, null=True)),
                ('geonames', models.CharField(max_length=250, null=True)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='PreceedingTitleLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, null=True)),
                ('lccn', models.CharField(max_length=50, null=True)),
                ('oclc', models.CharField(max_length=50, null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='PublicationDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=500)),
            ],
            options={
                'ordering': ['text'],
            },
        ),
        migrations.CreateModel(
            name='Reel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=50)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('implicit', models.BooleanField(default=False)),
                ('batch', models.ForeignKey(related_name='reels', to='core.Batch')),
            ],
        ),
        migrations.CreateModel(
            name='RelatedTitleLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, null=True)),
                ('lccn', models.CharField(max_length=50, null=True)),
                ('oclc', models.CharField(max_length=50, null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('heading', models.CharField(max_length=250)),
                ('type', models.CharField(max_length=1)),
            ],
            options={
                'ordering': ('heading',),
            },
        ),
        migrations.CreateModel(
            name='SucceedingTitleLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, null=True)),
                ('lccn', models.CharField(max_length=50, null=True)),
                ('oclc', models.CharField(max_length=50, null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('lccn', models.CharField(max_length=25, serialize=False, primary_key=True)),
                ('lccn_orig', models.CharField(max_length=25)),
                ('name', models.CharField(max_length=250)),
                ('name_normal', models.CharField(max_length=250)),
                ('edition', models.CharField(max_length=250, null=True)),
                ('place_of_publication', models.CharField(max_length=250, null=True)),
                ('publisher', models.CharField(max_length=250, null=True)),
                ('frequency', models.CharField(max_length=250, null=True)),
                ('frequency_date', models.CharField(max_length=250, null=True)),
                ('medium', models.CharField(help_text=b'245$h field', max_length=50, null=True)),
                ('oclc', models.CharField(max_length=25, null=True, db_index=True)),
                ('issn', models.CharField(max_length=15, null=True)),
                ('start_year', models.CharField(max_length=10)),
                ('end_year', models.CharField(max_length=10)),
                ('version', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('has_issues', models.BooleanField(default=False, db_index=True)),
                ('uri', models.URLField(help_text=b'856$u', max_length=500, null=True)),
                ('sitemap_indexed', models.DateTimeField(null=True)),
                ('country', models.ForeignKey(to='core.Country')),
            ],
            options={
                'ordering': ['name_normal'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
                ('topic_start_year', models.IntegerField()),
                ('topic_end_year', models.IntegerField()),
                ('suggested_search_terms', models.TextField()),
                ('intro_text', models.TextField()),
                ('important_dates', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TopicCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
                ('date_synced', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TopicPages',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('query_params', models.CharField(max_length=500)),
                ('title', models.CharField(max_length=250)),
                ('url', models.CharField(max_length=1000)),
                ('description', models.TextField()),
                ('page', models.ForeignKey(to='core.Page', null=True)),
                ('topic', models.ForeignKey(to='core.Topic')),
            ],
        ),
        migrations.CreateModel(
            name='Url',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField()),
                ('type', models.CharField(max_length=1, null=True)),
                ('title', models.ForeignKey(related_name='urls', to='core.Title')),
            ],
        ),
        migrations.AddField(
            model_name='topic',
            name='category',
            field=models.ForeignKey(to='core.TopicCategory'),
        ),
        migrations.AddField(
            model_name='succeedingtitlelink',
            name='title',
            field=models.ForeignKey(related_name='succeeding_title_links', to='core.Title'),
        ),
        migrations.AddField(
            model_name='subject',
            name='titles',
            field=models.ManyToManyField(related_name='subjects', to='core.Title'),
        ),
        migrations.AddField(
            model_name='relatedtitlelink',
            name='title',
            field=models.ForeignKey(related_name='related_title_links', to='core.Title'),
        ),
        migrations.AddField(
            model_name='publicationdate',
            name='titles',
            field=models.ForeignKey(related_name='publication_dates', to='core.Title'),
        ),
        migrations.AddField(
            model_name='preceedingtitlelink',
            name='title',
            field=models.ForeignKey(related_name='preceeding_title_links', to='core.Title'),
        ),
        migrations.AddField(
            model_name='place',
            name='titles',
            field=models.ManyToManyField(related_name='places', to='core.Title'),
        ),
        migrations.AddField(
            model_name='physicaldescription',
            name='title',
            field=models.ForeignKey(related_name='dates_of_publication', to='core.Title'),
        ),
        migrations.AddField(
            model_name='page',
            name='reel',
            field=models.ForeignKey(related_name='pages', to='core.Reel', null=True),
        ),
        migrations.AddField(
            model_name='ocr',
            name='page',
            field=models.OneToOneField(related_name='ocr', null=True, to='core.Page'),
        ),
        migrations.AddField(
            model_name='note',
            name='title',
            field=models.ForeignKey(related_name='notes', to='core.Title'),
        ),
        migrations.AddField(
            model_name='marc',
            name='title',
            field=models.OneToOneField(related_name='marc', to='core.Title'),
        ),
        migrations.AddField(
            model_name='languagetext',
            name='ocr',
            field=models.ForeignKey(related_name='language_texts', to='core.OCR'),
        ),
        migrations.AddField(
            model_name='language',
            name='titles',
            field=models.ManyToManyField(related_name='languages', to='core.Title'),
        ),
        migrations.AddField(
            model_name='issue',
            name='title',
            field=models.ForeignKey(related_name='issues', to='core.Title'),
        ),
        migrations.AddField(
            model_name='holding',
            name='institution',
            field=models.ForeignKey(related_name='holdings', to='core.Institution'),
        ),
        migrations.AddField(
            model_name='holding',
            name='title',
            field=models.ForeignKey(related_name='holdings', to='core.Title'),
        ),
        migrations.AddField(
            model_name='flickrurl',
            name='page',
            field=models.ForeignKey(related_name='flickr_urls', to='core.Page'),
        ),
        migrations.AddField(
            model_name='essay',
            name='titles',
            field=models.ManyToManyField(related_name='essays', to='core.Title'),
        ),
        migrations.AddField(
            model_name='alttitle',
            name='title',
            field=models.ForeignKey(related_name='alt_titles', to='core.Title'),
        ),
    ]
