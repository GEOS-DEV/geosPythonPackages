SupportedElements Filter
========================

.. automodule:: geos.mesh.doctor.filters.SupportedElements
   :members:
   :undoc-members:
   :show-inheritance:

GEOS Supported Element Types
----------------------------

GEOS supports the following VTK element types:

**0D & 1D Elements**

* VTK_VERTEX (1): These are individual point elements.
* VTK_LINE (3): These are linear, 1D elements defined by two points.

**2D Elements**

* VTK_TRIANGLE (5): These are 2D, three-noded triangular elements.
* VTK_POLYGON (7): This is a generic cell for 2D elements with more than four vertices.
* VTK_QUAD (9): These are 2D, four-noded quadrilateral elements.

**3D Elements**

* VTK_TETRA (10): These are four-noded tetrahedral elements (a triangular pyramid).
* VTK_HEXAHEDRON (12): These are eight-noded hexahedral elements, often called bricks or cubes.
* VTK_WEDGE (13): These are six-noded wedge or triangular prism elements.
* VTK_PYRAMID (14): These are five-noded pyramids with a quadrilateral base.
* VTK_PENTAGONAL_PRISM (15): These are ten-noded prisms with a pentagonal base.
* VTK_HEXAGONAL_PRISM (16): These are twelve-noded prisms with a hexagonal base.
* VTK_POLYHEDRON (42): Corresponds to Polyhedron as well as HeptagonalPrism, OctagonalPrism, NonagonalPrism, DecagonalPrism, and HendecagonalPrism. This is a general-purpose 3D cell type for arbitrary polyhedra not covered by the other specific types.

I/O
---

* **Input**: vtkUnstructuredGrid
* **Output**: vtkUnstructuredGrid with optional arrays marking problematic elements
* **Additional Data**: When painting is enabled, adds "WrongSupportElements" array to cell data

See Also
--------

* :doc:`AllChecks <Checks>` - Includes supported-elements check among others