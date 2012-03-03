View Variables
==============

Keystone makes several objects and functions available within Views as
global variables --- that is, they need not be declared, they are simply
available to your Python and template code.

``request``
-----------

.. py:class:: Request

   A Werkzeug :class:`~werkzeug.wrappers.Request` instance, available in
   views as ``request``. The `Werkzeug documentation
   <http://werkzeug.pocoo.org/docs/wrappers/#werkzeug.wrappers.Request>`_
   contains a more comlete list of available attributes.

   .. py:attribute:: method

      HTTP method name

   .. py:attribute:: cookies

      HTTP cookies, as an
      :class:`~werkzeug.datastructures.ImmutableTypeConversionDict`

   .. py:attribute:: args

      HTTP GET parameters (query string), as an
      :class:`~werkzeug.datastructures.ImmutableMultiDict`

   .. py:attribute:: form

      HTTP POST parameters, as an
      :class:`~werkzeug.datastructures.ImmutableMultiDict`

   .. py:attribute:: values

      Union of ``args`` and ``form``.


``headers``
-----------

The actual :class:`~werkzeug.wrappers.Response` instance is not constructed
until after a view's Python code executes, but aspects of it can be
controlled through several :doc:`view-variables`:

.. py:class:: Headers

   A Werkzeug :class:`~werkzeug.datastructures.Headers` instance, available
   in views as ``headers``. The `Werkzeug documentation
   <http://werkzeug.pocoo.org/docs/datastructures/#werkzeug.datastructures.Headers>`_
   contains a more comlete list of available attributes and methods.

   .. py:method:: add(key, value, **kw)

      Add the ``value`` to the header named ``key``. Keyword arguments can
      be used to specify additional parameters for the header:

      .. code-block:: python

         headers.add('Content-Type', 'text/plain')
         headers.add('Content-Disposition', 'attachment', filename='blah.txt')

   .. py:method:: set(key, value, **kw)

      Similar to :meth:`add`, but overwrites any previously set values for
      headers which accept multiple values.

   .. py:method:: get(key, default=None, type=None)

      Get the value of the header named ``key``, or the default value if no
      such header is set. Optionally convert using ``type`` (a callable of
      one argument).

   .. py:method:: has_key(key)

      Return ``True`` if the header named ``key`` exists, ``False``
      otherwise.


``return_response``
-------------------

.. py:function:: return_response(body)

   Bypass template rendering and immediately return the given `body`. `body`
   may be any iterable object or string.


``http``
--------

The ``http`` view variable is a module which contains subclasses of
:class:`~werkzeug.exceptions.HTTPException` for returning non-200-status
HTTP responses. Full documentation on the exceptions is available at
:doc:`http-errors`.


``set_cookie``
--------------

.. py:method:: set_cookie(key, value='', max_age=None, expires=None, path='/', domain=None, seucre=None, httponly=None)

   Set a cookie in the HTTP response. Cookies set using :meth:`set_cookie`
   will not be available in :class:`headers <Headers>` until the subsequent
   request from the user.

   See :meth:`~werkzeug.wrappers.BaseResponse.set_cookie` for an explanation
   of the arguments.


``delete_cookie``
-----------------

.. py:method:: delete_cookie(key, path='/', domain=None)

   Delete a cookie in the HTTP response. Cookies deleted using
   :meth:`delete_cookie` will still appear in :class:`headers <Headers>`
   until the subsequent request from the user.

   See :meth:`~werkzeug.wrappers.BaseResponse.delete_cookie` for an
   explanation of the arguments.


``app_dir``
-----------

.. py:attribute:: app_dir

   The full, absolute path to the root of the Keystone application
   directory.

