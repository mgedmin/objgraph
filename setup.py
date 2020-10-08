#!/usr/bin/python
import doctest
import io
import os
import re
import sys
import unittest

from setuptools import setup


def read(filename):
    with io.open(filename, encoding='UTF-8') as f:
        return f.read()


def unsphinx(text):
    # remove Sphinx extensions used in CHANGES.rst from reStructuredText
    # so that it can be handled by plain docutils
    return (text.replace(':func:', '')
            .replace('.. currentmodule:: objgraph', ''))


def get_version():
    r = re.compile('''^__version__ = ["'](.+)["']$''')
    for line in read('objgraph.py').splitlines():
        m = r.match(line)
        if m:
            # our read() returns unicode; coerce it back into str, or
            # python2.7 setup.py sdist will try to mix a unicode filename with
            # the byte stream of the .tar file
            return str(m.group(1))
    raise AssertionError('Could not determine version number from objgraph.py')


def get_description():
    readme = read('README.rst')
    changelog = read('CHANGES.rst')
    description = unsphinx(readme + '\n\n\n' + changelog)
    return description


def build_images(doctests=()):
    import tests
    if not doctests:
        doctests = tests.find_doctests()
    suite = doctest.DocFileSuite(optionflags=doctest.ELLIPSIS,
                                 checker=tests.IgnoreNodeCountChecker(),
                                 *doctests)
    os.chdir('docs')
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if len(sys.argv) > 1 and sys.argv[1] == '--build-images':
    build_images(sys.argv[2:])
    sys.exit(0)


setup(
    name='objgraph',
    version=get_version(),
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    url='https://mg.pov.lt/objgraph/',
    license='MIT',
    description='Draws Python object reference graphs with graphviz',
    long_description=get_description(),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='object graph visualization graphviz garbage collection',
    py_modules=['objgraph'],
    install_requires=[
        'graphviz',  # just for ipython support currently
    ],
    tests_require=['mock;python_version=="2.7"'],
    test_suite='tests.test_suite',
    zip_safe=True,
)
