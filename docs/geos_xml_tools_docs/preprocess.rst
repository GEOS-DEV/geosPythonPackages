preprocess
----------

Preprocesses GEOS XML files, performing variable substitution, merging included files, and applying symbolic math and unit conversions.

This tool is typically used to prepare input files for GEOS simulations by compiling multiple XML sources into a single, validated file. It supports parameter overrides, schema validation, and verbosity control.

Key features:
- Merges multiple XML files via <Included> tags
- Handles <Parameters> blocks and variable substitution
- Supports units and symbolic math in XML
- Optionally validates the final XML against a schema

Typical usage:
    geos-xml-tools preprocess -i input.xml -c output.xml

.. argparse::
   :module: geos.xml_tools.command_line_parsers
   :func: build_preprocessor_input_parser
   :prog: preprocess_xml 