# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20180116_1142'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='issue',
            index_together=set([('title', 'date_issued')]),
        ),
    ]
