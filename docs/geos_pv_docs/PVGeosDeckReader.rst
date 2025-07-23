PVGeosDeckReader
================

Overview
--------
- `PVGeosDeckReader` is a Python-based Paraview reader that allows users to open GEOS XML files and create mesh objects for visualization and analysis.
- The plugin is implemented in `PVGeosDeckReader.py` and registered as `PythonGeosDeckReader` in Paraview.
- It outputs a `vtkPartitionedDataSetCollection` representing the mesh and associated regions as defined in the XML file.

Key Features
------------
- **Direct XML loading**: Open GEOS XML input files (`.xml`) in Paraview as native datasets.
- **Region support**: The reader uses the `Region` attribute (or a user-specified attribute) to organize mesh data.
- **Integration with GEOS workflows**: Enables direct inspection and analysis of simulation input decks without conversion steps.

How to Use
----------
1. Install the geos-pv package and ensure Paraview is set up to use Python plugins.
2. In Paraview, load the plugin (typically via the Python Plugin Manager or by specifying the path to `PVGeosDeckReader.py`).
3. Use the "Open" dialog in Paraview to select a GEOS XML file. Choose the `PythonGeosDeckReader` when prompted.
4. The mesh and regions defined in the XML will be loaded as a multi-block dataset for visualization and further processing.

Technical Details
-----------------
- The plugin is implemented as a subclass of `VTKPythonAlgorithmBase` and uses the `create_vtk_deck` function from geos-xml-tools to build the VTK data structure.
- The plugin exposes a `FileName` property for selecting the XML file and can be extended to support additional attributes or options.

Example
-------
.. code-block:: console

    paraview --python-script=path/to/PVGeosDeckReader.py
    # Or load via the Paraview GUI

    # In Paraview:
    # File > Open > select input.xml > choose PythonGeosDeckReader

.. note::
    This plugin is intended for users who want to inspect or debug GEOS input decks visually, or to prepare data for further Paraview-based workflows. 