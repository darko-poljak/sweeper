#!/usr/bin/env python
# Author: Darko Poljak <darko.poljak@gmail.com>
# License: GPLv3

import unittest
from sweeper import file_dups, iter_file_dups
import os

mydir = os.path.dirname(os.path.realpath(__file__))


class TestSweeper(unittest.TestCase):
    def test_file_dups_dups(self):
        dups = file_dups([os.path.join(mydir, 'testfiles_dups')])
        dups_exist = False
        for h, flist in dups.items():
            if len(flist) > 1:
                dups_exist = True
        self.assertTrue(dups_exist)

    def test_file_dups_nodups(self):
        dups = file_dups([os.path.join(mydir, 'testfiles_nodups')])
        for h, flist in dups.items():
            self.assertTrue(len(flist) == 1)

    def test_iter_fule_dups_rethash(self):
        for item in iter_file_dups([os.path.join(mydir, 'testfiles_dups')],
                                   rethash=True):
            self.assertTrue(type(item).__name__ == 'tuple')

    def test_iter_fule_dups_norethash(self):
        for item in iter_file_dups([os.path.join(mydir, 'testfiles_dups')]):
            self.assertTrue(type(item).__name__ == 'list')


if __name__ == '__main__':
    unittest.main()
