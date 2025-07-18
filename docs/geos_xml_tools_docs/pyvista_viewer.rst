viewer
------

Launches a 3D visualization viewer for GEOS XML data using PyVista.

This tool provides an interactive interface for visualizing meshes, wells, boxes, and perforations defined in GEOS XML input files. It supports toggling visibility, attribute-based coloring, and Z amplification for enhanced inspection.

Key features:
- Loads GEOS XML files and displays mesh, wells, surfaces, and boxes
- Interactive controls for toggling elements and adjusting visualization
- Attribute-based coloring and Z amplification

Typical usage:
    geos-xml-tools viewer -xp input.xml --showmesh --showwells

.. argparse::
   :module: geos.xml_tools.pyvista_viewer
   :func: parsing
   :prog: viewer 