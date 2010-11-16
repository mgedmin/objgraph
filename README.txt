Python Object Graphs
====================

``objgraph`` is a module that lets you visually explore Python object graphs.
I've used it in the past to go hunt for memory leaks in Python programs as
described by this series of blog posts:

* http://mg.pov.lt/blog/hunting-python-memleaks.html
* http://mg.pov.lt/blog/python-object-graphs.html
* http://mg.pov.lt/blog/object-graphs-with-graphviz.html

You'll need `graphviz <http://www.graphviz.org/>`_ if you want to draw
pretty graphs.

I recommend `xdot <http://pypi.python.org/pypi/xdot>`_ as well, it is a nice
interactive graph viewer.

.. This is a reStructuredText file.  I recommend http://mg.pov.lt/restview
   for viewing it.


Examples
--------

Try this in a Python shell:

    >>> x = []
    >>> y = [x, [x], dict(x=x)]
    >>> import objgraph
    >>> objgraph.show_refs([y], filename='sample-graph.png')
    Graph written to ....dot (5 nodes)
    Image generated as sample-graph.png

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

