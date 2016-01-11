#!/usr/bin/env python

"""
this is a script that dumps an issue from batch batch_dlc_jamaica_ver01 
including all its page and ocr models as a json fixture for testing purposes
"""

import json
from django.core import serializers
from openoni.core.models import Batch, OCR, Reel, LanguageText

b = Batch.objects.get(name="batch_dlc_jamaica_ver01")
i = b.issues.all()[0]

# create the django json serializer
j = serializers.get_serializer("json")()

# collect a list of json objects while jumping through hoops to pass
# the serializer a queryset, which it expects instead of instance data
data = []
data.extend(json.loads(j.serialize(Batch.objects.filter(name="batch_dlc_jamaica_ver01"))))
data.extend(json.loads(j.serialize(Reel.objects.filter(pages__issue=i).distinct())))
data.extend(json.loads(j.serialize(b.issues.filter(id=i.id))))
data.extend(json.loads(j.serialize(i.pages.all())))
data.extend(json.loads(j.serialize(OCR.objects.filter(page__issue=i))))
data.extend(json.loads(j.serialize(LanguageText.objects.filter(ocr__page__issue=i))))

# write out the collected objects
open("jamaica_sample.json", "w").write(json.dumps(data, indent=2))
