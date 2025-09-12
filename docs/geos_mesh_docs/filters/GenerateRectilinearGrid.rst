GenerateRectilinearGrid Filter
==============================

.. automodule:: geos.mesh.doctor.filters.GenerateRectilinearGrid
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The GenerateRectilinearGrid filter creates simple rectilinear (structured) grids as vtkUnstructuredGrid objects. This filter is useful for generating regular meshes for testing, validation, or as starting points for more complex mesh generation workflows.

Features
--------

* Generation of 3D rectilinear grids with customizable dimensions
* Flexible block-based coordinate specification
* Variable element density per block
* Optional global ID generation for points and cells
* Customizable field generation with arbitrary dimensions
* Direct mesh generation without input requirements

Usage Example
-------------

.. code-block:: python

    from geos.mesh.doctor.filters.GenerateRectilinearGrid import GenerateRectilinearGrid
    from geos.mesh.doctor.actions.generate_cube import FieldInfo

    # Instantiate the filter
    generateRectilinearGridFilter = GenerateRectilinearGrid()

    # Set the coordinates of each block border for the X, Y and Z axis
    generateRectilinearGridFilter.setCoordinates([0.0, 5.0, 10.0], [0.0, 5.0, 10.0], [0.0, 10.0])

    # For each block defined, specify the number of cells that they should contain in the X, Y, Z axis
    generateRectilinearGridFilter.setNumberElements([5, 5], [5, 5], [10])

    # To add the GlobalIds for cells and points, set to True the generate global ids options
    generateRectilinearGridFilter.setGenerateCellsGlobalIds(True)
    generateRectilinearGridFilter.setGeneratePointsGlobalIds(True)

    # To create new arrays with a specific dimension, you can use the following commands
    cells_dim1 = FieldInfo("cell1", 1, "CELLS")  # array "cell1" of shape (number of cells, 1)
    cells_dim3 = FieldInfo("cell3", 3, "CELLS")  # array "cell3" of shape (number of cells, 3)
    points_dim1 = FieldInfo("point1", 1, "POINTS")  # array "point1" of shape (number of points, 1)
    points_dim3 = FieldInfo("point3", 3, "POINTS")  # array "point3" of shape (number of points, 3)
    generateRectilinearGridFilter.setFields([cells_dim1, cells_dim3, points_dim1, points_dim3])

    # Then, to obtain the constructed mesh out of all these operations, 2 solutions are available

    # Solution1 (recommended)
    mesh = generateRectilinearGridFilter.getGrid()

    # Solution2 (manual)
    generateRectilinearGridFilter.Update()
    mesh = generateRectilinearGridFilter.GetOutputDataObject(0)

    # Finally, you can write the mesh at a specific destination with:
    generateRectilinearGridFilter.writeGrid("output/filepath/of/your/grid.vtu")

Parameters
----------

setCoordinates(coordsX, coordsY, coordsZ)
    Set the coordinates that define block boundaries along each axis.
    
    * **coordsX** (Sequence[float]): X-coordinates of block boundaries
    * **coordsY** (Sequence[float]): Y-coordinates of block boundaries  
    * **coordsZ** (Sequence[float]): Z-coordinates of block boundaries

setNumberElements(numberElementsX, numberElementsY, numberElementsZ)
    Set the number of elements in each block along each axis.
    
    * **numberElementsX** (Sequence[int]): Number of elements in each X-block
    * **numberElementsY** (Sequence[int]): Number of elements in each Y-block
    * **numberElementsZ** (Sequence[int]): Number of elements in each Z-block

setGenerateCellsGlobalIds(generate)
    Enable/disable generation of global cell IDs.
    
    * **generate** (bool): True to generate global cell IDs

setGeneratePointsGlobalIds(generate)
    Enable/disable generation of global point IDs.
    
    * **generate** (bool): True to generate global point IDs

setFields(fields)
    Specify additional cell or point arrays to be added to the grid.
    
    * **fields** (Iterable[FieldInfo]): List of field specifications

