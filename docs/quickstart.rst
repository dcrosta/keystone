Keystone Quickstart
===================

This quickstart guide is designed for those familiar with Python and web
programming concepts. If you're new to Python or web programming, you may be
interested in :doc:`tutorial`, which introduces these concepts more gently.

Install Keystone
----------------

Keystone packages are available at `PyPi
<http://pypi.python.org/pypi/Keystone>`_ and source is available at `GitHub
<https://github.com/dcrosta/keystone>`_. Keystone can be installed with
`Pip <http://www.pip-installer.org/en/latest/index.html>`_, and works well
with `virtualenv <http://pypi.python.org/pypi/virtualenv>`_.


Application Directory
---------------------

Keystone uses the hierarchy of the filesystem, specifically of your
`application directory`, for view routing. Throughout this Quickstart, we
will use ``$APP`` to refer to the root of your application directory.


Running Keystone
----------------

The ``keystone`` script runs a local web server suitable for development of
Keystone applications. By default it listens on port 5000 and assumes
``$APP`` to be the current working directory. Run ``keystone --help`` for
details on usage.


Defining Views
--------------

Views in Keystone are files with extension ``.ks``, and contain both Python
code and `Jinja <http://jinja.pocoo.org/>`_ template code, separated by four
hyphens (``----``). If a view does not have a separator, it is assumed to
contain only template code and no Python.

The URL of a Keystone view is the path, relative to ``$APP``, of the file in
question, without the ``.ks`` extension. Views named ``index.ks`` are
treated specially, in that they are accessible both by their full path
(ending in `/index`) and at the bare directory path (ending in `/`).

Here's an example view:

.. code-block:: keystone

    import random
    greeting = random.choice(['Hello', 'Goodbye'])
    name = random.choice(['World', 'Moon'])
    ----
    <!doctype html>
    <html>
        <head>
            <title>{{greeting}} from Keystone</title>
        </head>
        <body>
            <h1>{{greeting}}, {{name}}</h1>
        </body>
    </html>

If this were saved as :file:`{$APP}/index.ks`, then this view would be
available at both `http://localhost:5000/` and
`http://localhost:5000/index`.

HTTP Request
------------

Keystone makes a ``request`` object available to your view code, with
several useful attributes and methods:

.. py:class:: Request

   A Werkzeug :class:`~werkzeug.wrappers.Request` instance, available in
   views as ``request``.

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


HTTP Response
-------------

The actual :class:`~werkzeug.wrappers.Response` instance is not constructed
until after a view's Python code executes, but aspects of it can be
controlled through several :doc:`view-variables`:

.. py:class:: Headers

   A Werkzeug :class:`~werkzeug.datastructures.Headers` instance, available
   in views as ``headers``.

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


You can also set or delete cookies:

.. py:method:: set_cookie(key, value='', max_age=None, expires=None, path='/', domain=None, seucre=None, httponly=None)

   See :meth:`~werkzeug.wrappers.BaseResponse.set_cookie` in the Werkzeug
   documentation.

.. py:method:: delete_cookie(key, path='/', domain=None)

   See :meth:`~werkzeug.wrappers.BaseResponse.delete_cookie` in the Werkzeug
   documentation.


Non-200 Responses
~~~~~~~~~~~~~~~~~

A full suite of Exceptions corresponding to non-200 HTTP status codes are
available in the :doc:`http-errors`. To send a non-200 response, raise the
appropriate exception.


Parameterized Paths
-------------------

Any directory or Keystone view file whose name begins with ``%`` defines a
parameterized path, and acts like a wildcard. Any requests to URLs which
match a parameterized path have :doc:`view-variables` defined for the
matched sections of the path. Such variables are always strings.

For example, suppose you have the following application directory::

   $APP/
      + index.ks
      + account/
         + %username.ks
         + %username.ks
         + %username/
            + profile.ks

Then requests to the following paths would map as follows:

`/` or `/index`
  :file:`{$APP}/index.ks`

`/account/` or `/account/index`
  :file:`{$APP}/account/index.ks`

`/account/alice` or `/account/bob`
  :file:`{$APP}/account/%username.ks` with variable ``username`` set to
  "alice" or "bob", respectively

`/account/alice/profile` or `/account/bob/profile`
  :file:`{$APP}/account/%username/profile.ks` with variable ``username`` set to
  "alice" or "bob", respectively


Application Initialization
--------------------------

If a file :file:`{$APP}/startup.py` exists, it will be imported as a normal
Python module when Keystone starts up. Use this hook to define shared
resources (like database connections), perform application initialization,
or tweak Keystone's behavior (like registering custom template filters).
