# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Any

from vtkmodules.vtkCommonDataModel import vtkPolyData
from geos.processing.post_processing.SurfaceGeomechanics import SurfaceGeomechanics


def test_SurfaceGeomechanics( dataSetTest: Any ) -> None:
    """Test SurfaceGeomechanics vtk filter."""
    surface: vtkPolyData = dataSetTest( "extractAndMergeFaultVtp" )

    sgFilter: SurfaceGeomechanics = SurfaceGeomechanics( surface )

    sgFilter.applyFilter()

    mesh: vtkPolyData = sgFilter.GetOutputMesh()
    assert mesh.GetCellData().HasArray( "SCU" )
    assert mesh.GetCellData().HasArray( "displacementJump_XYZ" )


def test_failingSurfaceGeomechanics() -> None:
    """Test failing of SurfaceGeomechanics due to absence of attributes in the mesh."""
    sgFilter: SurfaceGeomechanics = SurfaceGeomechanics( vtkPolyData() )
    with pytest.raises( AttributeError ):
        sgFilter.applyFilter()
