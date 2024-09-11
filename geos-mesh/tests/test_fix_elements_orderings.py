import os
import re
import pytest
import logging
import subprocess
import numpy as np
from geos.mesh.doctor.mesh_doctor import MESH_DOCTOR_FILEPATH
from geos.mesh.doctor.checks import fix_elements_orderings as feo
from geos.mesh.doctor.checks.generate_cube import Options, __build
from geos.mesh.doctor.checks.vtk_utils import ( VtkOutput, to_vtk_id_list, write_mesh )
from geos.mesh.doctor.checks.fix_elements_orderings import Options as opt, VTK_TYPE_TO_NAME
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkUnstructuredGrid,
    vtkCellArray,
    vtkHexahedron,
    vtkTetra,
    vtkPyramid,
    vtkVoxel,
    vtkWedge,
    vtkPentagonalPrism,
    vtkHexagonalPrism,
    VTK_HEXAHEDRON,
    VTK_TETRA,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_VOXEL,
    VTK_PENTAGONAL_PRISM,
    VTK_HEXAGONAL_PRISM
)


def reorder_cell_nodes( mesh: vtkDataSet, cell_id: int, node_ordering: list[ int ] ):
    """Utility function to reorder the nodes of one cell for test purposes.

    Args:
        mesh (vtkDataSet): A vtk grid.
        cell_id (int): Cell id to identify the cell which will be modified.
        node_ordering (list[ int ]): Nodes id ordering to construct a cell.
    """
    if mesh.GetCell( cell_id ).GetNumberOfPoints() != len( node_ordering ):
        raise ValueError( f"The cell to reorder needs to have '{mesh.GetCell( cell_id ).GetNumberOfPoints()}'" +
                          "nodes in reordering." )
    cells = mesh.GetCells()
    support_point_ids = vtkIdList()
    cells.GetCellAtId( cell_id, support_point_ids )
    new_support_point_ids = []
    node_ordering: list[ int ] = node_ordering
    for i in range( len( node_ordering ) ):
        new_support_point_ids.append( support_point_ids.GetId( node_ordering[ i ] ) )
    cells.ReplaceCellAtId( cell_id, to_vtk_id_list( new_support_point_ids ) )


"""
For creation of output test meshes
"""
current_file_path: str = __file__
dir_name: str = os.path.dirname( current_file_path )
filepath_non_ordered_mesh: str = os.path.join( dir_name, "to_reorder_mesh.vtu" )
filepath_reordered_mesh: str = os.path.join( dir_name, "reordered_mesh.vtu" )
test_file: VtkOutput = VtkOutput( filepath_non_ordered_mesh, True )
"""
Dict used to apply false nodes orderings for test purposes
"""
to_change_order: dict[ int, list[ int ] ] = {
    "Hexahedron": [ 0, 3, 2, 1, 4, 5, 6, 7 ],
    "Tetrahedron": [ 0, 2, 1, 3 ],
    "Pyramid": [ 0, 3, 2, 1, 4 ],
    "Wedge": [ 0, 2, 1, 3, 4, 5 ],
    "Prism5": [ 0, 4, 3, 2, 1, 5, 6, 7, 8, 9 ],
    "Prism6": [ 0, 1, 4, 2, 3, 5, 11, 10, 9, 8, 7, 6 ]
}
to_change_order = dict( sorted( to_change_order.items() ) )
"""
1 Hexahedron: no invalid ordering
"""
out: VtkOutput = VtkOutput( "test", False )
options_one_hex: Options = Options( vtk_output=out,
                                    generate_cells_global_ids=False,
                                    generate_points_global_ids=False,
                                    xs=np.array( [ 0.0, 1.0 ] ),
                                    ys=np.array( [ 0.0, 1.0 ] ),
                                    zs=np.array( [ 0.0, 1.0 ] ),
                                    nxs=[ 1 ],
                                    nys=[ 1 ],
                                    nzs=[ 1 ],
                                    fields=[] )
one_hex: vtkDataSet = __build( options_one_hex )
"""
4 Hexahedrons: no invalid ordering
"""
out: VtkOutput = VtkOutput( "test", False )
options_hexahedrons_grid: Options = Options( vtk_output=out,
                                             generate_cells_global_ids=False,
                                             generate_points_global_ids=False,
                                             xs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                             ys=np.array( [ 0.0, 1.0, 2.0 ] ),
                                             zs=np.array( [ 0.0, 1.0 ] ),
                                             nxs=[ 1, 1 ],
                                             nys=[ 1, 1 ],
                                             nzs=[ 1 ],
                                             fields=[] )
hexahedrons_grid: vtkDataSet = __build( options_hexahedrons_grid )
"""
4 Hexahedrons: 2 Hexahedrons with invalid ordering
"""
hexahedrons_grid_invalid: vtkDataSet = __build( options_hexahedrons_grid )
for i in range( 2 ):
    reorder_cell_nodes( hexahedrons_grid_invalid, i * 2 + 1, to_change_order[ "Hexahedron" ] )
"""
4 tetrahedrons
"""
points_tetras: vtkPoints = vtkPoints()
points_tetras_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ),
                                                 ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ) ]
for point_tetra in points_tetras_coords:
    points_tetras.InsertNextPoint( point_tetra )

tetra1: vtkTetra = vtkTetra()
tetra1.GetPointIds().SetId( 0, 3 )
tetra1.GetPointIds().SetId( 1, 0 )
tetra1.GetPointIds().SetId( 2, 1 )
tetra1.GetPointIds().SetId( 3, 4 )

tetra2: vtkTetra = vtkTetra()
tetra2.GetPointIds().SetId( 0, 6 )
tetra2.GetPointIds().SetId( 1, 5 )
tetra2.GetPointIds().SetId( 2, 4 )
tetra2.GetPointIds().SetId( 3, 1 )

tetra3: vtkTetra = vtkTetra()
tetra3.GetPointIds().SetId( 0, 1 )
tetra3.GetPointIds().SetId( 1, 2 )
tetra3.GetPointIds().SetId( 2, 3 )
tetra3.GetPointIds().SetId( 3, 6 )

tetra4: vtkTetra = vtkTetra()
tetra4.GetPointIds().SetId( 0, 4 )
tetra4.GetPointIds().SetId( 1, 7 )
tetra4.GetPointIds().SetId( 2, 6 )
tetra4.GetPointIds().SetId( 3, 3 )

tetras_cells: vtkCellArray = vtkCellArray()
tetras_cells.InsertNextCell( tetra1 )
tetras_cells.InsertNextCell( tetra2 )
tetras_cells.InsertNextCell( tetra3 )
tetras_cells.InsertNextCell( tetra4 )

