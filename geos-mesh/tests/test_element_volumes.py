import numpy as np
import numpy.typing as npt
import pytest
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkHexahedron, vtkTetra, vtkUnstructuredGrid, VTK_TETRA
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdList
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh.doctor.actions.element_volumes import Options, mesh_action
from geos.mesh.doctor.filters.ElementVolumes import ElementVolumes


@pytest.fixture
def tetra_mesh() -> vtkUnstructuredGrid:
    """Create a simple tetrahedron with known volume (1/6)"""
    points = vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )  # Point 0
    points.InsertNextPoint( 1, 0, 0 )  # Point 1
    points.InsertNextPoint( 0, 1, 0 )  # Point 2
    points.InsertNextPoint( 0, 0, 1 )  # Point 3

    tetra = vtkTetra()
    tetra.GetPointIds().SetId( 0, 0 )
    tetra.GetPointIds().SetId( 1, 1 )
    tetra.GetPointIds().SetId( 2, 2 )
    tetra.GetPointIds().SetId( 3, 3 )

    ug = vtkUnstructuredGrid()
    ug.SetPoints( points )
    ug.InsertNextCell( tetra.GetCellType(), tetra.GetPointIds() )
    return ug


@pytest.fixture
def hexa_mesh() -> vtkUnstructuredGrid:
    """Create a simple hexahedron with known volume (1.0)"""
    points = vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )  # Point 0
    points.InsertNextPoint( 1, 0, 0 )  # Point 1
    points.InsertNextPoint( 1, 1, 0 )  # Point 2
    points.InsertNextPoint( 0, 1, 0 )  # Point 3
    points.InsertNextPoint( 0, 0, 1 )  # Point 4
    points.InsertNextPoint( 1, 0, 1 )  # Point 5
    points.InsertNextPoint( 1, 1, 1 )  # Point 6
    points.InsertNextPoint( 0, 1, 1 )  # Point 7

    hexa = vtkHexahedron()
    for i in range( 8 ):
        hexa.GetPointIds().SetId( i, i )

    ug = vtkUnstructuredGrid()
    ug.SetPoints( points )
    ug.InsertNextCell( hexa.GetCellType(), hexa.GetPointIds() )
    return ug


@pytest.fixture
def negative_vol_mesh() -> vtkUnstructuredGrid:
    """Create a tetrahedron with negative volume (wrong winding)"""
    points = vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )  # Point 0
    points.InsertNextPoint( 1, 0, 0 )  # Point 1
    points.InsertNextPoint( 0, 1, 0 )  # Point 2
    points.InsertNextPoint( 0, 0, 1 )  # Point 3

    tetra = vtkTetra()
    # Switch two points to create negative volume
    tetra.GetPointIds().SetId( 0, 0 )
    tetra.GetPointIds().SetId( 1, 2 )  # Swapped from normal order
    tetra.GetPointIds().SetId( 2, 1 )  # Swapped from normal order
    tetra.GetPointIds().SetId( 3, 3 )

    ug = vtkUnstructuredGrid()
    ug.SetPoints( points )
    ug.InsertNextCell( tetra.GetCellType(), tetra.GetPointIds() )
    return ug


@pytest.fixture
def zero_vol_mesh() -> vtkUnstructuredGrid:
    """Create a tetrahedron with zero volume (coplanar points)"""
    points = vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )  # Point 0
    points.InsertNextPoint( 1, 0, 0 )  # Point 1
    points.InsertNextPoint( 0, 1, 0 )  # Point 2
    points.InsertNextPoint( 1, 1, 0 )  # Point 3 (coplanar with others)

    tetra = vtkTetra()
    tetra.GetPointIds().SetId( 0, 0 )
    tetra.GetPointIds().SetId( 1, 1 )
    tetra.GetPointIds().SetId( 2, 2 )
    tetra.GetPointIds().SetId( 3, 3 )

    ug = vtkUnstructuredGrid()
    ug.SetPoints( points )
    ug.InsertNextCell( tetra.GetCellType(), tetra.GetPointIds() )
    return ug


@pytest.fixture
def volume_filter() -> ElementVolumes:
    """Create a fresh ElementVolumes filter for each test"""
    return ElementVolumes()


def test_tetrahedron_volume( tetra_mesh: vtkUnstructuredGrid, volume_filter: ElementVolumes ) -> None:
    """Test volume calculation for a regular tetrahedron"""
    volume_filter.SetInputDataObject( 0, tetra_mesh )
    volume_filter.Update()
    output: vtkUnstructuredGrid = volume_filter.getGrid()

    volumes: npt.NDArray = vtk_to_numpy( output.GetCellData().GetArray( "MESH_DOCTOR_VOLUME" ) )
    expected_volume: float = 1 / 6  # Tetrahedron volume

    assert len( volumes ) == 1
    assert volumes[ 0 ] == pytest.approx( expected_volume, abs=1e-6 )


def test_hexahedron_volume( hexa_mesh: vtkUnstructuredGrid, volume_filter: ElementVolumes ) -> None:
    """Test volume calculation for a regular hexahedron"""
    volume_filter.SetInputDataObject( 0, hexa_mesh )
    volume_filter.Update()
    output: vtkUnstructuredGrid = volume_filter.getGrid()

    volumes: npt.NDArray = vtk_to_numpy( output.GetCellData().GetArray( "MESH_DOCTOR_VOLUME" ) )
    expected_volume: float = 1.0  # Unit cube volume

    assert len( volumes ) == 1
    assert volumes[ 0 ] == pytest.approx( expected_volume, abs=1e-6 )


