AllChecks Filter
================

.. autoclass:: geos.mesh.doctor.filters.Checks.AllChecks
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The AllChecks filter performs comprehensive mesh validation by running all available quality checks on a vtkUnstructuredGrid. This filter is part of the mesh doctor toolkit and provides detailed analysis of mesh quality, topology, and geometric integrity.

Features
--------

* Comprehensive mesh validation with all available quality checks
* Configurable check parameters for customized validation
* Detailed reporting of found issues
* Integration with mesh doctor parsing system
* Support for both individual check parameter customization and global parameter setting

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import AllChecks

    # Instantiate the filter for all available checks
    allChecksFilter = AllChecks()

    # Set input mesh
    allChecksFilter.SetInputData(mesh)

    # Optionally customize check parameters
    allChecksFilter.setCheckParameter("collocated_nodes", "tolerance", 1e-6)
    allChecksFilter.setGlobalParameter("tolerance", 1e-6)  # applies to all checks with tolerance parameter

    # Execute the checks and get output
    output_mesh = allChecksFilter.getGrid()

    # Get check results
    check_results = allChecksFilter.getCheckResults()

    # Write the output mesh
    allChecksFilter.writeGrid("output/mesh_with_check_results.vtu")

Parameters
----------

The AllChecks filter supports parameter customization for individual checks:

* **setCheckParameter(check_name, parameter_name, value)**: Set specific parameter for a named check
* **setGlobalParameter(parameter_name, value)**: Apply parameter to all checks that support it

Common parameters include:

* **tolerance**: Distance tolerance for geometric checks (e.g., collocated nodes, non-conformal interfaces)
* **angle_tolerance**: Angular tolerance for orientation checks
* **min_volume**: Minimum acceptable element volume

Available Checks
----------------

The AllChecks filter includes all checks available in the mesh doctor system:

* Collocated nodes detection
* Element volume validation
* Self-intersecting elements detection
* Non-conformal interface detection
* Supported element type validation
* And many more quality checks

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid (copy of input with potential additional arrays marking issues)
* **Check Results**: Detailed dictionary with results from all performed checks

See Also
--------

* :doc:`MainChecks <MainChecks>` - Subset of most important checks
* :doc:`CollocatedNodes <CollocatedNodes>` - Individual collocated nodes check
* :doc:`ElementVolumes <ElementVolumes>` - Individual element volume check
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Individual self-intersection check
