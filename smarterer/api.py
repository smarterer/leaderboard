"""
Simple Python wrapper for the Smarterer API.
"""

import requests
import json

API_BASE_URL = "https://smarterer.com/api/"
OAUTH_BASE_URL = "https://smarterer.com/oauth"


class SmartererApiHttpException(Exception):
    pass


class Smarterer(object):

    def __init__(self, access_token=None, client_id=None, client_secret=None, verify=True):
        '''
        Create smarterer object, with access_token, client_id and whether or
        not to verify the SSL certificate.
        '''
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.verify = verify

    def _fetch(self, url):
        """
        Fetch a URL. If anything other than a 200 OK response is received,
        raise an exception. Otherwise, return the content.
        """
        # create a dictionary of parameters that are available
        params = dict(filter(lambda x: x[1] is not None,
                                    (('client_id', self.client_id),
                                     ('access_token', self.access_token))
                                    ))

        # use the requests http library to get a URL
        response = requests.get(url, params=params, verify=self.verify)

        # check if the response is valid or not
        if response.status_code != 200:
            raise SmartererApiHttpException("Not-OK response. HTTP Status=%s, "
                                            "Response=%r" % (
                                                response.status_code,
                                                response.content))
        # otherwise, return the content
        return response.content

    def _req(self, resource_name):
        """
        Make an API request over HTTP and attempt to parse the JSON result.

        :param resource_name: Path to the API resource under the main
                              API_BASE_URL.
        """
        # build the service URL
        url = API_BASE_URL + resource_name
        return json.loads(self._fetch(url))

    def badges(self, username=None):
        resource = "badges"
        if username:
            resource = "/".join((resource, username))
        return self._req(resource)

    def authorize_url(self, callback=''):
        return '{oauth}/authorize?client_id={client_id}'.format(
                                                    oauth=OAUTH_BASE_URL,
                                                    client_id=self.client_id)

    def get_access_token(self, code=None):
        token_url = '{oauth}/access_token'.format(oauth=OAUTH_BASE_URL)
        resp = requests.get(token_url, params=dict(client_id=self.client_id,
                                       client_secret=self.client_secret,
                                       code=code,
                                       grant_type='authorization_code'),
                                       verify=self.verify)
        if resp.status_code != 200:
            raise SmartererApiHttpException("Not-OK response. HTTP Status=%s, "
                                            "Response=%r" % (
                                                resp.status_code,
                                                resp.content))
        return str(json.loads(resp.content)['access_token'])


