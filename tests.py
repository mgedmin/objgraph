#!/usr/bin/python
import doctest
import gc                   # noqa
import glob
import logging
import os
import re
import sys
import shutil
import string
import tempfile
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import objgraph


class CompatibilityMixin(object):

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


def skipIf(condition, reason):
    def wrapper(fn):
        if condition:
            def empty_test(case):
                pass
            return empty_test
        return fn
    return wrapper


def format(text, **kwargs):
    template = string.Template(text)
    return template.substitute(kwargs)


# Unit tests

SINGLE_ELEMENT_OUTPUT = (
    'digraph ObjectGraph {\n'
    '  node[shape=box, style=filled, fillcolor=white];\n'
    '  ${label_a}[label="TestObject\\nTestObject(A)"];\n'
    '  ${label_a}[fontcolor=red];\n'
    '  ${label_a}[fillcolor="0,0,1"];\n'
    '}\n')


TWO_ELEMENT_OUTPUT = (
    'digraph ObjectGraph {\n'
    '  node[shape=box, style=filled, fillcolor=white];\n'
    '  ${label_a}[label="TestObject\\nTestObject(A)"];\n'
    '  ${label_a}[fontcolor=red];\n'
    '  ${label_a}[fillcolor="0,0,1"];\n'
    '  ${label_b} -> ${label_a};\n'
    '  ${label_b}[label="TestObject\\nTestObject(B)"];\n'
    '  ${label_b}[fillcolor="0,0,0.766667"];\n'
    '}\n')


def empty_edge_function(obj):
    return []


class TestObject(object):
    _objs = {}

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'TestObject(%s)' % self.name

    @classmethod
    def get(cls, name):
        if name in cls._objs:
            return cls._objs[name]
        obj = TestObject(name)
        cls._objs[name] = obj
        return obj


def edge_function(chain_map):
    """Given a mapping of src name -> dst name  or src name -> [dst names]
    returns an edge_function."""
    def helper(src):
        if src.name not in chain_map:
            return []
        dst_names = chain_map[src.name]
        if not isinstance(dst_names, (list, tuple)):
            dst_names = [dst_names]
        return [TestObject.get(dst_name) for dst_name in dst_names]
    return helper


class GarbageCollectedTestCase(unittest.TestCase):
    """A base TestCase that garbage collects before running."""
    def setUp(self):
        gc.collect()


class ShowGraphTest(GarbageCollectedTestCase):
    """Tests for the show_graph function."""

    def test_basic_file_output(self):
        obj = TestObject.get("A")
        output = StringIO()
        objgraph.show_graph([obj], empty_edge_function, False, output=output,
                            shortnames=True)
        output_value = output.getvalue()
        label = objgraph._obj_node_id(obj)
        self.assertEqual(output_value,
                         format(SINGLE_ELEMENT_OUTPUT,
                                label_a=label))

    def test_simple_chain(self):
        edge_fn = edge_function({'A' : 'B'})
        output = StringIO()
        objgraph.show_graph([TestObject.get("A")], edge_fn, False, output=output,
                            shortnames=True)
        output_value = output.getvalue()
        label_a = objgraph._obj_node_id(TestObject.get("A"))
        label_b = objgraph._obj_node_id(TestObject.get("B"))
        self.assertEqual(output_value,
                         format(TWO_ELEMENT_OUTPUT,
                                label_a=label_a,
                                label_b=label_b))

    def test_filename_and_output(self):
        output = StringIO()
        self.assertRaises(ValueError, objgraph.show_graph, [],
                          empty_edge_function, False,
                          filename='filename', output=output)


class FindChainTest(GarbageCollectedTestCase):
    """Tests for the find_chain function."""

    def test_no_chain(self):
        a = object()
        self.assertEqual([a],
                         objgraph.find_chain(a,
                                             lambda x: False,
                                             gc.get_referrers))


class CountTest(GarbageCollectedTestCase):
    """Tests for the count function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        y = type('MyClass', (), {'__module__': 'other'})()
        self.assertEqual(2, objgraph.count('MyClass'))
        self.assertEqual(1, objgraph.count('mymodule.MyClass'))


class TypestatsTest(GarbageCollectedTestCase):
    """Tests for the typestats function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        stats = objgraph.typestats(shortnames=False)
        self.assertEqual(1, stats['mymodule.MyClass'])


class ByTypeTest(GarbageCollectedTestCase):
    """Tests for the by_test function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        self.assertEqual([x], objgraph.by_type('mymodule.MyClass'))


class StringRepresentationTest(GarbageCollectedTestCase,
                               CompatibilityMixin):
    """Tests for the string representation of objects and edges."""

    def test_obj_label_long_type_name(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()

        self.assertRegex(
            objgraph._obj_label(x, shortnames=False),
            'mymodule\.MyClass\\\\n<mymodule\.MyClass object at .*')

    def test_long_typename_with_no_module(self):
        x = type('MyClass', (), {'__module__': None})()
        self.assertEqual('MyClass', objgraph._long_typename(x))

    def test_safe_repr(self):
        class MyClass(object):
            def __repr__(self):
                return 1/0
        self.assertEqual('(unrepresentable)', objgraph._safe_repr(MyClass()))


    @skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
    def test_short_repr_unbound_method(self):
        class MyClass(object):
            def a_method(self):
                pass

        self.assertEqual('a_method', objgraph._short_repr(MyClass.a_method))

    def test_gradient_empty(self):
        self.assertEqual((0.1, 0.2, 0.3),
                         objgraph._gradient((0.1, 0.2, 0.3),
                                            (0.2, 0.3, 0.4),
                                            0, 0))


    @skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
    @skipIf(sys.version_info[:2] < (2, 6),
            "Python 2.5 and older has no __func__")
    def test_edge_label_unbound_method(self):
        class MyClass(object):
            def a_method(self):
                pass
        self.assertEqual(' [label="__func__",weight=10]',
                         objgraph._edge_label(MyClass.a_method,
                                              MyClass.a_method.__func__))


    def test_edge_label_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        d = {x: 1}

        self.assertRegex(
            objgraph._edge_label(d, 1, shortnames=False),
            ' [label="mymodule\.MyClass\\n<mymodule\.MyClass object at .*"]')


# Doctests


NODES_VARY = doctest.register_optionflag('NODES_VARY')
RANDOM_OUTPUT = doctest.register_optionflag('RANDOM_OUTPUT')


class RandomOutputChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if optionflags & RANDOM_OUTPUT:
            return True
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


class IgnoreNodeCountChecker(RandomOutputChecker):
    _r = re.compile(r'\(\d+ nodes\)$', re.MULTILINE)

    def check_output(self, want, got, optionflags):
        if optionflags & NODES_VARY:
            want = self._r.sub('(X nodes)', want)
            got = self._r.sub('(X nodes)', got)
        return RandomOutputChecker.check_output(self, want, got, optionflags)


class PrintHandler(logging.Handler):
    def emit(self, log):
        print(log.getMessage())


_print_handler = PrintHandler()
_logger = logging.getLogger('objgraph')


def setUp(test):
    # Add a special handler to make the docs tests nicer.

    _logger.setLevel(logging.INFO)
    _logger.addHandler(_print_handler)
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
    _logger.removeHandler(_print_handler)


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
