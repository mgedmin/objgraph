#!/usr/bin/python
import unittest
import doctest
import tempfile
import os
import shutil
import glob


def setUp(test):
    test.tmpdir = tempfile.mkdtemp(prefix='test-objgraph-')
    test.prevdir = os.getcwd()
    os.chdir(test.tmpdir)


def tearDown(test):
    os.chdir(test.prevdir)
    shutil.rmtree(test.tmpdir)


def test_suite():
    return doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                                optionflags=doctest.ELLIPSIS,
                                *glob.glob('*.txt'))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
