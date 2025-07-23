Command Line Reference
======================

The **geos-xml-tools** package provides a unified command-line interface for XML preprocessing, formatting, analysis, and visualization. All commands are accessed through the main `geos-xml-tools` executable.

Basic Usage
-----------

.. code-block:: bash

    geos-xml-tools <command> [OPTIONS]


For detailed help on any specific command:

.. code-block:: bash

    geos-xml-tools <command> --help


Available Commands
------------------

Preprocess
~~~~~~~~~~

XML preprocessing and variable substitution.

**Usage:**

.. code-block:: bash

    geos-xml-tools preprocess [OPTIONS]


**Options:**
    -i, --input FILE          Input XML file(s) (multiple allowed)
    -c, --compiled-name FILE  Output compiled XML file
    -s, --schema FILE         Schema file for validation
    -v, --verbose LEVEL       Verbosity level (0-3, default: 0)
    -p, --parameters NAME VALUE  Parameter overrides (multiple allowed)


**Examples:**

.. code-block:: bash

    # Basic preprocessing
    geos-xml-tools preprocess -i input.xml -c output.xml
    
    # Multiple input files with parameter overrides
    geos-xml-tools preprocess -i input1.xml -i input2.xml -p param1 value1
    
    # With schema validation
    geos-xml-tools preprocess -i input.xml -c output.xml -s schema.xsd -v 2


Format
~~~~~~

XML formatting and structure cleanup.

**Usage:**

.. code-block:: bash

    geos-xml-tools format FILE [OPTIONS]


**Options:**
    -i, --indent SIZE         Indent size (default: 2)
    -s, --style STYLE         Indent style (0=space, 1=tab, default: 0)
    -d, --depth DEPTH         Block separation depth (default: 2)
    -a, --alphebitize MODE    Alphabetize attributes (0=no, 1=yes, default: 0)
    -c, --close STYLE         Close tag style (0=same line, 1=new line, default: 0)
    -n, --namespace LEVEL     Include namespace (0=no, 1=yes, default: 0)


**Examples:**

.. code-block:: bash

    # Basic formatting with 4-space indentation
    geos-xml-tools format input.xml -i 4
    
    # Format with tab indentation and alphabetized attributes
    geos-xml-tools format input.xml -s 1 -a 1


Coverage
~~~~~~~~

XML attribute coverage analysis.

**Usage:**

.. code-block:: bash

    geos-xml-tools coverage [OPTIONS]


**Options:**
    -r, --root PATH           GEOS root directory
    -o, --output FILE         Output file name (default: attribute_test.xml)


**Examples:**

.. code-block:: bash

    # Basic coverage analysis
    geos-xml-tools coverage -r /path/to/geos/root
    
    # With custom output file
    geos-xml-tools coverage -r /path/to/geos/root -o my_coverage.xml


Redundancy
~~~~~~~~~~

XML redundancy checking.

**Usage:**

.. code-block:: bash

    geos-xml-tools redundancy [OPTIONS]


**Options:**
    -r, --root PATH           GEOS root directory


**Examples:**

.. code-block:: bash

    # Check for redundant attributes and elements
    geos-xml-tools redundancy -r /path/to/geos/root


VTK-Build
~~~~~~~~~

Build VTK deck from XML configuration.

**Usage:**

.. code-block:: bash

    geos-xml-tools vtk-build FILE [OPTIONS]


**Options:**
    -a, --attribute NAME      Cell attribute name for region marker (default: Region)
    -o, --output FILE         Output VTK file (optional)


**Examples:**

.. code-block:: bash

    # Basic VTK deck building
    geos-xml-tools vtk-build input.xml -a Region
    
    # Save to specific output file
    geos-xml-tools vtk-build input.xml -o output.vtk


Viewer
~~~~~~

3D visualization viewer for GEOS data.

**Usage:**

.. code-block:: bash

    geos-xml-tools viewer [OPTIONS]


**Options:**
    -xp, --xmlFilepath FILE   Path to XML file (required)
    --showmesh                Show mesh visualization
    --showwells               Show wells visualization
    --showperforations        Show perforations visualization
    --showbounds              Show bounds visualization
    --Zamplification FACTOR   Z amplification factor (default: 1.0)
    --attributeName NAME      Attribute name used to define regions when using VTKMesh (default: attribute)


**Examples:**

.. code-block:: bash

    # Basic viewer with mesh and wells
    geos-xml-tools viewer -xp input.xml --showmesh --showwells
    
    # Viewer with custom Z amplification
    geos-xml-tools viewer -xp input.xml --showmesh --Zamplification 2.0


Legacy Commands
---------------

For backward compatibility, the following legacy command names are also available:

- ``preprocess_xml`` - Alias for ``geos-xml-tools preprocess``
- ``format_xml`` - Alias for ``geos-xml-tools format``
- ``check_xml_attribute_coverage`` - Alias for ``geos-xml-tools coverage``
- ``check_xml_redundancy`` - Alias for ``geos-xml-tools redundancy``
- ``geos-viewer`` - Alias for ``geos-xml-tools viewer``

Error Handling
--------------

All commands provide informative error messages when:

- Input files are not found or are invalid
- Required arguments are missing
- XML syntax errors are encountered
- Processing fails due to invalid content

For debugging, use the verbose flag (-v) with preprocessing commands to get detailed output about the processing steps.

Parallel Processing
-------------------

The preprocess command supports parallel processing in MPI environments. When running in parallel:

- Only rank 0 performs the actual file processing
- Other ranks wait for the processed file to be available
- The ``--compiled-name`` argument is required in parallel mode 