tetras_grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
tetras_grid.SetPoints( points_tetras )
tetras_grid.SetCells( VTK_TETRA, tetras_cells )

# one of every other wedge has invalid ordering
tetras_grid_invalid = vtkUnstructuredGrid()
tetras_grid_invalid.DeepCopy( tetras_grid )
for i in range( 2 ):
    reorder_cell_nodes( tetras_grid_invalid, i * 2 + 1, to_change_order[ "Tetrahedron" ] )
"""
4 pyramids
"""
points_pyramids: vtkPoints = vtkPoints()
points_pyramids_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ),
                                                   ( 0.0, 1.0, 0.0 ), ( 0.5, 0.5, 1.0 ), ( 2.0, 0.0, 0.0 ),
                                                   ( 3.0, 0.0, 0.0 ), ( 3.0, 1.0, 0.0 ), ( 2.0, 1.0, 0.0 ),
                                                   ( 2.5, 0.5, 1.0 ), ( 0.0, 2.0, 0.0 ), ( 1.0, 2.0, 0.0 ),
                                                   ( 1.0, 3.0, 0.0 ), ( 0.0, 3.0, 0.0 ), ( 0.5, 2.5, 1.0 ),
                                                   ( 2.0, 2.0, 0.0 ), ( 3.0, 2.0, 0.0 ), ( 3.0, 3.0, 0.0 ),
                                                   ( 2.0, 3.0, 0.0 ), ( 2.5, 2.5, 1.0 ) ]
for point_pyramid in points_pyramids_coords:
    points_pyramids.InsertNextPoint( point_pyramid )

pyramid1: vtkPyramid = vtkPyramid()
pyramid1.GetPointIds().SetId( 0, 0 )
pyramid1.GetPointIds().SetId( 1, 1 )
pyramid1.GetPointIds().SetId( 2, 2 )
pyramid1.GetPointIds().SetId( 3, 3 )
pyramid1.GetPointIds().SetId( 4, 4 )

pyramid2: vtkPyramid = vtkPyramid()
pyramid2.GetPointIds().SetId( 0, 5 )
pyramid2.GetPointIds().SetId( 1, 6 )
pyramid2.GetPointIds().SetId( 2, 7 )
pyramid2.GetPointIds().SetId( 3, 8 )
pyramid2.GetPointIds().SetId( 4, 9 )

pyramid3: vtkPyramid = vtkPyramid()
pyramid3.GetPointIds().SetId( 0, 10 )
pyramid3.GetPointIds().SetId( 1, 11 )
pyramid3.GetPointIds().SetId( 2, 12 )
pyramid3.GetPointIds().SetId( 3, 13 )
pyramid3.GetPointIds().SetId( 4, 14 )

pyramid4: vtkPyramid = vtkPyramid()
pyramid4.GetPointIds().SetId( 0, 15 )
pyramid4.GetPointIds().SetId( 1, 16 )
pyramid4.GetPointIds().SetId( 2, 17 )
pyramid4.GetPointIds().SetId( 3, 18 )
pyramid4.GetPointIds().SetId( 4, 19 )

pyramids_cells: vtkCellArray = vtkCellArray()
pyramids_cells.InsertNextCell( pyramid1 )
pyramids_cells.InsertNextCell( pyramid2 )
pyramids_cells.InsertNextCell( pyramid3 )
pyramids_cells.InsertNextCell( pyramid4 )

pyramids_grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
pyramids_grid.SetPoints( points_pyramids )
pyramids_grid.SetCells( VTK_PYRAMID, pyramids_cells )

# one of every other wedge has invalid ordering
pyramids_grid_invalid = vtkUnstructuredGrid()
pyramids_grid_invalid.DeepCopy( pyramids_grid )
for i in range( 2 ):
    reorder_cell_nodes( pyramids_grid_invalid, i * 2 + 1, to_change_order[ "Pyramid" ] )
"""
4 voxels: this type of element cannot be used in GEOS, we just test that the feature rejects them
"""
points_voxels: vtkPoints = vtkPoints()
points_voxels_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ),
                                                 ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( 2.0, 0.0, 0.0 ),
                                                 ( 3.0, 0.0, 0.0 ), ( 3.0, 1.0, 0.0 ), ( 2.0, 1.0, 0.0 ),
                                                 ( 2.0, 0.0, 1.0 ), ( 3.0, 0.0, 1.0 ), ( 3.0, 1.0, 1.0 ),
                                                 ( 2.0, 1.0, 1.0 ), ( 0.0, 2.0, 0.0 ), ( 1.0, 2.0, 0.0 ),
                                                 ( 1.0, 3.0, 0.0 ), ( 0.0, 3.0, 0.0 ), ( 0.0, 2.0, 1.0 ),
                                                 ( 1.0, 2.0, 1.0 ), ( 1.0, 3.0, 1.0 ), ( 0.0, 3.0, 1.0 ),
                                                 ( 2.0, 2.0, 0.0 ), ( 3.0, 2.0, 0.0 ), ( 3.0, 3.0, 0.0 ),
                                                 ( 2.0, 3.0, 0.0 ), ( 2.0, 2.0, 1.0 ), ( 3.0, 2.0, 1.0 ),
                                                 ( 3.0, 3.0, 1.0 ), ( 2.0, 3.0, 1.0 ) ]
for point_voxel in points_voxels_coords:
    points_voxels.InsertNextPoint( point_voxel )

voxel1: vtkVoxel = vtkVoxel()
voxel1.GetPointIds().SetId( 0, 0 )
voxel1.GetPointIds().SetId( 1, 1 )
voxel1.GetPointIds().SetId( 2, 2 )
voxel1.GetPointIds().SetId( 3, 3 )
voxel1.GetPointIds().SetId( 4, 4 )
voxel1.GetPointIds().SetId( 5, 5 )
voxel1.GetPointIds().SetId( 6, 6 )
voxel1.GetPointIds().SetId( 7, 7 )

voxel2: vtkVoxel = vtkVoxel()
voxel2.GetPointIds().SetId( 0, 8 )
voxel2.GetPointIds().SetId( 1, 9 )
voxel2.GetPointIds().SetId( 2, 10 )
voxel2.GetPointIds().SetId( 3, 11 )
voxel2.GetPointIds().SetId( 4, 12 )
voxel2.GetPointIds().SetId( 5, 13 )
voxel2.GetPointIds().SetId( 6, 14 )
voxel2.GetPointIds().SetId( 7, 15 )

