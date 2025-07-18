vtk-build
---------

Builds a VTK deck from a GEOS XML configuration file for use in visualization and further analysis.

This tool reads a GEOS XML input file and generates a VTK PartitionedDataSetCollection, optionally saving it to a file. The output can be used in Paraview or other VTK-compatible tools.

Key features:
- Converts GEOS XML mesh and region definitions to VTK format
- Supports custom cell attribute names for region markers
- Can output directly to a .vtm or .vtpc file

Typical usage:
    geos-xml-tools vtk-build input.xml -a Region -o output.vtm

.. argparse::
   :module: geos.xml_tools.command_line_parsers
   :func: build_vtk_parser
   :prog: vtk-build 