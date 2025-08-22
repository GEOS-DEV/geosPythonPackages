GenerateFractures Filter
========================

.. automodule:: geos.mesh.doctor.filters.GenerateFractures
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The GenerateFractures filter splits a vtkUnstructuredGrid along non-embedded fractures. When a fracture plane is defined between two cells, the nodes of the shared face are duplicated to create a discontinuity. The filter generates both the split main mesh and separate fracture meshes.

Features
--------

* Mesh splitting along fracture planes with node duplication
* Multiple fracture policy support (internal vs boundary fractures)
* Configurable fracture identification via field values
* Generation of separate fracture mesh outputs
* Flexible output data modes (ASCII/binary)
* Automatic fracture mesh file management

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.GenerateFractures import GenerateFractures

    # Instantiate the filter
    generateFracturesFilter = GenerateFractures()

    # Set the field name that defines fracture regions
    generateFracturesFilter.setFieldName("fracture_field")

    # Set the field values that identify fracture boundaries
    generateFracturesFilter.setFieldValues("1,2")  # comma-separated values

    # Set fracture policy (0 for internal fractures, 1 for boundary fractures)
    generateFracturesFilter.setPolicy(1)

    # Set output directory for fracture meshes
    generateFracturesFilter.setFracturesOutputDirectory("./fractures/")

    # Optionally set data mode (0 for ASCII, 1 for binary)
    generateFracturesFilter.setOutputDataMode(1)
    generateFracturesFilter.setFracturesDataMode(1)

    # Set input mesh
    generateFracturesFilter.SetInputData(mesh)

    # Execute the filter
    generateFracturesFilter.Update()

    # Get the split mesh and fracture meshes
    split_mesh, fracture_meshes = generateFracturesFilter.getAllGrids()

    # Write all meshes
    generateFracturesFilter.writeMeshes("output/split_mesh.vtu", is_data_mode_binary=True)

Parameters
----------

setFieldName(field_name)
    Set the name of the cell data field that defines fracture regions.
    
    * **field_name** (str): Name of the field in cell data

setFieldValues(field_values)
    Set the field values that identify fracture boundaries.
    
    * **field_values** (str): Comma-separated list of values (e.g., "1,2,3")

setPolicy(choice)
    Set the fracture generation policy.
    
    * **choice** (int): 
      
      * 0: Internal fractures policy
      * 1: Boundary fractures policy

setFracturesOutputDirectory(directory)
    Set the output directory for individual fracture mesh files.
    
    * **directory** (str): Path to output directory

setOutputDataMode(choice)
    Set the data format for the main output mesh.
    
    * **choice** (int):
      
      * 0: ASCII format
      * 1: Binary format

setFracturesDataMode(choice)
    Set the data format for fracture mesh files.
    
    * **choice** (int):
      
      * 0: ASCII format
      * 1: Binary format

Fracture Policies
-----------------

**Internal Fractures Policy (0)**

* Creates fractures within the mesh interior
* Duplicates nodes at internal interfaces
* Suitable for modeling embedded fracture networks

**Boundary Fractures Policy (1)**

* Creates fractures at mesh boundaries
* Handles fractures that extend to domain edges
* Suitable for modeling fault systems extending beyond the domain

Results Access
--------------

getAllGrids()
    Returns both the split mesh and individual fracture meshes.
    
    * **Returns**: tuple (split_mesh, fracture_meshes)
      
      * **split_mesh**: vtkUnstructuredGrid - Main mesh with fractures applied
      * **fracture_meshes**: list[vtkUnstructuredGrid] - Individual fracture surfaces

writeMeshes(filepath, is_data_mode_binary, canOverwrite)
    Write all generated meshes to files.
    
    * **filepath** (str): Path for main split mesh
    * **is_data_mode_binary** (bool): Use binary format
    * **canOverwrite** (bool): Allow overwriting existing files

Understanding Fracture Generation
---------------------------------

**Input Requirements**

1. **Fracture Field**: Cell data array identifying regions separated by fractures
2. **Field Values**: Specific values indicating fracture boundaries
3. **Policy**: How to handle fracture creation

**Process**

1. **Identification**: Find interfaces between cells with different field values
2. **Node Duplication**: Create separate nodes for each side of the fracture
3. **Mesh Splitting**: Update connectivity to use duplicated nodes
4. **Fracture Extraction**: Generate separate meshes for fracture surfaces

**Output Structure**

* **Split Mesh**: Original mesh with fractures as discontinuities
* **Fracture Meshes**: Individual surface meshes for each fracture

Common Use Cases
----------------

* **Geomechanics**: Modeling fault systems in geological domains
* **Fluid Flow**: Creating discrete fracture networks
* **Contact Mechanics**: Preparing meshes for contact simulations
* **Multi-physics**: Coupling different physics across fracture interfaces

Example Workflow
----------------

.. code-block:: python

    # Complete fracture generation workflow
    fracture_filter = GenerateFractures()
    
    # Configure fracture detection
    fracture_filter.setFieldName("material_id")
    fracture_filter.setFieldValues("1,2")  # Fracture between materials 1 and 2
    fracture_filter.setPolicy(1)  # Boundary fractures
    
    # Configure output
    fracture_filter.setFracturesOutputDirectory("./fractures/")
    fracture_filter.setOutputDataMode(1)  # Binary for efficiency
    fracture_filter.setFracturesDataMode(1)
    
    # Process mesh
    fracture_filter.SetInputData(original_mesh)
    fracture_filter.Update()
    
    # Get results
    split_mesh, fracture_surfaces = fracture_filter.getAllGrids()
    
    print(f"Generated {len(fracture_surfaces)} fracture surfaces")
    
    # Write all outputs
    fracture_filter.writeMeshes("output/domain_with_fractures.vtu")

Output
------

* **Input**: vtkUnstructuredGrid with fracture identification field
* **Outputs**: 
  
  * Split mesh with fractures as discontinuities
  * Individual fracture surface meshes
* **File Output**: Automatic writing of fracture meshes to specified directory

Best Practices
--------------

* Ensure fracture field values are properly assigned to cells
* Use appropriate policy based on fracture geometry
* Check that fractures form continuous surfaces
* Verify mesh quality after fracture generation
* Use binary format for large meshes to improve I/O performance

See Also
--------

* :doc:`GenerateRectilinearGrid <GenerateRectilinearGrid>` - Basic mesh generation
* :doc:`CollocatedNodes <CollocatedNodes>` - May be needed after fracture generation
* :doc:`ElementVolumes <ElementVolumes>` - Quality check after splitting
