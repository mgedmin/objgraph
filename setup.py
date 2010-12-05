#!/usr/bin/python
import os, sys, doctest, glob

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


def get_version():
    d = {}
    exec read('objgraph.py') in d
    return d['__version__']


def get_description():
    readme = read('README.txt')
    changelog = read('CHANGES.txt')
    return readme + '\n\n\n' + changelog


def build_images():
    sources = glob.glob('*.txt')
    for fn in sources:
        doctest.testfile(fn, optionflags=doctest.ELLIPSIS)


if len(sys.argv) > 1 and sys.argv[1] == '--build-images':
    build_images()
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
