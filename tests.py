#!/usr/bin/python
import unittest
import doctest
import tempfile
import os
import shutil
import glob


RANDOM_OUTPUT = doctest.register_optionflag('RANDOM_OUTPUT')


class MyChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if optionflags & RANDOM_OUTPUT:
            return True
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


def setUp(test):
    test.tmpdir = tempfile.mkdtemp(prefix='test-objgraph-')
    test.prevdir = os.getcwd()
    test.prevtempdir = tempfile.tempdir
    tempfile.tempdir = test.tmpdir
    os.chdir(test.tmpdir)
    try:
        next
    except NameError:
        # Python < 2.6 compatibility
        test.globs['next'] = lambda it: it.next()


def tearDown(test):
    tempfile.tempdir = test.prevtempdir
    os.chdir(test.prevdir)
    shutil.rmtree(test.tmpdir)


def find_doctests():
    return [fn for fn in glob.glob('*.txt')
            if fn != 'HACKING.txt']


def test_suite():
    doctests = find_doctests()
    return doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                                optionflags=doctest.ELLIPSIS,
                                checker=MyChecker(),
                                *doctests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
