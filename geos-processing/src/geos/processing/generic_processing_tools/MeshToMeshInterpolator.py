# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import logging
from typing_extensions import Self, Union, Any
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkKdTree, vtkBoundingBox, vtkSelectionNode, vtkSelection, vtkUnstructuredGrid
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersCore import vtkCellCenters, vtkAppendFilter
from vtkmodules.vtkCommonCore import reference, vtkIdTypeArray, vtkPoints
from geos.mesh.utils.arrayHelpers import ( getAttributeSet )
from geos.utils.Logger import ( getLogger, Logger, CountVerbosityHandler, isHandlerInLogger, getLoggerHandlerType )
from geos.utils.pieceEnum import Piece

__doc__ = """
MeshToMeshInterpolator is a vtk filter that map data from a source mesh to a target mesh using by default nearest
neighbor interpolation rules.

It leverage KdPointTree structure to do so efficiently and numpy array storate for fast indexing.

To use the filter:


.. code-block:: python
    # Filter inputs.
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    attributeNames: set[ str ]
    # Optional inputs.
    speHandler: bool  # defaults to False

    meshToMeshInterpolator = MeshToMeshInterpolator(meshFrom, meshTo, attributeNames, speHandler)

    # opt. for external points' values (default to 0.)
    meshToMeshInterpolator.setFillInValue(42.0)
    # opt. for region-restricted mappings
    meshToMeshInterpolator.setCellRegionsIds("attribures",set({2,3}))

    try:
        meshToMeshInterpolator.applyFilter()
    except( ValueError, AttributeError ) as e:
        attributeMappingFilter.logger.error( f"The filter { attributeMappingFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { attributeMappingFilter.logger.name } failed due to: { e }"
        attributeMappingFilter.logger.critical( mess, exc_info=True )


"""

loggerTitle: str = "Mesh to mesh Mapping"

#TODO for efficient/robust vtm->vtm need s->t block adjacency and selective merge blocks
#TODO makes a perf log tooling


