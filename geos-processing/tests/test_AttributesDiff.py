# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import numpy as np

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet

from geos.processing.generic_processing_tools.AttributesDiff import AttributesDiff
from geos.mesh.utils.arrayHelpers import getArrayInObject
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.utils.pieceEnum import Piece


def test_AttributesDiff( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test the filter AttributesDiff."""
    mesh1: vtkMultiBlockDataSet = dataSetTest( "2Ranks" )
    mesh2: vtkMultiBlockDataSet = dataSetTest( "4Ranks" )

    attributesDiffFilter: AttributesDiff = AttributesDiff()
    attributesDiffFilter.setMeshes( [ mesh1, mesh2 ] )
    attributesDiffFilter.logSharedAttributeInfo()
    dictAttributesToCompare: dict[ Piece, set[ str ] ] = {
        Piece.POINTS: { 'totalDisplacement', 'localToGlobalMap', 'mass', 'externalForce' },
        Piece.CELLS: {
            'elementVolume', 'pressure', 'rock_bulkModulus', 'rockPorosity_referencePorosity', 'water_dInternalEnergy',
            'water_dViscosity', 'water_viscosity', 'averageStrain', 'water_dEnthalpy', 'deltaPressure',
            'rockPerm_permeability', 'rockPorosity_initialPorosity', 'localToGlobalMap', 'averagePlasticStrain',
            'temperature', 'rock_density', 'averageStress', 'rockPorosity_porosity', 'rock_shearModulus',
            'water_density', 'mass', 'water_internalEnergy', 'water_dDensity', 'rockPorosity_grainBulkModulus',
            'elementCenter', 'water_enthalpy', 'rockPorosity_biotCoefficient'
        },
    }
    attributesDiffFilter.setDictAttributesToCompare( dictAttributesToCompare )
    attributesDiffFilter.applyFilter()
    mesh: vtkDataSet | vtkMultiBlockDataSet = mesh1.NewInstance()
    mesh.ShallowCopy( attributesDiffFilter.getOutput() )
    dictAttributesDiffNames: dict[ Piece, set[ str ] ] = attributesDiffFilter.getDictAttributesDiffNames()
    listFlattenIndexes = getBlockElementIndexesFlatten( mesh )
    for it in listFlattenIndexes:
        dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( it ) )  # type: ignore[union-attr]
        for piece, listDiffAttributesName in dictAttributesDiffNames.items():
            for diffAttributeName in listDiffAttributesName:
                test = getArrayInObject( dataset, diffAttributeName, piece )
                assert ( test < np.array( [ 0.0001 for _ in range( test.size ) ] ) ).all()
