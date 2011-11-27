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


Static Files
------------

Most files other than ``.ks`` files are served as static files by Keystone.
The HTTP `Content-Type` header is set according to the MIME type guessed by
:func:`mimetypes.guess_type`, and if the MIME type begins with "``text/``",
it is served with charset UTF-8.

.. note::

   Files with extension ``.py``, ``.pyc``, ``.pyo``, ``.ks``,
   and any file whose name begins with an underscore are never served as
   static files by Keystone. Requests for such files will receive a 404
   response even if such a file exists.

.. note::

   Keystone makes all static responses cacheable by setting the
   `Last-Modified` header to the file's :func:`mtime <os.stat>`, `ETag` to
   the MD5 hex digest of the `mtime`, and a `Expires` to 1 day from the
   current date and time. This behavior is not yet easily customizable, but
   will be in a future version of Keystone.


HTTP Request and Response
-------------------------

Keystone makes a ``request`` object available to your view code, with
several useful attributes and methods. Full documentation on the ``Request``
object is available in :doc:`view-variables`.

The response object is not actually available to Keystone views, but several
objects and functions to control aspects of the response are. These, too,
are fully documented in :doc:`view-variables`.


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
