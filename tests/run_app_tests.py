import unittest

from arxiv.base.factory import create_web_app
from arxiv.base.app_tests import *

app = create_web_app()

if __name__ == '__main__':
    with app.app_context():
        unittest.main()
