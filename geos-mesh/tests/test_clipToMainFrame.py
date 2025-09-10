# SPDX-FileContributor: Jacques Franc
# SPEDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from dataclasses import dataclass
from typing import Generator
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkHexahedron
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader, vtkXMLMultiBlockDataWriter
import logging  # for debug
from vtkmodules.numpy_interface import dataset_adapter as dsa
import numpy as np
from vtkmodules.util.vtkConstants import VTK_HEXAHEDRON

from geos.mesh.processing.ClipToMainFrame import ClipToMainFrameFilter

Lx, Ly, Lz = 5, 2, 8
nx, ny, nz = 10, 10, 10


@dataclass( frozen=True )
class Expected:
    mesh: vtkUnstructuredGrid


def __gen_box( Lx: int, Ly: int, Lz: int, nx: int, ny: int, nz: int ) -> tuple[ np.ndarray, np.ndarray ]:
    # np.random.seed(1) # for reproducibility
    np.random.default_rng()
    off = np.random.randn( 1, 3 )
    pts = []
    x, y, z = np.meshgrid( np.linspace( 0, Lx, nx ), np.linspace( 0, Ly, ny ), np.linspace( 0, Lz, ny ) )
    for i in range( x.shape[ 0 ] ):
        for j in range( x.shape[ 1 ] ):
            for k in range( x.shape[ 2 ] ):
                pts.append( np.asarray( [ x[ i, j, k ], y[ i, j, k ], z[ i, j, k ] ] ) )

    return ( np.asarray( pts ), off )


def __rotate_box( angles: np.ndarray, pts: np.ndarray ) -> np.ndarray:
    a = angles[ 0 ]
    RX = np.asarray( [ [ 1., 0, 0 ], [ 0, np.cos( a ), -np.sin( a ) ], [ 0, np.sin( a ), np.cos( a ) ] ] )
    a = angles[ 1 ]
    RY = np.asarray( [ [ np.cos( a ), 0, np.sin( a ) ], [ 0, 1, 0 ], [ -np.sin( a ), 0, np.cos( a ) ] ] )
    a = angles[ 2 ]
    RZ = np.asarray( [ [ np.cos( a ), -np.sin( a ), 0 ], [ np.sin( a ), np.cos( a ), 0 ], [ 0, 0, 1 ] ] )

    return np.asarray( ( RZ @ RY @ RX @ pts.transpose() ).transpose() )


def __build_test_mesh() -> Generator[ Expected, None, None ]:
    # generate random points in a box Lx, Ly, Lz
    # np.random.seed(1) # for reproducibility
    np.random.default_rng()

    pts, off = __gen_box( Lx, Ly, Lz, nx, ny, nz )

    logging.info( f"Offseting of {off}" )
    logging.debug( f"Original pts : {pts}" )
    angles = -2 * np.pi + np.random.randn( 1, 3 ) * np.pi  # random angles in rad
    logging.info( f"angles {angles[0]}" )
    pts = __rotate_box( angles[ 0 ], pts )
    logging.debug( f"Rotated pts : {pts}" )
    pts[ :, 0 ] += off[ 0 ][ 0 ]
    pts[ :, 1 ] += off[ 0 ][ 1 ]
    pts[ :, 2 ] += off[ 0 ][ 2 ]
    logging.debug( f"Translated pts : {pts}" )

    # Creating multiple meshes, each time with a different angles
    mesh = vtkUnstructuredGrid()
    ( vtps := vtkPoints() ).SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
    mesh.SetPoints( vtps )

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


@pytest.mark.parametrize( "expected", __build_test_mesh() )
def test_clipToMainFrame_polyhedron( expected: Expected ) -> None:
    """Test the ClipToMainFrameFilter on a rotated and translated box hexa mesh."""
    ( filter := ClipToMainFrameFilter() ).SetInputData( expected.mesh )
    filter.Update()
    output_mesh = filter.GetOutput()
    assert output_mesh.GetNumberOfPoints() == expected.mesh.GetNumberOfPoints()
    assert output_mesh.GetNumberOfCells() == expected.mesh.GetNumberOfCells()
    assert output_mesh.GetBounds()[ 0 ] == pytest.approx(
        0., abs=1e-6 ) and output_mesh.GetBounds()[ 2 ] == pytest.approx(
            0., abs=1e-6 ) and output_mesh.GetBounds()[ 4 ] == pytest.approx( 0., abs=1e-6 )
    # test diagonal
    assert np.linalg.norm(
        np.array( [
            output_mesh.GetBounds()[ 1 ] - output_mesh.GetBounds()[ 0 ],
            output_mesh.GetBounds()[ 3 ] - output_mesh.GetBounds()[ 2 ],
            output_mesh.GetBounds()[ 5 ] - output_mesh.GetBounds()[ 4 ]
        ] ) ) == pytest.approx( np.linalg.norm( np.array( [ Lx, Ly, Lz ] ) ), abs=1e-5 )
    # test aligned with axis
    v0 = np.array( output_mesh.GetPoint( 1 ) ) - np.array( output_mesh.GetPoint( 0 ) )
    v1 = np.array( output_mesh.GetPoint( nx ) ) - np.array( output_mesh.GetPoint( 0 ) )
    v2 = np.array( output_mesh.GetPoint( nx * ny ) ) - np.array( output_mesh.GetPoint( 0 ) )
    assert np.abs( np.dot( v0, v1 ) ) < 1e-10
    assert np.abs( np.dot( v0, v2 ) ) < 1e-10
    assert np.abs( np.dot( v1, v2 ) ) < 1e-10

    #check if input has been modified
    # w = vtkXMLUnstructuredGridWriter()
    # w.SetFileName("./test_rotateAndTranslate_input.vtu")
    # w.SetInputData(expected.mesh)
    # w.Write()

    # w.SetFileName("./test_rotateAndTranslate.vtu")
    # w.SetInputData(output_mesh)
    # w.Write()


def test_clipToMainFrame_gen() -> None:
    """Test the ClipToMainFrameFilter on a MultiBlockDataSet."""
    reader = vtkXMLMultiBlockDataReader()
    reader.SetFileName( "./geos-mesh/tests/data/displacedFault.vtm" )
    reader.Update()
    input_mesh = reader.GetOutput()
    ( filter := ClipToMainFrameFilter() ).SetInputData( input_mesh )
    filter.Update()
    print( filter.GetTransform() )
    output_mesh = filter.GetOutputDataObject( 0 )
    assert output_mesh.GetNumberOfPoints() == input_mesh.GetNumberOfPoints()
    assert output_mesh.GetNumberOfCells() == input_mesh.GetNumberOfCells()

    # #check if input has been modified
    # w = vtkXMLMultiBlockDataWriter()
    # w.SetFileName( "./test_rotateAndTranslate_input.vtm" )
    # w.SetInputData( input_mesh )
    # w.Write()

    # w.SetFileName( "./test_rotateAndTranslate.vtm" )
    # w.SetInputData( output_mesh )
    # w.Write()
