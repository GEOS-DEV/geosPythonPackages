Paraview plugins
=====================

``geos-pv`` is a Python package that gathers `Paraview <https://www.paraview.org/>`_ plugins of GEOS python tools.

It includes:

* Mesh quality plugins
* GEOS pre-processing tools such as mesh-doctor plugins (not available yet)
* GEOS post-processing tools to clean GEOS output mesh, compute geomechanical properties, or create specific plots such as Mohr's circle plot.
* Paraview readers that parse GEOS output log file

The packages can be loaded into Paraview using the Plugin Manager from `Tools > Plugin Manager`. On success, you will
see the selected plugin in the `Filters` menu (see `Paraview documentation <https://docs.paraview.org/en/latest/ReferenceManual/pythonProgrammableFilter.html>`_).

Alternatively, ``geos-pv`` package can be build together with Paraview (see `Paraview compilation guide <https://gitlab.kitware.com/paraview/paraview/-/blob/master/Documentation/dev/build.md>`_).
It is recommended to use Paraview v5.12+, which is based on python 3.10+. If you need to build ``geos-pv`` package with the paraview dependency, use the command:

.. code-block:: bash

    pip install path/to/geosPythonPackages/geos-pv[paraview]


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   pv_generic.rst

   pv_preprocessing.rst

   pv_postprocessing.rst

   pv_qc.rst

   pv_utilities.rst