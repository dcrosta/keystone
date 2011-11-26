# Copyright (c) 2011, Daniel Crosta
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


__all__ = (
    # from Werkzeug
    'BadRequest', 'Unauthorized', 'Forbidden', 'NotFound', 'MethodNotAllowed',
    'NotAcceptable', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired',
    'PreconditionFailed', 'RequestEntityTooLarge', 'RequestURITooLarge',
    'UnsupportedMediaType', 'RequestedRangeNotSatisfiable', 'ExpectationFailed',
    'ImATeapot', 'InternalServerError', 'NotImplemented', 'BadGateway',
    'ServiceUnavailable',

    # from Keystone
    'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy',
    'TemporaryRedirect')

from werkzeug.exceptions import *
from werkzeug.datastructures import Headers
from werkzeug.utils import redirect

class ThreeOhX(HTTPException):
    def __init__(self, location):
        self.location = location

    def get_headers(self, environ):
        return Headers([('Location', self.location), ('Content-Type', 'text/html')])

    def get_description(self, environ):
        return '<p>%s: <a href="%s">%s</a></p>' % (self.message, self.location, self.location)

class MovedPermanently(ThreeOhX):
    """`301 Moved Permanently`

    Raise if the resource has moved, and the user agent should always
    redirect the user to the new location.
    """
    code = 301
    message = 'Moved Permanently'

class Found(ThreeOhX):
    """`302 Found`

    Raise if the resource has moved, but the user agent should request
    this request URI again in the future.
    """
    code = 302
    message = 'Found'

class SeeOther(ThreeOhX):
    """`303 See Other`

    Raise if the response to the request can be found at another location,
    usually sent after successfully processing a ``POST`` request.
    """
    code = 303
    message = 'See Other'

class NotModified(HTTPException):
    """`304 Not Modified`

    Sent in response to a conditional GET request when the user agent's
    cached copy is already up to date.
    """
    code = 304
    description = None

class UseProxy(ThreeOhX):
    """`305 Use Proxy`

    Indicate that the user-agent should retry the request using the proxy as
    defined in the ``Location`` header.
    """
    code = 305
    description = 'Use Proxy'

# 306 is unused

class TemporaryRedirect(ThreeOhX):
    """`307 Temporary Redirect`

    Raise if the resource may have moved, and to indicate that  the user
    agent should request this request URI again in the future.
    """
    code = 307
    description = 'Temporary Redirect'

