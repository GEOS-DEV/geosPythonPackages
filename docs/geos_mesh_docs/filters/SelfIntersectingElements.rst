SelfIntersectingElements Filter
===============================

.. automodule:: geos.mesh.doctor.filters.SelfIntersectingElements
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The SelfIntersectingElements filter identifies various types of invalid or problematic elements in a vtkUnstructuredGrid. It performs comprehensive geometric validation to detect elements with intersecting edges, intersecting faces, non-contiguous edges, non-convex shapes, incorrectly oriented faces, and wrong number of points.

Features
--------

* Detection of multiple types of geometric element problems
* Configurable minimum distance parameter for intersection detection
* Optional marking of invalid elements in output mesh
* Detailed classification of different problem types
* Comprehensive reporting of all detected issues

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.SelfIntersectingElements import SelfIntersectingElements

    # Instantiate the filter
    selfIntersectingElementsFilter = SelfIntersectingElements()

    # Set minimum distance parameter for intersection detection
    selfIntersectingElementsFilter.setMinDistance(1e-6)

    # Optionally enable painting of invalid elements
    selfIntersectingElementsFilter.setPaintInvalidElements(1)  # 1 to enable, 0 to disable

    # Set input mesh
    selfIntersectingElementsFilter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = selfIntersectingElementsFilter.getGrid()

    # Get different types of problematic elements
    wrong_points_elements = selfIntersectingElementsFilter.getWrongNumberOfPointsElements()
    intersecting_edges_elements = selfIntersectingElementsFilter.getIntersectingEdgesElements()
    intersecting_faces_elements = selfIntersectingElementsFilter.getIntersectingFacesElements()
    non_contiguous_edges_elements = selfIntersectingElementsFilter.getNonContiguousEdgesElements()
    non_convex_elements = selfIntersectingElementsFilter.getNonConvexElements()
    wrong_oriented_faces_elements = selfIntersectingElementsFilter.getFacesOrientedIncorrectlyElements()

    # Write the output mesh
    selfIntersectingElementsFilter.writeGrid("output/mesh_with_invalid_elements.vtu")

Parameters
----------

setMinDistance(distance)
    Set the minimum distance parameter for intersection detection.
    
    * **distance** (float): Minimum distance threshold for geometric calculations
    * **Default**: 0.0
    * **Usage**: Smaller values detect more subtle problems, larger values ignore minor issues

setPaintInvalidElements(choice)
    Enable/disable creation of arrays marking invalid elements.
    
    * **choice** (int): 1 to enable marking, 0 to disable
    * **Default**: 0
    * **Effect**: When enabled, adds arrays to cell data identifying different problem types

Types of Problems Detected
--------------------------

getWrongNumberOfPointsElements()
    Elements with incorrect number of points for their cell type.
    
    * **Returns**: list[int] - Element indices with wrong point counts
    * **Examples**: Triangle with 4 points, hexahedron with 7 points

getIntersectingEdgesElements()
    Elements where edges intersect themselves.
    
    * **Returns**: list[int] - Element indices with self-intersecting edges
    * **Examples**: Twisted quadrilaterals, folded triangles

getIntersectingFacesElements()
    Elements where faces intersect each other.
    
    * **Returns**: list[int] - Element indices with self-intersecting faces
    * **Examples**: Inverted tetrahedra, twisted hexahedra

getNonContiguousEdgesElements()
    Elements where edges are not properly connected.
    
    * **Returns**: list[int] - Element indices with connectivity issues
    * **Examples**: Disconnected edge loops, gaps in element boundaries

getNonConvexElements()
    Elements that are not convex as required.
    
    * **Returns**: list[int] - Element indices that are non-convex
    * **Examples**: Concave quadrilaterals, non-convex polygons

getFacesOrientedIncorrectlyElements()
    Elements with incorrectly oriented faces.
    
    * **Returns**: list[int] - Element indices with orientation problems
    * **Examples**: Inward-pointing face normals, inconsistent winding

Understanding Element Problems
------------------------------

**Wrong Number of Points**

Each VTK cell type has a specific number of points:

* Triangle: 3 points
* Quadrilateral: 4 points  
* Tetrahedron: 4 points
* Hexahedron: 8 points
* etc.

**Self-Intersecting Edges**

Edges that cross over themselves:

.. code-block::

    Valid triangle:     Invalid triangle (bow-tie):
         A                    A
        / \                  /|\
       /   \                / | \
      B-----C              B--+--C
                              \|/
                               D

