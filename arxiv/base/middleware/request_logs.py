"""
Provides middleware to support classic CUL/Apache log format.

For accurate request metrics, apply this middleware before any others.
"""

from typing import Type, Callable, List
from datetime import datetime
from pytz import timezone
from .base import BaseMiddleware

EASTERN = timezone('US/Eastern')

# The uwsgi package is injected into the Python environment by uWSGI, and is
# not available otherwise. If we can't import the package, there's not much
# else to do.
try:
    import uwsgi

    class ClassicLogsMiddleware(BaseMiddleware):
        """Add params to uwsgi to support classic CUL/Apache log format."""

        def __call__(self, environ, start_response):
            """
            Handle a WSGI request.

            Parameters
            ----------
            environ : dict
                WSGI request environment.
            start_response : function
                Function used to begin the HTTP response. See
                https://www.python.org/dev/peps/pep-0333/#the-start-response-callable

            Returns
            -------
            iterable
                Iterable that generates the HTTP response. See
                https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
            """
            start = datetime.now()

            # Express the time that the request was received in the classic
            # format.
            rtime = datetime.now(tz=EASTERN).strftime('%d/%m/%Y:%H:%M:%S %z')
            uwsgi.set_logvar('rtime', rtime)
            response = self.app(environ, start_response)
            # This is a close approximation of "TTFB" (time from the
            # request received to the start of the response).
            ttfb = (datetime.now() - start).microseconds
            uwsgi.set_logvar('ttfb', str(ttfb).encode('ascii'))
            return response

except ImportError as e:     # Not running in uWSGI.
    ClassicLogsMiddleware = BaseMiddleware      # BaseMiddleware does nothing.
