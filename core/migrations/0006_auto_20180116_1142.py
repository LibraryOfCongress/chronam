# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_languagetext_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batch',
            name='sitemap_indexed',
        ),
        migrations.RemoveField(
            model_name='title',
            name='sitemap_indexed',
        ),
        migrations.AlterField(
            model_name='essay',
            name='loaded',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
