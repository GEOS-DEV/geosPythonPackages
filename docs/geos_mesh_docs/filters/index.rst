Mesh Doctor Filters
===================

The mesh doctor filters provide VTK-based tools for mesh quality assessment, validation, and processing. All filters work with vtkUnstructuredGrid data and follow a consistent interface pattern.

Quality Assessment Filters
--------------------------

These filters analyze existing meshes for various quality issues and geometric problems.

.. toctree::
   :maxdepth: 1

   Checks
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

**For mesh validation**:
   Use :doc:`MainChecks <Checks>` for fast, essential checks

**For comprehensive analysis**:
   Use :doc:`AllChecks <Checks>` for detailed validation

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

**Painting New Properties**:
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

Error Handling
--------------

- Check filter results before proceeding with simulations
- Save problematic meshes for debugging
- Document known issues and their acceptable thresholds
- Use multiple validation approaches for critical applications

Base Classes
============

The fundamental base classes that all mesh doctor filters inherit from.

.. toctree::
   :maxdepth: 1

   MeshDoctorFilterBase

See Also
========

- **GEOS Documentation**: Supported element types and mesh requirements
- **VTK Documentation**: VTK data formats and cell types
- **ParaView**: Visualization of mesh quality results