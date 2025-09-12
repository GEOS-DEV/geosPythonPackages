NonConformal Filter
===================

.. automodule:: geos.mesh.doctor.filters.NonConformal
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The NonConformal filter detects non-conformal mesh interfaces in a vtkUnstructuredGrid. Non-conformal interfaces occur when adjacent cells do not share nodes or faces properly, which can indicate mesh quality issues or intentional non-matching grid interfaces that require special handling in simulations.

Features
--------

* Detection of non-conformal interfaces between mesh elements
* Configurable tolerance parameters for different geometric aspects
* Optional marking of non-conformal cells in output mesh
* Support for point, face, and angle tolerance specifications
* Detailed reporting of non-conformal cell pairs

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.NonConformal import NonConformal

    # Instantiate the filter
    nonConformalFilter = NonConformal()

    # Set tolerance parameters
    nonConformalFilter.setPointTolerance(1e-6)  # tolerance for point matching
    nonConformalFilter.setFaceTolerance(1e-6)   # tolerance for face matching
    nonConformalFilter.setAngleTolerance(10.0)  # angle tolerance in degrees

    # Optionally enable painting of non-conformal cells
    nonConformalFilter.setPaintNonConformalCells(1)  # 1 to enable, 0 to disable

    # Set input mesh
    nonConformalFilter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = nonConformalFilter.getGrid()

    # Get non-conformal cell pairs
    non_conformal_cells = nonConformalFilter.getNonConformalCells()
    # Returns list of tuples with (cell1_id, cell2_id) for non-conformal interfaces

    # Write the output mesh
    nonConformalFilter.writeGrid("output/mesh_with_nonconformal_info.vtu")

Parameters
----------

setPointTolerance(tolerance)
    Set the tolerance for point position matching.
    
    * **tolerance** (float): Distance below which points are considered coincident
    * **Default**: 0.0

setFaceTolerance(tolerance)
    Set the tolerance for face geometry matching.
    
    * **tolerance** (float): Distance tolerance for face-to-face matching
    * **Default**: 0.0

setAngleTolerance(tolerance)
    Set the tolerance for face normal angle differences.
    
    * **tolerance** (float): Maximum angle difference in degrees
    * **Default**: 10.0

setPaintNonConformalCells(choice)
    Enable/disable creation of array marking non-conformal cells.
    
    * **choice** (int): 1 to enable marking, 0 to disable
    * **Default**: 0

Results Access
--------------

getNonConformalCells()
    Returns pairs of cell indices that have non-conformal interfaces.
    
    * **Returns**: list[tuple[int, int]] - Each tuple contains (cell1_id, cell2_id)

getAngleTolerance()
    Get the current angle tolerance setting.
    
    * **Returns**: float - Current angle tolerance in degrees

getFaceTolerance()
    Get the current face tolerance setting.
    
    * **Returns**: float - Current face tolerance

getPointTolerance()
    Get the current point tolerance setting.
    
    * **Returns**: float - Current point tolerance

Understanding Non-Conformal Interfaces
---------------------------------------

**Conformal vs Non-Conformal**

**Conformal Interface**: Adjacent cells share exact nodes and faces

.. code-block::

    Cell A: nodes [1, 2, 3, 4]
    Cell B: nodes [3, 4, 5, 6]  # Shares nodes 3,4 with Cell A
    → CONFORMAL

**Non-Conformal Interface**: Adjacent cells do not share nodes/faces exactly

.. code-block::

    Cell A: nodes [1, 2, 3, 4]
    Cell B: nodes [5, 6, 7, 8]  # No shared nodes with Cell A but geometrically adjacent
    → NON-CONFORMAL

**Types of Non-Conformity**

1. **Hanging Nodes**: T-junctions where one element edge intersects another element face
2. **Mismatched Boundaries**: Interfaces where element boundaries don't align
3. **Gap Interfaces**: Small gaps between elements that should be connected
4. **Overlapping Interfaces**: Elements that overlap slightly due to meshing errors

Tolerance Parameters Explained
------------------------------

**Point Tolerance**

Controls how close points must be to be considered the same:

* **Too small**: May miss near-coincident points that should match
* **Too large**: May incorrectly group distinct points
* **Typical values**: 1e-6 to 1e-12 depending on mesh scale

**Face Tolerance**

Controls how closely face geometries must match:

* **Distance-based**: Maximum separation between face centroids or boundaries
* **Affects**: Detection of faces that should be conformal but have small gaps
* **Typical values**: 1e-6 to 1e-10

**Angle Tolerance**

Controls how closely face normals must align:

* **In degrees**: Maximum angle between face normal vectors
* **Affects**: Detection of faces that should be coplanar but have slight orientation differences
* **Typical values**: 0.1 to 10.0 degrees

Common Causes of Non-Conformity
-------------------------------

1. **Mesh Generation Issues**:
   
   * Different mesh densities in adjacent regions
   * Boundary misalignment during mesh merging
   * Floating-point precision errors

2. **Intentional Design**:
   
   * Adaptive mesh refinement interfaces
   * Multi-scale coupling boundaries
   * Domain decomposition interfaces

3. **Mesh Processing Errors**:
   
   * Node merging tolerances too strict
   * Coordinate transformation errors
   * File format conversion issues

Impact on Simulations
---------------------

**Potential Problems**:

* **Gaps**: Can cause fluid/heat leakage in flow simulations
* **Overlaps**: May create artificial constraints or stress concentrations
* **Inconsistent Physics**: Different discretizations across interfaces

**When Non-Conformity is Acceptable**:

* **Mortar Methods**: Designed to handle non-matching grids
* **Penalty Methods**: Use constraints to enforce continuity
* **Adaptive Refinement**: Temporary non-conformity during adaptation

Example Analysis Workflow
-------------------------

.. code-block:: python

    # Comprehensive non-conformity analysis
    nc_filter = NonConformal()
    
    # Configure for sensitive detection
    nc_filter.setPointTolerance(1e-8)
    nc_filter.setFaceTolerance(1e-8)
    nc_filter.setAngleTolerance(1.0)  # 1 degree tolerance
    
    # Enable visualization
    nc_filter.setPaintNonConformalCells(1)
    
    # Process mesh
    nc_filter.SetInputData(mesh)
    output_mesh = nc_filter.getGrid()
    
    # Analyze results
    non_conformal_pairs = nc_filter.getNonConformalCells()
    
    if len(non_conformal_pairs) == 0:
        print("Mesh is fully conformal - all interfaces match properly")
    else:
        print(f"Found {len(non_conformal_pairs)} non-conformal interfaces:")
        for cell1, cell2 in non_conformal_pairs[:10]:  # Show first 10
            print(f"  Cells {cell1} and {cell2} have non-conformal interface")
        
        # Write mesh with marking for visualization
        nc_filter.writeGrid("output/mesh_nonconformal_marked.vtu")

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional marking arrays
* **Marking Array**: When painting is enabled, adds "IsNonConformal" array to cell data
* **Cell Pairs**: List of non-conformal cell index pairs

Best Practices
--------------

* **Set appropriate tolerances** based on mesh precision and simulation requirements
* **Use painting** to visualize non-conformal regions in ParaView
* **Consider physics requirements** when deciding if non-conformity is acceptable
* **Combine with other checks** for comprehensive mesh validation
* **Document intentional non-conformity** for future reference

See Also
--------

* :doc:`AllChecks <AllChecks>` - Includes non-conformal check among others
* :doc:`CollocatedNodes <CollocatedNodes>` - Related to point matching issues
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Related geometric validation
