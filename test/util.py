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
import warnings

class MtimeChanger(object):
    def __init__(self):
        self.inc = 1

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

class WarningCatcher(object):
    """
    Context manager like warnings.catch_warnings, but with a simpler API
    for testing (and for Python 2.5 compatibility).
    """

    def __init__(self, *warnings_to_catch):
        self.warnings_to_catch = warnings_to_catch
        self.log = []
        self.showwarning = None

    def __enter__(self):
        self.showwarning = warnings.showwarning
        def showwarning(*args, **kwargs):
            # args[1] is the class of the warning
            self.log.append(args[1])
        warnings.showwarning = showwarning
        return self

    def __exit__(self, *exc_info):
        warnings.showwarning = self.showwarning

    def has_warning(self, warning_cls, count=1):
        count_of_type = sum(1 for w in self.log if w == warning_cls)
        return count_of_type == count

