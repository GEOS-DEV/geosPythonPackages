import os
import re
import pytest
import logging
import subprocess
import numpy as np
from math import pi
from geos.mesh.doctor.mesh_doctor import MESH_DOCTOR_FILEPATH
from geos.mesh.doctor.checks import fix_elements_orderings as feo
from geos.mesh.doctor.checks.generate_cube import Options, __build
from geos.mesh.doctor.checks.vtk_utils import ( VtkOutput, to_vtk_id_list, write_mesh )
from geos.mesh.doctor.checks.fix_elements_orderings import Options as opt, VTK_TYPE_TO_NAME
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkUnstructuredGrid, vtkCellArray, vtkHexahedron, vtkTetra,
                                            vtkPyramid, vtkVoxel, vtkWedge, vtkPentagonalPrism, vtkHexagonalPrism,
                                            VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_VOXEL,
                                            VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM )


def degrees_to_radians( degrees ):
    return degrees * ( pi / 180 )


def radians_to_degrees( radians ):
    return radians * ( 180 / pi )


# yapf: disable
def rotate_polygon_around_point( polygon: np.array, rotation_point: np.array, a: float, b: float, g: float ) -> np.array:
    rotation_matrix = np.array([ [ np.cos(b)*np.cos(g), np.sin(a)*np.sin(b)*np.cos(g) - np.cos(a)*np.sin(g), np.cos(a)*np.sin(b)*np.cos(g) + np.sin(a)*np.sin(g) ],
                                 [ np.cos(b)*np.sin(g), np.sin(a)*np.sin(b)*np.sin(g) + np.cos(a)*np.cos(g), np.cos(a)*np.sin(b)*np.sin(g) - np.sin(a)*np.cos(g) ],
                                 [ -np.sin(b),          np.sin(a)*np.cos(b),                                 np.cos(a)*np.cos(b)                                 ] ])
    translated_points = polygon - rotation_point
    rotated_points = np.dot( translated_points, rotation_matrix.T )
    rotated_polygon = rotated_points + rotation_point
    return rotated_polygon
# yapf: enable


def reorder_cell_nodes( mesh: vtkDataSet, cell_id: int, node_ordering: tuple[ int ] ):
    """Utility function to reorder the nodes of one cell for test purposes.

    Args:
        mesh (vtkDataSet): A vtk grid.
        cell_id (int): Cell id to identify the cell which will be modified.
        node_ordering (list[ int ]): Nodes id ordering to construct a cell.
    """
    if mesh.GetCell( cell_id ).GetNumberOfPoints() != len( node_ordering ):
        raise ValueError( f"The cell to reorder needs to have '{mesh.GetCell( cell_id ).GetNumberOfPoints()}'" +
                          " nodes in reordering." )
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
filepath_non_ordered_mesh2: str = os.path.join( dir_name, "to_reorder_mesh2.vtu" )
filepath_reordered_mesh2: str = os.path.join( dir_name, "reordered_mesh2.vtu" )
test_file2: VtkOutput = VtkOutput( filepath_non_ordered_mesh2, True )
"""
Dict used to apply false nodes orderings for test purposes
"""
to_change_order: dict[ int, tuple[ int ] ] = {
    "Hexahedron": ( 0, 3, 2, 1, 4, 7, 6, 5 ),
    "Tetrahedron": ( 0, 2, 1, 3 ),
    "Pyramid": ( 0, 3, 2, 1, 4 ),
    "Wedge": ( 0, 2, 1, 3, 5, 4 ),
    "Prism5": ( 0, 4, 3, 2, 1, 5, 9, 8, 7, 6 ),
    "Prism6": ( 0, 5, 4, 3, 2, 1, 6, 11, 10, 9, 8, 7 )
}
to_change_order = dict( sorted( to_change_order.items() ) )
to_change_order_for_degenerated_cells: dict[ int, tuple[ int ] ] = {
    "Hexahedron": ( 0, 2, 1, 3, 4, 6, 5, 7 ),
    "Wedge": ( 0, 1, 2, 5, 4, 3 ),
    "Prism5": ( 0, 1, 2, 3, 4, 7, 6, 5, 9, 8 ),
    "Prism6": ( 0, 1, 2, 3, 4, 5, 11, 10, 9, 8, 7, 6 )
}
to_change_order = dict( sorted( to_change_order.items() ) )
cell_names = list( VTK_TYPE_TO_NAME.values() )
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

opt_hexahedrons_grid = opt( test_file, [ "Hexahedron" ], "negative" )
opt_hexahedrons_grid_invalid = opt( test_file, [ "Hexahedron" ], "negative" )
"""
4 tetrahedrons
"""
points_tetras: vtkPoints = vtkPoints()
# yapf: disable
points_tetras_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                 ( 1.0, 0.0, 0.0 ),
                                                 ( 1.0, 1.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ),
                                                 ( 0.0, 0.0, 1.0 ),
                                                 ( 1.0, 0.0, 1.0 ),  # point5
                                                 ( 1.0, 1.0, 1.0 ),
                                                 ( 0.0, 1.0, 1.0 ) ]
# yapf: enable
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

opt_tetras_grid = opt( test_file, [ "Tetrahedron" ], "negative" )
opt_tetras_grid_invalid = opt( test_file, [ "Tetrahedron" ], "negative" )
"""
4 pyramids
"""
points_pyramids: vtkPoints = vtkPoints()
# yapf: disable
points_pyramids_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                   ( 1.0, 0.0, 0.0 ),
                                                   ( 1.0, 1.0, 0.0 ),
                                                   ( 0.0, 1.0, 0.0 ),
                                                   ( 0.5, 0.5, 1.0 ),
                                                   ( 2.0, 0.0, 0.0 ),  # point5
                                                   ( 3.0, 0.0, 0.0 ),
                                                   ( 3.0, 1.0, 0.0 ),
                                                   ( 2.0, 1.0, 0.0 ),
                                                   ( 2.5, 0.5, 1.0 ),
                                                   ( 0.0, 2.0, 0.0 ),  # point10
                                                   ( 1.0, 2.0, 0.0 ),
                                                   ( 1.0, 3.0, 0.0 ),
                                                   ( 0.0, 3.0, 0.0 ),
                                                   ( 0.5, 2.5, 1.0 ),
                                                   ( 2.0, 2.0, 0.0 ),  # point15
                                                   ( 3.0, 2.0, 0.0 ),
                                                   ( 3.0, 3.0, 0.0 ),
                                                   ( 2.0, 3.0, 0.0 ),
                                                   ( 2.5, 2.5, 1.0 ) ]
# yapf: enable
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

