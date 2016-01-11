#!/bin/bash

cd /opt/openoni/
source ENV/bin/activate

django-admin.py load_essays --settings openoni.settings 2>/dev/null
