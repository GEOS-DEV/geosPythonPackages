MainChecks Filter
=================

.. autoclass:: geos.mesh.doctor.filters.Checks.MainChecks
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The MainChecks filter performs essential mesh validation by running the most important quality checks on a vtkUnstructuredGrid. This filter provides a streamlined subset of checks that are most critical for mesh quality assessment.

Features
--------

* Essential mesh validation with the most important quality checks
* Faster execution compared to AllChecks
* Configurable check parameters
* Focused on critical mesh quality issues
* Same interface as AllChecks for consistency

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import MainChecks

    # Instantiate the filter for main checks only
    mainChecksFilter = MainChecks()

    # Set input mesh
    mainChecksFilter.SetInputData(mesh)

    # Optionally customize check parameters
    mainChecksFilter.setCheckParameter("collocated_nodes", "tolerance", 1e-6)

    # Execute the checks and get output
    output_mesh = mainChecksFilter.getGrid()

    # Get check results
    check_results = mainChecksFilter.getCheckResults()

    # Write the output mesh
    mainChecksFilter.writeGrid("output/mesh_main_checks.vtu")

Main Checks Included
--------------------

The MainChecks filter includes a curated subset of the most important checks:

* **Collocated nodes**: Detect duplicate/overlapping nodes
* **Element volumes**: Identify negative or zero volume elements
* **Self-intersecting elements**: Find geometrically invalid elements
* **Basic topology validation**: Ensure mesh connectivity is valid

These checks cover the most common and critical mesh quality issues that can affect simulation stability and accuracy.

When to Use MainChecks vs AllChecks
-----------------------------------

**Use MainChecks when:**

* You need quick mesh validation
* You're doing routine quality checks
* Performance is important
* You want to focus on critical issues only

**Use AllChecks when:**

* You need comprehensive mesh analysis
* You're debugging complex mesh issues
* You have time for thorough validation
* You need detailed reporting on all aspects

Parameters
----------

Same parameter interface as AllChecks:

* **setCheckParameter(check_name, parameter_name, value)**: Set specific parameter for a named check
* **setGlobalParameter(parameter_name, value)**: Apply parameter to all checks that support it

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid (copy of input with potential additional arrays marking issues)
* **Check Results**: Dictionary with results from performed main checks

See Also
--------

* :doc:`AllChecks <AllChecks>` - Comprehensive mesh validation with all checks
* :doc:`CollocatedNodes <CollocatedNodes>` - Individual collocated nodes check
* :doc:`ElementVolumes <ElementVolumes>` - Individual element volume check
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Individual self-intersection check
