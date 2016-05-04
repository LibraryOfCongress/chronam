import json
import urllib
import logging
import urlparse

import requests

logger = logging.getLogger(__name__)

class CTS(object):

    def __init__(self, username, password, base_url, verify_ssl=True):
        self.auth = (username, password)
        self.base_url = base_url
        if not self.base_url.endswith("/"):
            self.base_url += "/"
        self.verify_ssl = verify_ssl

    def get_project(self, project_id):
        """get a Project using its project_id e.g. "ndnp"
        """
        url = "project/%s" % project_id
        instance_data = self._request(url)
        return Project(instance_data, self)

    def next_service_request(self, queue_name, service_type):
        """get the next ServiceRequest for a given queue and service type
        """
        q = {'queue': queue_name, 'serviceType': service_type}
        d = self._request("service_request/serve_next", "put", data=q)
        if not d:
            return None
        return ServiceRequest(d, self)

    def get_service_requests(self, queue_name, service_type):
        """get a list of ServiceRequests for a given queue and service type
        """
        q = {'queue': queue_name, 'serviceType': service_type}
        d = self._request("service_requests", params=q)
        for request in d['results']:
            sr = ServiceRequest(request, self)
            sr.reload()
            yield sr

    def get_service_request(self, key):
        """get a ServiceRequest using its key
        """
        d = self._request("service_request/%s" % key)
        return ServiceRequest(d, self)

    def get_bag_instance(self, key):
        """get a BagInstance using its key
        """
        url = "inventory/bag_instance/%s" % key
        instance_data = self._request(url)
        return BagInstance(instance_data, self)

    def _request(self, url, method='get', params={}, data=None):
        headers = {"accept": "application/json"}
        url = urlparse.urljoin(self.base_url, url)
        if data != None:
            data = urllib.urlencode(data)
            headers["content-type"] = "application/x-www-form-urlencoded"

        r = requests.request(method, url,
                             params=params,
                             data=data,
                             headers=headers,
                             auth=self.auth,
                             verify=self.verify_ssl)

        if r.status_code == 200:
            return json.loads(r.content)
        elif r.status_code == 301 or r.status_code == 302:
            return self._request(r.headers['location'], method, params, data)
        elif r.status_code == 204:
            return None
        else:
            logger.error("%s %s with %s resulted in %s", method, url, params,
                    r.status_code)
            return None


class Resource(object):

    def __init__(self, json_data, cts):
        self.data = json_data
        self.cts = cts

    def reload(self):
        url = self.link('self')
        self.data = self.cts._request(url)

    @property
    def url(self):
        return urlparse.urljoin(self.cts.base_url, self.link('self'))

    def link(self, rel):
        "returns the first link data with a given rel value"
        for link in self.data.get('links', []):
            if link.get('rel', None) == rel:
                return link['href']
        return None


class ServiceRequest(Resource):

    def requeue(self):
        return self.cts._request(self.url, 'put', data={"action": "requeue"})

    def complete(self):
        q = {"action": "respond", "result": "COMPLETED"}
        return self.cts._request(self.url, 'put', data=q)

    def fail(self, message):
        q = {"action": "respond", "result": "FAILURE", "errorMessage": message}
        return self.cts._request(self.url, 'put', data=q)


class BagInstance(Resource):
    pass


class Bag(Resource):

    def get_bag_instances(self):
        instances = self.cts._request(self.link('bag_instances'))
        for instance_data in instances:
            yield BagInstance(instance_data, self.cts)


class Project(Resource):

    def get_bags(self):
        bags = self.cts._request(self.link('bags'))
        for bag_data in bags:
            yield Bag(bag_data, self.cts)
