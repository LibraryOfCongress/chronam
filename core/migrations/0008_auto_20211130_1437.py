# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_index_issue_titles_with_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuenote',
            name='text',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='note',
            name='text',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pagenote',
            name='text',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='physicaldescription',
            name='text',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='publicationdate',
            name='text',
            field=models.CharField(default=b'', max_length=500, blank=True),
        ),
    ]