voxel3: vtkVoxel = vtkVoxel()
voxel3.GetPointIds().SetId( 0, 16 )
voxel3.GetPointIds().SetId( 1, 17 )
voxel3.GetPointIds().SetId( 2, 18 )
voxel3.GetPointIds().SetId( 3, 19 )
voxel3.GetPointIds().SetId( 4, 20 )
voxel3.GetPointIds().SetId( 5, 21 )
voxel3.GetPointIds().SetId( 6, 22 )
voxel3.GetPointIds().SetId( 7, 23 )

voxel4: vtkVoxel = vtkVoxel()
voxel4.GetPointIds().SetId( 0, 24 )
voxel4.GetPointIds().SetId( 1, 25 )
voxel4.GetPointIds().SetId( 2, 26 )
voxel4.GetPointIds().SetId( 3, 27 )
voxel4.GetPointIds().SetId( 4, 28 )
voxel4.GetPointIds().SetId( 5, 29 )
voxel4.GetPointIds().SetId( 6, 30 )
voxel4.GetPointIds().SetId( 7, 31 )

voxels_cells: vtkCellArray = vtkCellArray()
voxels_cells.InsertNextCell( voxel1 )
voxels_cells.InsertNextCell( voxel2 )
voxels_cells.InsertNextCell( voxel3 )
voxels_cells.InsertNextCell( voxel4 )

voxels_grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
voxels_grid.SetPoints( points_voxels )
voxels_grid.SetCells( VTK_VOXEL, voxels_cells )
"""
4 wedges
"""
points_wedges: vtkPoints = vtkPoints()
points_wedges_coords: list[ tuple[ float ] ] = [ ( 0.5, 0.0, 0.0 ), ( 1.5, 0.0, 0.0 ), ( 2.5, 0.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 2.0, 1.0, 0.0 ),
                                                 ( 0.5, 0.0, 1.0 ), ( 1.5, 0.0, 1.0 ), ( 2.5, 0.0, 1.0 ),
                                                 ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 2.0, 1.0, 1.0 ) ]
for point_wedge in points_wedges_coords:
    points_wedges.InsertNextPoint( point_wedge )

wedge1: vtkWedge = vtkWedge()
wedge1.GetPointIds().SetId( 0, 9 )
wedge1.GetPointIds().SetId( 1, 6 )
wedge1.GetPointIds().SetId( 2, 10 )
wedge1.GetPointIds().SetId( 3, 3 )
wedge1.GetPointIds().SetId( 4, 0 )
wedge1.GetPointIds().SetId( 5, 4 )

wedge2: vtkWedge = vtkWedge()
wedge2.GetPointIds().SetId( 0, 7 )
wedge2.GetPointIds().SetId( 1, 10 )
wedge2.GetPointIds().SetId( 2, 6 )
wedge2.GetPointIds().SetId( 3, 1 )
wedge2.GetPointIds().SetId( 4, 4 )
wedge2.GetPointIds().SetId( 5, 0 )

wedge3: vtkWedge = vtkWedge()
wedge3.GetPointIds().SetId( 0, 10 )
wedge3.GetPointIds().SetId( 1, 7 )
wedge3.GetPointIds().SetId( 2, 11 )
wedge3.GetPointIds().SetId( 3, 4 )
wedge3.GetPointIds().SetId( 4, 1 )
wedge3.GetPointIds().SetId( 5, 5 )

wedge4: vtkWedge = vtkWedge()
wedge4.GetPointIds().SetId( 0, 8 )
wedge4.GetPointIds().SetId( 1, 11 )
wedge4.GetPointIds().SetId( 2, 7 )
wedge4.GetPointIds().SetId( 3, 2 )
wedge4.GetPointIds().SetId( 4, 5 )
wedge4.GetPointIds().SetId( 5, 1 )

wedges_cells: vtkCellArray = vtkCellArray()
wedges_cells.InsertNextCell( wedge1 )
wedges_cells.InsertNextCell( wedge2 )
wedges_cells.InsertNextCell( wedge3 )
wedges_cells.InsertNextCell( wedge4 )

wedges_grid = vtkUnstructuredGrid()
wedges_grid.SetPoints( points_wedges )
wedges_grid.SetCells( VTK_WEDGE, wedges_cells )

# one of every other wedge has invalid ordering
wedges_grid_invalid = vtkUnstructuredGrid()
wedges_grid_invalid.DeepCopy( wedges_grid )
for i in range( 2 ):
    reorder_cell_nodes( wedges_grid_invalid, i * 2 + 1, to_change_order[ "Wedge" ] )
"""
4 pentagonal prisms
"""
points_penta_prisms: vtkPoints = vtkPoints()
points_penta_prisms_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.5, 0.0 ),
                                                       ( 0.5, 1.0, 0.0 ), ( -0.5, 0.5, 0.0 ), ( 0.0, 0.0, 1.0 ),
                                                       ( 1.0, 0.0, 1.0 ), ( 1.5, 0.5, 1.0 ), ( 0.5, 1.0, 1.0 ),
                                                       ( -0.5, 0.5, 1.0 ), ( 2.0, 0.0, 0.0 ), ( 3.0, 0.0, 0.0 ),
                                                       ( 3.5, 0.5, 0.0 ), ( 2.5, 1.0, 0.0 ), ( 1.5, 0.5, 0.0 ),
                                                       ( 2.0, 0.0, 1.0 ), ( 3.0, 0.0, 1.0 ), ( 3.5, 0.5, 1.0 ),
                                                       ( 2.5, 1.0, 1.0 ), ( 1.5, 0.5, 1.0 ), ( 0.0, 2.0, 0.0 ),
                                                       ( 1.0, 2.0, 0.0 ), ( 1.5, 2.5, 0.0 ), ( 0.5, 3.0, 0.0 ),
                                                       ( -0.5, 2.5, 0.0 ), ( 0.0, 2.0, 1.0 ), ( 1.0, 2.0, 1.0 ),
                                                       ( 1.5, 2.5, 1.0 ), ( 0.5, 3.0, 1.0 ), ( -0.5, 2.5, 1.0 ),
                                                       ( 2.0, 2.0, 0.0 ), ( 3.0, 2.0, 0.0 ), ( 3.5, 2.5, 0.0 ),
                                                       ( 2.5, 3.0, 0.0 ), ( 1.5, 2.5, 0.0 ), ( 2.0, 2.0, 1.0 ),
                                                       ( 3.0, 2.0, 1.0 ), ( 3.5, 2.5, 1.0 ), ( 2.5, 3.0, 1.0 ),
                                                       ( 1.5, 2.5, 1.0 ) ]
