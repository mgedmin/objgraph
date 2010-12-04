#!/usr/bin/python
import unittest
import doctest
import tempfile
import os
import shutil


def setUp(test):
    test.tmpdir = tempfile.mkdtemp(prefix='test-objgraph-')
    test.prevdir = os.getcwd()
    os.chdir(test.tmpdir)


def tearDown(test):
    os.chdir(test.prevdir)
    shutil.rmtree(test.tmpdir)


def test_suite():
    return doctest.DocFileSuite('README.txt', 'examples.txt',
                                'generator-sample.txt',
                                setUp=setUp, tearDown=tearDown,
                                optionflags=doctest.ELLIPSIS)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
