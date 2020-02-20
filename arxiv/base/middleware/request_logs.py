"""
Provides middleware to support classic CUL/Apache log format.

For accurate request metrics, apply this middleware before any others.

You should use the following log format when running uWSGI with this
middleware installed:

.. code-block::

   %(addr) %(addr) - %(user_id)|%(session_id) [%(rtime)] [%(uagent)] "%(method) %(uri) %(proto)" %(status) %(size) %(micros) %(ttfb) %(requestid)

"""

from typing import Type, Callable, List, Iterable, Tuple
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

        def before(self, environ: dict, start_response: Callable) \
                -> Tuple[dict, Callable]:
            """
            Inject request time in CUL classic format, and start TTFB clock.

            Parameters
            ----------
            environ : dict
                WSGI request environment.
            start_response : function
                Function used to begin the HTTP response. See
                https://www.python.org/dev/peps/pep-0333/#the-start-response-callable

            Returns
            -------
            dict
                Request environment (``environ``).
            function
                ``start_response`` function.
            """
            self.start = datetime.now()

            # Add the request ID as a uWSGI log variable.
            uwsgi.set_logvar('requestid', environ.get('REQUEST_ID', ''))

            # Express the time that the request was received in the classic
            # format.
            rtime = datetime.now(tz=EASTERN).strftime('%d/%b/%Y:%H:%M:%S %z')
            uwsgi.set_logvar('rtime', rtime)
            return environ, start_response

        def after(self, response: Iterable) -> Iterable:
            """
            Set TTFB log variable.

            Parameters
            ----------
            response : iterable
                Iterable that generates the HTTP response. See
                https://www.python.org/dev/peps/pep-0333/#the-application-framework-side

            Returns
            -------
            iterable
                Iterable that generates the HTTP response. See
                https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
            """
            # This is a close approximation of "TTFB" (time from the
            # request received to the start of the response).
            ttfb = (datetime.now() - self.start).microseconds
            uwsgi.set_logvar('ttfb', str(ttfb).encode('ascii'))
            return response

except ImportError as ex:     # Not running in uWSGI.
    # BaseMiddleware does nothing.
    ClassicLogsMiddleware = BaseMiddleware  # type: ignore