for point_penta_prism in points_penta_prisms_coords:
    points_penta_prisms.InsertNextPoint( point_penta_prism )

penta_prism1: vtkPentagonalPrism = vtkPentagonalPrism()
penta_prism1.GetPointIds().SetId( 0, 0 )
penta_prism1.GetPointIds().SetId( 1, 1 )
penta_prism1.GetPointIds().SetId( 2, 2 )
penta_prism1.GetPointIds().SetId( 3, 3 )
penta_prism1.GetPointIds().SetId( 4, 4 )
penta_prism1.GetPointIds().SetId( 5, 5 )
penta_prism1.GetPointIds().SetId( 6, 6 )
penta_prism1.GetPointIds().SetId( 7, 7 )
penta_prism1.GetPointIds().SetId( 8, 8 )
penta_prism1.GetPointIds().SetId( 9, 9 )

penta_prism2: vtkPentagonalPrism = vtkPentagonalPrism()
penta_prism2.GetPointIds().SetId( 0, 10 )
penta_prism2.GetPointIds().SetId( 1, 11 )
penta_prism2.GetPointIds().SetId( 2, 12 )
penta_prism2.GetPointIds().SetId( 3, 13 )
penta_prism2.GetPointIds().SetId( 4, 14 )
penta_prism2.GetPointIds().SetId( 5, 15 )
penta_prism2.GetPointIds().SetId( 6, 16 )
penta_prism2.GetPointIds().SetId( 7, 17 )
penta_prism2.GetPointIds().SetId( 8, 18 )
penta_prism2.GetPointIds().SetId( 9, 19 )

penta_prism3: vtkPentagonalPrism = vtkPentagonalPrism()
penta_prism3.GetPointIds().SetId( 0, 20 )
penta_prism3.GetPointIds().SetId( 1, 21 )
penta_prism3.GetPointIds().SetId( 2, 22 )
penta_prism3.GetPointIds().SetId( 3, 23 )
penta_prism3.GetPointIds().SetId( 4, 24 )
penta_prism3.GetPointIds().SetId( 5, 25 )
penta_prism3.GetPointIds().SetId( 6, 26 )
penta_prism3.GetPointIds().SetId( 7, 27 )
penta_prism3.GetPointIds().SetId( 8, 28 )
penta_prism3.GetPointIds().SetId( 9, 29 )

penta_prism4: vtkPentagonalPrism = vtkPentagonalPrism()
penta_prism4.GetPointIds().SetId( 0, 30 )
penta_prism4.GetPointIds().SetId( 1, 31 )
penta_prism4.GetPointIds().SetId( 2, 32 )
penta_prism4.GetPointIds().SetId( 3, 33 )
penta_prism4.GetPointIds().SetId( 4, 34 )
penta_prism4.GetPointIds().SetId( 5, 35 )
penta_prism4.GetPointIds().SetId( 6, 36 )
penta_prism4.GetPointIds().SetId( 7, 37 )
penta_prism4.GetPointIds().SetId( 8, 38 )
penta_prism4.GetPointIds().SetId( 9, 39 )

penta_prism_cells = vtkCellArray()
penta_prism_cells.InsertNextCell( penta_prism1 )
penta_prism_cells.InsertNextCell( penta_prism2 )
penta_prism_cells.InsertNextCell( penta_prism3 )
penta_prism_cells.InsertNextCell( penta_prism4 )

penta_prism_grid = vtkUnstructuredGrid()
penta_prism_grid.SetPoints( points_penta_prisms )
penta_prism_grid.SetCells( VTK_PENTAGONAL_PRISM, penta_prism_cells )

# one of every other pentagonal prism has invalid ordering
penta_prism_grid_invalid = vtkUnstructuredGrid()
penta_prism_grid_invalid.DeepCopy( penta_prism_grid )
for i in range( 2 ):
    reorder_cell_nodes( penta_prism_grid_invalid, i * 2 + 1, to_change_order[ "Prism5" ] )
"""
4 hexagonal prisms
"""
points_hexa_prisms: vtkPoints = vtkPoints()
points_hexa_prisms_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.5, 0.0 ),
                                                      ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( -0.5, 0.5, 0.0 ),
                                                      ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.5, 0.5, 1.0 ),
                                                      ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( -0.5, 0.5, 1.0 ),
                                                      ( 2.0, 0.0, 0.0 ), ( 3.0, 0.0, 0.0 ), ( 3.5, 0.5, 0.0 ),
                                                      ( 3.0, 1.0, 0.0 ), ( 2.0, 1.0, 0.0 ), ( 1.5, 0.5, 0.0 ),
                                                      ( 2.0, 0.0, 1.0 ), ( 3.0, 0.0, 1.0 ), ( 3.5, 0.5, 1.0 ),
                                                      ( 3.0, 1.0, 1.0 ), ( 2.0, 1.0, 1.0 ), ( 1.5, 0.5, 1.0 ),
                                                      ( 0.0, 2.0, 0.0 ), ( 1.0, 2.0, 0.0 ), ( 1.5, 2.5, 0.0 ),
                                                      ( 1.0, 3.0, 0.0 ), ( 0.0, 3.0, 0.0 ), ( -0.5, 2.5, 0.0 ),
                                                      ( 0.0, 2.0, 1.0 ), ( 1.0, 2.0, 1.0 ), ( 1.5, 2.5, 1.0 ),
                                                      ( 1.0, 3.0, 1.0 ), ( 0.0, 3.0, 1.0 ), ( -0.5, 2.5, 1.0 ),
                                                      ( 2.0, 2.0, 0.0 ), ( 3.0, 2.0, 0.0 ), ( 3.5, 2.5, 0.0 ),
                                                      ( 3.0, 3.0, 0.0 ), ( 2.0, 3.0, 0.0 ), ( 1.5, 2.5, 0.0 ),
                                                      ( 2.0, 2.0, 1.0 ), ( 3.0, 2.0, 1.0 ), ( 3.5, 2.5, 1.0 ),
                                                      ( 3.0, 3.0, 1.0 ), ( 2.0, 3.0, 1.0 ), ( 1.5, 2.5, 1.0 ) ]
for point_hexa_prism in points_hexa_prisms_coords:
    points_hexa_prisms.InsertNextPoint( point_hexa_prism )

hexa_prism1: vtkHexagonalPrism = vtkHexagonalPrism()
for i in range( 12 ):
    hexa_prism1.GetPointIds().SetId( i, i )

