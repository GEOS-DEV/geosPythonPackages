import pytest
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray, vtkTetra, vtkUnstructuredGrid,
    VTK_TETRA
)
from geos.mesh.doctor.filters.Checks import AllChecks, MainChecks


@pytest.fixture
def simple_mesh_with_issues() -> vtkUnstructuredGrid:
    """Create a simple test mesh with known issues for testing checks.
    
    This mesh includes:
    - Collocated nodes (points 0 and 3 are at the same location)
    - A very small volume element
    - Wrong support elements (duplicate node indices in cells)
    
    Returns:
        vtkUnstructuredGrid: Test mesh with various issues
    """
    mesh = vtkUnstructuredGrid()
    
    # Create points with some collocated nodes
    points = vtkPoints()
    points.InsertNextPoint(0.0, 0.0, 0.0)  # Point 0
    points.InsertNextPoint(1.0, 0.0, 0.0)  # Point 1
    points.InsertNextPoint(0.0, 1.0, 0.0)  # Point 2
    points.InsertNextPoint(0.0, 0.0, 0.0)  # Point 3 - duplicate of Point 0
    points.InsertNextPoint(0.0, 0.0, 1.0)  # Point 4
    points.InsertNextPoint(2.0, 0.0, 0.0)  # Point 5
    points.InsertNextPoint(2.01, 0.0, 0.0)  # Point 6 - very close to Point 5 (small volume)
    points.InsertNextPoint(2.0, 0.01, 0.0)  # Point 7 - creates tiny element
    points.InsertNextPoint(2.0, 0.0, 0.01)  # Point 8 - creates tiny element
    mesh.SetPoints(points)
    
    # Create cells
    cells = vtkCellArray()
    cell_types = []
    
    # Normal tetrahedron
    tet1 = vtkTetra()
    tet1.GetPointIds().SetId(0, 0)
    tet1.GetPointIds().SetId(1, 1)
    tet1.GetPointIds().SetId(2, 2)
    tet1.GetPointIds().SetId(3, 4)
    cells.InsertNextCell(tet1)
    cell_types.append(VTK_TETRA)
    
    # Tetrahedron with duplicate node indices (wrong support)
    tet2 = vtkTetra()
    tet2.GetPointIds().SetId(0, 3)  # This is collocated with point 0
    tet2.GetPointIds().SetId(1, 1)
    tet2.GetPointIds().SetId(2, 2)
    tet2.GetPointIds().SetId(3, 0)  # Duplicate reference to same location
    cells.InsertNextCell(tet2)
    cell_types.append(VTK_TETRA)
    
    # Very small volume tetrahedron
    tet3 = vtkTetra()
    tet3.GetPointIds().SetId(0, 5)
    tet3.GetPointIds().SetId(1, 6)
    tet3.GetPointIds().SetId(2, 7)
    tet3.GetPointIds().SetId(3, 8)
    cells.InsertNextCell(tet3)
    cell_types.append(VTK_TETRA)
    
    mesh.SetCells(cell_types, cells)
    return mesh


@pytest.fixture
def clean_mesh() -> vtkUnstructuredGrid:
    """Create a clean test mesh without issues.
    
    Returns:
        vtkUnstructuredGrid: Clean test mesh
    """
    mesh = vtkUnstructuredGrid()
    
    # Create well-separated points
    points = vtkPoints()
    points.InsertNextPoint(0.0, 0.0, 0.0)  # Point 0
    points.InsertNextPoint(1.0, 0.0, 0.0)  # Point 1
    points.InsertNextPoint(0.0, 1.0, 0.0)  # Point 2
    points.InsertNextPoint(0.0, 0.0, 1.0)  # Point 3
    mesh.SetPoints(points)
    
    # Create a single clean tetrahedron
    cells = vtkCellArray()
    cell_types = []
    
    tet = vtkTetra()
    tet.GetPointIds().SetId(0, 0)
    tet.GetPointIds().SetId(1, 1)
    tet.GetPointIds().SetId(2, 2)
    tet.GetPointIds().SetId(3, 3)
    cells.InsertNextCell(tet)
    cell_types.append(VTK_TETRA)
    
    mesh.SetCells(cell_types, cells)
    return mesh


@pytest.fixture
def all_checks_filter() -> AllChecks:
    """Create a fresh AllChecks filter for each test."""
    return AllChecks()


@pytest.fixture
def main_checks_filter() -> MainChecks:
    """Create a fresh MainChecks filter for each test."""
    return MainChecks()


