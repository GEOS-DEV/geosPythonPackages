CollocatedNodes Filter
======================

.. automodule:: geos.mesh.doctor.filters.CollocatedNodes
   :members:
   :undoc-members:
   :show-inheritance:

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

Cell element IDs where the same node appears multiple times in the element's connectivity. This usually indicates:

* Degenerate elements
* Mesh generation errors
* Topology problems

Common Use Cases
----------------

* **Mesh Quality Assessment**: Identify potential mesh issues before simulation
* **Mesh Preprocessing**: Clean up meshes by detecting node duplicates
* **Debugging**: Understand why meshes might have connectivity problems
* **Validation**: Ensure mesh meets quality standards for specific applications

I/O
---

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional arrays marking problematic elements
* **Additional Data**: When painting is enabled, adds "WrongSupportElements" array to cell data

See Also
--------

* :doc:`AllChecks and MainChecks <Checks>` - Includes collocated nodes check among others