hexa_prism2: vtkHexagonalPrism = vtkHexagonalPrism()
for i in range( 12 ):
    hexa_prism2.GetPointIds().SetId( i, i + 12 )

hexa_prism3: vtkHexagonalPrism = vtkHexagonalPrism()
for i in range( 12 ):
    hexa_prism3.GetPointIds().SetId( i, i + 24 )

hexa_prism4: vtkHexagonalPrism = vtkHexagonalPrism()
for i in range( 12 ):
    hexa_prism4.GetPointIds().SetId( i, i + 36 )

hexa_prism_cells = vtkCellArray()
hexa_prism_cells.InsertNextCell( hexa_prism1 )
hexa_prism_cells.InsertNextCell( hexa_prism2 )
hexa_prism_cells.InsertNextCell( hexa_prism3 )
hexa_prism_cells.InsertNextCell( hexa_prism4 )

hexa_prism_grid = vtkUnstructuredGrid()
hexa_prism_grid.SetPoints( points_hexa_prisms )
hexa_prism_grid.SetCells( VTK_HEXAGONAL_PRISM, hexa_prism_cells )

# one of every other hexagonal prism has invalid ordering
hexa_prism_grid_invalid = vtkUnstructuredGrid()
hexa_prism_grid_invalid.DeepCopy( hexa_prism_grid )
for i in range( 2 ):
    reorder_cell_nodes( hexa_prism_grid_invalid, i * 2 + 1, to_change_order[ "Prism6" ] )
"""
2 hexahedrons, 2 tetrahedrons, 2 wedges, 2 pyramids, 2 voxels, 2 pentagonal prisms and 2 hexagonal prisms
"""
points_mix: vtkPoints = vtkPoints()
points_mix_coords: list[ tuple[ float ] ] = [
    ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 2.0, 0.0, 0.0 ), ( 2.5, -0.5, 0.0 ), ( 3.0, 0.0, 0.0 ), ( 3.5, -0.5, 0.0 ),
    ( 4.0, 0.0, 0.0 ), ( 4.5, -0.5, 0.0 ), ( 5.0, 0.0, 0.0 ), ( 5.5, -0.5, 0.0 ), ( 6.0, 0.5, 0.0 ), ( 0.0, 1.0, 0.0 ),
    ( 1.0, 1.0, 0.0 ), ( 2.0, 1.0, 0.0 ), ( 2.5, 1.5, 0.0 ), ( 3.0, 1.0, 0.0 ), ( 4.0, 1.0, 0.0 ), ( 5.0, 1.0, 0.0 ),
    ( 5.5, 1.5, 0.0 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 2.0, 0.0, 1.0 ), ( 2.5, -0.5, 1.0 ), ( 3.0, 0.0, 1.0 ),
    ( 3.5, -0.5, 1.0 ), ( 4.0, 0.0, 1.0 ), ( 4.5, -0.5, 1.0 ), ( 5.0, 0.0, 1.0 ), ( 5.5, -0.5, 1.0 ), ( 6.0, 0.5, 1.0 ),
    ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 2.0, 1.0, 1.0 ), ( 2.5, 1.5, 1.0 ), ( 3.0, 1.0, 1.0 ), ( 4.0, 1.0, 1.0 ),
    ( 5.0, 1.0, 1.0 ), ( 5.5, 1.5, 1.0 ), ( 0.5, 0.5, 2.0 ), ( 0.5, 1.5, 2.0 ), ( 1.5, 0.5, 2.0 ), ( 1.5, 1.5, 2.0 ),
    ( 2.0, 0.0, 2.0 ), ( 2.5, -0.5, 2.0 ), ( 3.0, 0.0, 2.0 ), ( 3.0, 1.0, 2.0 ), ( 2.5, 1.5, 2.0 ), ( 2.0, 1.0, 2.0 ),
    ( 5.0, 0.0, 2.0 ), ( 5.5, -0.5, 2.0 ), ( 6.0, 0.5, 2.0 ), ( 5.5, 1.5, 2.0 ), ( 5.0, 1.0, 2.0 )
]
for point_mix in points_mix_coords:
    points_mix.InsertNextPoint( point_mix )

mix_hex1: vtkHexahedron = vtkHexahedron()
mix_hex1.GetPointIds().SetId( 0, 0 )
mix_hex1.GetPointIds().SetId( 1, 1 )
mix_hex1.GetPointIds().SetId( 2, 12 )
mix_hex1.GetPointIds().SetId( 3, 11 )
mix_hex1.GetPointIds().SetId( 4, 19 )
mix_hex1.GetPointIds().SetId( 5, 20 )
mix_hex1.GetPointIds().SetId( 6, 31 )
mix_hex1.GetPointIds().SetId( 7, 30 )

mix_hex2: vtkHexahedron = vtkHexahedron()
mix_hex2.GetPointIds().SetId( 0, 1 )
mix_hex2.GetPointIds().SetId( 1, 2 )
mix_hex2.GetPointIds().SetId( 2, 13 )
mix_hex2.GetPointIds().SetId( 3, 12 )
mix_hex2.GetPointIds().SetId( 4, 20 )
mix_hex2.GetPointIds().SetId( 5, 21 )
mix_hex2.GetPointIds().SetId( 6, 32 )
mix_hex2.GetPointIds().SetId( 7, 31 )

mix_hex3: vtkHexahedron = vtkHexahedron()
mix_hex3.GetPointIds().SetId( 0, 4 )
mix_hex3.GetPointIds().SetId( 1, 6 )
mix_hex3.GetPointIds().SetId( 2, 16 )
mix_hex3.GetPointIds().SetId( 3, 15 )
mix_hex3.GetPointIds().SetId( 4, 23 )
mix_hex3.GetPointIds().SetId( 5, 25 )
mix_hex3.GetPointIds().SetId( 6, 35 )
mix_hex3.GetPointIds().SetId( 7, 34 )

mix_hex4: vtkHexahedron = vtkHexahedron()
mix_hex4.GetPointIds().SetId( 0, 6 )
mix_hex4.GetPointIds().SetId( 1, 8 )
mix_hex4.GetPointIds().SetId( 2, 17 )
mix_hex4.GetPointIds().SetId( 3, 16 )
mix_hex4.GetPointIds().SetId( 4, 25 )
mix_hex4.GetPointIds().SetId( 5, 27 )
mix_hex4.GetPointIds().SetId( 6, 36 )
mix_hex4.GetPointIds().SetId( 7, 35 )

