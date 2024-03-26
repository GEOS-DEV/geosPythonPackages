
.. _XMLToolsPackage:

GEOS XML Tools
--------------------------

The `geos-xml-tools` python package adds a set of advanced features to the GEOS xml format: units, parameters, and symbolic expressions.
See :ref:`PythonToolsSetup` for details on setup instructions, and `Advanced XML Features <https://geosx-geosx.readthedocs-hosted.com/en/latest/coreComponents/fileIO/doc/InputXMLFiles.html#advanced-xml-features>`_ for a detailed description of the input format.
The available console scripts for this package and its API are described below.


convert_abaqus
^^^^^^^^^^^^^^

Convert an abaqus format mesh file to gmsh or vtk format.

.. argparse::
   :module: geos.xml.tools.command_line_parsers
   :func: build_preprocessor_input_parser
   :prog: preprocess_xml


format_xml
^^^^^^^^^^^^^^

Formats an xml file.

.. argparse::
   :module: geos.xml.tools.command_line_parsers
   :func: build_xml_formatter_input_parser
   :prog: format_xml


check_xml_attribute_coverage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Checks xml attribute coverage for files in the GEOS repository.

.. argparse::
   :module: geos.xml.tools.command_line_parsers
   :func: build_attribute_coverage_input_parser
   :prog: check_xml_attribute_coverage


check_xml_redundancy
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Checks for redundant attribute definitions in an xml file, such as those that duplicate the default value.

.. argparse::
   :module: geos.xml.tools.command_line_parsers
   :func: build_xml_redundancy_input_parser
   :prog: check_xml_redundancy


API
^^^

.. automodule:: geos.xml.tools.main
    :members:

.. automodule:: geos.xml.tools.xml_processor
    :members:

.. automodule:: geos.xml.tools.xml_formatter
    :members:

.. automodule:: geos.xml.tools.unit_manager
    :members:

.. automodule:: geos.xml.tools.regex_tools
    :members:

.. automodule:: geos.xml.tools.xml_redundancy_check
    :members:

.. automodule:: geos.xml.tools.attribute_coverage
    :members:

.. automodule:: geos.xml.tools.table_generator
    :members:

