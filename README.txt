Python Object Graphs
====================

``objgraph`` is a module that lets you visually explore Python object graphs.

You'll need `graphviz <http://www.graphviz.org/>`_ if you want to draw
the pretty graphs.

I recommend `xdot <http://pypi.python.org/pypi/xdot>`_ for interactive use.
``pip install xdot`` should suffice; objgraph will automatically look for it
in your ``PATH``.


Quick start
-----------

Try this in a Python shell:

    >>> x = []
    >>> y = [x, [x], dict(x=x)]
    >>> import objgraph
    >>> objgraph.show_refs([y], filename='sample-graph.png')
    Graph written to ....dot (5 nodes)
    Image generated as sample-graph.png

(If you've installed ``xdot``, omit the filename argument to get the
interactive viewer.)

You should see a graph like this:

.. image:: sample-graph.png
    :alt: [graph of objects reachable from y]

Now try

    >>> objgraph.show_backrefs([x], filename='sample-backref-graph.png')
    Graph written to ....dot (8 nodes)
    Image generated as sample-backref-graph.png

and you'll see

.. image:: sample-backref-graph.png
    :alt: [graph of objects from which y is reachable]


More examples
-------------

.. toctree::
   :maxdepth: 2

   references
   highlighting
   uncollectable
   generator-sample


History
-------

I've developed a set of functions that eventually became objgraph when I
was hunting for memory leaks in a Python program.  The whole story -- with
illustrated examples -- is in this series of blog posts:

* `Hunting memory leaks in Python
  <http://mg.pov.lt/blog/hunting-python-memleaks.html>`_
* `Python object graphs
  <http://mg.pov.lt/blog/python-object-graphs.html>`_
* `Object graphs with graphviz
  <http://mg.pov.lt/blog/object-graphs-with-graphviz.html>`_

