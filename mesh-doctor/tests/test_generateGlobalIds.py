from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkUnstructuredGrid, vtkVertex, VTK_VERTEX
from geos.mesh_doctor.actions.generateGlobalIds import __buildGlobalIds


def test_generateGlobalIds():
    points = vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )

    vertex = vtkVertex()
    vertex.GetPointIds().SetId( 0, 0 )

    vertices = vtkCellArray()
    vertices.InsertNextCell( vertex )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( [ VTK_VERTEX ], vertices )

    __buildGlobalIds( mesh, True, True )

    globalCellIds = mesh.GetCellData().GetGlobalIds()
    globalPointIds = mesh.GetPointData().GetGlobalIds()
    assert globalCellIds.GetNumberOfValues() == 1
    assert globalPointIds.GetNumberOfValues() == 1
