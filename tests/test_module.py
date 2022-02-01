import unittest

import stactools.nclimgrid


class TestModule(unittest.TestCase):

    def test_version(self):
        self.assertIsNotNone(stactools.nclimgrid.__version__)
