# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2021 Virtual Cable S.L.U.
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
import logging
import typing

from django.urls import reverse
from django.http import HttpResponseRedirect
from uds.core.util.config import GlobalConfig

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


class RedirectMiddleware:
    """
    This class is responsible of redirection, if checked, requests to HTTPS.

    Some paths will not be redirected, to avoid problems, but they are advised to use SSL (this is for backwards compat)
    """

    NO_REDIRECT: typing.ClassVar[typing.List[str]] = [
        'rest',
        'pam',
        'guacamole',
        # For new paths
        # 'uds/rest',  # REST must be HTTPS if redirect is enabled
        'uds/pam',
        'uds/guacamole',
        # Test client can be http
        'uds/rest/client/test',
        # And also the tunnel
        'uds/rest/tunnel',
    ]

    get_response: typing.Any  # typing.Callable[['HttpRequest'], 'HttpResponse']

    def __init__(
        self, get_response: typing.Callable[['HttpRequest'], 'HttpResponse']
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: 'HttpRequest') -> 'HttpResponse':
        full_path = request.get_full_path()
        redirect = True
        for nr in RedirectMiddleware.NO_REDIRECT:
            if full_path.startswith('/' + nr):
                redirect = False
                break

        if (
            redirect
            and not request.is_secure()
            and GlobalConfig.REDIRECT_TO_HTTPS.getBool()
        ):
            if request.method == 'POST':
                # url = request.build_absolute_uri(GlobalConfig.LOGIN_URL.get())
                url = reverse('page.login')
            else:
                url = request.build_absolute_uri(full_path)
            url = url.replace('http://', 'https://')

            return HttpResponseRedirect(url)
        return self.get_response(request)

    @staticmethod
    def registerException(path: str) -> None:
        RedirectMiddleware.NO_REDIRECT.append(path)
