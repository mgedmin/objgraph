Changes
=======

.. currentmodule:: objgraph

3.5.0 (2020-10-11)
------------------

- Do not require ``mock`` for the test suite on Python 3; use unittest.mock
  instead.

- 100% test coverage for each version of Python rather than combined, using
  ``coverage-python-version``.

- Add the optional ``extra_node_attrs`` parameter to ``show_backrefs`` and
  ``show_backrefs``

- Fix IPython/Jupyter inline graph support code that would kick in even if you
  explicitly passed a filename='foo.png' argument to
  ``show_refs``/``show_backrefs``.  See `issue 47
  <https://github.com/mgedmin/objgraph/issues/47>`_.

- Add support for Python 3.8.

- Drop support for Python 3.5.


3.4.1 (2019-04-23)
------------------

- Add support for Python 3.7.

- Drop support for Python 3.3 and 3.4.


3.4.0 (2018-02-13)
------------------

- New functions: :func:`get_new_ids`, :func:`at_addrs`.

  Contributed by Justin Black in `PR 36
  <https://github.com/mgedmin/objgraph/pull/36>`_.


3.3.0 (2017-12-28)
------------------

- New function: :func:`growth`.


3.2.0 (2017-12-20)
------------------

- New ``filter`` argument for :func:`typestats`, :func:`most_common_types`,
  :func:`show_most_common_types`, :func:`show_growth`.

- Show lambda functions in a more human-friendly way.


3.1.2 (2017-11-27)
------------------

- Correct UTF-8 mojibake in the changelog and switch all links to HTTPS.


3.1.1 (2017-10-30)
------------------

- Add support for Python 3.6.

- Replace bare ``except:`` in ``safe_repr()`` with ``except Exception:``.


3.1.0 (2016-12-07)
------------------

- Support displaying graphs inline in IPython/Jupyter notebooks (`issue 28
  <https://github.com/mgedmin/objgraph/pull/28>`).


3.0.1 (2016-09-17)
------------------

- The ``file`` argument of :func:`show_most_common_types` and
  :func:`show_growth` now defaults to ``None`` instead of ``sys.stdout``.
  ``None`` is interpreted to be the same as ``sys.stdout``, which means
  the right stdout will be used if you change it at runtime (which happens,
  in doctests).


3.0.0 (2016-04-13)
------------------

- :func:`show_most_common_types` and :func:`show_growth` now accept a ``file``
  argument if you want to redirect the output elsewhere.

  Fixes `issue 24 <https://github.com/mgedmin/objgraph/pull/24>`_.  Contributed
  by "d-sun-d".

- Don't trust ``__class__`` to be accurate and ``__name__`` to be a string.
  Fixes errors in some convoluted corner cases when mocks are involved.

  Contributed by Andrew Shannon Brown in `PR 26
  <https://github.com/mgedmin/objgraph/pull/26>`_.

- Drop support for Python 2.4, 2.5, and 2.6.

- Drop support for Python 3.1 and 3.2.

- Add support for Python 3.5.


2.0.1 (2015-07-28)
------------------

- Avoid creating reference cycles between the stack frame and the local
  ``objects`` variable in :func:`by_type`, :func:`count`, and
  :func:`typestats`.

  Fixes `issue 22 <https://github.com/mgedmin/objgraph/pull/22>`_.  Contributed
  by Erik Bray.


2.0.0 (2015-04-18)
------------------

- :func:`show_refs` and :func:`show_backrefs` now accept a file-like object
  (via the new ``output`` argument) as an alternative to a filename.

- Made internal helper methods private. This includes :func:`find_chain`,
  :func:`show_graph`, :func:`obj_node_id`, :func:`obj_label`, :func:`quote`,
  :func:`long_typename`, :func:`safe_repr`, :func:`short_repr`,
  :func:`gradient`, :func:`edge_label`, and :func:`_program_in_path`.

- Correctly determine the name of old-style classes in :func:`count`,
  :func:`by_type`, and graph drawing functions.

  Fixes `issue 16 <https://github.com/mgedmin/objgraph/pull/16>`_.  Contributed
  by Mike Lambert.


1.8.1 (2014-05-15)
------------------

- Do not expect file objects to have an ``encoding`` attribute.  Makes objgraph
  compatible with Eventlet's monkey-patching.

  Fixes `issue 6 <https://github.com/mgedmin/objgraph/pull/6>`_.  Contributed
  by Jakub Stasiak.


1.8.0 (2014-02-13)
------------------

- Moved to GitHub.

- Python 3.4 support (`LP#1270872 <https://launchpad.net/bugs/1270872>`_).

- New function: :func:`is_proper_module`.

- New ``shortnames`` argument for :func:`typestats`, :func:`most_common_types`,
  :func:`show_most_common_types`, :func:`show_growth`, :func:`show_refs`,
  and :func:`show_backrefs`.

  :func:`count` and :func:`by_type` accept fully-qualified type names now.

  Fixes `issue 4 <https://github.com/mgedmin/objgraph/issues/4>`_.


1.7.2 (2012-10-23)
------------------

- Bugfix: setup.py sdist was broken on Python 2.7 (UnicodeDecodeError in
  tarfile).

