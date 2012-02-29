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

import contextlib
import os
import os.path
import time

class MtimeChanger(object):
    def __init__(self):
        self.inc = 0

    @contextlib.contextmanager
    def change_times(self, fileobj):
        """
        Ensure that if the file existed before the context manager
        was invoked, that the mtime of the file after __exit__
        has increased.
        """
        global count

        filename = fileobj.name
        if os.path.isfile(filename):
            mtime = os.stat(filename).st_mtime
        else:
            mtime = 0

        yield fileobj
        fileobj.close()

        if (not mtime and os.path.isfile(filename)) or (mtime and mtime >= os.stat(filename).st_mtime):
            if callable(getattr(os, 'utime')):
                newtime = max(time.time(), mtime + self.inc)
                self.inc += 1
                os.utime(filename, (newtime, newtime))
            else:
                time.sleep(1)
                fp = open(filename, 'a')
                fp.write('')
                fp.close()