mix_pyram1: vtkPyramid = vtkPyramid()
mix_pyram1.GetPointIds().SetId( 0, 19 )
mix_pyram1.GetPointIds().SetId( 1, 20 )
mix_pyram1.GetPointIds().SetId( 2, 31 )
mix_pyram1.GetPointIds().SetId( 3, 30 )
mix_pyram1.GetPointIds().SetId( 4, 38 )

mix_pyram2: vtkPyramid = vtkPyramid()
mix_pyram2.GetPointIds().SetId( 0, 20 )
mix_pyram2.GetPointIds().SetId( 1, 21 )
mix_pyram2.GetPointIds().SetId( 2, 32 )
mix_pyram2.GetPointIds().SetId( 3, 31 )
mix_pyram2.GetPointIds().SetId( 4, 40 )

mix_tetra1: vtkTetra = vtkTetra()
mix_tetra1.GetPointIds().SetId( 0, 31 )
mix_tetra1.GetPointIds().SetId( 1, 39 )
mix_tetra1.GetPointIds().SetId( 2, 30 )
mix_tetra1.GetPointIds().SetId( 3, 38 )

mix_tetra2: vtkTetra = vtkTetra()
mix_tetra2.GetPointIds().SetId( 0, 32 )
mix_tetra2.GetPointIds().SetId( 1, 41 )
mix_tetra2.GetPointIds().SetId( 2, 31 )
mix_tetra2.GetPointIds().SetId( 3, 40 )

mix_hex_prism1: vtkHexagonalPrism = vtkHexagonalPrism()
mix_hex_prism1.GetPointIds().SetId( 0, 2 )
mix_hex_prism1.GetPointIds().SetId( 1, 3 )
mix_hex_prism1.GetPointIds().SetId( 2, 4 )
mix_hex_prism1.GetPointIds().SetId( 3, 15 )
mix_hex_prism1.GetPointIds().SetId( 4, 14 )
mix_hex_prism1.GetPointIds().SetId( 5, 13 )
mix_hex_prism1.GetPointIds().SetId( 6, 21 )
mix_hex_prism1.GetPointIds().SetId( 7, 22 )
mix_hex_prism1.GetPointIds().SetId( 8, 23 )
mix_hex_prism1.GetPointIds().SetId( 9, 34 )
mix_hex_prism1.GetPointIds().SetId( 10, 33 )
mix_hex_prism1.GetPointIds().SetId( 11, 32 )

mix_hex_prism2: vtkHexagonalPrism = vtkHexagonalPrism()
mix_hex_prism2.GetPointIds().SetId( 0, 21 )
mix_hex_prism2.GetPointIds().SetId( 1, 22 )
mix_hex_prism2.GetPointIds().SetId( 2, 23 )
mix_hex_prism2.GetPointIds().SetId( 3, 34 )
mix_hex_prism2.GetPointIds().SetId( 4, 33 )
mix_hex_prism2.GetPointIds().SetId( 5, 32 )
mix_hex_prism2.GetPointIds().SetId( 6, 42 )
mix_hex_prism2.GetPointIds().SetId( 7, 43 )
mix_hex_prism2.GetPointIds().SetId( 8, 44 )
mix_hex_prism2.GetPointIds().SetId( 9, 45 )
mix_hex_prism2.GetPointIds().SetId( 10, 46 )
mix_hex_prism2.GetPointIds().SetId( 11, 47 )

mix_wedge1: vtkWedge = vtkWedge()
mix_wedge1.GetPointIds().SetId( 0, 23 )
mix_wedge1.GetPointIds().SetId( 1, 24 )
mix_wedge1.GetPointIds().SetId( 2, 25 )
mix_wedge1.GetPointIds().SetId( 3, 4 )
mix_wedge1.GetPointIds().SetId( 4, 5 )
mix_wedge1.GetPointIds().SetId( 5, 6 )

mix_wedge2: vtkWedge = vtkWedge()
mix_wedge2.GetPointIds().SetId( 0, 25 )
mix_wedge2.GetPointIds().SetId( 1, 26 )
mix_wedge2.GetPointIds().SetId( 2, 27 )
mix_wedge2.GetPointIds().SetId( 3, 6 )
mix_wedge2.GetPointIds().SetId( 4, 7 )
mix_wedge2.GetPointIds().SetId( 5, 8 )

mix_penta_prism1: vtkPentagonalPrism = vtkPentagonalPrism()
mix_penta_prism1.GetPointIds().SetId( 0, 8 )
mix_penta_prism1.GetPointIds().SetId( 1, 9 )
mix_penta_prism1.GetPointIds().SetId( 2, 10 )
mix_penta_prism1.GetPointIds().SetId( 3, 18 )
mix_penta_prism1.GetPointIds().SetId( 4, 17 )
mix_penta_prism1.GetPointIds().SetId( 5, 27 )
mix_penta_prism1.GetPointIds().SetId( 6, 28 )
mix_penta_prism1.GetPointIds().SetId( 7, 29 )
mix_penta_prism1.GetPointIds().SetId( 8, 37 )
mix_penta_prism1.GetPointIds().SetId( 9, 36 )

mix_penta_prism2: vtkPentagonalPrism = vtkPentagonalPrism()
mix_penta_prism2.GetPointIds().SetId( 0, 27 )
mix_penta_prism2.GetPointIds().SetId( 1, 28 )
mix_penta_prism2.GetPointIds().SetId( 2, 29 )
mix_penta_prism2.GetPointIds().SetId( 3, 37 )
mix_penta_prism2.GetPointIds().SetId( 4, 36 )
mix_penta_prism2.GetPointIds().SetId( 5, 48 )
mix_penta_prism2.GetPointIds().SetId( 6, 49 )
mix_penta_prism2.GetPointIds().SetId( 7, 50 )
mix_penta_prism2.GetPointIds().SetId( 8, 51 )
mix_penta_prism2.GetPointIds().SetId( 9, 52 )

