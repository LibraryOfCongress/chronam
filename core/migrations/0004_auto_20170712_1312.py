# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160928_0840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='section_label',
            field=models.CharField(max_length=250),
        ),
    ]
