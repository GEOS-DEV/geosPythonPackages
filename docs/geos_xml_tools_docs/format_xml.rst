format_xml
----------

Formats a GEOS XML file for improved readability and consistency.

This tool pretty-prints, re-indents, and alphabetizes attributes in XML files.
It offers options for indentation size and style, block separation, attribute sorting, namespace inclusion, and close-tag style.
Useful for cleaning up XML files before sharing or version control.

Typical usage:
    geos-xml-tools format input.xml -i 4

.. argparse::
   :module: geos.xml_tools.command_line_parsers
   :func: build_xml_formatter_input_parser
   :prog: format_xml 