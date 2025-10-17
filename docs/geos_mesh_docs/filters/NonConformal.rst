NonConformal Filter
===================

.. automodule:: geos.mesh.doctor.filters.NonConformal
   :members:
   :undoc-members:
   :show-inheritance:

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

* :doc:`AllChecks <Checks>` - Includes non-conformal check among others
