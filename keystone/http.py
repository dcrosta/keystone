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
    code = 301
    message = 'Moved Permanently'

class Found(ThreeOhX):
    code = 302
    message = 'Found'

class SeeOther(ThreeOhX):
    code = 303
    message = 'See Other'

class NotModified(HTTPException):
    code = 304
    description = None

class UseProxy(ThreeOhX):
    code = 305
    description = 'Use Proxy'

# 306 is unused

class TemporaryRedirect(ThreeOhX):
    code = 307
    description = 'Temporary Redirect'

