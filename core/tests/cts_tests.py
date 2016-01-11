from django.test import TestCase
from django.conf import settings

from openoni.core.cts import CTS

class CTSTest(TestCase):

    def test_settings(self):
        self.assertTrue(hasattr(settings, 'IS_PRODUCTION'))
        self.assertTrue(settings.CTS_USERNAME)
        self.assertTrue(settings.CTS_PASSWORD)
        self.assertTrue(settings.CTS_URL)
        self.assertTrue(settings.CTS_PROJECT_ID)
        self.assertTrue(settings.CTS_QUEUE)
        self.assertTrue(settings.CTS_SERVICE_TYPE)

    def test_project(self):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        project = cts.get_project(settings.CTS_PROJECT_ID)

    def test_bags(self):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        project = cts.get_project(settings.CTS_PROJECT_ID)
        bags = list(project.get_bags())
        self.assertTrue(len(bags) > 0)
        bag = bags[0]
        self.assertTrue(bag.data['id'])

    def test_bag_instances(self):
        cts = CTS(settings.CTS_USERNAME, settings.CTS_PASSWORD, settings.CTS_URL)
        project = cts.get_project(settings.CTS_PROJECT_ID)
        bag = list(project.get_bags())[0]

        instances = list(bag.get_bag_instances())
        self.assertTrue(len(instances) > 0)
