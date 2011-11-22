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

import argparse
import os
import os.path

def main():
    parser = argparse.ArgumentParser(description='Run a Keystone application')
    parser.add_argument('app_dir', nargs='?', default=os.getcwd(),
                        help='Path to Keystone application [current dir]')
    parser.add_argument('-p', '--port', dest='port', metavar='PORT', type=int, default=5000,
                        help='Port to listen on [5000]')
    parser.add_argument('-H', '--host', dest='host', metavar='HOST', type=str, default='0.0.0.0',
                        help='Hostname or IP address to listen on [0.0.0.0]')
    parser.add_argument('-t', '--threaded', dest='threaded', action='store_const', const=True, default=False,
                        help='Use threads for concurrency; always False if -d/--debug is set [False]')
    parser.add_argument('-d', '--debug', dest='debug', action='store_const', const=False, default=True,
                        help='Display Python tracebacks in the browser [False]')

    parser.add_argument('--configure', dest='paas', action='store', choices=['heroku', 'dotcloud'],
                        help='Set up configuration files in app_dir for PaaS services')

    args = parser.parse_args()

    if args.paas:
        return configure(args)

    return serve(args)

def serve(args):
    from keystone.main import Keystone
    import werkzeug.serving

    if args.paas == 'heroku':
        args.host = '0.0.0.0'
        args.port = int(os.environ['PORT'])
        args.app_dir = os.getcwd()

    if args.debug:
        args.threaded = False

    app = Keystone(app_dir=args.app_dir)
    return werkzeug.serving.run_simple(
        hostname=args.host,
        port=args.port,
        application=app,
        use_reloader=args.debug,
        use_debugger=args.debug,
        use_evalex=args.debug,
        threaded=args.threaded,
    )

def configure(args):
    import keystone

    def ensure_line(filename, line, mode='a'):
        filename = os.path.join(args.app_dir, filename)

        if os.path.exists(filename):
            with file(filename, 'r') as fp:
                for fpline in fp:
                    if fpline.strip('\n') == line:
                        return

        with file(filename, mode) as fp:
            fp.write(line)
            fp.write('\n')


    if args.paas in ('heroku', 'dotcloud'):
        ensure_line('requirements.txt', 'keystone == %s' % keystone.__version__)

    if args.paas == 'heroku':
        ensure_line('requirements.txt', 'gunicorn >= 0.13.4')

        ensure_line('wsgi.py', 'from keystone.main import Keystone')
        ensure_line('wsgi.py', 'application = Keystone("/app")')

        ensure_line('Procfile', 'web: gunicorn wsgi:application -w 4 -b 0.0.0.0:$PORT')

    if args.paas == 'dotcloud':
        ensure_line('dotcloud.yml', 'www:')
        ensure_line('dotcloud.yml', '  type: python')
        ensure_line('dotcloud.yml', '  approot: .')

        ensure_line('wsgi.py', 'from keystone.main import Keystone')
        ensure_line('wsgi.py', 'application = Keystone("/home/dotcloud/current")')