Field Specification
-------------------

Fields are specified using FieldInfo objects:

.. code-block:: python

    from geos.mesh.doctor.actions.generate_cube import FieldInfo
    
    # Create a field specification
    field = FieldInfo(name, dimension, location)

**Parameters:**

* **name** (str): Name of the array
* **dimension** (int): Number of components (1 for scalars, 3 for vectors, etc.)
* **location** (str): "CELLS" for cell data, "POINTS" for point data

**Examples:**

.. code-block:: python

    # Scalar cell field
    pressure = FieldInfo("pressure", 1, "CELLS")
    
    # Vector point field
    velocity = FieldInfo("velocity", 3, "POINTS")
    
    # Tensor cell field
    stress = FieldInfo("stress", 6, "CELLS")  # 6 components for symmetric tensor

Grid Construction Logic
-----------------------

**Coordinate Specification**

Coordinates define block boundaries. For example:

.. code-block:: python

    coordsX = [0.0, 5.0, 10.0]  # Creates 2 blocks in X: [0,5] and [5,10]
    numberElementsX = [5, 10]   # 5 elements in first block, 10 in second

**Element Distribution**

Each block can have different element densities:

* Block 1: 5 elements distributed uniformly in [0.0, 5.0]
* Block 2: 10 elements distributed uniformly in [5.0, 10.0]

**Total Grid Size**

* Total elements: numberElementsX[0] × numberElementsY[0] × numberElementsZ[0] + ... (for each block combination)
* Total points: (sum(numberElementsX) + len(numberElementsX)) × (sum(numberElementsY) + len(numberElementsY)) × (sum(numberElementsZ) + len(numberElementsZ))

Example: Multi-Block Grid
-------------------------

.. code-block:: python

    # Create a grid with 3 blocks in X, 2 in Y, 1 in Z
    filter = GenerateRectilinearGrid()
    
    # Define block boundaries
    filter.setCoordinates(
        [0.0, 1.0, 3.0, 5.0],  # 3 blocks: [0,1], [1,3], [3,5]
        [0.0, 2.0, 4.0],       # 2 blocks: [0,2], [2,4]
        [0.0, 1.0]             # 1 block: [0,1]
    )
    
    # Define element counts per block
    filter.setNumberElements(
        [10, 20, 10],  # 10, 20, 10 elements in X blocks
        [15, 15],      # 15, 15 elements in Y blocks
        [5]            # 5 elements in Z block
    )
    
    # Add global IDs and custom fields
    filter.setGenerateCellsGlobalIds(True)
    filter.setGeneratePointsGlobalIds(True)
    
    material_id = FieldInfo("material", 1, "CELLS")
    coordinates = FieldInfo("coords", 3, "POINTS")
    filter.setFields([material_id, coordinates])
    
    # Generate the grid
    mesh = filter.getGrid()

Output
------

* **Input**: None (generator filter)
* **Output**: vtkUnstructuredGrid with hexahedral elements
* **Additional Arrays**: 
  
  * Global IDs (if enabled)
  * Custom fields (if specified)
  * All arrays filled with constant value 1.0

Use Cases
---------

* **Testing**: Create simple grids for algorithm testing
* **Validation**: Generate known geometries for code validation
* **Prototyping**: Quick mesh generation for initial simulations
* **Benchmarking**: Standard grids for performance testing
* **Education**: Simple examples for learning mesh-based methods

Best Practices
--------------

* Start with simple single-block grids before using multi-block configurations
* Ensure coordinate sequences are monotonically increasing
* Match the length of numberElements arrays with coordinate block counts
* Use meaningful field names for better mesh organization
* Enable global IDs when mesh will be used in parallel computations

See Also
--------

* :doc:`GenerateFractures <GenerateFractures>` - Advanced mesh modification
* :doc:`ElementVolumes <ElementVolumes>` - Quality assessment for generated meshes
* :doc:`AllChecks <AllChecks>` - Comprehensive validation of generated meshes