class TestAllChecks:
    """Test class for AllChecks filter functionality."""
    
    def test_filter_creation(self, all_checks_filter: AllChecks):
        """Test that AllChecks filter can be created successfully."""
        assert all_checks_filter is not None
        assert hasattr(all_checks_filter, 'getAvailableChecks')
        assert hasattr(all_checks_filter, 'setChecksToPerform')
        assert hasattr(all_checks_filter, 'setCheckParameter')
    
    def test_available_checks(self, all_checks_filter: AllChecks):
        """Test that all expected checks are available."""
        available_checks = all_checks_filter.getAvailableChecks()
        
        # Check that we have the expected checks for AllChecks
        expected_checks = [
            'collocated_nodes',
            'element_volumes',
            'non_conformal',
            'self_intersecting_elements',
            'supported_elements'
        ]
        
        for check in expected_checks:
            assert check in available_checks, f"Check '{check}' should be available"
    
    def test_default_parameters(self, all_checks_filter: AllChecks):
        """Test that default parameters are correctly retrieved."""
        available_checks = all_checks_filter.getAvailableChecks()
        
        for check_name in available_checks:
            defaults = all_checks_filter.getDefaultParameters(check_name)
            assert isinstance(defaults, dict), f"Default parameters for '{check_name}' should be a dict"
            
        # Test specific known defaults
        collocated_defaults = all_checks_filter.getDefaultParameters('collocated_nodes')
        assert 'tolerance' in collocated_defaults
        
        volume_defaults = all_checks_filter.getDefaultParameters('element_volumes')
        assert 'min_volume' in volume_defaults
    
    def test_set_checks_to_perform(self, all_checks_filter: AllChecks):
        """Test setting specific checks to perform."""
        # Set specific checks
        checks_to_perform = ['collocated_nodes', 'element_volumes']
        all_checks_filter.setChecksToPerform(checks_to_perform)
        
        # Verify by checking if the filter state changed
        assert hasattr(all_checks_filter, 'm_checks_to_perform')
        assert all_checks_filter.m_checks_to_perform == checks_to_perform
    
    def test_set_check_parameter(self, all_checks_filter: AllChecks):
        """Test setting parameters for specific checks."""
        # Set a tolerance parameter for collocated nodes
        all_checks_filter.setCheckParameter('collocated_nodes', 'tolerance', 1e-6)
        
        # Set minimum volume for element volumes
        all_checks_filter.setCheckParameter('element_volumes', 'min_volume', 0.001)
        
        # Verify parameters are stored
        assert 'collocated_nodes' in all_checks_filter.m_check_parameters
        assert all_checks_filter.m_check_parameters['collocated_nodes']['tolerance'] == 1e-6
        assert all_checks_filter.m_check_parameters['element_volumes']['min_volume'] == 0.001
    
    def test_set_all_checks_parameter(self, all_checks_filter: AllChecks):
        """Test setting a parameter that applies to all compatible checks."""
        # Set tolerance for all checks that support it
        all_checks_filter.setAllChecksParameter('tolerance', 1e-8)
        
        # Check that tolerance was set for checks that support it
        if 'collocated_nodes' in all_checks_filter.m_check_parameters:
            assert all_checks_filter.m_check_parameters['collocated_nodes']['tolerance'] == 1e-8
    
    def test_process_mesh_with_issues(self, all_checks_filter: AllChecks, simple_mesh_with_issues: vtkUnstructuredGrid):
        """Test processing a mesh with known issues."""
        # Configure for specific checks
        all_checks_filter.setChecksToPerform(['collocated_nodes', 'element_volumes'])
        all_checks_filter.setCheckParameter('collocated_nodes', 'tolerance', 1e-12)
        all_checks_filter.setCheckParameter('element_volumes', 'min_volume', 1e-3)
        
        # Process the mesh
        all_checks_filter.SetInputDataObject(0, simple_mesh_with_issues)
        all_checks_filter.Update()
        
        # Check results
        results = all_checks_filter.getCheckResults()
        
        assert 'collocated_nodes' in results
        assert 'element_volumes' in results
        
        # Check that collocated nodes were found
        collocated_result = results['collocated_nodes']
        assert hasattr(collocated_result, 'nodes_buckets')
        # We expect to find collocated nodes (points 0 and 3)
        assert len(collocated_result.nodes_buckets) > 0
        
        # Check that volume issues were detected
        volume_result = results['element_volumes']
        assert hasattr(volume_result, 'element_volumes')
    
    def test_process_clean_mesh(self, all_checks_filter: AllChecks, clean_mesh: vtkUnstructuredGrid):
        """Test processing a clean mesh without issues."""
        # Configure checks
        all_checks_filter.setChecksToPerform(['collocated_nodes', 'element_volumes'])
        all_checks_filter.setCheckParameter('collocated_nodes', 'tolerance', 1e-12)
        all_checks_filter.setCheckParameter('element_volumes', 'min_volume', 1e-6)
        
        # Process the mesh
        all_checks_filter.SetInputDataObject(0, clean_mesh)
        all_checks_filter.Update()
        
        # Check results
        results = all_checks_filter.getCheckResults()
        
        assert 'collocated_nodes' in results
        assert 'element_volumes' in results
        
        # Check that no issues were found
        collocated_result = results['collocated_nodes']
        assert len(collocated_result.nodes_buckets) == 0
        
        volume_result = results['element_volumes']
        assert len(volume_result.element_volumes) == 0
    
    def test_output_mesh_unchanged(self, all_checks_filter: AllChecks, clean_mesh: vtkUnstructuredGrid):
        """Test that the output mesh is unchanged from the input (checks don't modify geometry)."""
        original_num_points = clean_mesh.GetNumberOfPoints()
        original_num_cells = clean_mesh.GetNumberOfCells()
        
        # Process the mesh
        all_checks_filter.SetInputDataObject(0, clean_mesh)
        all_checks_filter.Update()
        
        # Get output mesh
        output_mesh = all_checks_filter.getGrid()
        
        # Verify structure is unchanged
        assert output_mesh.GetNumberOfPoints() == original_num_points
        assert output_mesh.GetNumberOfCells() == original_num_cells
        
        # Verify points are the same
        for i in range(original_num_points):
            original_point = clean_mesh.GetPoint(i)
            output_point = output_mesh.GetPoint(i)
            assert original_point == output_point


