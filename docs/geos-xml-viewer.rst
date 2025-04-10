GEOS XML VIEWER
===============

The `geos-xml-viewer` python package defines tools to read, process, and visualize objects from GEOS input xml file.
See `Advanced XML Features <https://geosx-geosx.readthedocs-hosted.com/en/latest/coreComponents/fileIO/doc/InputXMLFiles.html#advanced-xml-features>`_ for a detailed description of the input format.

This package defines multiple console scripts and a vtk ilter associated with a Paraview reader.

Consol scripts
--------------

geos-exporter
^^^^^^^^^^^^^

Reads the xml file and writes a PartionedDataSetCollection file containing all the mesh objects (mesh, wells, boxes) defind in the xml.

.. argparse::
   :module: geos_xml_viewer.bin.exporter
   :func: parsing
   :prog: geos-exporter

geos-modifier
^^^^^^^^^^^^^

Rewrite wells into VTK file and modify the xml file accordingly.

.. argparse::
   :module: geos_xml_viewer.bin.modifier
   :func: parsing
   :prog: geos-modifier

geos-splitter
^^^^^^^^^^^^^

Extract Internal wells into VTK files.

.. argparse::
   :module: geos_xml_viewer.bin.splitter
   :func: parsing
   :prog: geos-splitter

geos-viewer
^^^^^^^^^^^^^

Viewer dedicated to xml mesh objects (mesh, wells, boxes).

.. argparse::
   :module: geos_xml_viewer.bin.viewer
   :func: parsing
   :prog: geos-viewer


WIP consol scripts
------------------

geos-validate
^^^^^^^^^^^^^

Validate xml file according to GEOS scheme.

.. argparse::
   :module: geos_xml_viewer.bin.validate
   :func: parsing
   :prog: geos-validate


vtk filter
----------

Geos deck reader
^^^^^^^^^^^^^^^^

Vtk reader of GEOS xml file to load or build vtk objects (mesh, wells, boxes).

.. automodule:: geos_xml_viewer.filters.geosDeckReader
   :members:
   :undoc-members:
   :show-inheritance:


Paraview plugin
----------------

Paraview plugin of Geos Deck Reader.

.. automodule:: PVPlugins.deckReader
   :no-members:
   :no-undoc-members:

Utilities
---------

.. automodule:: geos_xml_viewer.algorithms.deck
   :members:
   :undoc-members:

.. automodule:: geos_xml_viewer.algorithms.write_wells
   :members:
   :undoc-members: