Mesh Doctor Filters
===================

The mesh doctor filters provide VTK-based tools for mesh quality assessment, validation, and processing. All filters work with vtkUnstructuredGrid data and follow a consistent interface pattern.

Quality Assessment Filters
--------------------------

These filters analyze existing meshes for various quality issues and geometric problems.

.. toctree::
   :maxdepth: 1

   AllChecks
   MainChecks
   CollocatedNodes
   ElementVolumes
   SelfIntersectingElements
   NonConformal

Mesh Generation Filters
-----------------------

These filters create new meshes from scratch or modify existing meshes.

.. toctree::
   :maxdepth: 1

   GenerateRectilinearGrid
   GenerateFractures

Processing Filters
------------------

These filters perform specialized processing and validation tasks.

.. toctree::
   :maxdepth: 1

   SupportedElements

Common Usage Pattern
====================

All mesh doctor filters follow a consistent usage pattern:

.. code-block:: python

    from geos.mesh.doctor.filters.FilterName import FilterName

    # Instantiate the filter
    filter = FilterName()

    # Configure filter parameters
    filter.setParameter(value)

    # Set input data (for processing filters, not needed for generators)
    filter.SetInputData(mesh)

    # Execute the filter and get output
    output_mesh = filter.getGrid()

    # Access specific results (filter-dependent)
    results = filter.getSpecificResults()

    # Write results to file
    filter.writeGrid("output/result.vtu")

Filter Categories Explained
===========================

Quality Assessment
------------------

**Purpose**: Identify mesh quality issues, geometric problems, and topology errors

**When to use**: 
- Before running simulations
- After mesh generation or modification
- During mesh debugging
- For mesh quality reporting

**Key filters**:
- **AllChecks/MainChecks**: Comprehensive validation suites
- **CollocatedNodes**: Duplicate node detection
- **ElementVolumes**: Volume validation
- **SelfIntersectingElements**: Geometric integrity
- **NonConformal**: Interface validation

Mesh Generation
---------------

**Purpose**: Create new meshes or modify existing ones

**When to use**:
- Creating test meshes
- Generating simple geometries
- Adding fractures to existing meshes
- Prototyping mesh-based algorithms

**Key filters**:
- **GenerateRectilinearGrid**: Simple structured grids
- **GenerateFractures**: Fracture network generation

Processing
----------

**Purpose**: Specialized mesh processing and validation

**When to use**:
- Validating element type compatibility
- Preparing meshes for specific solvers
- Advanced geometric analysis

**Key filters**:
- **SupportedElements**: GEOS compatibility validation

Quick Reference
===============

Filter Selection Guide
----------------------

**For routine mesh validation**:
   Use :doc:`MainChecks <MainChecks>` for fast, essential checks

**For comprehensive analysis**:
   Use :doc:`AllChecks <AllChecks>` for detailed validation

**For specific problems**:
   - Duplicate nodes → :doc:`CollocatedNodes <CollocatedNodes>`
   - Negative volumes → :doc:`ElementVolumes <ElementVolumes>`
   - Invalid geometry → :doc:`SelfIntersectingElements <SelfIntersectingElements>`
   - Interface issues → :doc:`NonConformal <NonConformal>`

**For mesh generation**:
   - Simple grids → :doc:`GenerateRectilinearGrid <GenerateRectilinearGrid>`
   - Fracture networks → :doc:`GenerateFractures <GenerateFractures>`

**For compatibility checking**:
   - GEOS support → :doc:`SupportedElements <SupportedElements>`

Parameter Guidelines
--------------------

**Tolerance Parameters**:
   - High precision meshes: 1e-12 to 1e-8
   - Standard meshes: 1e-8 to 1e-6  
   - Coarse meshes: 1e-6 to 1e-4

**Painting Options**:
   - Enable (1) for visualization in ParaView
   - Disable (0) for performance in batch processing

**Output Modes**:
   - Binary for large meshes and performance
   - ASCII for debugging and text processing

Best Practices
==============

Workflow Integration
--------------------

1. **Start with quality assessment** using MainChecks or AllChecks
2. **Address specific issues** with targeted filters
3. **Validate fixes** by re-running quality checks
4. **Document mesh quality** for simulation reference

Performance Considerations
--------------------------

- Use appropriate tolerances (not unnecessarily strict)
- Enable painting only when needed for visualization
- Use binary output for large meshes
- Run comprehensive checks during development, lighter checks in production

Error Handling
--------------

- Check filter results before proceeding with simulations
- Save problematic meshes for debugging
- Document known issues and their acceptable thresholds
- Use multiple validation approaches for critical applications

See Also
========

- **GEOS Documentation**: Supported element types and mesh requirements
- **VTK Documentation**: VTK data formats and cell types  
- **ParaView**: Visualization of mesh quality results
- **Mesh Generation Tools**: Creating high-quality input meshes
