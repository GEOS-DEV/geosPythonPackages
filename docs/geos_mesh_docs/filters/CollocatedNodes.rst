CollocatedNodes Filter
======================

.. automodule:: geos.mesh.doctor.filters.CollocatedNodes
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The CollocatedNodes filter identifies and handles duplicated/collocated nodes in a vtkUnstructuredGrid. Collocated nodes are nodes that are positioned very close to each other (within a specified tolerance), which can indicate mesh quality issues or modeling problems.

Features
--------

* Detection of collocated/duplicated nodes within specified tolerance
* Identification of elements with wrong support (nodes appearing multiple times)
* Optional marking of problematic elements in output mesh
* Configurable tolerance for distance-based node comparison
* Detailed reporting of found collocated node groups

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.CollocatedNodes import CollocatedNodes

    # Instantiate the filter
    collocatedNodesFilter = CollocatedNodes()

    # Set the tolerance for detecting collocated nodes
    collocatedNodesFilter.setTolerance(1e-6)

    # Optionally enable painting of wrong support elements
    collocatedNodesFilter.setPaintWrongSupportElements(1)  # 1 to enable, 0 to disable

    # Set input mesh
    collocatedNodesFilter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = collocatedNodesFilter.getGrid()

    # Get results
    collocated_buckets = collocatedNodesFilter.getCollocatedNodeBuckets()  # list of tuples with collocated node indices
    wrong_support_elements = collocatedNodesFilter.getWrongSupportElements()  # list of problematic element indices

    # Write the output mesh
    collocatedNodesFilter.writeGrid("output/mesh_with_collocated_info.vtu")

Parameters
----------

setTolerance(tolerance)
    Set the distance tolerance for determining if two nodes are collocated.
    
    * **tolerance** (float): Distance threshold below which nodes are considered collocated
    * **Default**: 0.0

setPaintWrongSupportElements(choice)
    Enable/disable creation of array marking elements with wrong support nodes.
    
    * **choice** (int): 1 to enable marking, 0 to disable
    * **Default**: 0

Results Access
--------------

getCollocatedNodeBuckets()
    Returns groups of collocated node indices.
    
    * **Returns**: list[tuple[int]] - Each tuple contains indices of nodes that are collocated

getWrongSupportElements()
    Returns element indices that have support nodes appearing more than once.
    
    * **Returns**: list[int] - Element indices with problematic support nodes

Understanding the Results
-------------------------

**Collocated Node Buckets**

Each bucket is a tuple containing node indices that are within the specified tolerance of each other:

.. code-block:: python

    # Example result: [(0, 15, 23), (7, 42), (100, 101, 102, 103)]
    # This means:
    # - Nodes 0, 15, and 23 are collocated
    # - Nodes 7 and 42 are collocated
    # - Nodes 100, 101, 102, and 103 are collocated

**Wrong Support Elements**

Elements where the same node appears multiple times in the element's connectivity. This usually indicates:

* Degenerate elements
* Mesh generation errors
* Topology problems

Common Use Cases
----------------

* **Mesh Quality Assessment**: Identify potential mesh issues before simulation
* **Mesh Preprocessing**: Clean up meshes by detecting node duplicates
* **Debugging**: Understand why meshes might have connectivity problems
* **Validation**: Ensure mesh meets quality standards for specific applications

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional arrays marking problematic elements
* **Additional Data**: When painting is enabled, adds "WrongSupportElements" array to cell data

Best Practices
--------------

* Set tolerance based on mesh scale and precision requirements
* Use smaller tolerances for high-precision meshes
* Enable painting to visualize problematic areas in ParaView
* Check both collocated buckets and wrong support elements for comprehensive analysis

See Also
--------

* :doc:`AllChecks <AllChecks>` - Includes collocated nodes check among others
* :doc:`MainChecks <MainChecks>` - Includes collocated nodes check in main set
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Related geometric validation
