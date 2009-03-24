import os, sys

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


def build_script_to_build_images():
    yield 'import os'
    for line in open(relative('README.txt')):
        if line.startswith('    >>>') or line.startswith('    ...'):
            yield line[8:].rstrip()
        if line.startswith('.. image:: '):
            filename = line.split()[2]
            yield 'os.system("dot -Tpng objects.dot > %s")' % filename


def script_to_build_images():
    return '\n'.join(build_script_to_build_images())


def build_images():
    os.popen(sys.executable, 'w').write(script_to_build_images())


if len(sys.argv) > 1 and sys.argv[1] == '--show-image-script':
    print script_to_build_images()
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] == '--build-images':
    build_images()
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] == '--objgraph-version':
    print get_version()
    sys.exit(0)

setup(name='objgraph',
      version=get_version(),
      author='Marius Gedminas',
      author_email='marius@gedmin.as',
      url='http://mg.pov.lt/objgraph/',
      license='MIT',
      description='Draws Python object reference graphs with graphviz',
      py_modules=['objgraph'])
