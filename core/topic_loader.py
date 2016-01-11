import urllib
import logging
import re

from lxml import html

from django.conf import settings
from django.http import HttpResponse, Http404
from openoni.core import models
from openoni.core.utils import utils

_logger = logging.getLogger(__name__)

def load_topic_and_categories():
    """
    This function takes a list topics/topic_categories and creates 
    instances of models.Topic and models.TopicCategory exist with the 
    given name, if one such instance doesn't already exist.

    #TODO: some parts of the code has ugly hacks to scrub text out of 
           html. This will fail if structure of target html changes. 
           Revisit! 
    """
    page = html.fromstring(urllib.urlopen('%s%s' % (settings.TOPICS_ROOT_URL,
                                                settings.TOPICS_SUBJECT_URL)).read())
    total_topics = total_categories = new_topics = new_categories = filed_topics = 0
    topics = list(page.iterdescendants('li'))
    category = None
    for topic_or_category in topics:
        if topic_or_category.text:
            #its a category, check if exists/ create one
            total_categories += 1
            category_name = topic_or_category.text.rstrip(':')
            category, is_new = models.TopicCategory.objects.get_or_create(name=category_name)
            if is_new:
                new_categories += 1
            _logger.info('Syncing category %s' % category_name)
        else:
            topic, start, end = prepare_topic_for_db_insert(
                                          topic_or_category.text_content())
            total_topics += 1
            topic, is_new = models.Topic.objects.get_or_create(name=topic, topic_start_year=start, 
                                       topic_end_year=end, category=category)
            if is_new:
                new_topics += 1
            _logger.info('Syncing topic %s' % topic.name)
            topic_url = list(topic_or_category.iterlinks())[0][2]
            if not topic_url.startswith('http://'):
                topic_url = '%s/%s' % (settings.TOPICS_ROOT_URL, topic_url)
            topic_page = html.fromstring(urllib.urlopen(topic_url).read())
            topic.intro_text = list(topic_page.iterdescendants('p'))[0].text_content().encode('utf-8')
            topic.important_dates = list(topic_page.iterdescendants('ul'))[0].text_content().encode('utf-8')
            topic.suggested_search_terms = list(topic_page.iterdescendants('ul'))[1].text_content().encode('utf-8')
            topic.save()
            pages = list(topic_page.iterdescendants('ul'))[-1]
            for page in pages:
                page_url = list(page.iterlinks())[0][2]
                params = page_url.split('/')
                openoni_page = None
                try:
                    params = params[params.index('lccn')+1:]
                    openoni_page = utils.get_page(params[0], params[1], 
                                                  params[2][-1:], params[3][-1:])
                    _logger.info('Syncing topic with page :- lccn:%s.' % params[0])

                except ValueError: pass
                except Http404: pass

                models.TopicPages.objects.get_or_create(page=openoni_page, topic=topic,
                                          query_params=params[-1], url=page_url,
                                          title=list(page.iterlinks())[0][0].text,
                                          description=page.text_content().lstrip(list(
                                             page.iterchildren())[0].text).lstrip('"').lstrip(','))

def prepare_topic_for_db_insert(topic_text):
    """
    this function takes a string like Christmas Truce (1914-1915) and
    returns a tuple (Christmas Truce, 1914, 1915)
    """
    topic_name = topic_text[:topic_text.index('(')].rstrip().lstrip()
    topic_start_year = topic_end_year = 9999
    range_op_index = topic_text.rfind('-')
    if not range_op_index == -1 and topic_text[range_op_index+1:range_op_index+4].isdigit():
        topic_start_year = topic_text[topic_text.rindex('(')+1:topic_text.rindex('-')]
        topic_end_year = topic_text[topic_text.rindex('-')+1:topic_text.rindex(')')]
    else:
        topic_start_year = topic_end_year = topic_text[topic_text.rindex('(')+1:topic_text.rindex(')')]
    if not topic_start_year.isdigit() or topic_end_year: 
        # some cases where there is a year in the text but messed up format
        match = re.search('\d{4}', topic_text)
        if match:
            topic_start_year = topic_end_year = match.group()    
    return (topic_name, topic_start_year, topic_end_year)    