def test_negative_volume_detection( negative_vol_mesh: vtkUnstructuredGrid, volume_filter: ElementVolumes ) -> None:
    """Test detection of negative volumes"""
    volume_filter.SetInputDataObject( 0, negative_vol_mesh )
    volume_filter.setReturnNegativeZeroVolumes( True )
    volume_filter.Update()

    output: vtkUnstructuredGrid = volume_filter.getGrid()
    volumes: npt.NDArray = vtk_to_numpy( output.GetCellData().GetArray( "MESH_DOCTOR_VOLUME" ) )

    assert len( volumes ) == 1
    assert volumes[ 0 ] < 0

    # Test getNegativeZeroVolumes method
    negative_zero_volumes: npt.NDArray = volume_filter.getNegativeZeroVolumes()
    assert len( negative_zero_volumes ) == 1
    assert negative_zero_volumes[ 0, 0 ] == 0  # First cell index
    assert negative_zero_volumes[ 0, 1 ] == volumes[ 0 ]  # Volume value


def test_zero_volume_detection( zero_vol_mesh: vtkUnstructuredGrid, volume_filter: ElementVolumes ) -> None:
    """Test detection of zero volumes"""
    volume_filter.SetInputDataObject( 0, zero_vol_mesh )
    volume_filter.setReturnNegativeZeroVolumes( True )
    volume_filter.Update()

    output: vtkUnstructuredGrid = volume_filter.getGrid()
    volumes: npt.NDArray = vtk_to_numpy( output.GetCellData().GetArray( "MESH_DOCTOR_VOLUME" ) )

    assert len( volumes ) == 1
    assert volumes[ 0 ] == pytest.approx( 0.0, abs=1e-6 )

    # Test getNegativeZeroVolumes method
    negative_zero_volumes: npt.NDArray = volume_filter.getNegativeZeroVolumes()
    assert len( negative_zero_volumes ) == 1
    assert negative_zero_volumes[ 0, 0 ] == 0  # First cell index
    assert negative_zero_volumes[ 0, 1 ] == pytest.approx( 0.0, abs=1e-6 )  # Volume value


def test_return_negative_zero_volumes_flag( volume_filter: ElementVolumes ) -> None:
    """Test setting and getting the returnNegativeZeroVolumes flag"""
    # Default should be False
    assert not volume_filter.m_returnNegativeZeroVolumes

    # Set to True and verify
    volume_filter.setReturnNegativeZeroVolumes( True )
    assert volume_filter.m_returnNegativeZeroVolumes

    # Set to False and verify
    volume_filter.setReturnNegativeZeroVolumes( False )
    assert not volume_filter.m_returnNegativeZeroVolumes


def test_mixed_mesh( tetra_mesh: vtkUnstructuredGrid, hexa_mesh: vtkUnstructuredGrid,
                     volume_filter: ElementVolumes ) -> None:
    """Test with a combined mesh containing multiple element types"""
    # Create a mixed mesh with both tet and hex
    mixed_mesh = vtkUnstructuredGrid()

    # Copy points from tetra_mesh
    tetra_points: vtkPoints = tetra_mesh.GetPoints()
    points = vtkPoints()
    for i in range( tetra_points.GetNumberOfPoints() ):
        points.InsertNextPoint( tetra_points.GetPoint( i ) )

    # Add points from hexa_mesh with offset
    hexa_points: vtkPoints = hexa_mesh.GetPoints()
    offset: int = points.GetNumberOfPoints()
    for i in range( hexa_points.GetNumberOfPoints() ):
        x, y, z = hexa_points.GetPoint( i )
        points.InsertNextPoint( x + 2, y, z )  # Offset in x-direction

    mixed_mesh.SetPoints( points )

    # Add tetra cell
    tetra_cell: vtkTetra = tetra_mesh.GetCell( 0 )
    ids: vtkIdList = tetra_cell.GetPointIds()
    mixed_mesh.InsertNextCell( tetra_cell.GetCellType(), ids.GetNumberOfIds(),
                               [ ids.GetId( i ) for i in range( ids.GetNumberOfIds() ) ] )

    # Add hexa cell with offset ids
    hexa_cell: vtkHexahedron = hexa_mesh.GetCell( 0 )
    ids: vtkIdList = hexa_cell.GetPointIds()
    hexa_ids: list[ int ] = [ ids.GetId( i ) + offset for i in range( ids.GetNumberOfIds() ) ]
    mixed_mesh.InsertNextCell( hexa_cell.GetCellType(), len( hexa_ids ), hexa_ids )

    # Apply filter
    volume_filter.SetInputDataObject( 0, mixed_mesh )
    volume_filter.Update()
    output: vtkUnstructuredGrid = volume_filter.getGrid()

    # Check volumes
    volumes: npt.NDArray = vtk_to_numpy( output.GetCellData().GetArray( "MESH_DOCTOR_VOLUME" ) )

    assert len( volumes ) == 2
    assert volumes[ 0 ] == pytest.approx( 1 / 6, abs=1e-6 )  # Tetrahedron volume
    assert volumes[ 1 ] == pytest.approx( 1.0, abs=1e-6 )  # Hexahedron volume


def test_simple_tet():
    # creating a simple tetrahedron
    points = vtkPoints()
    points.SetNumberOfPoints( 4 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 0, 1, 0 ) )
    points.SetPoint( 3, ( 0, 0, 1 ) )

    cell_types = [ VTK_TETRA ]
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
    mesh.SetCells( cell_types, cells )

    result = mesh_action( mesh, Options( min_volume=1. ) )

    assert len( result.element_volumes ) == 1
    assert result.element_volumes[ 0 ][ 0 ] == 0
    assert abs( result.element_volumes[ 0 ][ 1 ] - 1. / 6. ) < 10 * np.finfo( float ).eps

    result = mesh_action( mesh, Options( min_volume=0. ) )

    assert len( result.element_volumes ) == 0