class MeshToMeshInterpolator:

    def __init__(
        self: Self,
        meshFrom: Union[
            vtkDataSet,
        ],
        meshTo: Union[
            vtkDataSet,
        ],
        attributeNames: set[ str ],
        speHandler: bool = False,
    ) -> None:
        """Paint attribute from a source mesh to a target mesh.

        It allows painting of cell or point data, with configurable fill-in value for point in the target mesh which
        lies outside the source mesh.

        It also offers conditional painting based on integer cell attribute flag.

        Args:
            meshFrom (Union[vtkDataSet, ]): The source mesh with attributes to transfer.
            meshTo (Union[vtkDataSet, ]): The target mesh where to transfer attributes.
            attributeNames (set[str]): Names of the attributes to transfer.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        # making sure that meshFrom is subset or whole of meshTo
        if not MeshToMeshInterpolator._isSubset( meshFrom, meshTo ):
            raise NotImplementedError( "meshFrom should be a subset or whole meshTo" )

        self.meshFrom, _ = MeshToMeshInterpolator._filterVolumeCells( meshFrom )
        self.meshTo, self.nonVolumicPart = MeshToMeshInterpolator._filterVolumeCells( meshTo )

        if self.meshFrom.GetNumberOfCells() == 0:
            raise NotImplementedError( "MeshFrom : Not implemented for pure surface mesh" )
        if self.meshTo.GetNumberOfCells() == 0:
            raise NotImplementedError( "MeshTo : Not implemented for pure surface mesh" )

        self.attributes: dict[ Piece, set[ str ] ] = {}
        self.isApplied: bool = False
        self.fillInValue: float = 0.0

        self.attrName: str = ''
        self.regionIds: list = []
        self.fieldnc: dict = {}

        # sorting attribute to map by support
        for piece in [ Piece.POINTS, Piece.CELLS ]:
            self.attributes[ piece ] = attributeNames.intersection( getAttributeSet( self.meshFrom, piece ) )

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

        counter: CountVerbosityHandler = CountVerbosityHandler()
        self.counter: CountVerbosityHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

        # info
        for piece in [ Piece.POINTS, Piece.CELLS ]:
            self.logger.info( f"{self.attributes[piece]} on {piece}" )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not isHandlerInLogger( handler, self.logger ):
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has this handler, it has not been added." )

    def setFillInValue( self: Self, val: float = 0. ) -> None:
        """Set a specific fill-in value for points in target mesh that lies outside the source mesh.

        Args:
            val (float): the float value
        """
        self.fillInValue = val

    def setCellRegionsIds( self: Self, attrName: str, regionIds: list[ int ] ) -> None:
        """Set a conditional integer flag for painting in the source mesh, with true equality check values.

        Args:
            attrName (str) : attribute's name to look up in the source mesh
            regionIds (list[int]) : list of ints to be true

        """
        if not self.meshFrom.GetCellData().HasArray( attrName ):
            availableFrom = {
                self.meshFrom.GetCellData().GetArrayName( i )
                for i in range( self.meshFrom.GetCellData().GetNumberOfArrays() )
            }
            availableTo = {
                self.meshTo.GetCellData().GetArrayName( i )
                for i in range( self.meshTo.GetCellData().GetNumberOfArrays() )
            }
            raise KeyError( f"Attribute '{attrName}' not found.\n"
                            f"  Available arrays (MeshFrom X MeshTo): {availableFrom.intersection(availableTo)}" )

        self.attrName = attrName
        self.regionIds = regionIds

    def _getFromMaskFromId( self: Self, id: int ) -> npt.NDArray:

        mask = np.zeros( self.meshFrom.GetNumberOfCells(), dtype=bool )
        attr = vtk_to_numpy( self.meshFrom.GetCellData().GetArray( self.attrName ) ).astype( np.int64 )
        mask = ( attr == id )

        return mask
        # return self._extractRegion( self.meshFrom, mask )

    def _getToMaskFromId( self: Self, id: int ) -> npt.NDArray:

        mask = np.zeros( self.meshTo.GetNumberOfCells(), dtype=bool )
        attr = vtk_to_numpy( self.meshTo.GetCellData().GetArray( self.attrName ) ).astype( np.int64 )
        mask = ( attr == id )

        return mask

    @staticmethod
    def _isSubset( meshSource: Union[
        vtkDataSet,
    ], meshTarget: Union[
        vtkDataSet,
    ] ) -> int:
        """Check if meshSource is fully contained in meshTarget.

        Args:
            meshSource (Union[vtkDataSet,]): mesh source
            meshTarget (Union[vtkDataSet,]): mesh target
        """
        boundSource = np.asarray( meshSource.GetBounds() )
        boundTarget = np.asarray( meshTarget.GetBounds() )

        #find the lowest point and translate up
        minPoint = np.min( np.vstack( [ boundTarget[ [ 0, 0, 2, 2, 4, 4 ] ], boundSource[ [ 0, 0, 2, 2, 4, 4 ] ] ] ),
                           axis=0 )
        boundSource -= minPoint
        boundTarget -= minPoint
        targetBox = vtkBoundingBox( tuple( boundTarget ) )
        #non isotropic inflation to get the condition more robust for real world mesh
        targetBox.Inflate( 0.1 * targetBox.GetLength( 0 ), 0.1 * targetBox.GetLength( 1 ),
                           0.1 * targetBox.GetLength( 2 ) )
        getLogger( loggerTitle, True ).debug( f"boundSource={boundSource}" )
        getLogger( loggerTitle, True ).debug( f"boundTarget={boundTarget}" )
        getLogger( loggerTitle, True ).debug( f"Inflate box target={[targetBox.GetBound(i) for i in range(6)]}" )

        return targetBox.Contains( vtkBoundingBox( tuple( boundSource ) ) )

    @staticmethod
    def _clampInterpolate( meshSource: Union[
        vtkDataSet,
    ],
                           meshTarget: Union[
                               vtkDataSet,
                           ],
                           _getPoints: Any,
                            toMask: npt.NDArray = np.ndarray( [] )  ) -> list:
        """Clamp interpolation of points from meshSource to meshTarget, return list of list of tuple (distance,id_closer) for each point in target mesh.

        Args:
            meshSource (Union[vtkDataSet, ]): source mesh
            meshTarget (Union[vtkDataSet, ]): target mesh
            _getPoints (Any): function to get points from mesh (e.g. cell centers or points)
            toMask (npt.NDArray): optional restriction list
        """
        #because of distributed vtm format we use distributed datastruct (e.g. list are list of list then reduced)
        kd = vtkKdTree()
        kd.BuildLocatorFromPoints( _getPoints( meshSource ) )

        tgPts = _getPoints( meshTarget )
        source2target: list = [ [] for i in range( tgPts.GetNumberOfPoints() ) ]  # map index from source to target
        box = vtkBoundingBox( meshSource.GetBounds() )
        getLogger( loggerTitle, True ).info( f"[before] Inflate clamping target={[box.GetBound(i) for i in range(6)]}" )
        box.Inflate( .05 * box.GetLength( 0 ), .05 * box.GetLength( 1 ), .05 * box.GetLength( 2 ) )
        getLogger( loggerTitle, True ).info( f"[after] Inflate clamping target={[box.GetBound(i) for i in range(6)]}" )

        for i in range( tgPts.GetNumberOfPoints() ):
            dist = reference( 0. )
            idSource = kd.FindClosestPoint( tgPts.GetPoint( i ), dist )  # type: ignore[call-overload]
            if np.ndim( toMask ) == 0 or ( np.ndim( toMask ) == 1 and toMask[ i ] ):
                if box.ContainsPoint( tgPts.GetPoint( i ) ):
                    source2target[ i ].append( ( dist, idSource ) )
                else:
                    source2target[ i ].append( ( np.inf, -1 ) )
            else:
                source2target[ i ].append( ( np.inf, -1 ) )

        return source2target

    @staticmethod
    def _reduce( listOfList: list ) -> list:
        """Reduction of list of list of tuple (float,int) to list of index based on the first values.

        Args:
            listOfList(list) : list of list of tuples of (distance,id_closer)

        """
        return [ min( llist )[ 1 ] for llist in listOfList ]

    @staticmethod
    def _getCellCenters( mesh: Union[
        vtkDataSet,
    ] ) -> vtkPoints:
        """Wrapping the cell centers derivation from vtk and return the pointset.

        Args:
            mesh(Union[vtkDataSet]): for here but works for broader input type

        """
        centers = vtkCellCenters()
        centers.SetInputData( mesh )
        centers.Update()

        return centers.GetOutput().GetPoints()

    def _vectorizeFieldsOut( self: Self, fieldnames: set[ str ],
                             mesh: Union[
                                 vtkDataSet,
                             ], piece: Piece ) -> tuple[ npt.NDArray, list[ int ] ]:
        """Return a vector of fields in numpy format to speed up things.

        Args:
            fieldnames (set[str]): set of field names to vectorize
            mesh (Union[vtkDataSet,]): mesh to vectorize from
            piece (Piece): support of the field (point or cell)

        """
        #use numpy for some speedup
        #assuming any vector fields will not have more than 9 components
        fieldnc = []
        if piece == Piece.POINTS:
            fp = np.zeros( shape=( mesh.GetNumberOfPoints() + 1, len( fieldnames ), 9 ), dtype=float )
        elif piece == Piece.CELLS:
            fp = np.zeros( shape=( mesh.GetNumberOfCells() + 1, len( fieldnames ), 9 ), dtype=float )

        for j, field in enumerate( fieldnames ):
            self.logger.info( f"Treating {field} on {piece}" )
            if piece == Piece.POINTS:
                if not mesh.GetPointData().HasArray( field ):
                    self.logger.warning( f"{field} is not an array of  point data's source mesh" )
                else:
                    data = mesh.GetPointData().GetArray( field )
                    fieldnc.append( data.GetNumberOfComponents() )
            elif piece == Piece.CELLS:
                if not mesh.GetCellData().HasArray( field ):
                    self.logger.warning( f"{field} is not an array of cell data's source mesh" )
                else:
                    data = mesh.GetCellData().GetArray( field )
                    fieldnc.append( data.GetNumberOfComponents() )

            fp[ :-1, j, :fieldnc[ -1 ] ] = vtk_to_numpy( data ).reshape( -1, fieldnc[ -1 ] )

        fp[ -1, :, : ] = self.fillInValue

        return fp, fieldnc

    @staticmethod
    def _vectorizeFieldsIn( fieldnames: set[ str ], fieldnc: list[ int ], mesh: Union[
        vtkDataSet,
    ], nonVolMesh: Union[
        vtkDataSet,
    ], fp: npt.NDArray, piece: Piece ) -> npt.NDArray:
        """Vectorize fields from numpy format back to vtk format.

        Args:
            fieldnames (set[str]): set of field names to vectorize
            fieldnc (list[int]): list of number of components for each field
            mesh (Union[vtkDataSet,]): mesh to vectorize to
            nonVolMesh (Union[vtkDataSet,]): non-volumetric mesh fill void for consistency
            fp (npt.NDArray): numpy array of fields
            piece (Piece): support of the field (point or cell)
        """
        #use numpy for some speedup

        for j, field in enumerate( fieldnames ):
            arr = numpy_to_vtk( fp[ :, j, :fieldnc[ j ] ] )
            arr.SetName( f'mapped{field.capitalize()}' )
            getLogger( loggerTitle, True ).info( f"Adding mapped{field.capitalize()} to output on {piece}" )
            if piece == Piece.POINTS:
                void_arr = numpy_to_vtk( np.zeros( shape=( nonVolMesh.GetNumberOfPoints(), fieldnc[ j ] ) ) )
                void_arr.SetName( f'mapped{field.capitalize()}' )
                nonVolMesh.GetPointData().AddArray( void_arr )
                mesh.GetPointData().AddArray( arr )
            elif piece == Piece.CELLS:
                void_arr = numpy_to_vtk( np.zeros( shape=( nonVolMesh.GetNumberOfCells(), fieldnc[ j ] ) ) )
                void_arr.SetName( f'mapped{field.capitalize()}' )
                nonVolMesh.GetCellData().AddArray( void_arr )
                mesh.GetCellData().AddArray( arr )

        return fp

    @staticmethod
    def _filterVolumeCells( mesh: vtkDataSet ) -> tuple:
        """Keep only 3D volume cells; optionally save 2D cells to VTU.

        Args:
            mesh (vtkDataSet): input mesh to filter
        """
        volumeIds = vtkIdTypeArray()
        surfaceIds = vtkIdTypeArray()
        nVolume = nSurface = nOther = 0

        for i in range( mesh.GetNumberOfCells() ):
            dim = mesh.GetCell( i ).GetCellDimension()
            if dim == 3:
                volumeIds.InsertNextValue( i )
                nVolume += 1
            elif dim == 2:
                surfaceIds.InsertNextValue( i )
                nSurface += 1
            else:
                nOther += 1

        getLogger( loggerTitle, True ).info( f"  Cell types: {nVolume} volume (3D) | "
                                             f"{nSurface} surface (2D) | {nOther} other" )

        if nSurface == 0 and nOther == 0:
            getLogger( loggerTitle, True ).info( "No filtering needed (all cells are 3D)" )
            return mesh, mesh.NewInstance()

        sn = vtkSelectionNode()
        sn.SetFieldType( vtkSelectionNode.CELL )
        sn.SetContentType( vtkSelectionNode.INDICES )
        sn.SetSelectionList( volumeIds )
        Esn = vtkSelectionNode()
        Esn.GetProperties().Set( vtkSelectionNode.INVERSE(), 1 )
        Esn.SetFieldType( vtkSelectionNode.CELL )
        Esn.SetContentType( vtkSelectionNode.INDICES )
        Esn.SetSelectionList( volumeIds )

        sel = vtkSelection()
        sel.AddNode( sn )
        Esel = vtkSelection()
        Esel.AddNode( Esn )

        ext = vtkExtractSelection()
        ext.SetInputData( 0, mesh )
        ext.SetInputData( 1, sel )
        ext.Update()
        Eext = vtkExtractSelection()
        Eext.SetInputData( 0, mesh )
        Eext.SetInputData( 1, Esel )
        Eext.Update()

        getLogger( loggerTitle, True ).info( f"Filtered → {nVolume} cells "
                                             f"(removed {nSurface + nOther})" )

        if nVolume > 0:
            if nSurface > 0:
                return ext.GetOutput(), Eext.GetOutput()
            else:
                return ext.GetOutput(), mesh.NewInstance()

        return mesh.NewInstance(), mesh.NewInstance()

    def _extractRegion( self: Self, meshFrom: Union[
        vtkDataSet,
    ], mask: npt.NDArray ) -> vtkUnstructuredGrid:
        """Wrapping extract Selection on the mask.

        Args:
            meshFrom (Union[vtkDataSet,]): mesh to extract from
            mask (npt.NDArray): boolean array of cells to extract
        """
        # Build vtkIdTypeArray of selected indices
        idArr = vtkIdTypeArray()
        for idx in np.where( mask )[ 0 ]:
            idArr.InsertNextValue( int( idx ) )

        sn = vtkSelectionNode()
        sn.SetFieldType( vtkSelectionNode.CELL )
        sn.SetContentType( vtkSelectionNode.INDICES )
        sn.SetSelectionList( idArr )
        sel = vtkSelection()
        sel.AddNode( sn )

        ext = vtkExtractSelection()
        ext.SetInputData( 0, meshFrom )
        ext.SetInputData( 1, sel )
        ext.Update()

        sub = vtkUnstructuredGrid()
        sub.ShallowCopy( ext.GetOutput() )

        return sub

    def _apply( self: Self, regionId: int = -1 ) -> tuple[ npt.NDArray, npt.NDArray ]:
        """Apply the filter globally."""
        s2t = {}
        sourceVec = {}
        transferCell, transferPoint = np.zeros( shape=( self.meshTo.GetNumberOfCells(),
                                                        len( self.attributes[ Piece.CELLS ] ),
                                                        9 ) ), np.zeros( shape=( self.meshTo.GetNumberOfPoints(),
                                                                                 len( self.attributes[ Piece.POINTS ] ),
                                                                                 9 ) )

        meshFrom = self.meshFrom
        maskId = np.ndarray( [] )

        if regionId >= 0:
            meshFrom = self._extractRegion( self.meshFrom, self._getFromMaskFromId( regionId ) )
            getLogger( loggerTitle, True ).info( f"meshFrom extracted to [{regionId}] ({meshFrom.GetNumberOfCells()})" )
            maskId = self._getToMaskFromId( regionId )

        if len( self.attributes[ Piece.CELLS ] ) > 0:
            sourceVec[ Piece.CELLS ], self.fieldnc[ Piece.CELLS ] = self._vectorizeFieldsOut(
                self.attributes[ Piece.CELLS ], meshFrom, Piece.CELLS )
            s2t[ Piece.CELLS ] = [
                i if i != -1 else meshFrom.GetNumberOfCells() for i in MeshToMeshInterpolator._reduce(
                    MeshToMeshInterpolator._clampInterpolate(
                        meshFrom, self.meshTo, lambda m: MeshToMeshInterpolator._getCellCenters( m ), maskId ) )
            ]

            transferCell += sourceVec[ Piece.CELLS ][ s2t[ Piece.CELLS ], :, : ]


        if len( self.attributes[ Piece.POINTS ] ) > 0:
            sourceVec[ Piece.POINTS ], self.fieldnc[ Piece.POINTS ] = self._vectorizeFieldsOut(
                self.attributes[ Piece.POINTS ], meshFrom, Piece.POINTS )
            s2t[ Piece.POINTS ] = [
                i if i != -1 else self.meshFrom.GetNumberOfPoints() for i in MeshToMeshInterpolator._reduce(
                    MeshToMeshInterpolator._clampInterpolate( self.meshFrom, self.meshTo, lambda m: m.GetPoints() ) )
            ]
            transferPoint += sourceVec[ Piece.CELLS ][ s2t[ Piece.CELLS ], :, : ]

        return transferCell, transferPoint

    def applyFilter( self: Self ) -> None:
        """"Apply the filter and map attributes from meshFrom to meshTo."""
        # construct the appropriate mappings
        transferCell, transferPoint = np.zeros( shape=( self.meshTo.GetNumberOfCells(),
                                                        len( self.attributes[ Piece.CELLS ] ),
                                                        9 ) ), np.zeros( shape=( self.meshTo.GetNumberOfPoints(),
                                                                                 len( self.attributes[ Piece.POINTS ] ),
                                                                                 9 ) )

        if len( self.regionIds ) > 0:

            for regionId in self.regionIds:
                #regionalized point-wise is not supported
                if len( self.attributes[ Piece.POINTS ] ) > 0:
                    raise KeyError( "Regionalized point-wise is not supported yet." )
                tC, _ = self._apply( regionId )
                transferCell += tC
        else:
            transferCell, transferPoint = self._apply()

        # factorized final build
        if len( self.attributes[ Piece.CELLS ] ) > 0:
            MeshToMeshInterpolator._vectorizeFieldsIn( self.attributes[ Piece.CELLS ], self.fieldnc[ Piece.CELLS ],
                                                       self.meshTo, self.nonVolumicPart, transferCell, Piece.CELLS )

        if len( self.attributes[ Piece.POINTS ] ) > 0:
            MeshToMeshInterpolator._vectorizeFieldsIn( self.attributes[ Piece.POINTS ], self.fieldnc[ Piece.POINTS ],
                                                       self.meshTo, self.nonVolumicPart, transferPoint, Piece.POINTS )
        self.isApplied = True

        return

    def getOutput( self: Self ) -> vtkDataSet:
        """Get the output mesh after applying the filter."""
        if self.isApplied:
            f = vtkAppendFilter()
            f.SetInputData( self.meshTo )
            self.logger.debug(
                f"Available field [Vol] {[self.meshTo.GetCellData().GetArrayName(i) for i in range(self.meshTo.GetCellData().GetNumberOfArrays())]}"
            )
            if self.nonVolumicPart.GetNumberOfCells() > 0 or self.nonVolumicPart.GetNumberOfPoints() > 0:
                self.logger.debug(
                    f"Available field [nonVol] {[self.nonVolumicPart.GetCellData().GetArrayName(i) for i in range(self.meshTo.GetCellData().GetNumberOfArrays())]}"
                )
                f.AddInputData( self.nonVolumicPart )
            f.Update()

            self.logger.debug(
                f"Available field [Appended] {[f.GetOutput().GetCellData().GetArrayName(i) for i in range(self.meshTo.GetCellData().GetNumberOfArrays())]}"
            )
            return f.GetOutput()
        # return empty is VTK behaviour on non-updated filter
        return self.meshTo.NewInstance()
