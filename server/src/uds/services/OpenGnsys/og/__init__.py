# -*- coding: utf-8 -*-

#
# Copyright (c) 2017 Virtual Cable S.L.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
.. moduleauthor:: Adolfo Gómez, dkmaster at dkmon dot com
'''
from __future__ import unicode_literals

from . import urls
from . import fake

import sys
import imp
import re

import logging
import six

import requests
import  json

# API URL 1: https://www.informatica.us.es/~ramon/opengnsys/?url=opengnsys-api.yml
# API URL 2: http://opengnsys.es/wiki/ApiRest

__updated__ = '2017-05-17'

logger = logging.getLogger(__name__)

# URLS

# Fake part
FAKE = True


# Decorator
def ensureConnected(fnc):
    def inner(*args, **kwargs):
        args[0].connect()
        return fnc(*args, **kwargs)
    return inner

# Result checker
def ensureResponseIsValid(response, errMsg=None):
    if response.ok is False:
        if errMsg is None:
            errMsg = 'Invalid response'

        # If response.code is not 200, the response is an error and should have a message
        # FIX THIS
        if response.code != 200:
            try:
                err = response.json()['message']  # Extract any key, in case of error is expected to have only one top key so this will work
            except Exception:
                err = response.content
            errMsg = '{}: {}, ({})'.format(errMsg, err, response.code)
            logger.error('{}: {}'.format(errMsg, response.content))
            raise Exception(errMsg)

    return json.loads(response.content)

class OpenGnsysClient(object):
    def __init__(self, username, password, endpoint, verifyCert=False):
        self.username = username
        self.password = password
        self.endpoint = endpoint
        self.auth = None
        self.verifyCert = verifyCert
        self.cachedVersion = None

    @property
    def headers(self):
        headers = {'content-type': 'application/json'}
        if self.auth is not None:
            headers['Authorization'] = self.auth

        return headers

    def _ogUrl(self, path):
        return self.endpoint + '/' + path

    def _post(self, path, data, errMsg=None):
        if not FAKE:
            return ensureResponseIsValid(
                requests.post(self._ogUrl(path), data=json.dumps(data), headers=self.headers, verify=self.verifyCert),
                errMsg=errMsg
            )
        # FAKE Connection :)
        return fake.post(path, data)

    def _get(self, path, errMsg=None):
        if not FAKE:
            return ensureResponseIsValid(
                requests.get(self._ogUrl(path), headers=self.headers, verify=self.verifyCert),
                errMsg=errMsg
            )
        # FAKE Connection :)
        return fake.get(path)


    def _delete(self, path, errMsg=None):
        return ensureResponseIsValid(
            requests.delete(self._ogUrl(path), headers=self.headers, verify=self.verifyCert),
            errMsg=errMsg
        )

    def connect(self):
        if self.auth is not None:
            return

        auth = self._post(urls.LOGIN,
            data={
                'username': self.username,
                'password': self.password
            },
            errMsg='Loggin in'
        )

        self.auth = auth['apikey']


    @property
    def version(self):
        logger.debug('Getting version')
        if self.cachedVersion is None:
            # Retrieve Version & keep it
            info = self._get(urls.INFO, errMsg="Retrieving info")
            self.cachedVersion = info['version']

        return self.cachedVersion

    @ensureConnected
    def getOus(self):
        # Returns an array of elements with:
        # 'id': OpenGnsys Id
        # 'name': OU name
        # OpenGnsys already returns it in this format :)
        return self._get(urls.OUS, errMsg='Getting list of ous')

    @ensureConnected
    def getLabs(self, ou):
        # Returns a list of available labs on an ou
        # /ous/{ouid}/labs
        # Take into accout that we must exclude the ones with "inremotepc" set to false.
        return [{'id': l['id'], 'name': l['name']} for l in self._get(urls.LABS.format(ou=ou)) if l.get('inremotepc', False) is True]


    @ensureConnected
    def getImages(self, ou):
        # Returns a list of available labs on an ou
        # /ous/{ouid}/images
        # Take into accout that we must exclude the ones with "inremotepc" set to false.
        return [{'id': l['id'], 'name': l['name']} for l in self._get(urls.IMAGES.format(ou=ou)) if l.get('inremotepc', False) is True]

    @ensureConnected
    def reserve(self, ou, image):
        # This method is inteded to "get" a machine from OpenGnsys
        # The method used is POST
        # invokes /ous/{ouid}}/images/{imageid}/reserve
        # also remember to store "labid"
        # Labid can be "0" that means "all laboratories"
        return self._get(urls.RESERVE.format(ou=ou, image=image))

    @ensureConnected
    def unreserve(self, machine):
        # This method releases the previous reservation
        # Invoked every time we need to release a reservation (i mean, if a reservation is done, this will be called with the obtained id from that reservation)
        pass

    @ensureConnected
    def status(self, machine):
        # This method gets the status of the machine
        # /ous/{uoid}/labs/{labid}/clients/{clientid}/status
        # possible status are ("off", "oglive", "busy", "linux", "windows", "macos" o "unknown").
        # Look at api at informatica.us..
        pass