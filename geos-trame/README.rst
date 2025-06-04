==========
geos-trame
==========

GEOS-TRAME is a graphical user interface using Kitware's TRAME technology for GEOS.
It is a client-server dashboard for GEOS users written in python that allows to:

* visualize GEOS components as a tree structure
* fill the components properties in a dynamically-computed form or as an XML snippet
* visualize the 3D objects (reservoir, fractures, boundary features, wells) on whom simulation will be run
* visualize relative permeability 2D curves dynamically-computed from the simulation deck parameters
* visualize the events of the simulation on an unitless timeline (coarse scale) and  in a chart with units (fine scale)


Installing
----------
Build and install the Vue components

.. code-block:: console

    cd vue-components
    npm i
    npm run build
    cd -

Install the application

.. code-block:: console

    pip install -e .


Run the application

.. code-block:: console

    geos-trame -I /path/to/<your-xml-config-file>

Testing
-------

To be able to run the test suite, make sure to install the additionals dependencies:

.. code-block:: python

    pip install -e '.[test]'

Then you can run the test with `pytest .`

Optional
--------

To use pre-commit hooks (ruff, mypy, yapf,...), make sure to install the dev dependencies:

.. code-block:: console

    pip install -e .[dev]

Regarding GEOS
--------------

This application takes an XML file from the GEOS project to load dynamically all of its components.
To be able to do that, we need first to generate the corresponding python class based on a
xsd schema provided by GEOS.

`For more details <src/geos_trame/schema_generated/README.md>`_

Features
--------

* TODO
