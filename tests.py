#!/usr/bin/python
import doctest
import glob
import os
import re
import shutil
import tempfile
import unittest


NODES_VARY = doctest.register_optionflag('NODES_VARY')
RANDOM_OUTPUT = doctest.register_optionflag('RANDOM_OUTPUT')


class RandomOutputChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if optionflags & RANDOM_OUTPUT:
            return True
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


class IgnoreNodeCountChecker(RandomOutputChecker):
    _r = re.compile('\(\d+ nodes\)$', re.MULTILINE)

    def check_output(self, want, got, optionflags):
        if optionflags & NODES_VARY:
            want = self._r.sub('(X nodes)', want)
            got = self._r.sub('(X nodes)', got)
        return RandomOutputChecker.check_output(self, want, got, optionflags)


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
    return glob.glob('docs/*.txt')


def doctest_setup_py_works():
    """Test that setup.py works

        >>> import sys
        >>> orig_argv = sys.argv
        >>> sys.argv = ['setup.py', '--description']

        >>> import setup
        Draws Python object reference graphs with graphviz

        >>> sys.argv = orig_argv

    """


def test_suite():
    doctests = find_doctests()
    return unittest.TestSuite([
        doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                             optionflags=doctest.ELLIPSIS,
                             checker=IgnoreNodeCountChecker(),
                             *doctests),
        doctest.DocTestSuite(),
    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
