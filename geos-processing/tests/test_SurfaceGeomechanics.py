# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file

import pytest
from typing_extensions import Self, Union
import numpy.typing as npt
import numpy as np

from dataclasses import dataclass, field
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkTriangle, vtkCellArray
from vtkmodules.vtkCommonCore import vtkPoints, vtkFloatArray
import vtkmodules.util.numpy_support as vnp
from geos.processing.post_processing.SurfaceGeomechanics import SurfaceGeomechanics


@dataclass
class TriangulatedSurfaceTestCase:
    pointsCoords: npt.NDArray[ np.float64 ]
    triangles: list[ tuple[ int, int, int ] ]
    mesh: vtkPolyData = field( init=False )
    attributes: Union[ None, dict[ str, npt.NDArray ] ]

    def __post_init__( self: Self ) -> None:
        """Generate the mesh."""
        vtk_points = vtkPoints()
        for coord in self.pointsCoords:
            vtk_points.InsertNextPoint( coord )

        vtk_triangles = vtkCellArray()
        for t in self.triangles:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId( 0, t[ 0 ] )
            triangle.GetPointIds().SetId( 1, t[ 1 ] )
            triangle.GetPointIds().SetId( 2, t[ 2 ] )
            vtk_triangles.InsertNextCell( triangle )

        polydata = vtkPolyData()
        polydata.SetPoints( vtk_points )
        polydata.SetPolys( vtk_triangles )

        self.mesh = polydata

        if self.attributes is not None:
            for attrName, attrValue in self.attributes.items():
                newAttribute: vtkFloatArray = vnp.numpy_to_vtk( attrValue, deep=True )
                newAttribute.SetName( attrName )

                self.mesh.GetCellData().AddArray( newAttribute )
                self.mesh.Modified()

                assert self.mesh.GetCellData().HasArray( attrName )


# yapf: disable
pointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0, 0, 0 ], [ 0, 1, 0 ], [ 0, 2, 0 ], [ 0, 2, 1 ], [ 1, 1, 1.5 ], [ 0, 0, 1 ] ] )
triangles: list[ tuple[ int, int, int ] ] = [ ( 0, 1, 5 ), ( 1, 4, 5 ), ( 1, 2, 3 ), ( 1, 4, 3 ) ]
attributes: dict[ str, npt.NDArray ] = { "traction": np.array( [ [ -9e-10, 3e-15, 0.0 ], [ -9e-10, 3e-15, 0.0 ], [ 0.0, 3e-15, -3e-17 ], [ 0.0, 3e-15, -3e-17 ], ] ),
                                         "displacementJump": np.array( [ [ 4e-02, 8e-07, 3e-08 ], [ 4e-02, 8e-07, 3e-08 ], [ 2e-02, 4e-07, -8e-08 ], [ 2e-02, 4e-07, -8e-08 ], ] )
}
# yapf: enable


def test_SurfaceGeomechanics() -> None:
    """Test SurfaceGeomechanics vtk filter."""
    testCase: TriangulatedSurfaceTestCase = TriangulatedSurfaceTestCase( pointsCoords, triangles, attributes )

    sgFilter: SurfaceGeomechanics = SurfaceGeomechanics( testCase.mesh )

    assert sgFilter.applyFilter()

    mesh: vtkPolyData = sgFilter.GetOutputMesh()
    assert mesh.GetCellData().HasArray( "SCU" )
    assert mesh.GetCellData().HasArray( "displacementJump_XYZ" )


def test_failingSurfaceGeomechanics() -> None:
    """Test failing of SurfaceGeomechanics due to absence of attributes in the mesh."""
    failingCase: TriangulatedSurfaceTestCase = TriangulatedSurfaceTestCase( pointsCoords, triangles, None )
    sgFilter: SurfaceGeomechanics = SurfaceGeomechanics( failingCase.mesh )
    with pytest.raises( AssertionError ):
        assert sgFilter.applyFilter()
