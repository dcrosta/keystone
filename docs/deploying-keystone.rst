Deploying Keystone
==================

Keystone is a WSGI framework, and as such can run within any WSGI-compliant
container, such as Apache with mod_wsgi, Nginx with uWSGI, Gunicorn, etc.
The :class:`~keystone.main.Keystone` class implements a WSGI application in
its :meth:`~keystone.main.Keystone.__call__` method.

You can automatically generate a ``wsgi.py`` file for use in such scenarios
using the ``keystone`` script::

    $ keystone --configure wsgi
    $ cat wsgi.py
    from os.path import abspath, dirname
    here = abspath(dirname(__file__))
    from keystone.main import Keystone
    application = Keystone(here)

The ``wsgi.py`` file is intended as a working starting point, but may
require customization to work within your deployment environment.


Deploying Keystone to PaaS Providers
------------------------------------

The ``keystone`` script has options to automatically generate boilerplate
for several Platform-as-a-Service ("PaaS") providers. As of Keystone 0.2,
supported providers are `Heroku <http://www.heroku.com/>`_, `DotCloud
<https://www.dotcloud.com/>`_, and `ep.io <https://www.ep.io/>`_. In the
future, additional providers may be supported.

To create files necessary for deployment on a PaaS provider, invoke the
``keystone`` script with ``--configure`` and the name of one of the
supported providers. For example, for Heroku::

    $ keystone --configure heroku
    $ cat wsgi.py 
    from keystone.main import Keystone
    application = Keystone("/app")
    $ cat requirements.txt 
    keystone == 0.2.0
    gunicorn >= 0.13.4
    $ cat Procfile 
    web: gunicorn wsgi:application -w 4 -b 0.0.0.0:$PORT

The exact files created by ``--configure`` and their contents will vary
from one PaaS provider to another. The generated files are meant as a
starting point, and may require customization.

The version of Keystone required in ``requirements.txt`` will be the version
you are running when you invoke ``--configure``, and not necessarily the
latest version available.

.. note::

   When deploying to Heroku, be sure to use the "Cedar" stack.
