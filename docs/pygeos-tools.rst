
PyGEOS Tools
=============

The `pygeos-tools` python package adds a variety of tools for working with pygeosx objects.
These include common operations such as setting the value of geosx wrappers with python functions, parallel communication, and file IO.
Examples using these tools can be found here: `PYGEOSX Examples <https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/advancedExamples/pygeosxExamples/Index.html>`_ .

To get the pygeosx objects, you need to build your GEOS with pygeosx, using this command in your cmake file.

.. code-block:: cmake

   set(ENABLE_PYGEOSX ON CACHE BOOL "")


**The python used to build GEOS with pygeosx will be the python to build the pygeos-tools.**
Once the correct python is selected, you need to run in your virtual environment.

.. code-block:: console

   python -m pip install ./pygeos-tools/


.. toctree::
   :maxdepth: 1
   :caption: Contents

   ./pygeos_tools_docs/api.rst

   ./pygeos_tools_docs/acquisition_library.rst

   ./pygeos_tools_docs/input.rst

   ./pygeos_tools_docs/mesh.rst

   ./pygeos_tools_docs/model.rst

   ./pygeos_tools_docs/output.rst

   ./pygeos_tools_docs/solvers.rst


.. toctree::
   :maxdepth: 1
   :caption: Example

   ./pygeos_tools_docs/example.rst