# this mix grid has only valid cell volumes
mix_grid = vtkUnstructuredGrid()
mix_grid.SetPoints( points_mix )
all_cell_types_mix_grid = [
    VTK_HEXAHEDRON, VTK_HEXAHEDRON, VTK_PYRAMID, VTK_PYRAMID, VTK_TETRA, VTK_TETRA, VTK_HEXAGONAL_PRISM,
    VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON, VTK_HEXAHEDRON, VTK_WEDGE, VTK_WEDGE, VTK_PENTAGONAL_PRISM,
    VTK_PENTAGONAL_PRISM
]
all_cell_names_mix_grid = [
    "Hexahedron", "Hexahedron", "Pyramid", "Pyramid", "Tetrahedron", "Tetrahedron", "Prism6", "Prism6", "Hexahedron",
    "Hexahedron", "Wedge", "Wedge", "Prism5", "Prism5"
]
all_cells_mix_grid = [
    mix_hex1, mix_hex2, mix_pyram1, mix_pyram2, mix_tetra1, mix_tetra2, mix_hex_prism1, mix_hex_prism2, mix_hex3,
    mix_hex4, mix_wedge1, mix_wedge2, mix_penta_prism1, mix_penta_prism2
]
for cell_type, cell in zip( all_cell_types_mix_grid, all_cells_mix_grid ):
    mix_grid.InsertNextCell( cell_type, cell.GetPointIds() )

