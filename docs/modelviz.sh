#!/bin/sh

# a little script for generating a visualization of the models
# using django-graphviz http://code.djangoproject.com/wiki/DjangoGraphviz
# and dot from graphviz 

export PYTHONPATH=/home/ed/Projects/chronam/trunk
export DJANGO_SETTINGS_MODULE=chronam.settings 

modelviz.py web > schema.dot
dot schema.dot -T png -o schema.png
