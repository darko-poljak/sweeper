#!/usr/bin/env python
# Author: Darko Poljak <darko.poljak@gmail.com>
# License: GPLv3

import unittest
from sweeper import file_dups
import os

mydir = os.path.dirname(os.path.realpath(__file__))


class TestSweeper(unittest.TestCase):
    def test_file_dups_dups(self):
        dups = file_dups([os.path.join(mydir, 'testfiles_dups')], 'md5')
        dups_exist = False
        for h, flist in dups.items():
            if len(flist) > 1:
                dups_exist = True
        self.assertTrue(dups_exist)

    def test_file_dups_nodups(self):
        dups = file_dups([os.path.join(mydir, 'testfiles_nodups')], 'md5')
        for h, flist in dups.items():
            self.assertTrue(len(flist) == 1)


if __name__ == '__main__':
    unittest.main()
