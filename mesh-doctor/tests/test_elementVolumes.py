import numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_TETRA, vtkCellArray, vtkTetra, vtkUnstructuredGrid
from geos.mesh_doctor.actions.elementVolumes import Options, __action


def test_simpleTet():
    # creating a simple tetrahedron
    points = vtkPoints()
    points.SetNumberOfPoints( 4 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 0, 1, 0 ) )
    points.SetPoint( 3, ( 0, 0, 1 ) )

    cellTypes = [ VTK_TETRA ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 4 )

    tet = vtkTetra()
    tet.GetPointIds().SetId( 0, 0 )
    tet.GetPointIds().SetId( 1, 1 )
    tet.GetPointIds().SetId( 2, 2 )
    tet.GetPointIds().SetId( 3, 3 )
    cells.InsertNextCell( tet )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    result = __action( mesh, Options( minVolume=1. ) )

    assert len( result.elementVolumes ) == 1
    assert result.elementVolumes[ 0 ][ 0 ] == 0
    assert abs( result.elementVolumes[ 0 ][ 1 ] - 1. / 6. ) < 10 * numpy.finfo( float ).eps

    result = __action( mesh, Options( minVolume=0. ) )

    assert len( result.elementVolumes ) == 0
