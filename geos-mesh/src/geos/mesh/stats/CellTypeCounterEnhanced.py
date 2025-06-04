# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkIntArray,
)
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCell, vtkTable, vtkCellTypes, VTK_VERTEX )

from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.processing.meshQualityMetricHelpers import getAllCellTypes

__doc__ = """
CellTypeCounterEnhanced module is a vtk filter that computes cell type counts.

Filter input is a vtkUnstructuredGrid, output is a vtkTable

To use the filter:

.. code-block:: python

    from geos.mesh.stats.CellTypeCounterEnhanced import CellTypeCounterEnhanced

    # filter inputs
    input :vtkUnstructuredGrid

    # instantiate the filter
    filter :CellTypeCounterEnhanced = CellTypeCounterEnhanced()
    # set input data object
    filter.SetInputDataObject(input)
    # do calculations
    filter.Update()
    # get counts
    counts :CellTypeCounts = filter.GetCellTypeCountsObject()
"""


class CellTypeCounterEnhanced( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """CellTypeCounterEnhanced filter computes mesh stats."""
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType="vtkUnstructuredGrid", outputType="vtkTable" )
        self._counts: CellTypeCounts = CellTypeCounts()

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): Input port
            info (vtkInformationVector): Info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outTable: vtkTable = vtkTable.GetData( outInfoVec, 0 )
        assert inData is not None, "Input mesh is undefined."
        assert outTable is not None, "Output table is undefined."

        # compute cell type counts
        self._counts.reset()
        self._counts.setTypeCount( VTK_VERTEX, inData.GetNumberOfPoints() )
        for i in range( inData.GetNumberOfCells() ):
            cell: vtkCell = inData.GetCell( i )
            self._counts.addType( cell.GetCellType() )

        # create output table
        # first reset output table
        outTable.RemoveAllRows()
        outTable.RemoveAllColumns()
        outTable.SetNumberOfRows( 1 )

        # create columns per types
        for cellType in getAllCellTypes():
            array: vtkIntArray = vtkIntArray()
            array.SetName( vtkCellTypes.GetClassNameFromTypeId( cellType ) )
            array.SetNumberOfComponents( 1 )
            array.SetNumberOfValues( 1 )
            array.SetValue( 0, self._counts.getTypeCount( cellType ) )
            outTable.AddColumn( array )
        return 1

    def GetCellTypeCountsObject( self: Self ) -> CellTypeCounts:
        """Get CellTypeCounts object.

        Returns:
            CellTypeCounts: CellTypeCounts object.
        """
        return self._counts