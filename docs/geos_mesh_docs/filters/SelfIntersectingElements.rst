SelfIntersectingElements Filter
===============================

.. automodule:: geos.mesh.doctor.filters.SelfIntersectingElements
   :members:
   :undoc-members:
   :show-inheritance:

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

Output
------

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional marking arrays
* **Problem Lists**: Separate lists for each type of geometric problem
* **Marking Arrays**: When painting is enabled, adds arrays identifying problem types

See Also
--------

* :doc:`AllChecks and MainChecks <Checks>` - Includes self-intersection check among others