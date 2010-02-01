import os, sys, itertools

try:
    from setuptools import setup
except ImportError:
    from distutils import setup


def relative(filename):
    here = os.path.dirname('__file__')
    return os.path.join(here, filename)


def get_version():
    d = {}
    exec open(relative('objgraph.py')).read() in d
    return d['__version__']


def build_images():
    env = {}
    block = []
    for line in itertools.chain(open(relative('README.txt')),
                                open(relative('examples.txt'))):
        if line.startswith('    ...'):
            block.append(line[8:].rstrip())
        if line.startswith('    >>>'):
            if block:
                exec('\n'.join(block), env)
                block = []
            block.append(line[8:].rstrip())
    if block:
        exec('\n'.join(block), env)


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
      py_modules=['objgraph'])
