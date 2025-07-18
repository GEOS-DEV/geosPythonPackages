check_xml_attribute_coverage
----------------------------

Analyzes how well a project's XML files cover the possibilities defined in an XML Schema Definition (.xsd) file.

This tool parses the schema, scans XML files in the specified directory, and generates a report showing which attributes are used, their values, and their default values from the schema.
Useful for identifying missing or underused attributes in a codebase.

Typical usage:
    geos-xml-tools coverage -r /path/to/geos/root -o coverage_report.xml

.. argparse::
   :module: geos.xml_tools.command_line_parsers
   :func: build_attribute_coverage_input_parser
   :prog: check_xml_attribute_coverage 