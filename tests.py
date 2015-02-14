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

from objgraph import obj_node_id
from objgraph import show_graph

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


# Unit tests

SINGLE_ELEMENT_OUTPUT = ('digraph ObjectGraph {\n'
    '  node[shape=box, style=filled, fillcolor=white];\n'
    '  %s[fontcolor=red];\n'
    '  %s[label="instance\\nTestObject(A)"];\n'
    '  %s[fillcolor="0,0,1"];\n'
    '}\n')


TWO_ELEMENT_OUTPUT = ('digraph ObjectGraph {\n'
    '  node[shape=box, style=filled, fillcolor=white];\n'
    '  %s[fontcolor=red];\n'
    '  %s[label="instance\\nTestObject(A)"];\n'
    '  %s[fillcolor="0,0,1"];\n'
    '  %s -> %s;\n'
    '  %s[label="instance\\nTestObject(B)"];\n'
    '  %s[fillcolor="0,0,0.766667"];\n'
    '}\n')


def empty_edge_function(obj):
  return []


class TestObject:
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


class ShowGraphTest(unittest.TestCase):
    """Tests for the show_graph function."""

    def test_basic_file_output(self):
        obj = TestObject.get("A")
        output = StringIO()
        show_graph([obj], empty_edge_function, False, output=output,
                   shortnames=True)
        output_value = output.getvalue()
        label = obj_node_id(obj)
        self.assertEqual(output_value, SINGLE_ELEMENT_OUTPUT %
            (label, label, label))

    def test_simple_chain(self):
        edge_fn = edge_function({'A' : 'B'})
        output = StringIO()
        show_graph([TestObject.get("A")], edge_fn, False, output=output,
                   shortnames=True)
        output_value = output.getvalue()
        label_a = obj_node_id(TestObject.get("A"))
        label_b = obj_node_id(TestObject.get("B"))
        self.assertEqual(output_value, TWO_ELEMENT_OUTPUT %
            (label_a, label_a, label_a, label_b, label_a, label_b, label_b))


class FindChainTest(unittest.TestCase):
    """Tests for the find_chain function."""

    def test_single_chain(self):
        chain = edge_function({
            "A": "B",
            "B": "C",
            "C": "D"
        })

# Doc tests

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

        >>> from objgraph import find_chain
        >>> a = object()
        >>> find_chain(a, lambda x: False, gc.get_referrers) == [a]
        True

    """


def doctest_obj_label_long_type_names():
    r"""Test for obj_label

        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()

        >>> from objgraph import obj_label
        >>> obj_label(x, shortnames=False)  # doctest: +ELLIPSIS
        'mymodule.MyClass\\n<mymodule.MyClass object at ...'

    """


def doctest_long_typename_with_no_module():
    r"""Test for long_typename

        >>> x = type('MyClass', (), {'__module__': None})()

        >>> from objgraph import long_typename
        >>> long_typename(x)
        'MyClass'

    """


def doctest_safe_repr_unsafe():
    r"""Test for long_typename

        >>> class MyClass(object):
        ...     def __repr__(self):
        ...         return 1/0
        >>> x = MyClass()

        >>> from objgraph import safe_repr
        >>> safe_repr(x)
        '(unrepresentable)'

    """


@skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
def doctest_short_repr_unbound_method():
    r"""Test for long_typename

        >>> class MyClass(object):
        ...     def a_method(self):
        ...         pass

        >>> from objgraph import short_repr
        >>> short_repr(MyClass.a_method)
        'a_method'

    """


def doctest_gradient_empty():
    """Test for gradient

        >>> from objgraph import gradient
        >>> gradient((0.1, 0.2, 0.3), (0.2, 0.3, 0.4), 0, 0) == (0.1, 0.2, 0.3)
        True

    """


@skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
@skipIf(sys.version_info[:2] < (2, 6), "Python 2.5 and older has no __func__")
def doctest_edge_label_unbound_method():
    r"""Test for edge_label

        >>> class MyClass(object):
        ...     def a_method(self):
        ...         pass

        >>> from objgraph import edge_label
        >>> edge_label(MyClass.a_method, MyClass.a_method.__func__)
        ' [label="__func__",weight=10]'

    """


def doctest_edge_label_long_type_names():
    r"""Test for edge_label

        >>> x = type('MyClass', (), {'__module__': 'mymodule'})()
        >>> d = {x: 1}

        >>> from objgraph import edge_label
        >>> edge_label(d, 1, shortnames=False)  # doctest: +ELLIPSIS
        ' [label="mymodule.MyClass\\n<mymodule.MyClass object at ..."]'

    """


class DocTestSuite(unittest.TestSuite):

    def __init__(self):
        doctests = find_doctests()
        suite = unittest.TestSuite([
            doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                                 optionflags=doctest.ELLIPSIS,
                                 checker=IgnoreNodeCountChecker(),
                                 *doctests),
            doctest.DocTestSuite(),
        ])
        self.addTest(suite)
        print 'HERE'

def doc_test_suite():
    doctests = find_doctests()
    return unittest.TestSuite([
        doctest.DocFileSuite(setUp=setUp, tearDown=tearDown,
                             optionflags=doctest.ELLIPSIS,
                             checker=IgnoreNodeCountChecker(),
                             *doctests),
        doctest.DocTestSuite(),
    ])


# Test suite rules.


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ShowGraphTest))
    suite.addTest(doc_test_suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
