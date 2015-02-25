#!/usr/bin/python
import doctest
import gc                   # noqa
import glob
import os
import re
import sys
import shutil
import tempfile
import unittest

import objgraph

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


class CompatibilityMixin:

    # Python 2.7 .. 3.1 has assertRegexpMatches but not assertRegex
    # Python <= 2.6 has neither
    # Python >= 3.2 has both and emits deprecation warnings if you use
    # assertRegexpMatches.

    if not hasattr(unittest.TestCase, 'assertRegex'):
        if hasattr(unittest.TestCase, 'assertRegexpMatches'):
            # This is needed for Python 3.1: let's reuse the existing
            # function because our replacement doesn't work on Python 3
            assertRegex = unittest.TestCase.assertRegexpMatches
        else:
            def assertRegex(self, text, expected_regexp, msg=None):
                if isinstance(expected_regexp, basestring):
                    expected_regexp = re.compile(expected_regexp)
                if not expected_regexp.search(text):
                    msg = msg or "Regexp didn't match"
                    msg = '%s: %r not found in %r' % (msg, expected_regexp.pattern, text)
                    raise self.failureException(msg)


# Unit tests


def empty_edge_function(obj):
    return []


class TestObject:
    pass


class ShowGraphTest(unittest.TestCase, CompatibilityMixin):
    """Tests for the show_graph function."""

    def test_basic_file_output(self):
        obj = TestObject()
        output = StringIO()
        objgraph._show_graph([obj], empty_edge_function, False, output=output)
        output_value = output.getvalue()
        self.assertRegex(output_value, r'digraph ObjectGraph')
        self.assertRegex(output_value,
                         r'%s\[.*?\]' % objgraph._obj_node_id(obj))

    def test_filename_and_output(self):
        output = StringIO()
        self.assertRaises(ValueError,
            objgraph._show_graph, [], empty_edge_function, False,
            filename='filename', output=output)


# Doctests

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


def skipIf(condition, reason):
    def wrapper(fn):
        if condition:
            fn.__doc__ = 'Skipped because %s' % reason
        return fn
    return wrapper


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
    doctests = set(glob.glob('docs/*.txt'))
    if sys.version_info >= (3, 4):
        # Skip uncollectable.txt on Python 3.4 and newer
        doctests.discard(os.path.join('docs', 'uncollectable.txt'))
    return sorted(doctests)


def doctest_setup_py_works():
    """Test that setup.py works

        >>> import sys
        >>> orig_argv = sys.argv
        >>> sys.argv = ['setup.py', '--description']

        >>> import setup  # noqa
        Draws Python object reference graphs with graphviz

        >>> sys.argv = orig_argv

    """


def doctest_count_long_type_names():
    """Test for count

        >>> _ = gc.collect()
        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()
        >>> y = type('MyClass', (), {'__module__': 'other'})()

        >>> from objgraph import count
        >>> count('MyClass')
        2
        >>> count('mymodule.MyClass')
        1

    """


def doctest_typestats_long_type_names():
    """Test for typestats

        >>> _ = gc.collect()
        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()

        >>> from objgraph import typestats
        >>> stats = typestats(shortnames=False)
        >>> stats['mymodule.MyClass']
        1

    """


def doctest_by_type_long_type_names():
    """Test for by_type

        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()

        >>> from objgraph import by_type
        >>> by_type('mymodule.MyClass') == [x]
        True

    """


def doctest_find_chain_no_chain():
    """Test for find_chain

        >>> from objgraph import _find_chain
        >>> a = object()
        >>> _find_chain(a, lambda x: False, gc.get_referrers) == [a]
        True

    """


def doctest_obj_label_long_type_names():
    r"""Test for obj_label

        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()

        >>> from objgraph import _obj_label
        >>> _obj_label(x, shortnames=False)  # doctest: +ELLIPSIS
        'mymodule.MyClass\\n<mymodule.MyClass object at ...'

    """


def doctest_long_typename_with_no_module():
    r"""Test for long_typename

        >>> x = type('MyClass', (), {'__module__': None})()

        >>> from objgraph import _long_typename
        >>> _long_typename(x)
        'MyClass'

    """


def doctest_safe_repr_unsafe():
    r"""Test for safe_repr

        >>> class MyClass(object):
        ...     def __repr__(self):
        ...         return 1/0
        >>> x = MyClass()

        >>> from objgraph import _safe_repr
        >>> _safe_repr(x)
        '(unrepresentable)'

    """


@skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
def doctest_short_repr_unbound_method():
    r"""Test for short_repr

        >>> class MyClass(object):
        ...     def a_method(self):
        ...         pass

        >>> from objgraph import _short_repr
        >>> _short_repr(MyClass.a_method)
        'a_method'

    """


@skipIf(sys.version_info[0] > 2, "Python 3 has no old-style classes")
def doctest_short_typename():
    r"""Test for short_typename

        >>> class OldClass:
        ...     pass
        >>> class NewClass(object):
        ...     pass

        >>> from objgraph import _short_typename
        >>> _short_typename(OldClass())
        'OldClass'
        >>> _short_typename(NewClass())
        'NewClass'
        >>> _short_typename({})
        'dict'

    """


def doctest_gradient_empty():
    """Test for gradient

        >>> from objgraph import _gradient
        >>> _gradient((0.1, 0.2, 0.3), (0.2, 0.3, 0.4), 0, 0) == (0.1, 0.2, 0.3)
        True

    """


@skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
@skipIf(sys.version_info[:2] < (2, 6), "Python 2.5 and older has no __func__")
def doctest_edge_label_unbound_method():
    r"""Test for edge_label

        >>> class MyClass(object):
        ...     def a_method(self):
        ...         pass

        >>> from objgraph import _edge_label
        >>> _edge_label(MyClass.a_method, MyClass.a_method.__func__)
        ' [label="__func__",weight=10]'

    """


def doctest_edge_label_long_type_names():
    r"""Test for edge_label

        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()
        >>> d = {x: 1}

        >>> from objgraph import _edge_label
        >>> _edge_label(d, 1, shortnames=False)  # doctest: +ELLIPSIS
        ' [label="mymodule.MyClass\\n<mymodule.MyClass object at ..."]'

    """


def test_suite():
    doctests = find_doctests()
    return unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromName(__name__),
        doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                             optionflags=doctest.ELLIPSIS,
                             checker=IgnoreNodeCountChecker(),
                             *doctests),
        doctest.DocTestSuite(),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
