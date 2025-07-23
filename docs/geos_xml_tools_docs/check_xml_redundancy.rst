Cehck redundancy
----------------

Checks for redundant attribute definitions in XML files, such as those that duplicate default values or are otherwise unnecessary.

This tool scans XML files in the specified directory and reports attributes that are defined but do not differ from their defaults, helping to clean up and simplify XML configurations.

Typical usage:
    geos-xml-tools redundancy -r /path/to/geos/root

.. argparse::
   :module: geos.xml_tools.command_line_parsers
   :func: build_xml_redundancy_input_parser
   :prog: check_xml_redundancy 