# this mix grid has one invalid cell for each different element type
mix_grid_invalid = vtkUnstructuredGrid()
mix_grid_invalid.DeepCopy( mix_grid )
for i in range( len( all_cell_types_mix_grid ) // 2 ):
    reorder_cell_nodes( mix_grid_invalid, i * 2 + 1, to_change_order[ all_cell_names_mix_grid[ i * 2 + 1 ] ] )


class TestClass:

    def test_reorder_cell_nodes( self ):
        expected_nodes_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ),
                                                          ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ),
                                                          ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ) ]
        for i in range( one_hex.GetCell( 0 ).GetNumberOfPoints() ):
            assert one_hex.GetCell( 0 ).GetPoints().GetPoint( i ) == expected_nodes_coords[ i ]

        # reorder the cell to make it invalid
        reorder_cell_nodes( one_hex, 0, to_change_order[ "Hexahedron" ] )
        expected_nodes_coords_modified = [ ( 0.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 0.0, 0.0 ),
                                           ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ) ]
        for i in range( one_hex.GetCell( 0 ).GetNumberOfPoints() ):
            assert one_hex.GetCell( 0 ).GetPoints().GetPoint( i ) == expected_nodes_coords_modified[ i ]

        # reorder the cell again to make it valid again
        reorder_cell_nodes( one_hex, 0, to_change_order[ "Hexahedron" ] )
        expected_nodes_coords_modified2 = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ),
                                            ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ) ]
        for i in range( one_hex.GetCell( 0 ).GetNumberOfPoints() ):
            assert one_hex.GetCell( 0 ).GetPoints().GetPoint( i ) == expected_nodes_coords_modified2[ i ]

    def test_compute_mesh_cells_volume( self ):
        grid_volumes = {
            hexahedrons_grid: [ 1.0, 1.0, 1.0, 1.0 ],
            hexahedrons_grid_invalid: [ 1.0, -0.333, 1.0, -0.333 ],
            tetras_grid: [ 0.167, 0.167, 0.167, 0.167 ],
            tetras_grid_invalid: [ 0.167, -0.167, 0.167, -0.167 ],
            pyramids_grid: [ 0.333, 0.333, 0.333, 0.333 ],
            pyramids_grid_invalid: [ 0.333, -0.333, 0.333, -0.333 ],
            voxels_grid: [ 1.0, 1.0, 1.0, 1.0 ],
            wedges_grid: [ 0.5, 0.5, 0.5, 0.5 ],
            wedges_grid_invalid: [ 0.5, -0.167, 0.5, -0.167 ],
            penta_prism_grid: [ 1.25, 1.25, 1.25, 1.25 ],
            penta_prism_grid_invalid: [ 1.25, -0.083, 1.25, -0.083 ],
            hexa_prism_grid: [ 1.5, 1.5, 1.5, 1.5 ],
            hexa_prism_grid_invalid: [ 1.5, -0.333, 1.5, -0.333 ],
            mix_grid: [ 1.0, 1.0, 0.333, 0.333, 0.167, 0.167, 1.5, 1.5, 1.0, 1.0, 0.25, 0.25, 1.25, 1.25 ],
            mix_grid_invalid:
            [ 1.0, -0.333, 0.333, -0.333, 0.167, -0.167, 1.5, -0.333, 1.0, -0.333, 0.25, -0.083, 1.25, -0.083 ]
        }
        for grid, volumes_expected in grid_volumes.items():
            volumes_computed = feo.compute_mesh_cells_volume( grid )
            for i in range( len( volumes_computed ) ):
                assert round( float( volumes_computed[ i ] ), 3 ) == volumes_expected[ i ]

    def test_is_cell_to_reorder( self ):
        grid_needs_ordering = {
            hexahedrons_grid: [ False ] * 4,
            hexahedrons_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            tetras_grid: [ False ] * 4,
            tetras_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            pyramids_grid: [ False ] * 4,
            pyramids_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            wedges_grid: [ False ] * 4,
            wedges_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            penta_prism_grid: [ False ] * 4,
            penta_prism_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            hexa_prism_grid: [ False ] * 4,
            hexa_prism_grid_invalid: [ i % 2 != 0 for i in range( 4 ) ],
            mix_grid: [ False ] * 14,
            mix_grid_invalid: [ i % 2 != 0 for i in range( 14 ) ]
        }
        for grid, needs_ordering in grid_needs_ordering.items():
            volumes = feo.compute_mesh_cells_volume( grid )
            for i in range( len( volumes ) ):
                options = opt( out, to_change_order, "negative" )
                assert feo.is_cell_to_reorder( volumes[ i ], options ) == needs_ordering[ i ]
                options = opt( out, to_change_order, "positive" )
                assert feo.is_cell_to_reorder( volumes[ i ], options ) != needs_ordering[ i ]
                options = opt( out, to_change_order, "all" )
                assert feo.is_cell_to_reorder( volumes[ i ], options ) == True

    def test_get_cell_types_and_number( self ):
        assert feo.get_cell_types_and_number( hexahedrons_grid ) == ( [ VTK_HEXAHEDRON ], [ 4 ] )
        assert feo.get_cell_types_and_number( hexahedrons_grid_invalid ) == ( [ VTK_HEXAHEDRON ], [ 4 ] )
        assert feo.get_cell_types_and_number( tetras_grid ) == ( [ VTK_TETRA ], [ 4 ] )
        assert feo.get_cell_types_and_number( tetras_grid_invalid ) == ( [ VTK_TETRA ], [ 4 ] )
        assert feo.get_cell_types_and_number( pyramids_grid ) == ( [ VTK_PYRAMID ], [ 4 ] )
        assert feo.get_cell_types_and_number( pyramids_grid_invalid ) == ( [ VTK_PYRAMID ], [ 4 ] )
        assert feo.get_cell_types_and_number( wedges_grid ) == ( [ VTK_WEDGE ], [ 4 ] )
        assert feo.get_cell_types_and_number( wedges_grid_invalid ) == ( [ VTK_WEDGE ], [ 4 ] )
        assert feo.get_cell_types_and_number( penta_prism_grid ) == ( [ VTK_PENTAGONAL_PRISM ], [ 4 ] )
        assert feo.get_cell_types_and_number( penta_prism_grid_invalid ) == ( [ VTK_PENTAGONAL_PRISM ], [ 4 ] )
        assert feo.get_cell_types_and_number( hexa_prism_grid ) == ( [ VTK_HEXAGONAL_PRISM ], [ 4 ] )
        assert feo.get_cell_types_and_number( hexa_prism_grid_invalid ) == ( [ VTK_HEXAGONAL_PRISM ], [ 4 ] )
        assert feo.get_cell_types_and_number( mix_grid ) == ( [
            VTK_TETRA, VTK_HEXAHEDRON, VTK_WEDGE, VTK_PYRAMID, VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM
        ], [ 2, 4, 2, 2, 2, 2 ] )
        assert feo.get_cell_types_and_number( mix_grid_invalid ) == ( [
            VTK_TETRA, VTK_HEXAHEDRON, VTK_WEDGE, VTK_PYRAMID, VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM
        ], [ 2, 4, 2, 2, 2, 2 ] )
        expected_error: str = f"Invalid type '11' for GEOS is in the mesh. Dying ..."
        with pytest.raises( ValueError, match=expected_error ):
            feo.get_cell_types_and_number( voxels_grid )

    def test_reorder_nodes_to_new_mesh( self ):
        options = opt( out, to_change_order, "negative" )
        # single element grids except voxels because it is an invalid cell type for GEOS
        grid_cell_type = {
            hexahedrons_grid_invalid: VTK_HEXAHEDRON,
            tetras_grid_invalid: VTK_TETRA,
            pyramids_grid_invalid: VTK_PYRAMID,
            wedges_grid_invalid: VTK_WEDGE,
            penta_prism_grid_invalid: VTK_PENTAGONAL_PRISM,
            hexa_prism_grid_invalid: VTK_HEXAGONAL_PRISM
        }
        for grid, cell_type in grid_cell_type.items():
            new_invalid = vtkUnstructuredGrid()
            new_invalid.DeepCopy( grid )
            not_use_invalid, reorder_stats = feo.reorder_nodes_to_new_mesh( new_invalid, options )
            expected = {
                "Types reordered": [ VTK_TYPE_TO_NAME[ cell_type ] ],
                "Number of cells reordered": [ 2 ],
                "Types non reordered": [ VTK_TYPE_TO_NAME[ cell_type ] ],
                "Number of cells non reordered": [ 2 ]
            }
            for prop in expected.keys():
                assert reorder_stats[ prop ] == expected[ prop ]

        # mix elements grid
        mix_invalid = vtkUnstructuredGrid()
        mix_invalid.DeepCopy( mix_grid_invalid )
        not_use_invalid, mix_stats = feo.reorder_nodes_to_new_mesh( mix_invalid, options )
        expected = {
            "Types reordered": [ VTK_TYPE_TO_NAME[ cell_type ] for cell_type in [ 12, 15, 16, 14, 10, 13 ] ],
            "Number of cells reordered": [ 2, 1, 1, 1, 1, 1 ],
            "Types non reordered": [ VTK_TYPE_TO_NAME[ cell_type ] for cell_type in [ 12, 15, 16, 14, 10, 13 ] ],
            "Number of cells non reordered": [ 2, 1, 1, 1, 1, 1 ]
        }
        for prop in expected.keys():
            assert mix_stats[ prop ] == expected[ prop ]

    def test_fix_elements_orderings_execution( self ):
        # for mix_grid_invalid mesh, checks that reordered mesh was created and that reoredring_stats are valid
        write_mesh( mix_grid_invalid, test_file )
        invalidTest = False
        command = [
            "python", MESH_DOCTOR_FILEPATH, "-v", "-i", test_file.output, "fix_elements_orderings", "--Hexahedron",
            str( to_change_order[ "Hexahedron" ] ).replace( "[", "" ).replace( "]", "" ), "--Tetrahedron",
            str( to_change_order[ "Tetrahedron" ] ).replace( "[", "" ).replace( "]", "" ), "--Pyramid",
            str( to_change_order[ "Pyramid" ] ).replace( "[", "" ).replace( "]", "" ), "--Wedge",
            str( to_change_order[ "Wedge" ] ).replace( "[", "" ).replace( "]", "" ), "--Prism5",
            str( to_change_order[ "Prism5" ] ).replace( "[", "" ).replace( "]", "" ), "--Prism6",
            str( to_change_order[ "Prism6" ] ).replace( "[", "" ).replace( "]", "" ), "--volume_to_reorder", "negative",
            "--data-mode", "binary", "--output", filepath_reordered_mesh
        ]
        try:
            result = subprocess.run( command, shell=True, stderr=subprocess.PIPE, universal_newlines=True )
            os.remove( filepath_reordered_mesh )
            stderr = result.stderr
            assert result.returncode == 0
            raw_stderr = r"{}".format( stderr )
            pattern = r"\[.*?\]\[.*?\] (.*)"
            matches = re.findall( pattern, raw_stderr )
            no_log = "\n".join( matches )
            reordering_stats: str = no_log[ no_log.index( "Number of cells reordered" ): ]
            expected_stats: str = ( "Number of cells reordered:\n" + "\tCellType\tNumber\n" + f"\tHexahedron\t\t2\n" +
                                    f"\tPrism5\t\t1\n" + f"\tPrism6\t\t1\n" + f"\tPyramid\t\t1\n" +
                                    f"\tTetrahedron\t\t1\n" + f"\tWedge\t\t1\n" + "Number of cells non reordered:\n" +
                                    "\tCellType\tNumber\n" + f"\tHexahedron\t\t2\n" + f"\tPrism5\t\t1\n" +
                                    f"\tPrism6\t\t1\n" + f"\tPyramid\t\t1\n" + f"\tTetrahedron\t\t1\n" +
                                    f"\tWedge\t\t1" )
            assert reordering_stats == expected_stats
        except Exception as e:
            logging.error( "Invalid command input. Test has failed." )
            logging.error( e )
            invalidTest = True
        os.remove( test_file.output )
        if invalidTest:
            raise ValueError( "test_fix_elements_orderings_execution has failed." )
