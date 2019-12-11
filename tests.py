#!/usr/bin/python
import doctest
import gc
import glob
import os
import re
import shutil
import string
import sys
import tempfile
import textwrap
import types
import unittest

# setuptools imports `imp`, which triggers a DeprecationWarning starting with
# Python 3.4 in the middle of my pristine test suite.  But if I do the import
# upfront, there's no warning.  I cannot explain this, I'm just happy there's
# no warning.
import setuptools  # noqa

try:
    from unittest import mock
except ImportError:
    import mock

import objgraph

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


try:
    from unittest import skipIf
except ImportError:
    def skipIf(condition, reason):
        def wrapper(fn):
            if condition:
                def empty_test(case):
                    pass
                empty_test.__doc__ = '%s skipped because %s' % (
                    fn.__name__, reason)
                return empty_test
            return fn
        return wrapper


def format(text, **kwargs):
    template = string.Template(text)
    return template.substitute(kwargs)


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
                if isinstance(expected_regexp, basestring):  # noqa
                    expected_regexp = re.compile(expected_regexp)
                if not expected_regexp.search(text):
                    msg = msg or "Regexp didn't match"
                    msg = '%s: %r not found in %r' % (msg,
                                                      expected_regexp.pattern,
                                                      text)
                    raise self.failureException(msg)


class GarbageCollectedMixin(object):
    """A mixin for test cases that garbage collects before running."""

    def setUp(self):
        super(GarbageCollectedMixin, self).setUp()
        gc.collect()

    def tearDown(self):
        super(GarbageCollectedMixin, self).tearDown()
        gc.enable()


class CaptureMixin(object):
    """A mixing that captures sys.stdout"""

    def setUp(self):
        super(CaptureMixin, self).setUp()
        self.real_stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self.real_stdout
        super(CaptureMixin, self).tearDown()

    def assertOutput(self, output):
        self.assertEqual(sys.stdout.getvalue(),
                         textwrap.dedent(output.lstrip('\n')))


class TemporaryDirectoryMixin(object):
    """A mixin that sets up a temporary directory"""

    def setUp(self):
        super(TemporaryDirectoryMixin, self).setUp()
        self.prevdir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp(prefix='test-objgraph-')
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.prevdir)
        shutil.rmtree(self.tmpdir)
        super(TemporaryDirectoryMixin, self).tearDown()


# Unit tests

SINGLE_ELEMENT_OUTPUT = textwrap.dedent('''\
    digraph ObjectGraph {
      node[shape=box, style=filled, fillcolor=white];
      ${label_a}[fontcolor=red];
      ${label_a}[label="TestObject\\nTestObject(A)"];
      ${label_a}[fillcolor="0,0,1"];
    }
''')


SINGLE_ELEMENT_OUTPUT_WITH_ATTR = textwrap.dedent('''\
    digraph ObjectGraph {
      node[shape=box, style=filled, fillcolor=white];
      ${label_a}[fontcolor=red];
      ${label_a}[label="TestObject\\nTestObject(A)", x="y"];
      ${label_a}[fillcolor="0,0,1"];
    }
''')


TWO_ELEMENT_OUTPUT = textwrap.dedent('''\
    digraph ObjectGraph {
      node[shape=box, style=filled, fillcolor=white];
      ${label_a}[fontcolor=red];
      ${label_a}[label="TestObject\\nTestObject(A)"];
      ${label_a}[fillcolor="0,0,1"];
      ${label_b} -> ${label_a};
      ${label_b}[label="TestObject\\nTestObject(B)"];
      ${label_b}[fillcolor="0,0,0.766667"];
    }
''')


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


