GenerateFractures Filter
========================

.. automodule:: geos.mesh.doctor.filters.GenerateFractures
   :members:
   :undoc-members:
   :show-inheritance:

Fracture Policies
-----------------

**Field Fractures Policy (field)**

| Obtained by setting ``--policy field``.
|
| Creates fractures by using internal interfaces between cells regions.
| These interfaces corresponds to a change in the values of a CellData array stored in your mesh.
| Suppose you have a CellData array named "Regions" with 3 different values indicating geological layers. 1 is caprock, 2 is reservoir, and 3 is underburden as represented here (below is a 2D representation along Z for simplicity):
|
| 111111111111111111
| 111111222222222222
| 222222222223333333
| 333333333333333333
|
| In this example, I define the interface between reservoir and caprock as a fracture, and the interface between reservoir and underburden as another fracture.
| So when specifying your field values as ``--values 1,2:2,3``, the filter will create a fracture along the interface between these two regions. The result will be a new mesh with the fracture represented as a separate entity. The nodes will be split along these interfaces, allowing for discontinuities in the mesh:
|
| 111111111111111111
| 111111------------
| ------222222222222
| 22222222222+++++++
| +++++++++++3333333
| 333333333333333333
|
| with ``----`` representing the first fracture and ``+++++++`` representing the second fracture.

**Internal Fractures Policy (internal_surfaces)**

| Obtained by setting ``--policy internal_surfaces``.
|
| Creates fractures by using tagged 2D cells that are identified as a fracture.
| In VTK, ``2D cells`` are refering to ``VTK_TRIANGLE`` or ``VTK_QUAD`` cell types.
| These 2D cells should be part of the input mesh and tagged with a specific CellData array value.
| Suppose you have a CellData array named "isFault" with 3 different values to tag fractures. 0 is for all non fault cells, 1 is fault1, and 2 is fault2 as represented here (below is a 2D representation along Z for simplicity):
|
| 000000000000000000
| 000000111111111111
| 111111000000000000
| 000000000002222222
| 222222222220000000
| 000000000000000000
|
| So when specifying your field values as ``--values 1:2``, the filter will create one fracture for each cells tagged with 1 and 2.

Understanding Fracture Generation
---------------------------------

**Process**

1. **Identification**: Find interfaces between cells with different field values
2. **Node Duplication**: Create separate nodes for each side of the fracture
3. **Mesh Splitting**: Update connectivity to use duplicated nodes
4. **Fracture Extraction**: Generate separate meshes for fracture surfaces

**Output Structure**

* **Split Mesh**: Original mesh with fractures as discontinuities
* **Fracture Meshes**: Individual surface meshes for each fracture

I/O
---

* **Input**: vtkUnstructuredGrid with fracture identification field or tagged 2D cells
* **Outputs**: 
  
  * Split mesh with fractures as discontinuities
  * Individual fracture surface meshes
* **File Output**: Automatic writing of fracture meshes to specified directory
