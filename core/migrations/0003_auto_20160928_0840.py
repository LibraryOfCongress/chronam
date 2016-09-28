# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160405_0900'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='category',
        ),
        migrations.RemoveField(
            model_name='topicpages',
            name='page',
        ),
        migrations.RemoveField(
            model_name='topicpages',
            name='topic',
        ),
        migrations.DeleteModel(
            name='Topic',
        ),
        migrations.DeleteModel(
            name='TopicCategory',
        ),
        migrations.DeleteModel(
            name='TopicPages',
        ),
    ]
