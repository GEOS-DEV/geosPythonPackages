# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file

from collections.abc import MutableSequence

import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkDoubleArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellData,
    vtkCellLocator,
    vtkUnstructuredGrid,
)

from geos_posp.processing.vtkUtils import (
    computeCellCenterCoordinates,
    createEmptyAttribute,
    getVtkArrayInObject,
)
from geos.utils.Logger import Logger, getLogger

__doc__ = """
AttributeMappingFromCellCoords module is a vtk filter that map two identical mesh (or a mesh is
an extract from the other one) and create an attribute containing shared cell ids.

Filter input and output types are vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.AttributeMappingFromCellCoords import AttributeMappingFromCellCoords

    # filter inputs
    logger :Logger
    input :vtkUnstructuredGrid
    TransferAttributeName : str

    # instanciate the filter
    filter :AttributeMappingFromCellCoords = AttributeMappingFromCellCoords()
    # set the logger
    filter.SetLogger(logger)
    # set input data object
    filter.SetInputDataObject(input)
    # set Attribute to transfer
    filter.SetTransferAttributeNames(AttributeName)
    # set Attribute to compare
    filter.SetIDAttributeName(AttributeName)
    # do calculations
    filter.Update()
    # get output object
    output :vtkPolyData = filter.GetOutputDataObject(0)
    # get created attribute names
    newAttributeNames :set[str] = filter.GetNewAttributeNames()
"""


class AttributeMappingFromCellCoords( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a source mesh to a receiver mesh."""
        super().__init__( nInputPorts=2, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        # source mesh
        self.m_clientMesh: vtkUnstructuredGrid
        # input mesh
        self.m_serverMesh: vtkUnstructuredGrid
        # cell map
        self.m_cellMap: npt.NDArray[ np.int64 ] = np.empty( 0 ).astype( int )

        # Transfer Attribute name
        self.m_transferedAttributeNames: set[ str ] = set()
        # logger
        self.m_logger: Logger = getLogger( "Attribute Mapping From Cell Coords Filter" )

    def SetTransferAttributeNames( self: Self, transferredAttributeNames: set[ str ] ) -> None:
        """Setter for transferredAttributeName.

        Args:
            transferredAttributeNames (set[str]): set of names of the
                attributes to transfer.

        """
        self.m_transferedAttributeNames.clear()
        for name in transferredAttributeNames:
            self.m_transferedAttributeNames.add( name )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger
        self.Modified()

    def GetCellMap( self: Self ) -> npt.NDArray[ np.int64 ]:
        """Getter of cell map."""
        return self.m_cellMap

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
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
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
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

        try:
            self.m_serverMesh = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
            clientMesh = vtkUnstructuredGrid.GetData( inInfoVec[ 1 ] )
            self.m_clientMesh = self.GetOutputData( outInfoVec, 0 )

            assert self.m_serverMesh is not None, "Server mesh is null."
            assert clientMesh is not None, "Client mesh is null."
            assert self.m_clientMesh is not None, "Output pipeline is null."

            self.m_clientMesh.ShallowCopy( clientMesh )

            # create cell map
            self.computeCellMapping()

            # transfer attributes if at least one corresponding cell
            if np.any( self.m_cellMap > -1 ):
                self.transferAttributes()
                self.m_clientMesh.Modified()
            else:
                self.m_logger.warning( "Input and output meshes do not have any corresponding cells" )

        except AssertionError as e:
            mess1: str = "Mapping Transfer Coord failed due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "Mapping Transfer Coord failed due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        mess2: str = "Mapping Transfer Coord were successfully computed."
        self.m_logger.info( mess2 )

        return 1

    def computeCellMapping( self: Self ) -> bool:
        """Create the cell map from client to server mesh cell indexes.

        For each cell index of the client mesh, stores the index of the cell
        in the server mesh.

        Returns:
            bool: True if the map was computed.

        """
        self.m_cellMap = np.full( self.m_clientMesh.GetNumberOfCells(), -1 ).astype( int )
        cellLocator: vtkCellLocator = vtkCellLocator()
        cellLocator.SetDataSet( self.m_serverMesh )
        cellLocator.BuildLocator()

        cellCenters: vtkDataArray = computeCellCenterCoordinates( self.m_clientMesh )
        for i in range( self.m_clientMesh.GetNumberOfCells() ):
            cellCoords: MutableSequence[ float ] = [ 0.0, 0.0, 0.0 ]
            cellCenters.GetTuple( i, cellCoords )
            cellIndex: int = cellLocator.FindCell( cellCoords )
            self.m_cellMap[ i ] = cellIndex
        return True

    def transferAttributes( self: Self ) -> bool:
        """Transfer attributes from server to client meshes using cell mapping.

        Returns:
            bool: True if transfer successfully ended.

        """
        for attributeName in self.m_transferedAttributeNames:
            array: vtkDoubleArray = getVtkArrayInObject( self.m_serverMesh, attributeName, False )

            dataType = array.GetDataType()
            nbComponents: int = array.GetNumberOfComponents()
            componentNames: list[ str ] = []
            if nbComponents > 1:
                for i in range( nbComponents ):
                    componentNames.append( array.GetComponentName( i ) )
            newArray: vtkDataArray = createEmptyAttribute( self.m_clientMesh, attributeName, tuple( componentNames ),
                                                           dataType, False )
            nanValues: list[ float ] = [ np.nan for _ in range( nbComponents ) ]
            for indexClient in range( self.m_clientMesh.GetNumberOfCells() ):
                indexServer: int = self.m_cellMap[ indexClient ]
                data: MutableSequence[ float ] = nanValues
                if indexServer > -1:
                    array.GetTuple( indexServer, data )
                newArray.InsertNextTuple( data )

            cellData: vtkCellData = self.m_clientMesh.GetCellData()
            assert cellData is not None, "CellData is undefined."
            cellData.AddArray( newArray )
            cellData.Modified()
        return True
