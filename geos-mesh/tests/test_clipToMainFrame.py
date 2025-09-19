# SPDX-FileContributor: Jacques Franc
# SPEDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
import itertools
from dataclasses import dataclass
from typing import Generator, Tuple, List
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkHexahedron, vtkMultiBlockDataSet
from vtkmodules.numpy_interface import dataset_adapter as dsa
import numpy as np
import numpy.typing as npt
from vtkmodules.util.vtkConstants import VTK_HEXAHEDRON

from geos.mesh.processing.ClipToMainFrame import ClipToMainFrame

Lx, Ly, Lz = 5, 2, 8
nx, ny, nz = 10, 10, 10


@dataclass( frozen=True )
class Expected:
    mesh: vtkUnstructuredGrid


def __gen_box( Lx: int, Ly: int, Lz: int, nx: int, ny: int, nz: int, multx: int, multy: int,
               multz: int ) -> Tuple[ npt.NDArray[ np.double ], npt.NDArray[ np.double ] ]:
    off: npt.NDArray[ np.double ] = np.max( [ Lx, Ly, Lz ] ) * np.asarray( [ [ multx, multy, multz ] ] )
    pts: List[ npt.NDArray[ np.double ] ] = []
    x, y, z = np.meshgrid( np.linspace( 0, Lx, nx ), np.linspace( 0, Ly, ny ), np.linspace( 0, Lz, ny ) )
    for i in range( x.shape[ 0 ] ):
        for j in range( x.shape[ 1 ] ):
            for k in range( x.shape[ 2 ] ):
                pts.append( np.asarray( [ x[ i, j, k ], y[ i, j, k ], z[ i, j, k ] ] ) )

    return ( np.asarray( pts ), off )


def __rotate_box( angles: npt.NDArray[ np.double ], pts: npt.NDArray[ np.double ] ) -> npt.NDArray[ np.double ]:
    a: np.double = angles[ 0 ]
    RX: npt.NDArray[ np.double ] = np.asarray( [ [ 1., 0, 0 ], [ 0, np.cos( a ), -np.sin( a ) ],
                                                 [ 0, np.sin( a ), np.cos( a ) ] ] )
    a = angles[ 1 ]
    RY: npt.NDArray[ np.double ] = np.asarray( [ [ np.cos( a ), 0, np.sin( a ) ], [ 0, 1, 0 ],
                                                 [ -np.sin( a ), 0, np.cos( a ) ] ] )
    a = angles[ 2 ]
    RZ: npt.NDArray[ np.double ] = np.asarray( [ [ np.cos( a ), -np.sin( a ), 0 ], [ np.sin( a ),
                                                                                     np.cos( a ), 0 ], [ 0, 0, 1 ] ] )

    return np.asarray( ( RZ @ RY @ RX @ pts.transpose() ).transpose() )


def __build_test_mesh( mxx: Tuple[ int, ...] ) -> Generator[ Expected, None, None ]:
    # generate random points in a box Lx, Ly, Lz
    # np.random.seed(1) # for reproducibility
    np.random.default_rng()

    #test all quadrant
    multx: int
    multy: int
    multz: int
    multx, multy, multz = mxx
    pts: npt.NDArray[ np.double ]
    off: npt.NDArray[ np.double ]
    pts, off = __gen_box( Lx, Ly, Lz, nx, ny, nz, multx, multy, multz )

    angles: npt.NDArray[ np.double ] = -2 * np.pi + np.random.randn( 1, 3 ) * np.pi  # random angles in rad
    pts = __rotate_box( angles[ 0 ], pts )
    pts[ :, 0 ] += off[ 0 ][ 0 ]
    pts[ :, 1 ] += off[ 0 ][ 1 ]
    pts[ :, 2 ] += off[ 0 ][ 2 ]

    # Creating multiple meshes, each time with a different angles
    mesh = vtkUnstructuredGrid()
    vpts = vtkPoints()
    vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
    mesh.SetPoints( vpts )

    ids = vtkIdList()
    for i in range( nx - 1 ):
        for j in range( ny - 1 ):
            for k in range( nz - 1 ):
                hex = vtkHexahedron()
                ids = hex.GetPointIds()
                ids.SetId( 0, i + j * nx + k * nx * ny )
                ids.SetId( 1, i + j * nx + k * nx * ny + 1 )
                ids.SetId( 2, i + j * nx + k * nx * ny + nx * ny + 1 )
                ids.SetId( 3, i + j * nx + k * nx * ny + nx * ny )
                ids.SetId( 4, i + j * nx + k * nx * ny + nx )
                ids.SetId( 5, i + j * nx + k * nx * ny + nx + 1 )
                ids.SetId( 6, i + j * nx + k * nx * ny + nx * ny + nx + 1 )
                ids.SetId( 7, i + j * nx + k * nx * ny + nx * ny + nx )
                mesh.InsertNextCell( VTK_HEXAHEDRON, ids )

    yield Expected( mesh=mesh )


