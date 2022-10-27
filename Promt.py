import unittest

import Prompt
from Prompt import *


class MyTestCase(unittest.TestCase):
    p = Prompt()

    def test_target_debris_on_wrong_argument_number(self):
        self.assertFalse(self.p.do_target_debris("1 2"))

    def test_target_debris_on_non_existent_debris(self):
        self.assertFalse(self.p.do_target_debris("1 2"))

    def test_target_satellites_on_non_existing_satllites(self):
        self.assertFalse(self.p.do_target_satellites("plop"))

    def test_add_catalog_on_wrong_argument_number(self):
        self.assertFalse(self.p.do_target_satellites(""))

    def test_add_catalog_on_wrong_argument_type(self):
        self.assertFalse(self.p.do_target_satellites("plop https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle"))

    def test_add_catalog_on_already_existing_url(self):
        self.assertFalse(self.p.do_target_satellites("deb https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle"))



if __name__ == '__main__':
    unittest.main()
