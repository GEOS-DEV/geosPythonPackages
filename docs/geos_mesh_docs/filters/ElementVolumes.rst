ElementVolumes Filter
=====================

.. automodule:: geos.mesh.doctor.filters.ElementVolumes
   :members:
   :undoc-members:
   :show-inheritance:

Understanding Volume Issues
---------------------------

**Negative Volumes**

Indicate elements with inverted geometry:

* **Tetrahedra**: Nodes ordered incorrectly (clockwise instead of counter-clockwise)
* **Hexahedra**: Faces oriented inward instead of outward
* **Other elements**: Similar orientation/ordering issues

**Zero Volumes**

Indicate degenerate elements:

* **Collapsed elements**: All nodes lie in the same plane (3D) or line (2D)
* **Duplicate nodes**: Multiple nodes at the same location within the element
* **Extreme aspect ratios**: Elements stretched to near-zero thickness

**Impact on Simulations**

Elements with non-positive volumes can cause:

* Numerical instabilities
* Convergence problems
* Incorrect physical results
* Solver failures

Common Fixes
------------

**For Negative Volumes:**

1. **Reorder nodes**: Correct the connectivity order
2. **Flip elements**: Use mesh repair tools
3. **Regenerate mesh**: If issues are widespread

**For Zero Volumes:**

1. **Remove degenerate elements**: Delete problematic cells
2. **Merge collocated nodes**: Fix duplicate node issues
3. **Improve mesh quality**: Regenerate with better settings

I/O
---

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with volume information added as cell data
* **Volume Array**: "Volume" array added to cell data containing computed volumes
* **Additional Data**: When returnNegativeZeroVolumes is enabled, provides detailed problematic element information

See Also
--------

* :doc:`AllChecks and MainChecks <Checks>` - Includes element volumes check among others
