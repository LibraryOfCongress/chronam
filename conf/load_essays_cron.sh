#!/bin/bash

cd /opt/chronam/
source ENV/bin/activate

django-admin.py load_essays --settings chronam.settings 2>/dev/null
