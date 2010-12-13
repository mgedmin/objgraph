#!/usr/bin/python
import os, re, sys, unittest, doctest

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def relative(filename):
    here = os.path.dirname('__file__')
    return os.path.join(here, filename)


def read(filename):
    f = open(relative(filename))
    try:
        return f.read()
    finally:
        f.close()


def unsphinx(text):
    # remove Sphinx extensions used in CHANGES.txt from reStructuredText
    # so that it can be handled by plain docutils
    return text.replace(':func:', '').replace('.. currentmodule:: objgraph', '')


def get_version():
    r = re.compile('^__version__ = "(.+)"$')
    for line in read('objgraph.py').splitlines():
        m = r.match(line)
        if m:
            return m.group(1)


def get_description():
    readme = read('README.txt')
    changelog = read('CHANGES.txt')
    return unsphinx(readme + '\n\n\n' + changelog)


def build_images(doctests=()):
    import tests
    if not doctests:
        doctests = tests.find_doctests()
    suite = doctest.DocFileSuite(optionflags=doctest.ELLIPSIS,
                                 checker=tests.MyChecker(),
                                 *doctests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if len(sys.argv) > 1 and sys.argv[1] == '--build-images':
    build_images(sys.argv[2:])
    sys.exit(0)


setup(name='objgraph',
      version=get_version(),
      author='Marius Gedminas',
      author_email='marius@gedmin.as',
      url='http://mg.pov.lt/objgraph/',
      license='MIT',
      description='Draws Python object reference graphs with graphviz',
      long_description=get_description(),
      py_modules=['objgraph'])