def edge_function(chain_map=None):
    """Given a mapping of src name -> dst name  or src name -> [dst names]
    returns an edge_function. The default edge_function is empty."""
    if not chain_map:
        chain_map = {}

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
        objgraph._show_graph([obj], edge_function(), False, output=output,
                             shortnames=True)
        output_value = output.getvalue()
        label = objgraph._obj_node_id(obj)
        self.assertEqual(output_value,
                         format(SINGLE_ELEMENT_OUTPUT,
                                label_a=label))

    def test_with_extra_node_attrs(self):
        obj = TestObject.get("A")
        output = StringIO()
        objgraph._show_graph([obj], edge_function(), False, output=output,
                             shortnames=True,
                             extra_node_attrs=lambda o: {'x': 'y'})
        output_value = output.getvalue()
        label = objgraph._obj_node_id(obj)
        self.assertEqual(output_value,
                         format(SINGLE_ELEMENT_OUTPUT_WITH_ATTR,
                                label_a=label))

    def test_filename_and_output(self):
        output = StringIO()
        self.assertRaises(ValueError, objgraph._show_graph, [],
                          edge_function(), False, filename='filename',
                          output=output)

    def test_simple_chain(self):
        edge_fn = edge_function({'A': 'B'})
        output = StringIO()
        objgraph._show_graph([TestObject.get("A")], edge_fn, False,
                             output=output, shortnames=True)
        output_value = output.getvalue()
        label_a = objgraph._obj_node_id(TestObject.get("A"))
        label_b = objgraph._obj_node_id(TestObject.get("B"))
        self.assertEqual(output_value,
                         format(TWO_ELEMENT_OUTPUT,
                                label_a=label_a,
                                label_b=label_b))

    def test_cull_func(self):
        edge_fn = edge_function({'A': 'B', 'B': 'C'})
        output = StringIO()
        objgraph._show_graph([TestObject.get("A")], edge_fn, False,
                             output=output, shortnames=True,
                             cull_func=lambda obj: obj.name == 'B')
        output_value = output.getvalue()
        label_a = objgraph._obj_node_id(TestObject.get("A"))
        label_b = objgraph._obj_node_id(TestObject.get("B"))
        self.assertEqual(output_value,
                         format(TWO_ELEMENT_OUTPUT,
                                label_a=label_a,
                                label_b=label_b))

    @mock.patch('objgraph.IS_INTERACTIVE', True)
    @mock.patch('objgraph.graphviz', create=True)
    def test_ipython(self, mock_graphviz):
        mock_graphviz.Source = lambda x: x
        res = objgraph._show_graph([TestObject.get("A")], edge_function(),
                                   False)
        self.assertTrue(res.startswith('digraph'))


class FindChainTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the find_chain function."""

    def test_no_chain(self):
        a = object()
        self.assertEqual(
            [a],
            objgraph._find_chain(a, lambda x: False, gc.get_referrers))


class CountTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the count function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        y = type('MyClass', (), {'__module__': 'other'})()  # noqa
        self.assertEqual(2, objgraph.count('MyClass'))
        self.assertEqual(1, objgraph.count('mymodule.MyClass'))

    def test_no_new_reference_cycles(self):
        # Similar to https://github.com/mgedmin/objgraph/pull/22 but for
        # count()
        gc.disable()
        x = type('MyClass', (), {})()
        before = len(gc.get_referrers(x))
        objgraph.count('MyClass')
        after = len(gc.get_referrers(x))
        self.assertEqual(before, after)


class TypestatsTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the typestats function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        stats = objgraph.typestats(shortnames=False)
        self.assertEqual(1, stats['mymodule.MyClass'])

    def test_no_new_reference_cycles(self):
        # Similar to https://github.com/mgedmin/objgraph/pull/22 but for
        # typestats()
        gc.disable()
        x = type('MyClass', (), {})()
        before = len(gc.get_referrers(x))
        objgraph.typestats()
        after = len(gc.get_referrers(x))
        self.assertEqual(before, after)


class TypestatsFilterArguTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the typestats function, especially for augument
    ``filter`` which is added at version 3.1.3"""

    def test_without_filter(self):
        MyClass = type('MyClass', (), {'__module__': 'mymodule'})  # noqa
        x, y = MyClass(), MyClass()
        x.magic_attr = True
        y.magic_attr = False
        stats = objgraph.typestats(shortnames=False)
        self.assertEqual(2, stats['mymodule.MyClass'])

    def test_with_filter(self):
        MyClass = type('MyClass', (), {'__module__': 'mymodule'})  # noqa
        x, y = MyClass(), MyClass()
        x.magic_attr = True
        y.magic_attr = False
        stats = objgraph.typestats(
            shortnames=False,
            filter=lambda e: isinstance(e, MyClass) and e.magic_attr)
        self.assertEqual(1, stats['mymodule.MyClass'])


class GrowthTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the growth function."""

    def test_growth(self):
        objgraph.growth(limit=None)
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        growth_info = objgraph.growth(limit=None)
        cared = [record for record in growth_info if record[0] == 'MyClass']
        self.assertEqual(1, len(cared))
        self.assertEqual(1, cared[0][2])

    def test_show_growth_custom_peak_stats(self):
        ps = {}
        objgraph.show_growth(peak_stats=ps, file=StringIO())
        self.assertNotEqual(ps, {})


class GetNewIdsTest(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        objgraph.get_new_ids(limit=0, shortnames=True)

    def test_get_new_ids(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        new_ids = objgraph.get_new_ids(limit=0)
        self.assertIn(id(x), new_ids['MyClass'])
        new_ids = objgraph.get_new_ids(limit=0)
        self.assertNotIn(id(x), new_ids['MyClass'])

    def test_get_new_ids_skip_update(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        new_ids = objgraph.get_new_ids(limit=0)
        self.assertIn(id(x), new_ids['MyClass'])
        new_ids = objgraph.get_new_ids(skip_update=True, limit=0)
        self.assertIn(id(x), new_ids['MyClass'])

    def test_get_new_ids_long_typename(self):
        objgraph.get_new_ids(limit=0, shortnames=False)
        x = type('MyClass', (), {'__module__': 'mymodule'})()  # noqa
        new_ids = objgraph.get_new_ids(limit=0)
        self.assertIn(id(x), new_ids['mymodule.MyClass'])


def doctest_get_new_ids_prints():
    """Test for get_new_ids()

        >>> _ = objgraph.get_new_ids(limit=0)
        >>> _ = objgraph.get_new_ids(limit=0)
        >>> a = [0, 1, 2]  # noqa
        >>> b = [3, 4, 5]  # noqa
        >>> _ = objgraph.get_new_ids(limit=1)
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        ========================================================
        Type      Old_ids  Current_ids      New_ids Count_Deltas
        ========================================================
        list          ...          ...          ...           +2
        ========================================================

    """


class ByTypeTest(GarbageCollectedMixin, unittest.TestCase):
    """Tests for the by_test function."""

    def test_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        self.assertEqual([x], objgraph.by_type('mymodule.MyClass'))

    def test_new_garbage(self):
        # Regression test for https://github.com/mgedmin/objgraph/pull/22
        gc.disable()
        x = type('MyClass', (), {})()
        res = objgraph.by_type('MyClass')
        self.assertEqual(res, [x])
        # referrers we expect:
        # 1. this stack frame (except on Python 3.7 where it's somehow missing)
        # 2. the `res` list
        # referrers we don't want:
        # the ``objects`` list in the now-dead stack frame of objgraph.by_type
        self.assertLessEqual(len(gc.get_referrers(res[0])), 2)


class AtAddrsTest(unittest.TestCase):

    def test_at_addrs(self):
        a = [0, 1, 2]
        new_ids = objgraph.get_new_ids(limit=0)
        new_lists = objgraph.at_addrs(new_ids['list'])
        self.assertIn(a, new_lists)


class StringRepresentationTest(GarbageCollectedMixin,
                               CompatibilityMixin,
                               unittest.TestCase):
    """Tests for the string representation of objects and edges."""

    def test_obj_label_long_type_name(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()

        self.assertRegex(
            objgraph._obj_label(x, shortnames=False),
            r'mymodule\.MyClass\\n<mymodule\.MyClass object at .*')

    def test_obj_attrs(self):
        x = object()
        self.assertEqual(
            objgraph._obj_attrs(
                x,
                lambda o: {'url': 'http://e.com/' + o.__class__.__name__,
                           'shape': 'diamond',
                           'ignored': None}),
            r', shape="diamond", url="http://e.com/object"')

    def test_long_typename_with_no_module(self):
        x = type('MyClass', (), {'__module__': None})()
        self.assertEqual('MyClass', objgraph._long_typename(x))

    def test_safe_repr(self):
        class MyClass(object):
            def __repr__(self):
                return 1/0
        self.assertEqual('(unrepresentable)', objgraph._safe_repr(MyClass()))

    def test_short_repr_mocked_instance_method(self):
        class MyClass(object):
            def my_method(self):
                pass

        my_mock = mock.create_autospec(MyClass)
        self.assertRegex(objgraph._short_repr(my_mock.my_method), '<MagicMock')

    def test_short_repr_mocked_instance_method_bound(self):
        class MyClass(object):
            def my_method(self):
                pass

        mock_method = mock.Mock()

        obj = MyClass()
        with mock.patch.object(obj, 'my_method',
                               types.MethodType(mock_method, obj)):
            self.assertRegex(objgraph._short_repr(obj.my_method), '<Mock')

    def test_short_repr_mocked_name(self):
        self.assertRegex(objgraph._short_repr(mock.Mock(__name__=mock.Mock())),
                         '<Mock')

    def test_short_repr_magic_mocked_name(self):
        self.assertRegex(objgraph._short_repr(mock.Mock(
            __name__=mock.MagicMock())), '<Mock')

    def test_short_repr_mock_with_spec(self):
        self.assertRegex(objgraph._short_repr(mock.Mock(spec=list)), '<Mock')

    def test_short_repr_mocked_instance_method_bound_with_mocked_name(self):
        class MyClass(object):
            def my_method(self):
                pass

        mock_method = mock.Mock(__name__=mock.MagicMock())

        obj = MyClass()
        with mock.patch.object(obj, 'my_method',
                               types.MethodType(mock_method, obj)):
            self.assertRegex(objgraph._short_repr(obj.my_method), '<Mock')

    @skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
    def test_short_repr_unbound_method(self):
        class MyClass(object):
            def a_method(self):
                pass

        self.assertEqual('a_method', objgraph._short_repr(MyClass.a_method))

    def test_gradient_empty(self):
        self.assertEqual((0.1, 0.2, 0.3),
                         objgraph._gradient((0.1, 0.2, 0.3),
                                            (0.2, 0.3, 0.4), 0, 0))

    def test_edge_label_frame_locals(self):
        frame = sys._getframe()
        self.assertEqual(' [label="f_locals",weight=10]',
                         objgraph._edge_label(frame, frame.f_locals))

    @skipIf(sys.version_info[0] > 2, "Python 3 has no unbound methods")
    def test_edge_label_unbound_method(self):
        class MyClass(object):
            def a_method(self):
                pass
        self.assertEqual(' [label="__func__",weight=10]',
                         objgraph._edge_label(MyClass.a_method,
                                              MyClass.a_method.__func__))

    def test_edge_label_bound_method(self):
        class MyClass(object):
            def a_method(self):
                pass
        self.assertEqual(' [label="__func__",weight=10]',
                         objgraph._edge_label(MyClass().a_method,
                                              MyClass().a_method.__func__))

    def test_edge_label_long_type_names(self):
        x = type('MyClass', (), {'__module__': 'mymodule'})()
        d = {x: 1}

        self.assertRegex(
            objgraph._edge_label(d, 1, shortnames=False),
            r' [label="mymodule\.MyClass\n<mymodule\.MyClass object at .*"]')

    def test_short_repr_lambda(self):
        f = lambda x: x  # noqa
        lambda_lineno = sys._getframe().f_lineno - 1
        self.assertEqual('lambda: tests.py:%s' % lambda_lineno,
                         objgraph._short_repr(f))

    def test_short_repr_function(self):
        self.assertRegex(objgraph._short_repr(sample_func),
                         'function sample_func at .*')


def sample_func():
    pass


class StubSubprocess(object):

    should_fail = False

    def Popen(self, args, close_fds=False):
        return StubPopen(args, close_fds=close_fds,
                         should_fail=self.should_fail)


class StubPopen(object):

    def __init__(self, args, close_fds=False, should_fail=False):
        print("subprocess.Popen(%s)" % repr(args))
        self.args = args
        self.should_fail = should_fail

    def wait(self):
        self.returncode = int(self.should_fail)


class PresentGraphTest(CaptureMixin, TemporaryDirectoryMixin,
                       unittest.TestCase):

    def setUp(self):
        super(PresentGraphTest, self).setUp()
        self.orig_subprocess = objgraph.subprocess
        self.orig_program_in_path = objgraph._program_in_path
        objgraph.subprocess = StubSubprocess()
        self.programsInPath([])

    def tearDown(self):
        objgraph._program_in_path = self.orig_program_in_path
        objgraph.subprocess = self.orig_subprocess
        super(PresentGraphTest, self).tearDown()

    def programsInPath(self, programs):
        objgraph._program_in_path = set(programs).__contains__

    def test_present_dot(self):
        objgraph._present_graph('foo.dot', 'foo.dot')
        self.assertOutput("")

    def test_present_png(self):
        self.programsInPath(['dot'])
        objgraph._present_graph('foo.dot', 'bar.png')
        self.assertOutput("""
            subprocess.Popen(['dot', '-Tpng', '-obar.png', 'foo.dot'])
            Image generated as bar.png
        """)

    def test_present_png_failure(self):
        self.programsInPath(['dot'])
        objgraph.subprocess.should_fail = True
        objgraph._present_graph('f.dot', 'b.png')
        self.assertOutput("""
            subprocess.Popen(['dot', '-Tpng', '-ob.png', 'f.dot'])
            dot failed (exit code 1) while executing "dot -Tpng -ob.png f.dot"
        """)

    def test_present_png_no_dot(self):
        self.programsInPath([])
        objgraph._present_graph('foo.dot', 'bar.png')
        self.assertOutput("""
            Image renderer (dot) not found, not doing anything else
        """)
        self.assertFalse(os.path.exists('bar.png'))

    def test_present_xdot(self):
        self.programsInPath(['xdot'])
        objgraph._present_graph('foo.dot')
        self.assertOutput("""
            Spawning graph viewer (xdot)
            subprocess.Popen(['xdot', 'foo.dot'])
        """)

    def test_present_no_xdot(self):
        self.programsInPath(['dot'])
        objgraph._present_graph('foo.dot')
        self.assertOutput("""
            Graph viewer (xdot) not found, generating a png instead
            subprocess.Popen(['dot', '-Tpng', '-ofoo.png', 'foo.dot'])
            Image generated as foo.png
        """)

    def test_present_no_xdot_and_no_not(self):
        self.programsInPath([])
        objgraph._present_graph('foo.dot')
        self.assertOutput("Graph viewer (xdot) and image renderer (dot)"
                          " not found, not doing anything else\n")


# Doctests


NODES_VARY = doctest.register_optionflag('NODES_VARY')
RANDOM_OUTPUT = doctest.register_optionflag('RANDOM_OUTPUT')


class RandomOutputChecker(doctest.OutputChecker):

    def check_output(self, want, got, optionflags):
        if optionflags & RANDOM_OUTPUT:
            return got != ""
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


class IgnoreNodeCountChecker(RandomOutputChecker):
    _r = re.compile(r'\(\d+ nodes\)$', re.MULTILINE)

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
