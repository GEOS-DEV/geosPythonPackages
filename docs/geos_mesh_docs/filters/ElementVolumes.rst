ElementVolumes Filter
=====================

.. automodule:: geos.mesh.doctor.filters.ElementVolumes
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ElementVolumes filter calculates the volumes of all elements in a vtkUnstructuredGrid and can identify elements with negative or zero volumes. Such elements typically indicate serious mesh quality issues including inverted elements, degenerate cells, or incorrect node ordering.

Features
--------

* Volume calculation for all element types
* Detection of negative and zero volume elements
* Detailed reporting of problematic elements with their volumes
* Integration with VTK's cell size computation
* Optional filtering to return only problematic elements

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.ElementVolumes import ElementVolumes

    # Instantiate the filter
    elementVolumesFilter = ElementVolumes()

    # Optionally enable detection of negative/zero volume elements
    elementVolumesFilter.setReturnNegativeZeroVolumes(True)

    # Set input mesh
    elementVolumesFilter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = elementVolumesFilter.getGrid()

    # Get problematic elements (if enabled)
    if elementVolumesFilter.m_returnNegativeZeroVolumes:
        negative_zero_volumes = elementVolumesFilter.getNegativeZeroVolumes()
        # Returns numpy array with shape (n, 2) where first column is element index, second is volume

    # Write the output mesh with volume information
    elementVolumesFilter.writeGrid("output/mesh_with_volumes.vtu")

Parameters
----------

setReturnNegativeZeroVolumes(returnNegativeZeroVolumes)
    Enable/disable specific detection and return of elements with negative or zero volumes.
    
    * **returnNegativeZeroVolumes** (bool): True to enable detection, False to disable
    * **Default**: False

Results Access
--------------

getNegativeZeroVolumes()
    Returns detailed information about elements with negative or zero volumes.
    
    * **Returns**: numpy.ndarray with shape (n, 2)
      
      * Column 0: Element indices with problematic volumes
      * Column 1: Corresponding volume values (≤ 0)
    
    * **Note**: Only available when returnNegativeZeroVolumes is enabled

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

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with volume information added as cell data
* **Volume Array**: "Volume" array added to cell data containing computed volumes
* **Additional Data**: When returnNegativeZeroVolumes is enabled, provides detailed problematic element information

Integration with Other Filters
------------------------------

The ElementVolumes filter works well in combination with:

* **CollocatedNodes**: Fix node duplication that can cause zero volumes
* **SelfIntersectingElements**: Detect other geometric problems
* **AllChecks/MainChecks**: Comprehensive mesh validation including volume checks

Example Workflow
----------------

.. code-block:: python

    # Complete volume analysis workflow
    volumeFilter = ElementVolumes()
    volumeFilter.setReturnNegativeZeroVolumes(True)
    volumeFilter.SetInputData(mesh)
    
    output_mesh = volumeFilter.getGrid()
    
    # Analyze results
    problematic = volumeFilter.getNegativeZeroVolumes()
    
    if len(problematic) > 0:
        print(f"Found {len(problematic)} elements with non-positive volumes:")
        for idx, volume in problematic:
            print(f"  Element {idx}: volume = {volume}")
    else:
        print("All elements have positive volumes - mesh is good!")

See Also
--------

* :doc:`AllChecks <AllChecks>` - Includes element volume check among others
* :doc:`MainChecks <MainChecks>` - Includes element volume check in main set
* :doc:`CollocatedNodes <CollocatedNodes>` - Can help fix zero volume issues
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Related geometric validation
