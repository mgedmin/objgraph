#!/usr/bin/python
import doctest
import gc
import glob
import os
import re
import sys
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
        doctests.discard('docs/uncollectable.txt')
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
