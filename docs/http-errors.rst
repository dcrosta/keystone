``http`` Module
===============

These exceptions may be raised from within view code to send non-200
responses back to the user agent. Within views, this module is available as
the ``http`` :doc:`View Variable <view-variables>`.

Redirection 3xx
---------------

.. autoclass:: keystone.http.MovedPermanently
.. autoclass:: keystone.http.Found
.. autoclass:: keystone.http.SeeOther
.. autoclass:: keystone.http.NotModified
.. autoclass:: keystone.http.UseProxy
.. autoclass:: keystone.http.TemporaryRedirect

Client Error 4xx
----------------

.. autoclass:: keystone.http.BadRequest
.. autoclass:: keystone.http.Unauthorized
.. autoclass:: keystone.http.Forbidden
.. autoclass:: keystone.http.NotFound
.. autoclass:: keystone.http.MethodNotAllowed
.. autoclass:: keystone.http.NotAcceptable
.. autoclass:: keystone.http.RequestTimeout
.. autoclass:: keystone.http.Conflict
.. autoclass:: keystone.http.Gone
.. autoclass:: keystone.http.LengthRequired
.. autoclass:: keystone.http.PreconditionFailed
.. autoclass:: keystone.http.RequestEntityTooLarge
.. autoclass:: keystone.http.RequestURITooLarge
.. autoclass:: keystone.http.UnsupportedMediaType
.. autoclass:: keystone.http.RequestedRangeNotSatisfiable
.. autoclass:: keystone.http.ExpectationFailed
.. autoclass:: keystone.http.ImATeapot

Server Error 5xx
----------------

.. autoclass:: keystone.http.InternalServerError
.. autoclass:: keystone.http.NotImplemented
.. autoclass:: keystone.http.BadGateway
.. autoclass:: keystone.http.ServiceUnavailable