# arg-type: ignore
@pytest.mark.parametrize(
    "expected", [ item for t in list( itertools.product( [ -1, 1 ], repeat=3 ) ) for item in __build_test_mesh( t ) ] )
def test_clipToMainFrame_polyhedron( expected: Expected ) -> None:
    """Test the ClipToMainFrameFilter on a rotated and translated box hexa mesh."""
    filter = ClipToMainFrame()
    filter.SetInputData( expected.mesh )
    filter.ComputeTransform()
    filter.Update()
    output_mesh: vtkUnstructuredGrid = filter.GetOutput()
    assert output_mesh.GetNumberOfPoints() == expected.mesh.GetNumberOfPoints()
    assert output_mesh.GetNumberOfCells() == expected.mesh.GetNumberOfCells()

    assert output_mesh.GetBounds()[ 0 ] == pytest.approx(
        0., abs=1e-4 ) and output_mesh.GetBounds()[ 2 ] == pytest.approx( 0., abs=1e-4 ) and np.max(
            [ np.abs( output_mesh.GetBounds()[ 4 ] ),
              np.abs( output_mesh.GetBounds()[ 5 ] ) ] ) == pytest.approx( Lz, abs=1e-4 )
    # test diagonal
    assert np.linalg.norm(
        np.array( [
            output_mesh.GetBounds()[ 1 ] - output_mesh.GetBounds()[ 0 ],
            output_mesh.GetBounds()[ 3 ] - output_mesh.GetBounds()[ 2 ],
            output_mesh.GetBounds()[ 5 ] - output_mesh.GetBounds()[ 4 ]
        ] ) ) == pytest.approx( np.linalg.norm( np.array( [ Lx, Ly, Lz ] ) ), abs=1e-4 )
    # test aligned with axis
    v0: npt.NDArray[ np.double ] = np.array( output_mesh.GetPoint( 1 ) ) - np.array( output_mesh.GetPoint( 0 ) )
    v1: npt.NDArray[ np.double ] = np.array( output_mesh.GetPoint( nx ) ) - np.array( output_mesh.GetPoint( 0 ) )
    v2: npt.NDArray[ np.double ] = np.array( output_mesh.GetPoint( nx * ny ) ) - np.array( output_mesh.GetPoint( 0 ) )
    assert np.abs( np.dot( v0, v1 ) ) < 1e-10
    assert np.abs( np.dot( v0, v2 ) ) < 1e-10
    assert np.abs( np.dot( v1, v2 ) ) < 1e-10


def test_clipToMainFrame_generic( dataSetTest: vtkMultiBlockDataSet ) -> None:
    """Test the ClipToMainFrameFilter on a MultiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    filter = ClipToMainFrame()
    filter.SetInputData( multiBlockDataSet )
    filter.ComputeTransform()
    filter.Update()
    print( filter.GetTransform() )
    output_mesh: vtkMultiBlockDataSet = filter.GetOutputDataObject( 0 )
    assert output_mesh.GetNumberOfPoints() == multiBlockDataSet.GetNumberOfPoints()
    assert output_mesh.GetNumberOfCells() == multiBlockDataSet.GetNumberOfCells()
    assert output_mesh.IsA( 'vtkMultiBlockDataSet' )