class TestMainChecks:
    """Test class for MainChecks filter functionality."""
    
    def test_filter_creation(self, main_checks_filter: MainChecks):
        """Test that MainChecks filter can be created successfully."""
        assert main_checks_filter is not None
        assert hasattr(main_checks_filter, 'getAvailableChecks')
        assert hasattr(main_checks_filter, 'setChecksToPerform')
        assert hasattr(main_checks_filter, 'setCheckParameter')
    
    def test_available_checks(self, main_checks_filter: MainChecks):
        """Test that main checks are available (subset of all checks)."""
        available_checks = main_checks_filter.getAvailableChecks()
        
        # MainChecks should have a subset of checks
        expected_main_checks = [
            'collocated_nodes',
            'element_volumes',
            'self_intersecting_elements'
        ]
        
        for check in expected_main_checks:
            assert check in available_checks, f"Main check '{check}' should be available"
    
    def test_process_mesh(self, main_checks_filter: MainChecks, simple_mesh_with_issues: vtkUnstructuredGrid):
        """Test processing a mesh with MainChecks."""
        # Process the mesh with default configuration
        main_checks_filter.SetInputDataObject(0, simple_mesh_with_issues)
        main_checks_filter.Update()
        
        # Check that results are obtained
        results = main_checks_filter.getCheckResults()
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check that main checks were performed
        available_checks = main_checks_filter.getAvailableChecks()
        for check_name in available_checks:
            if check_name in results:
                result = results[check_name]
                assert result is not None


class TestFilterComparison:
    """Test class for comparing AllChecks and MainChecks filters."""
    
    def test_all_checks_vs_main_checks_availability(self, all_checks_filter: AllChecks, main_checks_filter: MainChecks):
        """Test that MainChecks is a subset of AllChecks."""
        all_checks = set(all_checks_filter.getAvailableChecks())
        main_checks = set(main_checks_filter.getAvailableChecks())
        
        # MainChecks should be a subset of AllChecks
        assert main_checks.issubset(all_checks), "MainChecks should be a subset of AllChecks"
        
        # AllChecks should have more checks than MainChecks
        assert len(all_checks) >= len(main_checks), "AllChecks should have at least as many checks as MainChecks"
    
    def test_parameter_consistency(self, all_checks_filter: AllChecks, main_checks_filter: MainChecks):
        """Test that parameter handling is consistent between filters."""
        # Get common checks
        all_checks = set(all_checks_filter.getAvailableChecks())
        main_checks = set(main_checks_filter.getAvailableChecks())
        common_checks = all_checks.intersection(main_checks)
        
        # Test that default parameters are the same for common checks
        for check_name in common_checks:
            all_defaults = all_checks_filter.getDefaultParameters(check_name)
            main_defaults = main_checks_filter.getDefaultParameters(check_name)
            assert all_defaults == main_defaults, f"Default parameters should be the same for '{check_name}'"


class TestErrorHandling:
    """Test class for error handling and edge cases."""
    
    def test_invalid_check_name(self, all_checks_filter: AllChecks):
        """Test handling of invalid check names."""
        # Try to set an invalid check
        invalid_checks = ['nonexistent_check']
        all_checks_filter.setChecksToPerform(invalid_checks)
        
        # The filter should handle this gracefully
        # (The actual behavior depends on implementation - it might warn or ignore)
        assert all_checks_filter.m_checks_to_perform == invalid_checks
    
    def test_invalid_parameter_name(self, all_checks_filter: AllChecks):
        """Test handling of invalid parameter names."""
        # Try to set an invalid parameter
        all_checks_filter.setCheckParameter('collocated_nodes', 'invalid_param', 123)
        
        # This should not crash the filter
        assert 'collocated_nodes' in all_checks_filter.m_check_parameters
        assert 'invalid_param' in all_checks_filter.m_check_parameters['collocated_nodes']
    
    def test_empty_mesh(self, all_checks_filter: AllChecks):
        """Test handling of empty mesh."""
        # Create an empty mesh
        empty_mesh = vtkUnstructuredGrid()
        empty_mesh.SetPoints(vtkPoints())
        
        # Process the empty mesh
        all_checks_filter.setChecksToPerform(['collocated_nodes'])
        all_checks_filter.SetInputDataObject(0, empty_mesh)
        all_checks_filter.Update()
        
        # Should complete without error
        results = all_checks_filter.getCheckResults()
        assert isinstance(results, dict)
