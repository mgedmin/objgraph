#!/usr/bin/python
import codecs, os, re, sys, unittest, doctest

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def relative(filename):
    here = os.path.dirname('__file__')
    return os.path.join(here, filename)


def read(filename):
    f = codecs.open(relative(filename), 'r', 'utf-8')
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
    description = unsphinx(readme + '\n\n\n' + changelog)
    if '--unicode-description' in sys.argv:
        sys.argv.remove('--unicode-description')
    else:
        description = description.encode('ascii', 'replace').decode('ascii')
    return description


def build_images(doctests=()):
    import tests
    if not doctests:
        doctests = tests.find_doctests()
    suite = doctest.DocFileSuite(optionflags=doctest.ELLIPSIS,
                                 checker=tests.RandomOutputChecker(),
                                 *doctests)
    os.chdir('docs')
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
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.4',
          'Programming Language :: Python :: 2.5',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
      ],
      py_modules=['objgraph'])