opt_pyramids_grid = opt( test_file, [ "Pyramid" ], "negative" )
opt_pyramids_grid_invalid = opt( test_file, [ "Pyramid" ], "negative" )
"""
4 voxels: this type of element cannot be used in GEOS, we just test that the feature rejects them
"""
points_voxels: vtkPoints = vtkPoints()
# yapf: disable
points_voxels_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                 ( 1.0, 0.0, 0.0 ),
                                                 ( 1.0, 1.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ),
                                                 ( 0.0, 0.0, 1.0 ),
                                                 ( 1.0, 0.0, 1.0 ),  # point5
                                                 ( 1.0, 1.0, 1.0 ),
                                                 ( 0.0, 1.0, 1.0 ),
                                                 ( 2.0, 0.0, 0.0 ),
                                                 ( 3.0, 0.0, 0.0 ),
                                                 ( 3.0, 1.0, 0.0 ),  # point10
                                                 ( 2.0, 1.0, 0.0 ),
                                                 ( 2.0, 0.0, 1.0 ),
                                                 ( 3.0, 0.0, 1.0 ),
                                                 ( 3.0, 1.0, 1.0 ),
                                                 ( 2.0, 1.0, 1.0 ),  # point15
                                                 ( 0.0, 2.0, 0.0 ),
                                                 ( 1.0, 2.0, 0.0 ),
                                                 ( 1.0, 3.0, 0.0 ),
                                                 ( 0.0, 3.0, 0.0 ),
                                                 ( 0.0, 2.0, 1.0 ),  # point20
                                                 ( 1.0, 2.0, 1.0 ),
                                                 ( 1.0, 3.0, 1.0 ),
                                                 ( 0.0, 3.0, 1.0 ),
                                                 ( 2.0, 2.0, 0.0 ),
                                                 ( 3.0, 2.0, 0.0 ),  # point25
                                                 ( 3.0, 3.0, 0.0 ),
                                                 ( 2.0, 3.0, 0.0 ),
                                                 ( 2.0, 2.0, 1.0 ),
                                                 ( 3.0, 2.0, 1.0 ),
                                                 ( 3.0, 3.0, 1.0 ),  # point30
                                                 ( 2.0, 3.0, 1.0 ) ]
# yapf: enable
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

opt_voxels_grid = opt( test_file, [ "Voxel" ], "negative" )
opt_voxels_grid_invalid = opt( test_file, [ "Voxel" ], "negative" )
"""
4 wedges
"""
points_wedges: vtkPoints = vtkPoints()
# yapf: disable
points_wedges_coords: list[ tuple[ float ] ] = [ ( 0.5, 0.0, 0.0 ),  # point0
                                                 ( 1.5, 0.0, 0.0 ),
                                                 ( 2.5, 0.0, 0.0 ),
                                                 ( 0.0, 1.0, 0.0 ),
                                                 ( 1.0, 1.0, 0.0 ),
                                                 ( 2.0, 1.0, 0.0 ),  # point5
                                                 ( 0.5, 0.0, 1.0 ),
                                                 ( 1.5, 0.0, 1.0 ),
                                                 ( 2.5, 0.0, 1.0 ),
                                                 ( 0.0, 1.0, 1.0 ),
                                                 ( 1.0, 1.0, 1.0 ),  # point10
                                                 ( 2.0, 1.0, 1.0 ) ]
# yapf: enable
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

opt_wedges_grid = opt( test_file, [ "Wedge" ], "negative" )
opt_wedges_grid_invalid = opt( test_file, [ "Wedge" ], "negative" )
"""
4 pentagonal prisms
"""
points_penta_prisms: vtkPoints = vtkPoints()
# yapf: disable
points_penta_prisms_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                       ( 1.0, 0.0, 0.0 ),
                                                       ( 1.5, 0.5, 0.0 ),
                                                       ( 0.5, 1.0, 0.0 ),
                                                       ( -0.5, 0.5, 0.0 ),
                                                       ( 0.0, 0.0, 1.0 ),  # point5
                                                       ( 1.0, 0.0, 1.0 ),
                                                       ( 1.5, 0.5, 1.0 ),
                                                       ( 0.5, 1.0, 1.0 ),
                                                       ( -0.5, 0.5, 1.0 ),
                                                       ( 2.0, 0.0, 0.0 ),  # point10
                                                       ( 3.0, 0.0, 0.0 ),
                                                       ( 3.5, 0.5, 0.0 ),
                                                       ( 2.5, 1.0, 0.0 ),
                                                       ( 1.5, 0.5, 0.0 ),
                                                       ( 2.0, 0.0, 1.0 ),  # point15
                                                       ( 3.0, 0.0, 1.0 ),
                                                       ( 3.5, 0.5, 1.0 ),
                                                       ( 2.5, 1.0, 1.0 ),
                                                       ( 1.5, 0.5, 1.0 ),
                                                       ( 0.0, 2.0, 0.0 ),  # point20
                                                       ( 1.0, 2.0, 0.0 ),
                                                       ( 1.5, 2.5, 0.0 ),
                                                       ( 0.5, 3.0, 0.0 ),
                                                       ( -0.5, 2.5, 0.0 ),
                                                       ( 0.0, 2.0, 1.0 ),  # point25
                                                       ( 1.0, 2.0, 1.0 ),
                                                       ( 1.5, 2.5, 1.0 ),
                                                       ( 0.5, 3.0, 1.0 ),
                                                       ( -0.5, 2.5, 1.0 ),
                                                       ( 2.0, 2.0, 0.0 ),  # point30
                                                       ( 3.0, 2.0, 0.0 ),
                                                       ( 3.5, 2.5, 0.0 ),
                                                       ( 2.5, 3.0, 0.0 ),
                                                       ( 1.5, 2.5, 0.0 ),
                                                       ( 2.0, 2.0, 1.0 ),  # point35
                                                       ( 3.0, 2.0, 1.0 ),
                                                       ( 3.5, 2.5, 1.0 ),
                                                       ( 2.5, 3.0, 1.0 ),
                                                       ( 1.5, 2.5, 1.0 ) ]
# yapf: enable
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

