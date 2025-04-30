# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkIntArray,
    vtkInformation,
    vtkInformationVector,
    vtkPoints,
    reference,
    vtkIdList,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkIncrementalOctreePointLocator,
    vtkCellTypes,
    vtkCell,
)

__doc__ = """
MergeColocatedPoints module is a vtk filter that merges colocated points from input mesh.

Filter input and output types are vtkUnstructuredGrid.

.. Warning:: This operation uses geometrical tests that may not be accurate in case of very small cells.


To use the filter:

.. code-block:: python

    from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

    # filter inputs
    input :vtkUnstructuredGrid

    # instanciate the filter
    filter :MergeColocatedPoints = MergeColocatedPoints()
    # set input data object
    filter.SetInputDataObject(input)
    # do calculations
    filter.Update()
    # get output object
    output :vtkUnstructuredGrid = filter.GetOutputDataObject(0)
"""


class MergeColocatedPoints( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """MergeColocatedPoints filter merges duplacted points of the input mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
        output: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None, "Input mesh is undefined."
        assert output is not None, "Output mesh is undefined."
        vertexMap: list[ int ] = self.setMergePoints( inData, output )
        self.setCells( inData, output, vertexMap )
        return 1

    def setMergePoints( self: Self, input: vtkUnstructuredGrid, output: vtkUnstructuredGrid ) -> list[ int ]:
        """Merge duplicated points and set new points and attributes to output mesh.

        Args:
            input (vtkUnstructuredGrid): input mesh
            output (vtkUnstructuredGrid): output mesh

        Returns:
            list[int]: list containing new point ids.
        """
        vertexMap: list[ int ] = []
        newPoints: vtkPoints = vtkPoints()
        # use point locator to check for colocated points
        pointsLocator = vtkIncrementalOctreePointLocator()
        pointsLocator.InitPointInsertion( newPoints, input.GetBounds() )
        # create an array to count the number of colocated points
        vertexCount: vtkIntArray = vtkIntArray()
        vertexCount.SetName( "Count" )
        ptId = reference( 0 )
        countD: int = 0  # total number of colocated points
        for v in range( input.GetNumberOfPoints() ):
            inserted: bool = pointsLocator.InsertUniquePoint( input.GetPoints().GetPoint( v ), ptId )
            if inserted:
                vertexCount.InsertNextValue( 1 )
            else:
                vertexCount.SetValue( ptId, vertexCount.GetValue( ptId ) + 1 )
                countD = countD + 1
            vertexMap += [ ptId.get() ]

        output.SetPoints( pointsLocator.GetLocatorPoints() )
        # copy point attributes
        output.GetPointData().DeepCopy( input.GetPointData() )
        # add the array to points data
        output.GetPointData().AddArray( vertexCount )
        return vertexMap

    def setCells( self: Self, input: vtkUnstructuredGrid, output: vtkUnstructuredGrid, vertexMap: list[ int ] ) -> bool:
        """Set cell point ids and attributes to output mesh.

        Args:
            input (vtkUnstructuredGrid): input mesh
            output (vtkUnstructuredGrid): output mesh
            vertexMap (list[int)]): list containing new point ids

        Returns:
            bool: True if calculation successfully ended.
        """
        nbCells: int = input.GetNumberOfCells()
        nbPoints: int = output.GetNumberOfPoints()
        assert np.unique(
            vertexMap ).size == nbPoints, "The size of the list of point ids must be equal to the number of points."
        cellTypes: vtkCellTypes = vtkCellTypes()
        input.GetCellTypes( cellTypes )
        output.Allocate( nbCells )
        # create mesh cells
        for cellId in range( nbCells ):
            cell: vtkCell = input.GetCell( cellId )
            # create cells from point ids
            cellsID: vtkIdList = vtkIdList()
            for ptId in range( cell.GetNumberOfPoints() ):
                ptIdOld: int = cell.GetPointId( ptId )
                ptIdNew: int = vertexMap[ ptIdOld ]
                cellsID.InsertNextId( ptIdNew )
            output.InsertNextCell( cell.GetCellType(), cellsID )
        # copy cell attributes
        assert output.GetNumberOfCells() == nbCells, "Output and input mesh must have the same number of cells."
        output.GetCellData().DeepCopy( input.GetCellData() )
        return True