**Self-Intersecting Faces**

3D elements where faces intersect:

.. code-block::

    Valid tetrahedron    Invalid tetrahedron (inverted)
         D                     D
        /|\                   /|\
       / | \                 / | \
      A--+--C               C--+--A  (face ABC flipped)
       \ | /                 \ | /
        \|/                   \|/
         B                     B

**Non-Contiguous Edges**

Element boundaries that don't form continuous loops:

* Missing edges between consecutive points
* Duplicate edges
* Gaps in the boundary

**Non-Convex Elements**

Elements that have internal angles > 180 degrees:

* Can cause numerical issues in finite element calculations
* May indicate mesh generation problems
* Some solvers require strictly convex elements

**Incorrectly Oriented Faces**

Faces with normals pointing in wrong directions:

* Outward normals pointing inward
* Inconsistent winding order
* Can affect normal-based calculations

Common Causes and Solutions
---------------------------

**Wrong Number of Points**

* **Cause**: Mesh file corruption, wrong cell type specification
* **Solution**: Fix cell type definitions or regenerate mesh

**Self-Intersecting Edges/Faces**

* **Cause**: Node coordinate errors, mesh deformation, bad mesh generation
* **Solution**: Fix node coordinates, improve mesh quality settings

**Non-Contiguous Edges**

* **Cause**: Missing connectivity information, duplicate nodes
* **Solution**: Fix element connectivity, merge duplicate nodes

**Non-Convex Elements**

* **Cause**: Poor mesh quality, extreme deformation
* **Solution**: Improve mesh generation parameters, element quality checks

**Wrong Face Orientation**

* **Cause**: Inconsistent node ordering, mesh processing errors
* **Solution**: Fix element node ordering, use mesh repair tools

Example Comprehensive Analysis
------------------------------

.. code-block:: python

    # Detailed element validation workflow
    validator = SelfIntersectingElements()
    validator.setMinDistance(1e-8)  # Very sensitive detection
    validator.setPaintInvalidElements(1)  # Enable visualization
    
    validator.SetInputData(mesh)
    output_mesh = validator.getGrid()
    
    # Collect all problems
    problems = {
        'Wrong points': validator.getWrongNumberOfPointsElements(),
        'Intersecting edges': validator.getIntersectingEdgesElements(),
        'Intersecting faces': validator.getIntersectingFacesElements(),
        'Non-contiguous edges': validator.getNonContiguousEdgesElements(),
        'Non-convex': validator.getNonConvexElements(),
        'Wrong orientation': validator.getFacesOrientedIncorrectlyElements()
    }
    
    # Report results
    total_problems = sum(len(elements) for elements in problems.values())
    
    if total_problems == 0:
        print("✓ All elements are geometrically valid!")
    else:
        print(f"⚠ Found {total_problems} problematic elements:")
        for problem_type, elements in problems.items():
            if elements:
                print(f"  {problem_type}: {len(elements)} elements")
                print(f"    Examples: {elements[:5]}")  # Show first 5
    
    # Save results for visualization
    validator.writeGrid("output/mesh_validation_results.vtu")

Impact on Simulations
---------------------

**Numerical Issues**

* Poor convergence
* Solver instabilities  
* Incorrect results
* Simulation crashes

**Physical Accuracy**

* Wrong material volumes
* Incorrect flow paths
* Bad stress/strain calculations
* Energy conservation violations

**Performance Impact**

* Slower convergence
* Need for smaller time steps
* Additional stabilization methods
* Increased computational cost

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional marking arrays
* **Problem Lists**: Separate lists for each type of geometric problem
* **Marking Arrays**: When painting is enabled, adds arrays identifying problem types

Best Practices
--------------

* **Set appropriate minimum distance** based on mesh precision
* **Enable painting** to visualize problems in ParaView
* **Check all problem types** for comprehensive validation
* **Fix problems before simulation** to avoid numerical issues
* **Use with other validators** for complete mesh assessment
* **Document any intentionally invalid elements** if they serve a purpose

See Also
--------

* :doc:`AllChecks <AllChecks>` - Includes self-intersection check among others
* :doc:`MainChecks <MainChecks>` - Includes self-intersection check in main set
* :doc:`ElementVolumes <ElementVolumes>` - Related to geometric validity
* :doc:`CollocatedNodes <CollocatedNodes>` - Can help fix some geometric issues
* :doc:`NonConformal <NonConformal>` - Related interface validation