opt_penta_prism_grid = opt( test_file, [ "Prism5" ], "negative" )
opt_penta_prism_grid_invalid = opt( test_file, [ "Prism5" ], "negative" )
"""
4 hexagonal prisms
"""
points_hexa_prisms: vtkPoints = vtkPoints()
# yapf: disable
points_hexa_prisms_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                      ( 1.0, 0.0, 0.0 ),
                                                      ( 1.5, 0.5, 0.0 ),
                                                      ( 1.0, 1.0, 0.0 ),
                                                      ( 0.0, 1.0, 0.0 ),
                                                      ( -0.5, 0.5, 0.0 ),  # point5
                                                      ( 0.0, 0.0, 1.0 ),
                                                      ( 1.0, 0.0, 1.0 ),
                                                      ( 1.5, 0.5, 1.0 ),
                                                      ( 1.0, 1.0, 1.0 ),
                                                      ( 0.0, 1.0, 1.0 ),  # point10
                                                      ( -0.5, 0.5, 1.0 ),
                                                      ( 2.0, 0.0, 0.0 ),
                                                      ( 3.0, 0.0, 0.0 ),
                                                      ( 3.5, 0.5, 0.0 ),
                                                      ( 3.0, 1.0, 0.0 ),  # point15
                                                      ( 2.0, 1.0, 0.0 ),
                                                      ( 1.5, 0.5, 0.0 ),
                                                      ( 2.0, 0.0, 1.0 ),
                                                      ( 3.0, 0.0, 1.0 ),
                                                      ( 3.5, 0.5, 1.0 ),  # point20
                                                      ( 3.0, 1.0, 1.0 ),
                                                      ( 2.0, 1.0, 1.0 ),
                                                      ( 1.5, 0.5, 1.0 ),
                                                      ( 0.0, 2.0, 0.0 ),
                                                      ( 1.0, 2.0, 0.0 ),  # point25
                                                      ( 1.5, 2.5, 0.0 ),
                                                      ( 1.0, 3.0, 0.0 ),
                                                      ( 0.0, 3.0, 0.0 ),
                                                      ( -0.5, 2.5, 0.0 ),
                                                      ( 0.0, 2.0, 1.0 ),  # point30
                                                      ( 1.0, 2.0, 1.0 ),
                                                      ( 1.5, 2.5, 1.0 ),
                                                      ( 1.0, 3.0, 1.0 ),
                                                      ( 0.0, 3.0, 1.0 ),
                                                      ( -0.5, 2.5, 1.0 ),  # point35
                                                      ( 2.0, 2.0, 0.0 ),
                                                      ( 3.0, 2.0, 0.0 ),
                                                      ( 3.5, 2.5, 0.0 ),
                                                      ( 3.0, 3.0, 0.0 ),
                                                      ( 2.0, 3.0, 0.0 ),  # point40
                                                      ( 1.5, 2.5, 0.0 ),
                                                      ( 2.0, 2.0, 1.0 ),
                                                      ( 3.0, 2.0, 1.0 ),
                                                      ( 3.5, 2.5, 1.0 ),
                                                      ( 3.0, 3.0, 1.0 ),  # point45
                                                      ( 2.0, 3.0, 1.0 ),
                                                      ( 1.5, 2.5, 1.0 ) ]
# yapf: enable
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

opt_hexa_prism_grid = opt( test_file, [ "Prism6" ], "negative" )
opt_hexa_prism_grid_invalid = opt( test_file, [ "Prism6" ], "negative" )
"""
2 hexahedrons, 2 tetrahedrons, 2 wedges, 2 pyramids, 2 voxels, 2 pentagonal prisms and 2 hexagonal prisms
"""
points_mix: vtkPoints = vtkPoints()
# yapf: disable
points_mix_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                              ( 1.0, 0.0, 0.0 ),
                                              ( 2.0, 0.0, 0.0 ),
                                              ( 2.5, -0.5, 0.0 ),
                                              ( 3.0, 0.0, 0.0 ),
                                              ( 3.5, -0.5, 0.0 ),  # point5
                                              ( 4.0, 0.0, 0.0 ),
                                              ( 4.5, -0.5, 0.0 ),
                                              ( 5.0, 0.0, 0.0 ),
                                              ( 5.5, -0.5, 0.0 ),
                                              ( 6.0, 0.5, 0.0 ),  # point10
                                              ( 0.0, 1.0, 0.0 ),
                                              ( 1.0, 1.0, 0.0 ),
                                              ( 2.0, 1.0, 0.0 ),
                                              ( 2.5, 1.5, 0.0 ),
                                              ( 3.0, 1.0, 0.0 ),  # point15
                                              ( 4.0, 1.0, 0.0 ),
                                              ( 5.0, 1.0, 0.0 ),
                                              ( 5.5, 1.5, 0.0 ),
                                              ( 0.0, 0.0, 1.0 ),
                                              ( 1.0, 0.0, 1.0 ),  # point20
                                              ( 2.0, 0.0, 1.0 ),
                                              ( 2.5, -0.5, 1.0 ),
                                              ( 3.0, 0.0, 1.0 ),
                                              ( 3.5, -0.5, 1.0 ),
                                              ( 4.0, 0.0, 1.0 ),  # point25
                                              ( 4.5, -0.5, 1.0 ),
                                              ( 5.0, 0.0, 1.0 ),
                                              ( 5.5, -0.5, 1.0 ),
                                              ( 6.0, 0.5, 1.0 ),
                                              ( 0.0, 1.0, 1.0 ),  # point30
                                              ( 1.0, 1.0, 1.0 ),
                                              ( 2.0, 1.0, 1.0 ),
                                              ( 2.5, 1.5, 1.0 ),
                                              ( 3.0, 1.0, 1.0 ),
                                              ( 4.0, 1.0, 1.0 ),  # point35
                                              ( 5.0, 1.0, 1.0 ),
                                              ( 5.5, 1.5, 1.0 ),
                                              ( 0.5, 0.5, 2.0 ),
                                              ( 0.5, 1.5, 2.0 ),
                                              ( 1.5, 0.5, 2.0 ),  # point40
                                              ( 1.5, 1.5, 2.0 ),
                                              ( 2.0, 0.0, 2.0 ),
                                              ( 2.5, -0.5, 2.0 ),
                                              ( 3.0, 0.0, 2.0 ),
                                              ( 3.0, 1.0, 2.0 ),  # point45
                                              ( 2.5, 1.5, 2.0 ),
                                              ( 2.0, 1.0, 2.0 ),
                                              ( 5.0, 0.0, 2.0 ),
                                              ( 5.5, -0.5, 2.0 ),
                                              ( 6.0, 0.5, 2.0 ),  # point50
                                              ( 5.5, 1.5, 2.0 ),
                                              ( 5.0, 1.0, 2.0 ) ]
# yapf: enable
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

opt_mix_grid = opt( test_file, tuple( ( "Hexahedron", "Tetrahedron", "Pyramid", "Wedge", "Prism5", "Prism6" ) ),
                    "negative" )
opt_mix_grid_inv = opt( test_file, tuple( ( "Hexahedron", "Tetrahedron", "Pyramid", "Wedge", "Prism5", "Prism6" ) ),
                        "negative" )

