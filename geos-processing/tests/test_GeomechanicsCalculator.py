# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid

from geos.mesh.utils.arrayHelpers import isAttributeInObject
from geos.processing.post_processing.GeomechanicsCalculator import ( GeomechanicsCalculator, BASIC_PROPERTIES, ADVANCED_PROPERTIES, LITHOSTATIC_STRESS )

@pytest.mark.parametrize( "computeAdvancedProperties", [
    ( False ),
    ( True ),
] )
def test_GeomechanicsCalculator(
    dataSetTest: vtkUnstructuredGrid,
    computeAdvancedProperties: bool,
) -> None:
    """Test the VTK filter GeomechanicsCalculator."""
    mesh: vtkUnstructuredGrid = dataSetTest( "extractAndMergeVolume" )

    geomechanicsCalculatorFilter: GeomechanicsCalculator = GeomechanicsCalculator( mesh, computeAdvancedProperties )
    geomechanicsCalculatorFilter.applyFilter()

    output: vtkUnstructuredGrid = geomechanicsCalculatorFilter.getOutput()

    for attribute in BASIC_PROPERTIES:
        if attribute != LITHOSTATIC_STRESS: # TODO: lithostatic stress calculation is deactivated until the formula is not fixed
            assert isAttributeInObject( output, attribute.attributeName, attribute.piece )

    if computeAdvancedProperties:
        for attribute in ADVANCED_PROPERTIES:
            assert isAttributeInObject( output, attribute.attributeName, attribute.piece )
