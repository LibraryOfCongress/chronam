# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160928_0840'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='languagetext',
            name='language',
        ),
        migrations.RemoveField(
            model_name='languagetext',
            name='ocr',
        ),
        migrations.DeleteModel(
            name='LanguageText',
        ),
    ]