- The ``filename`` argument for :func:`show_refs` and :func:`show_backrefs` now
  allows arbitrary image formats, not just PNG.  Patch by `Riccardo
  Murri <https://launchpad.net/~rmurri>`_.

- Temporary dot files are now named `objgraph-*.dot` instead of `tmp*.dot`.

- Python 3.3 support: no code changes, but some tests started failing because
  the new and improved dictionary implementation no longer holds references to
  str objects used as dict keys.

- Added a tox.ini for convenient multi-Python testing.


1.7.1 (2011-12-11)
------------------

- Bugfix: non-ASCII characters in object representations would break graph
  generation on Python 3.x, in some locales (e.g. with LC_ALL=C).  Reported and
  fixed by `Stefano Rivera <https://launchpad.net/~stefanor>`_.

- Bugfix: setup.py was broken on Python 3.x

- Bugfix: dot.exe/xdot.exe were not found on Windows (`LP#767239
  <https://launchpad.net/bugs/767239>`_).

- Documentation updates: document the forgotten :func:`find_ref_chain`,
  update :func:`show_chain` prototype.


1.7.0 (2011-03-11)
------------------

- New function: :func:`find_ref_chain`.

- New ``backrefs`` argument for :func:`show_chain`.

- New function: :func:`get_leaking_objects`, based on `a blog post by
  Kristján Valur
  <https://cosmicpercolator.com/2010/12/08/finding-c-reference-leaks-using-the-gc-module/>`_.

- New ``objects`` argument for :func:`count`, :func:`typestats`,
  :func:`most_common_types`, :func:`show_most_common_types`, and
  :func:`by_type`.

- Edges pointing to function attributes such as __defaults__ or __globals__
  are now labeled.

- Edge labels that are not simple strings now show the type.

- Bugfix: '\0' and other unsafe characters used in a dictionary key could
  break graph generation.

- Bugfix: show_refs(..., filename='graph.dot') would then go to complain
  about unrecognized file types and then produce a png.


1.6.0 (2010-12-18)
------------------

- Python 3 support, thanks to Stefano Rivera (fixes `LP#687601
  <https://launchpad.net/bugs/687601>`_).

- Removed weird weakref special-casing.


1.5.1 (2010-12-09)
------------------

- Avoid test failures in uncollectable-garbage.txt (fixes `LP#686731
  <https://launchpad.net/bugs/686731>`_).

- Added HACKING.txt (later renamed to HACKING.rst).


1.5.0 (2010-12-05)
------------------

- Show frame objects as well (fixes `LP#361704
  <https://launchpad.net/bugs/361704>`_).

- New functions: :func:`show_growth`, :func:`show_chain`.

- :func:`find_backref_chain` returns ``[obj]`` instead of ``None`` when a chain
  could not be found.  This makes ``show_chain(find_backref_chain(...), ...)``
  not break.

- Show how many references were skipped from the output of
  :func:`show_refs`/:func:`show_backrefs` by specifying ``too_many``.

- Make :func:`show_refs` descend into modules.

- Do not highlight classes that define a ``__del__``, highlight only instances of
  those classes.

- Option to show reference counts in :func:`show_refs`/:func:`show_backrefs`.

- Add `Sphinx <https://pypi.python.org/pypi/Sphinx>`_ documentation and a PyPI
  long description.


1.4.0 (2010-11-03)
------------------

- Compatibility with Python 2.4 and 2.5 (``tempfile.NamedTemporaryFile`` has no
  ``delete`` argument).

- New function: :func:`most_common_types`.


1.3.1 (2010-07-17)
------------------

- Rebuild an sdist with no missing files (fixes `LP#606604
  <https://launchpad.net/bugs/606604>`_).

- Added MANIFEST.in and a Makefile to check that setup.py sdist generates
  source distributions with no files missing.


1.3 (2010-07-13)
----------------

- Highlight objects with a ``__del__`` method.

- Fixes `LP#483411 <https://launchpad.net/bugs/483411>`_: suggest always passing
  ``[obj]`` to :func:`show_refs`, :func:`show_backrefs`, since obj might be a
  list/tuple.

- Fixes `LP#514422 <https://launchpad.net/bugs/514422>`_: :func:`show_refs`,
  :func:`show_backrefs` don't create files in the current working directory any
  more.  Instead they accept a filename argument, which can be a .dot file or a
  .png file.  If None or not specified, those functions will try to spawn xdot
  as before.

- New extra_info argument to graph-generating functions (patch by Thouis Jones,
  `LP#558914 <https://launchpad.net/bugs/558914>`_).

- setup.py should work with distutils now (`LP#604430
  <https://launchpad.net/bugs/604430>`_, thanks to Randy Heydon).


1.2 (2009-03-25)
----------------

- Project website, public source repository, uploaded to PyPI.

- No code changes.


1.1 (2008-09-10)
----------------

- New function: :func:`show_refs` for showing forward references.

- New functions: :func:`typestats` and :func:`show_most_common_types`.

- Object boxes are less crammed with useless information (such as IDs).

- Spawns `xdot <https://pypi.python.org/pypi/xdot>`_ if it is available.


1.0 (2008-06-14)
----------------

- First public release.