mix_grid_degenerated = vtkUnstructuredGrid()
mix_grid_degenerated.DeepCopy( mix_grid )
for i in [ 1, 7, 11, 13 ]:
    reorder_cell_nodes( mix_grid_degenerated, i, to_change_order_for_degenerated_cells[ all_cell_names_mix_grid[ i ] ] )


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
                                           ( 0.0, 0.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 0.0, 1.0 ) ]
        for i in range( one_hex.GetCell( 0 ).GetNumberOfPoints() ):
            assert one_hex.GetCell( 0 ).GetPoints().GetPoint( i ) == expected_nodes_coords_modified[ i ]

        # reorder the cell again to make it valid again
        reorder_cell_nodes( one_hex, 0, to_change_order[ "Hexahedron" ] )
        expected_nodes_coords_modified2 = [ ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ),
                                            ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ) ]
        for i in range( one_hex.GetCell( 0 ).GetNumberOfPoints() ):
            assert one_hex.GetCell( 0 ).GetPoints().GetPoint( i ) == expected_nodes_coords_modified2[ i ]

    def test_compute_mesh_cells_volume( self ):
        # yapf: disable
        grid_volumes = {
            hexahedrons_grid: [ 1.0, 1.0, 1.0, 1.0 ],
            hexahedrons_grid_invalid: [ 1.0, -1.0, 1.0, -1.0 ],
            tetras_grid: [ 0.167, 0.167, 0.167, 0.167 ],
            tetras_grid_invalid: [ 0.167, -0.167, 0.167, -0.167 ],
            pyramids_grid: [ 0.333, 0.333, 0.333, 0.333 ],
            pyramids_grid_invalid: [ 0.333, -0.333, 0.333, -0.333 ],
            voxels_grid: [ 1.0, 1.0, 1.0, 1.0 ],
            wedges_grid: [ 0.5, 0.5, 0.5, 0.5 ],
            wedges_grid_invalid: [ 0.5, -0.5, 0.5, -0.5 ],
            penta_prism_grid: [ 1.25, 1.25, 1.25, 1.25 ],
            penta_prism_grid_invalid: [ 1.25, -1.25, 1.25, -1.25 ],
            hexa_prism_grid: [ 1.5, 1.5, 1.5, 1.5 ],
            hexa_prism_grid_invalid: [ 1.5, -1.5, 1.5, -1.5 ],
            mix_grid: [ 1.0, 1.0, 0.333, 0.333, 0.167, 0.167, 1.5, 1.5, 1.0, 1.0, 0.25, 0.25, 1.25, 1.25 ],
            mix_grid_invalid: [ 1.0, -1.0, 0.333, -0.333, 0.167, -0.167, 1.5, -1.5, 1.0, -1.0, 0.25, -0.25, 1.25, -1.25 ]
        }
        # yapf: enable
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
        grid_options = {
            hexahedrons_grid: opt_hexahedrons_grid,
            hexahedrons_grid_invalid: opt_hexahedrons_grid_invalid,
            tetras_grid: opt_tetras_grid,
            tetras_grid_invalid: opt_tetras_grid_invalid,
            pyramids_grid: opt_pyramids_grid,
            pyramids_grid_invalid: opt_pyramids_grid_invalid,
            wedges_grid: opt_wedges_grid,
            wedges_grid_invalid: opt_wedges_grid_invalid,
            penta_prism_grid: opt_penta_prism_grid,
            penta_prism_grid_invalid: opt_penta_prism_grid,
            hexa_prism_grid: opt_hexa_prism_grid,
            hexa_prism_grid_invalid: opt_hexa_prism_grid_invalid,
            mix_grid: opt_mix_grid,
            mix_grid_invalid: opt_mix_grid_inv
        }
        for grid, needs_ordering in grid_needs_ordering.items():
            volumes = feo.compute_mesh_cells_volume( grid )
            opt_to_use = grid_options[ grid ]
            for i in range( len( volumes ) ):
                assert feo.is_cell_to_reorder( volumes[ i ], opt_to_use ) == needs_ordering[ i ]

    def test_cell_ids_to_reorder_by_cell_type( self ):
        options_per_grid = {
            hexahedrons_grid: opt_hexahedrons_grid,
            hexahedrons_grid_invalid: opt_hexahedrons_grid_invalid,
            tetras_grid: opt_tetras_grid,
            tetras_grid_invalid: opt_tetras_grid_invalid,
            pyramids_grid: opt_pyramids_grid,
            pyramids_grid_invalid: opt_pyramids_grid_invalid,
            wedges_grid: opt_wedges_grid,
            wedges_grid_invalid: opt_wedges_grid_invalid,
            penta_prism_grid: opt_penta_prism_grid,
            penta_prism_grid_invalid: opt_penta_prism_grid_invalid,
            hexa_prism_grid: opt_hexa_prism_grid,
            hexa_prism_grid_invalid: opt_hexa_prism_grid_invalid,
            mix_grid: opt_mix_grid,
            mix_grid_invalid: opt_mix_grid_inv
        }
        # yapf: disable
        expected_per_grid = {
            hexahedrons_grid: {},
            hexahedrons_grid_invalid: { 12: np.array( [ 1, 3 ] ) },
            tetras_grid: {},
            tetras_grid_invalid: { 10: np.array( [ 1, 3 ] ) },
            pyramids_grid: {},
            pyramids_grid_invalid: { 14: np.array( [ 1, 3 ] ) },
            wedges_grid: {},
            wedges_grid_invalid: { 13: np.array( [ 1, 3 ] ) },
            penta_prism_grid: {},
            penta_prism_grid_invalid: { 15: np.array( [ 1, 3 ] ) },
            hexa_prism_grid: {},
            hexa_prism_grid_invalid: { 16: np.array( [ 1, 3 ] ) },
            mix_grid: {},
            mix_grid_invalid: { 12: np.array( [ 1, 9 ] ), 14: np.array( [ 3 ] ), 10: np.array( [ 5 ] ),
                                16: np.array( [ 7 ] ), 13: np.array( [ 11 ] ), 15: np.array( [ 13 ] ) }
        }
        # yapf: enable
        for grid, options in options_per_grid.items():
            result = feo.cell_ids_to_reorder_by_cell_type( grid, options )
            for vtk_type, array in result.items():
                assert np.array_equal( array, expected_per_grid[ grid ][ vtk_type ] )

    def test_is_polygon_counterclockwise( self ):
        # yapf: disable
        polygons_available = {
            "triangle_ccw": np.array([ [0.0, 0.5, 0.33], [0.0, 1.5, 0.33], [0.0, 1.0, 0.67] ]),
            "triangle_cw": np.array([ [0.0, 0.5, 0.33], [0.0, 1.0, 0.67], [0.0, 1.5, 0.33] ]),
            "quad_ccw": np.array([ [0.0, 0.5, 0.33], [0.0, 1.5, 0.33], [0.0, 1.5, 0.67], [0.0, 0.5, 0.67] ]),
            "quad_cw": np.array([ [0.0, 0.5, 0.33], [0.0, 0.5, 0.67], [0.0, 1.5, 0.67], [0.0, 1.5, 0.33] ]),
            "hexagon_ccw": np.array([ [0.0, 0.5, 0.33], [0.0, 1.5, 0.33], [0.0, 2.0, 0.5], [0, 1.5, 0.67], [0, 0.5, 0.67], [0.0, 0.0, 0.5] ]),
            "hexagon_cw": np.array([ [0.0, 0.5, 0.33], [0.0, 0.0, 0.5], [0, 0.5, 0.67], [0, 1.5, 0.67], [0.0, 2.0, 0.5], [0.0, 1.5, 0.33] ]),
        }
        rotation_point = np.array([1, 1, 1])

        for polygon_name, polygon in polygons_available.items():
            subdivisions = 24
            all_alphas = [ degrees_to_radians( ( 360/subdivisions )*i ) for i in range( subdivisions ) ]
            all_betas = all_alphas.copy()
            all_gammas = all_alphas.copy()

            polygons_are_clockwise = list()
            for alpha_id in range( len( all_alphas ) ):
                for beta_id in range( len( all_betas ) ):
                    for gamma_id in range( len( all_betas ) ):
                        rotated_polygon = rotate_polygon_around_point( polygon, rotation_point, all_alphas[ alpha_id ],
                                                                       all_betas[ beta_id ], all_gammas[ gamma_id ] )
                        is_clockwise = feo.is_polygon_counterclockwise( rotated_polygon.tolist(), rotation_point.tolist() )
                        polygons_are_clockwise.append( is_clockwise )

        if "ccw" in polygon_name:
            assert False not in polygons_are_clockwise
        else:
            assert True not in polygons_are_clockwise

        concave_polygon = ( ( 0.0, 0.5, 0.33 ), ( 0.0, 1.5, 0.67 ), ( 0.0, 1.5, 0.33 ), ( 0.0, 0.5, 0.67 ) )
        with pytest.raises( ValueError ) as err_msg:
            feo.is_polygon_counterclockwise( concave_polygon, rotation_point.tolist() )
        assert str( err_msg.value ) == f"Polygon checked is concave with points: {concave_polygon}."
        # yapf: enable

    def test_reordering_functions( self ):
        # yapf: disable
        points_tetras_coords = [
            ( ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 0.0, 1.0 ) ), # valid
            ( ( 0.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 0.0, 0.0, 1.0 ) ), # invalid ordering, can be reordered
        ]
        assert feo.reorder_tetrahedron( points_tetras_coords[ 0 ] ) == ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        assert feo.reorder_tetrahedron( points_tetras_coords[ 1 ] ) == ((0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))

        points_pyrams_coords = [
            ( ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 0.5, 0.5, 1.0 ) ), # valid
            ( ( 1.0, 1.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 0.5, 0.5, 1.0 ) ), # invalid quad base ordering, can be reordered
            ( ( 1.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 0.5, 0.5, 1.0 ) ), # invalid base definition, cannot reorder
        ]
        assert feo.reorder_pyramid( points_pyrams_coords[ 0 ] ) == ((1.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 0.5, 1.0))
        assert feo.reorder_pyramid( points_pyrams_coords[ 1 ] ) == ((1.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 0.5, 1.0))
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_pyramid( points_pyrams_coords[ 2 ] )
        assert str( err_msg.value ) == "The first 4 points of your pyramid do not represent its base. No ordering possible."

        points_wedges_coords = [
            ( ( 0.0, 0.5, 1.0 ), ( 0.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 1.0, 0.5, 1.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ) ), # valid
            ( ( 0.0, 0.5, 1.0 ), ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.5, 1.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 0.0, 0.0 ) ), # two invalid bases ordering in the same way, can be reordered
            ( ( 0.0, 0.5, 1.0 ), ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.5, 1.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ) ), # one invalid base ordering creating degenerated wedge
            ( ( 0.0, 0.5, 1.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 1.0, 0.5, 1.0 ), ( 1.0, 0.0, 0.0 ) ), # the first / last 3 points do not represent the triangle base
        ]
        assert feo.reorder_wedge( points_wedges_coords[ 0 ] ) == ((0.0, 0.5, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.5, 1.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        assert feo.reorder_wedge( points_wedges_coords[ 1 ] ) == ((0.0, 0.5, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.5, 1.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_wedge( points_wedges_coords[ 2 ] )
        assert str( err_msg.value ) == ( "When looking at a wedge cell for reordering, we need to construct the two triangle faces that represent the basis. With respect to the centroid of the wedge, the faces are both oriented in the same direction with points0 '((0.0, 0.5, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0))' and with points1 '((1.0, 0.5, 1.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0))'. When respecting VTK convention, they should be oriented in opposite direction. This create a degenerated wedge that cannot be reordered." )
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_wedge( points_wedges_coords[ 3 ] )
        assert str( err_msg.value ) == ( "When looking at a wedge cell for reordering, we need to construct the two triangle faces that represent the basis. When checking its geometry, the first 3 points'((0.0, 0.5, 1.0), (0.0, 0.0, 0.0), (1.0, 1.0, 0.0))' and/or last 3 points '((0.0, 1.0, 0.0), (1.0, 0.5, 1.0), (1.0, 0.0, 0.0))' cannot represent the wedge basis because they created quad faces that are concave. This create a degenerated wedge that cannot be reordered." )

        points_hexas_coords = [
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 0.0, 1.0 ), ( 0.0, 0.0, 1.0 ) ), # valid
            ( ( 0.0, 1.0, 0.0 ), ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.0, 0.0, 0.0 ) ), # two invalid bases ordering in the same way, can be reordered
            ( ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 0.0, 1.0 ), ( 0.0, 0.0, 1.0 ) ), # one invalid base ordering creating degenerated hexahedron
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.0, 0.0, 1.0 ), ( 0.0, 0.0, 1.0 ) ), # the first / last 4 points do not represent the quad base
        ]
        assert feo.reorder_hexahedron( points_hexas_coords[ 0 ] ) == ((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0))
        assert feo.reorder_hexahedron( points_hexas_coords[ 1 ] ) == ((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0))
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_hexahedron( points_hexas_coords[ 2 ] )
        assert str( err_msg.value ) == ( "When looking at a hexahedron cell for reordering, we need to construct two quad faces that represent two faces that do not have a point common. With respect to the centroid of the hexahedron, the faces are not both oriented in the same direction with points0 '((0.0, 1.0, 1.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0))' and with points1 '((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0))'. When respecting VTK convention, they both should be oriented in the same direction. This create a degenerated hexahedron that cannot be reordered." )
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_hexahedron( points_hexas_coords[ 3 ] )
        assert str( err_msg.value ) == ( "When looking at a hexahedron cell for reordering, we need to construct two quad faces that represent two faces that do not have a point common. When checking its geometry, the first 4 points '((0.0, 1.0, 0.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (1.0, 1.0, 0.0))' and/or last 4 points '((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0))' cannot represent two hexahedron quad faces because they are concave. This create a degenerated hexahedron that cannot be reordered." )

        points_penta_prisms_coords = [
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( 0.5, 1.0, 1.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.0, 0.5 ), ( 0.5, 0.0, 1.0 ), ( -0.5, 0.0, 0.5 ) ), # valid
            ( ( 0.0, 1.0, 0.0 ), ( -0.5, 1.0, 0.5 ), ( 0.5, 1.0, 1.0 ), ( 1.5, 1.0, 0.5 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( -0.5, 0.0, 0.5 ), ( 0.5, 0.0, 1.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 0.0 ) ), # two invalid bases ordering in the same way, can be reordered
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( 0.5, 1.0, 1.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 0.0, 0.0 ), ( -0.5, 0.0, 0.5 ), ( 0.5, 0.0, 1.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 0.0 ) ), # one invalid base ordering creating degenerated pentagonal prism
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( -0.5, 1.0, 0.5 ), ( 0.5, 1.0, 1.0 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.0, 0.5 ), ( 0.5, 0.0, 1.0 ), ( -0.5, 0.0, 0.5 ) ), # the first / last 5 points do not represent the pentagon base
        ]
        assert feo.reorder_pentagonal_prism( points_penta_prisms_coords[ 0 ] ) == ((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.5, 1.0, 0.5), (0.5, 1.0, 1.0), (-0.5, 1.0, 0.5), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (0.5, 0.0, 1.0), (-0.5, 0.0, 0.5))
        assert feo.reorder_pentagonal_prism( points_penta_prisms_coords[ 1 ] ) == ((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.5, 1.0, 0.5), (0.5, 1.0, 1.0), (-0.5, 1.0, 0.5), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (0.5, 0.0, 1.0), (-0.5, 0.0, 0.5))
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_pentagonal_prism( points_penta_prisms_coords[ 2 ] )
        assert str( err_msg.value ) == ( "When looking at a pentagonal prism cell for reordering, we need to construct the two pentagon faces that represent the basis. With respect to the centroid of the wedge, the faces are oriented in opposite direction with points0 '((0.0, 1.0, 0.0), (-0.5, 1.0, 0.5), (0.5, 1.0, 1.0), (1.5, 1.0, 0.5), (1.0, 1.0, 0.0))' and with points1 '((0.0, 0.0, 0.0), (-0.5, 0.0, 0.5), (0.5, 0.0, 1.0), (1.5, 0.0, 0.5), (1.0, 0.0, 0.0))'. When respecting VTK convention, they should be oriented in the same direction. This create a degenerated pentagonal prism that cannot be reordered." )
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_pentagonal_prism( points_penta_prisms_coords[ 3 ] )
        assert str( err_msg.value ) == ( "When looking at a pentagonal prism cell for reordering, we need to construct the two pentagon faces that represent the basis. When checking its geometry, the first 5 points'((0.0, 1.0, 0.0), (0.5, 1.0, 1.0), (-0.5, 1.0, 0.5), (1.5, 1.0, 0.5), (1.0, 1.0, 0.0))' and/or last 5 points '((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (0.5, 0.0, 1.0), (-0.5, 0.0, 0.5))' cannot represent the pentagonal prism basis because they created pentagon faces that are concave. This create a degenerated pentagonal prism that cannot be reordered." )

        points_hexa_prisms_coords = [
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 1.0 ), ( 0.0, 0.0, 1.0 ), ( -0.5, 0.0, 0.5 ) ), # valid
            ( ( 0.0, 1.0, 0.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( 1.5, 1.0, 0.5 ), ( 1.0, 1.0, 0.0 ), ( 0.0, 0.0, 0.0 ), ( -0.5, 0.0, 0.5 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 0.0 ) ), # two invalid bases ordering in the same way, can be reordered
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( 1.0, 1.0, 1.0 ), ( 0.0, 1.0, 1.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 0.0, 0.0 ), ( -0.5, 0.0, 0.5 ), ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 1.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 0.0 ) ), # one invalid base ordering creating degenerated hexagonal prism
            ( ( 0.0, 1.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.5, 1.0, 0.5 ), ( 0.0, 1.0, 1.0 ), ( 1.0, 1.0, 1.0 ), ( -0.5, 1.0, 0.5 ), ( 0.0, 0.0, 0.0 ), ( 1.0, 0.0, 0.0 ), ( 1.5, 0.0, 0.5 ), ( 1.0, 0.0, 1.0 ), ( 0.0, 0.0, 1.0 ), ( -0.5, 0.0, 0.5 ) ), # the first / last 5 points do not represent the hexagon base
        ]
        assert feo.reorder_hexagonal_prism( points_hexa_prisms_coords[ 0 ] ) == ((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.5, 1.0, 0.5), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (-0.5, 1.0, 0.5), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0), (-0.5, 0.0, 0.5))
        assert feo.reorder_hexagonal_prism( points_hexa_prisms_coords[ 1 ] ) == ((1.0, 1.0, 0.0), (1.5, 1.0, 0.5), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (-0.5, 1.0, 0.5), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0), (-0.5, 0.0, 0.5), (0.0, 0.0, 0.0))
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_hexagonal_prism( points_hexa_prisms_coords[ 2 ] )
        assert str( err_msg.value ) == ( "When looking at a hexagonal prism cell for reordering, we need to construct the two hexagon faces that represent the basis. With respect to the centroid of the wedge, the faces are oriented in opposite direction with points0 '((0.0, 1.0, 0.0), (-0.5, 1.0, 0.5), (0.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.5, 1.0, 0.5), (1.0, 1.0, 0.0))' and with points1 '((0.0, 0.0, 0.0), (-0.5, 0.0, 0.5), (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.5, 0.0, 0.5), (1.0, 0.0, 0.0))'. When respecting VTK convention, they should be oriented in the same direction. This create a degenerated hexagonal prism that cannot be reordered." )
        with pytest.raises( ValueError ) as err_msg:
            feo.reorder_hexagonal_prism( points_hexa_prisms_coords[ 3 ] )
        assert str( err_msg.value ) == ( "When looking at a hexagonal prism cell for reordering, we need to construct the two hexagon faces that represent the basis. When checking its geometry, the first 6 points'((0.0, 1.0, 0.0), (-0.5, 1.0, 0.5), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (1.5, 1.0, 0.5), (1.0, 1.0, 0.0))' and/or last 6 points '((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.5), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0), (-0.5, 0.0, 0.5))' cannot represent the hexagonal prism basis because they created hexagon faces that are concave. This create a degenerated hexagonal prism that cannot be reordered." )
        # yapf: enable

    def test_cell_point_ids_ordering_method( self ):
        # yapf: disable
        assert feo.cell_point_ids_ordering_method( tetras_grid.GetCell( 0 ), 10 ) == ( ( 0, 1, 2, 3 ), False )
        assert feo.cell_point_ids_ordering_method( tetras_grid_invalid.GetCell( 0 ), 10 ) == ( ( 0, 1, 2, 3 ), False )
        assert feo.cell_point_ids_ordering_method( tetras_grid.GetCell( 1 ), 10 ) == ( ( 0, 1, 2, 3 ), False )
        assert feo.cell_point_ids_ordering_method( tetras_grid_invalid.GetCell( 1 ), 10 ) == ( ( 0, 1, 3, 2 ), True )

        assert feo.cell_point_ids_ordering_method( pyramids_grid.GetCell( 0 ), 14 ) == ( ( 0, 1, 2, 3, 4 ), False )
        assert feo.cell_point_ids_ordering_method( pyramids_grid_invalid.GetCell( 0 ), 14 ) == ( ( 0, 1, 2, 3, 4 ), False )
        assert feo.cell_point_ids_ordering_method( pyramids_grid.GetCell( 1 ), 14 ) == ( ( 0, 1, 2, 3, 4 ), False )
        assert feo.cell_point_ids_ordering_method( pyramids_grid_invalid.GetCell( 1 ), 14 ) == ( ( 0, 3, 2, 1, 4 ), True )

        assert feo.cell_point_ids_ordering_method( wedges_grid.GetCell( 0 ), 13 ) == ( ( 0, 1, 2, 3, 4, 5 ), False )
        assert feo.cell_point_ids_ordering_method( wedges_grid_invalid.GetCell( 0 ), 13 ) == ( ( 0, 1, 2, 3, 4, 5 ), False )
        assert feo.cell_point_ids_ordering_method( wedges_grid.GetCell( 1 ), 13 ) == ( ( 0, 1, 2, 3, 4, 5 ), False )
        assert feo.cell_point_ids_ordering_method( wedges_grid_invalid.GetCell( 1 ), 13 ) == ( ( 0, 2, 1, 3, 5, 4 ), True )

        assert feo.cell_point_ids_ordering_method( hexahedrons_grid.GetCell( 0 ), 12 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7 ), False )
        assert feo.cell_point_ids_ordering_method( hexahedrons_grid_invalid.GetCell( 0 ), 12 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7 ), False )
        assert feo.cell_point_ids_ordering_method( hexahedrons_grid.GetCell( 1 ), 12 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7 ), False )
        assert feo.cell_point_ids_ordering_method( hexahedrons_grid_invalid.GetCell( 1 ), 12 ) == ( ( 0, 3, 2, 1, 4, 7, 6, 5 ), True )

        assert feo.cell_point_ids_ordering_method( penta_prism_grid.GetCell( 0 ), 15 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ), False )
        assert feo.cell_point_ids_ordering_method( penta_prism_grid_invalid.GetCell( 0 ), 15 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ), False )
        assert feo.cell_point_ids_ordering_method( penta_prism_grid.GetCell( 1 ), 15 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ), False )
        assert feo.cell_point_ids_ordering_method( penta_prism_grid_invalid.GetCell( 1 ), 15 ) == ( ( 0, 4, 3, 2, 1, 5, 9, 8, 7, 6 ), True )

        assert feo.cell_point_ids_ordering_method( hexa_prism_grid.GetCell( 0 ), 16 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ), False )
        assert feo.cell_point_ids_ordering_method( hexa_prism_grid_invalid.GetCell( 0 ), 16 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ), False )
        assert feo.cell_point_ids_ordering_method( hexa_prism_grid.GetCell( 1 ), 16 ) == ( ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ), False )
        assert feo.cell_point_ids_ordering_method( hexa_prism_grid_invalid.GetCell( 1 ), 16 ) == ( ( 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7, 6 ), True )
        # yapf: enable

    def test_reorder_points_to_new_mesh( self ):
        options = opt( out, cell_names, "negative" )
        # single element grids except voxels because it is an invalid cell type for GEOS
        grid_cell_type_and_expected_volumes = {
            hexahedrons_grid_invalid: ( VTK_HEXAHEDRON, [ 1.0, 1.0, 1.0, 1.0 ] ),
            tetras_grid_invalid: ( VTK_TETRA, [ 0.167, 0.167, 0.167, 0.167 ] ),
            pyramids_grid_invalid: ( VTK_PYRAMID, [ 0.333, 0.333, 0.333, 0.333 ] ),
            wedges_grid_invalid: ( VTK_WEDGE, [ 0.5, 0.5, 0.5, 0.5 ] ),
            penta_prism_grid_invalid: ( VTK_PENTAGONAL_PRISM, [ 1.25, 1.25, 1.25, 1.25 ] ),
            hexa_prism_grid_invalid: ( VTK_HEXAGONAL_PRISM, [ 1.5, 1.5, 1.5, 1.5 ] )
        }
        for grid, cell_type_and_volumes in grid_cell_type_and_expected_volumes.items():
            new_invalid = vtkUnstructuredGrid()
            new_invalid.DeepCopy( grid )
            new_corrected, reorder_stats = feo.reorder_points_to_new_mesh( new_invalid, options )
            expected = {
                "Types reordered": [ VTK_TYPE_TO_NAME[ cell_type_and_volumes[ 0 ] ] ],
                "Number of cells reordered": [ 2 ],
                'Types non reordered because of errors': list(),
                'Number of cells non reordered because of errors': list(),
                'Error message given': list()
            }
            for prop in expected.keys():
                assert reorder_stats[ prop ] == expected[ prop ]
            volumes = feo.compute_mesh_cells_volume( new_corrected )
            expected_volumes = cell_type_and_volumes[ 1 ]
            for i in range( len( volumes ) ):
                assert round( float( volumes[ i ] ), 3 ) == expected_volumes[ i ]

        # mix elements grid
        mix_invalid = vtkUnstructuredGrid()
        mix_invalid.DeepCopy( mix_grid_invalid )
        new_mix_corrected, mix_stats = feo.reorder_points_to_new_mesh( mix_invalid, options )
        expected = {
            "Types reordered": [ VTK_TYPE_TO_NAME[ cell_type ] for cell_type in [ 10, 12, 13, 14, 15, 16 ] ],
            "Number of cells reordered": [ 1, 2, 1, 1, 1, 1 ],
            "Types non reordered because ordering is already correct": list(),
            "Number of cells non reordered because ordering is already correct": list(),
            "Types non reordered because of errors": list(),
            "Number of cells non reordered because of errors": list(),
            "Error message given": list()
        }
        for prop in expected.keys():
            assert mix_stats[ prop ] == expected[ prop ]
        volumes = feo.compute_mesh_cells_volume( new_mix_corrected )
        expected_volumes = [ 1.0, 1.0, 0.333, 0.333, 0.167, 0.167, 1.5, 1.5, 1.0, 1.0, 0.25, 0.25, 1.25, 1.25 ]
        for i in range( len( volumes ) ):
            assert round( float( volumes[ i ] ), 3 ) == expected_volumes[ i ]

        # mix elements grid
        options = opt( out, cell_names, "all" )
        mix_degenerated = vtkUnstructuredGrid()
        mix_degenerated.DeepCopy( mix_grid_degenerated )
        not_used, mix_degen_stats = feo.reorder_points_to_new_mesh( mix_degenerated, options )
        # yapf: disable
        expected = {
            "Types reordered": list(),
            "Number of cells reordered": list(),
            "Types non reordered because ordering is already correct": [ VTK_TYPE_TO_NAME[ cell_type ] for cell_type in [ 10, 14 ] ],
            "Number of cells non reordered because ordering is already correct": [ 2, 2 ],
            "Types non reordered because of errors": [ VTK_TYPE_TO_NAME[ cell_type ] for cell_type in [ 12, 13, 15, 16 ] ],
            "Number of cells non reordered because of errors": [ 4, 2, 2, 2 ],
            "Error message given": list()
        }
        # yapf: enable
        for prop in expected.keys():
            if prop == "Error message given":
                assert len( mix_degen_stats[ prop ] ) == 4
            else:
                assert mix_degen_stats[ prop ] == expected[ prop ]

    def test_fix_elements_orderings_execution( self ):
        # for mix_grid_invalid mesh, checks that reordered mesh was created and that reoredring_stats are valid
        write_mesh( mix_grid_invalid, test_file )
        invalidTest = False
        command = [
            "python", MESH_DOCTOR_FILEPATH, "-v", "-i", test_file.output, "fix_elements_orderings", "--cell_names",
            ",".join( map( str, cell_names ) ), "--volume_to_reorder", "all", "--data-mode", "binary", "--output",
            filepath_reordered_mesh
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
            # yapf: disable
            expected_stats: str = ( "Number of cells reordered:\n" +
                                    "\tCellType\tNumber\n" +
                                    "\tTetrahedron\t\t2\n" +
                                    "\tHexahedron\t\t4\n" +
                                    "\tWedge\t\t2\n" +
                                    "\tPyramid\t\t2\n" +
                                    "\tPrism5\t\t2\n" +
                                    "\tPrism6\t\t2" )
            # yapf: enable
            assert reordering_stats == expected_stats
        except Exception as e:
            logging.error( "Invalid command input. Test has failed." )
            logging.error( e )
            invalidTest = True
        os.remove( test_file.output )

        write_mesh( mix_grid_degenerated, test_file2 )
        command = [
            "python", MESH_DOCTOR_FILEPATH, "-v", "-i", test_file2.output, "fix_elements_orderings", "--cell_names",
            ",".join( map( str, cell_names ) ), "--volume_to_reorder", "all", "--data-mode", "binary", "--output",
            filepath_reordered_mesh2
        ]
        try:
            result = subprocess.run( command, shell=True, stderr=subprocess.PIPE, universal_newlines=True )
            os.remove( filepath_reordered_mesh2 )
            stderr = result.stderr
            assert result.returncode == 0
            raw_stderr = r"{}".format( stderr )
            pattern = r"\[.*?\]\[.*?\] (.*)"
            matches = re.findall( pattern, raw_stderr )
            no_log = "\n".join( matches )
            reordering_stats: str = no_log[ no_log.index( "Number of cells non reordered because of errors" ): ]
            # yapf: disable
            expected_stats: str = ( "Number of cells non reordered because of errors:\n" +
                                    "\tCellType\tNumber\n" +
                                    "\tHexahedron\t\t4\n" +
                                    "\tError message: When looking at a hexahedron cell for reordering, we need to construct two quad faces that represent two faces that do not have a point common. When checking its geometry, the first 4 points '((1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (2.0, 0.0, 0.0), (2.0, 1.0, 0.0))' and/or last 4 points '((1.0, 0.0, 1.0), (2.0, 1.0, 1.0), (2.0, 0.0, 1.0), (1.0, 1.0, 1.0))' cannot represent two hexahedron quad faces because they are concave. This create a degenerated hexahedron that cannot be reordered.\n" +
                                    "\tWedge\t\t2\n" +
                                    "\tError message: When looking at a wedge cell for reordering, we need to construct the two triangle faces that represent the basis. With respect to the centroid of the wedge, the faces are both oriented in the same direction with points0 '((4.0, 0.0, 1.0), (4.5, -0.5, 1.0), (5.0, 0.0, 1.0))' and with points1 '((5.0, 0.0, 0.0), (4.5, -0.5, 0.0), (4.0, 0.0, 0.0))'. When respecting VTK convention, they should be oriented in opposite direction. This create a degenerated wedge that cannot be reordered.\n" +
                                    "\tPrism5\t\t2\n" +
                                    "\tError message: When looking at a pentagonal prism cell for reordering, we need to construct the two pentagon faces that represent the basis. With respect to the centroid of the wedge, the faces are oriented in opposite direction with points0 '((5.0, 0.0, 1.0), (5.0, 1.0, 1.0), (5.5, 1.5, 1.0), (6.0, 0.5, 1.0), (5.5, -0.5, 1.0))' and with points1 '((6.0, 0.5, 2.0), (5.5, -0.5, 2.0), (5.0, 0.0, 2.0), (5.0, 1.0, 2.0), (5.5, 1.5, 2.0))'. When respecting VTK convention, they should be oriented in the same direction. This create a degenerated pentagonal prism that cannot be reordered.\n" +
                                    "\tPrism6\t\t2\n" +
                                    "\tError message: When looking at a hexagonal prism cell for reordering, we need to construct the two hexagon faces that represent the basis. With respect to the centroid of the wedge, the faces are oriented in opposite direction with points0 '((2.0, 0.0, 1.0), (2.0, 1.0, 1.0), (2.5, 1.5, 1.0), (3.0, 1.0, 1.0), (3.0, 0.0, 1.0), (2.5, -0.5, 1.0))' and with points1 '((2.0, 1.0, 2.0), (2.5, 1.5, 2.0), (3.0, 1.0, 2.0), (3.0, 0.0, 2.0), (2.5, -0.5, 2.0), (2.0, 0.0, 2.0))'. When respecting VTK convention, they should be oriented in the same direction. This create a degenerated hexagonal prism that cannot be reordered." )
            # yapf: enable
            assert reordering_stats == expected_stats
        except Exception as e:
            logging.error( "Invalid command input. Test has failed." )
            logging.error( e )
            invalidTest = True
        os.remove( test_file2.output )

        if invalidTest:
            raise ValueError( "test_fix_elements_orderings_execution has failed." )
