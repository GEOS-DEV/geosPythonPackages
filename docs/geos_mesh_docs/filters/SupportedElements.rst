SupportedElements Filter
========================

.. automodule:: geos.mesh.doctor.filters.SupportedElements
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The SupportedElements filter identifies unsupported element types and problematic polyhedron elements in a vtkUnstructuredGrid. It validates that all elements in the mesh are supported by GEOS and checks polyhedron elements for geometric correctness.

.. note::
   This filter is currently disabled due to multiprocessing requirements that are incompatible with the VTK filter framework. The implementation exists but is commented out in the source code.

Features (When Available)
-------------------------

* Detection of unsupported VTK element types
* Validation of polyhedron element geometry
* Optional marking of unsupported elements in output mesh
* Integration with parallel processing for large meshes
* Detailed reporting of element type compatibility

Intended Usage Example
----------------------

.. code-block:: python

    from geos.mesh.doctor.filters.SupportedElements import SupportedElements

    # Instantiate the filter
    supportedElementsFilter = SupportedElements()

    # Optionally enable painting of unsupported element types
    supportedElementsFilter.setPaintUnsupportedElementTypes(1)  # 1 to enable, 0 to disable

    # Set input mesh
    supportedElementsFilter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = supportedElementsFilter.getGrid()

    # Get unsupported elements
    unsupported_elements = supportedElementsFilter.getUnsupportedElements()

    # Write the output mesh
    supportedElementsFilter.writeGrid("output/mesh_with_support_info.vtu")

GEOS Supported Element Types
----------------------------

GEOS supports the following VTK element types:

**Standard Elements**

* **VTK_VERTEX** (1): Point elements
* **VTK_LINE** (3): Line segments  
* **VTK_TRIANGLE** (5): Triangular elements
* **VTK_QUAD** (9): Quadrilateral elements
* **VTK_TETRA** (10): Tetrahedral elements
* **VTK_HEXAHEDRON** (12): Hexahedral (brick) elements
* **VTK_WEDGE** (13): Wedge/prism elements
* **VTK_PYRAMID** (14): Pyramid elements

**Higher-Order Elements**

* **VTK_QUADRATIC_TRIANGLE** (22): 6-node triangles
* **VTK_QUADRATIC_QUAD** (23): 8-node quadrilaterals
* **VTK_QUADRATIC_TETRA** (24): 10-node tetrahedra
* **VTK_QUADRATIC_HEXAHEDRON** (25): 20-node hexahedra

**Special Elements**

* **VTK_POLYHEDRON** (42): General polyhedra (with validation)

Unsupported Element Types
-------------------------

Elements not supported by GEOS include:

* **VTK_PIXEL** (8): Axis-aligned rectangles
* **VTK_VOXEL** (11): Axis-aligned boxes
* **VTK_PENTAGONAL_PRISM** (15): 5-sided prisms
* **VTK_HEXAGONAL_PRISM** (16): 6-sided prisms
* Various specialized or experimental VTK cell types

Polyhedron Validation
---------------------

For polyhedron elements (VTK_POLYHEDRON), additional checks are performed:

**Geometric Validation**

* Face planarity
* Edge connectivity
* Volume calculation
* Normal consistency

**Topological Validation**

* Manifold surface verification
* Closed surface check
* Face orientation consistency

**Quality Checks**

* Aspect ratio limits
* Volume positivity
* Face area positivity

Common Issues and Solutions
---------------------------

**Unsupported Standard Elements**

* **Problem**: Mesh contains VTK_PIXEL or VTK_VOXEL elements
* **Solution**: Convert to VTK_QUAD or VTK_HEXAHEDRON respectively
* **Tools**: VTK conversion filters or mesh processing software

**Invalid Polyhedra**

* **Problem**: Non-manifold or self-intersecting polyhedra
* **Solution**: Use mesh repair tools or regenerate with better quality settings
* **Prevention**: Validate polyhedra during mesh generation

**Mixed Element Types**

* **Problem**: Mesh contains both supported and unsupported elements
* **Solution**: Selective element type conversion or mesh region separation

Current Status and Alternatives
-------------------------------

**Why Disabled**

The SupportedElements filter requires multiprocessing capabilities for efficient polyhedron validation on large meshes. However, the VTK Python filter framework doesn't integrate well with multiprocessing, leading to:

* Process spawning issues
* Memory management problems
* Inconsistent results across platforms

**Alternative Approaches**

1. **Command-Line Tool**: Use the ``mesh-doctor supported_elements`` command instead
2. **Direct Function Calls**: Import and use the underlying functions directly
3. **Manual Validation**: Check element types programmatically

**Command-Line Alternative**

.. code-block:: bash

    # Use mesh-doctor command line tool instead
    mesh-doctor -i input_mesh.vtu supported_elements --help

**Direct Function Usage**

.. code-block:: python

    from geos.mesh.doctor.actions.supported_elements import (
        find_unsupported_std_elements_types,
        find_unsupported_polyhedron_elements
    )
    
    # Direct function usage (not as VTK filter)
    unsupported_std = find_unsupported_std_elements_types(mesh)
    # Note: polyhedron validation requires multiprocessing setup

Future Development
------------------

**Planned Improvements**

* Integration with VTK's parallel processing capabilities
* Alternative implementation without multiprocessing dependency
* Better error handling and reporting
* Performance optimizations for large meshes

**Workaround Implementation**

Until the filter is re-enabled, users can:

1. Use the command-line interface
2. Implement custom validation loops
3. Use external mesh validation tools
4. Perform validation in separate processes

Example Manual Validation
-------------------------

.. code-block:: python

    import vtk
    
    def check_supported_elements(mesh):
        """Manual check for supported element types."""
        supported_types = {
            vtk.VTK_VERTEX, vtk.VTK_LINE, vtk.VTK_TRIANGLE, vtk.VTK_QUAD,
            vtk.VTK_TETRA, vtk.VTK_HEXAHEDRON, vtk.VTK_WEDGE, vtk.VTK_PYRAMID,
            vtk.VTK_QUADRATIC_TRIANGLE, vtk.VTK_QUADRATIC_QUAD,
            vtk.VTK_QUADRATIC_TETRA, vtk.VTK_QUADRATIC_HEXAHEDRON,
            vtk.VTK_POLYHEDRON
        }
        
        unsupported = []
        for i in range(mesh.GetNumberOfCells()):
            cell_type = mesh.GetCellType(i)
            if cell_type not in supported_types:
                unsupported.append((i, cell_type))
        
        return unsupported
    
    # Usage
    unsupported_elements = check_supported_elements(mesh)
    if unsupported_elements:
        print(f"Found {len(unsupported_elements)} unsupported elements")
        for cell_id, cell_type in unsupported_elements[:5]:
            print(f"  Cell {cell_id}: type {cell_type}")

See Also
--------

* :doc:`AllChecks <AllChecks>` - Would include supported elements check when available
* :doc:`SelfIntersectingElements <SelfIntersectingElements>` - Related geometric validation
* :doc:`ElementVolumes <ElementVolumes>` - Basic element validation
* GEOS documentation on supported element types
* VTK documentation on cell types
