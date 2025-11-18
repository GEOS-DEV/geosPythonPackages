# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import logging
import numpy as np
import numpy.typing as npt
from typing_extensions import Self

from vtkmodules.vtkCommonCore import ( vtkPoints, vtkIdTypeArray, vtkDataArray )
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellArray, vtkCellData, vtkCell, vtkCellTypes,
                                            VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID, VTK_WEDGE,
                                            VTK_POLYHEDRON, VTK_POLYGON )
from vtkmodules.util.numpy_support import ( numpy_to_vtk, vtk_to_numpy )

from geos.utils.Logger import ( Logger, getLogger )
from geos.processing.pre_processing.CellTypeCounterEnhanced import CellTypeCounterEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts

__doc__ = """
SplitMesh module is a vtk filter that split cells of a mesh composed of Tetrahedra, pyramids, and hexahedra.

Filter input and output types are vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from geos.processing.generic_processing_tools.SplitMesh import SplitMesh

    # Filter inputs
    inputMesh: vtkUnstructuredGrid
    speHandler: bool # optional

    # Instantiate the filter
    splitMeshFilter: SplitMesh = SplitMesh( inputMesh, speHandler )

    # Use your own handler (if speHandler is True)
    yourHandler: logging.Handler
    splitMeshFilter.setLoggerHandler( yourHandler )

    # Do calculations
    splitMeshFilter.applyFilter()

    # Get splitted mesh
    outputMesh: vtkUnstructuredGrid = splitMeshFilter.getOutput()
"""

loggerTitle: str = "Split Mesh"


class SplitMesh():

    def __init__( self, inputMesh: vtkUnstructuredGrid, speHandler: bool = False ) -> None:
        """SplitMesh filter splits each cell using edge centers.

        Args:
            inputMesh (vtkUnstructuredGrid): The input mesh.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.inputMesh: vtkUnstructuredGrid = inputMesh
        self.outputMesh: vtkUnstructuredGrid = inputMesh.NewInstance()
        self.cells: vtkCellArray
        self.points: vtkPoints
        self.originalId: vtkIdTypeArray
        self.cellTypes: list[ int ]
        self.speHandler: bool = speHandler
        self.handler: None | logging.Handler = None

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        self.handler = handler
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True"
                                 " during the filter initialization." )

    def applyFilter( self: Self ) -> None:
        """Apply the filter SplitMesh."""
        self.logger.info( f"Applying filter { self.logger.name }." )
        try:
            nbCells: int = self.inputMesh.GetNumberOfCells()
            counts: CellTypeCounts = self._getCellCounts()
            nbTet: int = counts.getTypeCount( VTK_TETRA )
            nbPyr: int = counts.getTypeCount( VTK_PYRAMID )
            nbHex: int = counts.getTypeCount( VTK_HEXAHEDRON )
            nbTriangles: int = counts.getTypeCount( VTK_TRIANGLE )
            nbQuad: int = counts.getTypeCount( VTK_QUAD )
            nbPolygon: int = counts.getTypeCount( VTK_POLYGON )
            nbPolyhedra: int = counts.getTypeCount( VTK_POLYHEDRON )
            assert counts.getTypeCount( VTK_WEDGE ) == 0, "Input mesh contains wedges that are not currently supported."
            assert nbPolyhedra * nbPolygon == 0, ( "Input mesh is composed of both polygons and polyhedra,"
                                                   " but it must contains only one of the two." )
            nbNewPoints: int = 0
            nbNewPoints = nbHex * 19 + nbTet * 6 + nbPyr * 9 if nbPolyhedra > 0 else nbTriangles * 3 + nbQuad * 5
            nbNewCells: int = nbHex * 8 + nbTet * 8 + nbPyr * 10 * nbTriangles * 4 + nbQuad * 4

            self.points = vtkPoints()
            self.points.DeepCopy( self.inputMesh.GetPoints() )
            self.points.Resize( self.inputMesh.GetNumberOfPoints() + nbNewPoints )

            self.cells = vtkCellArray()
            self.cells.AllocateExact( nbNewCells, 8 )
            self.originalId = vtkIdTypeArray()
            self.originalId.SetName( "OriginalID" )
            self.originalId.Allocate( nbNewCells )
            self.cellTypes = []
            for c in range( nbCells ):
                cell: vtkCell = self.inputMesh.GetCell( c )
                cellType: int = cell.GetCellType()
                if cellType == VTK_HEXAHEDRON:
                    self._splitHexahedron( cell, c )
                elif cellType == VTK_TETRA:
                    self._splitTetrahedron( cell, c )
                elif cellType == VTK_PYRAMID:
                    self._splitPyramid( cell, c )
                elif cellType == VTK_TRIANGLE:
                    self._splitTriangle( cell, c )
                elif cellType == VTK_QUAD:
                    self._splitQuad( cell, c )
                else:
                    raise TypeError( f"Cell type {vtkCellTypes.GetClassNameFromTypeId(cellType)} is not supported." )
            # add points and cells
            self.outputMesh.SetPoints( self.points )
            self.outputMesh.SetCells( self.cellTypes, self.cells )
            # add attribute saving original cell ids
            cellArrays: vtkCellData = self.outputMesh.GetCellData()
            assert cellArrays is not None, "Cell data is undefined."
            cellArrays.AddArray( self.originalId )
            # transfer all cell arrays
            self._transferCellArrays( self.outputMesh )
            self.logger.info( f"The filter { self.logger.name } succeeded." )
        except Exception as e:
            self.logger.error( f"The filter {self.logger.name } failed.\n{ e }" )

        return

    def getOutput( self: Self ) -> vtkUnstructuredGrid:
        """Get the splitted mesh computed."""
        return self.outputMesh

    def _getCellCounts( self: Self ) -> CellTypeCounts:
        """Get the number of cells of each type.

        Returns:
            CellTypeCounts: cell type counts
        """
        cellTypeCounterEnhancedFilter: CellTypeCounterEnhanced = CellTypeCounterEnhanced(
            self.inputMesh, self.speHandler )
        if self.speHandler and len( cellTypeCounterEnhancedFilter.logger.handlers ) == 0:
            cellTypeCounterEnhancedFilter.setLoggerHandler( self.handler )
        cellTypeCounterEnhancedFilter.applyFilter()
        return cellTypeCounterEnhancedFilter.GetCellTypeCountsObject()

    def _addMidPoint( self: Self, ptA: int, ptB: int ) -> int:
        """Add a point at the center of the edge defined by input point ids.

        Args:
            ptA (int): first point Id
            ptB (int): second point Id

        Returns:
            int: inserted point Id
        """
        ptACoor: npt.NDArray[ np.float64 ] = np.array( self.points.GetPoint( ptA ) )
        ptBCoor: npt.NDArray[ np.float64 ] = np.array( self.points.GetPoint( ptB ) )
        center: npt.NDArray[ np.float64 ] = ( ptACoor + ptBCoor ) / 2.
        return self.points.InsertNextPoint( center[ 0 ], center[ 1 ], center[ 2 ] )

    def _splitTetrahedron( self: Self, cell: vtkCell, index: int ) -> None:
        r"""Split a tetrahedron.

        Let's suppose an input tetrahedron composed of nodes (0, 1, 2, 3),
        the cell is splitted in 8 tetrahedra using edge centers.

                   2
                 ,/|`\
               ,/  |  `\
             ,6    '.   `5
           ,/       8     `\
         ,/         |       `\
        0--------4--'.--------1
         `\.         |      ,/
            `\.      |    ,9
               `7.   '. ,/
                  `\. |/
                     `3

        Args:
            cell (vtkCell): cell to split
            index (int): index of the cell
        """
        pt0: int = cell.GetPointId( 0 )
        pt1: int = cell.GetPointId( 1 )
        pt2: int = cell.GetPointId( 2 )
        pt3: int = cell.GetPointId( 3 )
        pt4: int = self._addMidPoint( pt0, pt1 )
        pt5: int = self._addMidPoint( pt1, pt2 )
        pt6: int = self._addMidPoint( pt0, pt2 )
        pt7: int = self._addMidPoint( pt0, pt3 )
        pt8: int = self._addMidPoint( pt2, pt3 )
        pt9: int = self._addMidPoint( pt1, pt3 )

        self.cells.InsertNextCell( 4, [ pt0, pt4, pt6, pt7 ] )
        self.cells.InsertNextCell( 4, [ pt7, pt9, pt8, pt3 ] )
        self.cells.InsertNextCell( 4, [ pt9, pt4, pt5, pt1 ] )
        self.cells.InsertNextCell( 4, [ pt5, pt6, pt8, pt2 ] )
        self.cells.InsertNextCell( 4, [ pt6, pt8, pt7, pt4 ] )
        self.cells.InsertNextCell( 4, [ pt4, pt8, pt7, pt9 ] )
        self.cells.InsertNextCell( 4, [ pt4, pt8, pt9, pt5 ] )
        self.cells.InsertNextCell( 4, [ pt5, pt4, pt8, pt6 ] )
        for _ in range( 8 ):
            self.originalId.InsertNextValue( index )
        self.cellTypes.extend( [ VTK_TETRA ] * 8 )

    def _splitPyramid( self: Self, cell: vtkCell, index: int ) -> None:
        r"""Split a pyramid.

        Let's suppose an input pyramid composed of nodes (0, 1, 2, 3, 4),
        the cell is splitted in 8 pyramids using edge centers.

                       4
                     ,/|\
                   ,/ .'|\
                 ,/   | | \
               ,/    .' | `.
             ,7      |  12  \
           ,/       .'   |   \
         ,/         9    |    11
        0--------6-.'----3    `.
          `\        |      `\    \
            `5     .'13      10   \
              `\   |           `\  \
                `\.'             `\`
                   1--------8-------2

        Args:
            cell (vtkCell): cell to split
            index (int): index of the cell
        """
        pt0: int = cell.GetPointId( 0 )
        pt1: int = cell.GetPointId( 1 )
        pt2: int = cell.GetPointId( 2 )
        pt3: int = cell.GetPointId( 3 )
        pt4: int = cell.GetPointId( 4 )
        pt5: int = self._addMidPoint( pt0, pt1 )
        pt6: int = self._addMidPoint( pt0, pt3 )
        pt7: int = self._addMidPoint( pt0, pt4 )
        pt8: int = self._addMidPoint( pt1, pt2 )
        pt9: int = self._addMidPoint( pt1, pt4 )
        pt10: int = self._addMidPoint( pt2, pt3 )
        pt11: int = self._addMidPoint( pt2, pt4 )
        pt12: int = self._addMidPoint( pt3, pt4 )
        pt13: int = self._addMidPoint( pt5, pt10 )

        self.cells.InsertNextCell( 5, [ pt5, pt1, pt8, pt13, pt9 ] )
        self.cells.InsertNextCell( 5, [ pt13, pt8, pt2, pt10, pt11 ] )
        self.cells.InsertNextCell( 5, [ pt3, pt6, pt13, pt10, pt12 ] )
        self.cells.InsertNextCell( 5, [ pt6, pt0, pt5, pt13, pt7 ] )
        self.cells.InsertNextCell( 5, [ pt12, pt7, pt9, pt11, pt4 ] )
        self.cells.InsertNextCell( 5, [ pt11, pt9, pt7, pt12, pt13 ] )

        self.cells.InsertNextCell( 4, [ pt7, pt9, pt5, pt13 ] )
        self.cells.InsertNextCell( 4, [ pt9, pt11, pt8, pt13 ] )
        self.cells.InsertNextCell( 4, [ pt11, pt12, pt10, pt13 ] )
        self.cells.InsertNextCell( 4, [ pt12, pt7, pt6, pt13 ] )
        for _ in range( 10 ):
            self.originalId.InsertNextValue( index )
        self.cellTypes.extend( [ VTK_PYRAMID ] * 8 )

    def _splitHexahedron( self: Self, cell: vtkCell, index: int ) -> None:
        r"""Split a hexahedron.

        Let's suppose an input hexahedron composed of nodes (0, 1, 2, 3, 4, 5, 6, 7),
        the cell is splitted in 8 hexahedra using edge centers.

        3----13----2
        |\         |\
        |15    24  | 14
        9  \ 20    11 \
        |   7----19+---6
        |22 |  26  | 23|
        0---+-8----1   |
         \ 17    25 \  18
          10|  21    12|
           \|         \|
            4----16----5

        Args:
            cell (vtkCell): cell to split
            index (int): index of the cell
        """
        pt0: int = cell.GetPointId( 0 )
        pt1: int = cell.GetPointId( 1 )
        pt2: int = cell.GetPointId( 2 )
        pt3: int = cell.GetPointId( 3 )
        pt4: int = cell.GetPointId( 4 )
        pt5: int = cell.GetPointId( 5 )
        pt6: int = cell.GetPointId( 6 )
        pt7: int = cell.GetPointId( 7 )
        pt8: int = self._addMidPoint( pt0, pt1 )
        pt9: int = self._addMidPoint( pt0, pt3 )
        pt10: int = self._addMidPoint( pt0, pt4 )
        pt11: int = self._addMidPoint( pt1, pt2 )
        pt12: int = self._addMidPoint( pt1, pt5 )
        pt13: int = self._addMidPoint( pt2, pt3 )
        pt14: int = self._addMidPoint( pt2, pt6 )
        pt15: int = self._addMidPoint( pt3, pt7 )
        pt16: int = self._addMidPoint( pt4, pt5 )
        pt17: int = self._addMidPoint( pt4, pt7 )
        pt18: int = self._addMidPoint( pt5, pt6 )
        pt19: int = self._addMidPoint( pt6, pt7 )
        pt20: int = self._addMidPoint( pt9, pt11 )
        pt21: int = self._addMidPoint( pt10, pt12 )
        pt22: int = self._addMidPoint( pt9, pt17 )
        pt23: int = self._addMidPoint( pt11, pt18 )
        pt24: int = self._addMidPoint( pt14, pt15 )
        pt25: int = self._addMidPoint( pt17, pt18 )
        pt26: int = self._addMidPoint( pt22, pt23 )

        self.cells.InsertNextCell( 8, [ pt10, pt21, pt26, pt22, pt4, pt16, pt25, pt17 ] )
        self.cells.InsertNextCell( 8, [ pt21, pt12, pt23, pt26, pt16, pt5, pt18, pt25 ] )
        self.cells.InsertNextCell( 8, [ pt0, pt8, pt20, pt9, pt10, pt21, pt26, pt22 ] )
        self.cells.InsertNextCell( 8, [ pt8, pt1, pt11, pt20, pt21, pt12, pt23, pt26 ] )
        self.cells.InsertNextCell( 8, [ pt22, pt26, pt24, pt15, pt17, pt25, pt19, pt7 ] )
        self.cells.InsertNextCell( 8, [ pt26, pt23, pt14, pt24, pt25, pt18, pt6, pt19 ] )
        self.cells.InsertNextCell( 8, [ pt9, pt20, pt13, pt3, pt22, pt26, pt24, pt15 ] )
        self.cells.InsertNextCell( 8, [ pt20, pt11, pt2, pt13, pt26, pt23, pt14, pt24 ] )
        for _ in range( 8 ):
            self.originalId.InsertNextValue( index )
        self.cellTypes.extend( [ VTK_HEXAHEDRON ] * 8 )

    def _splitTriangle( self: Self, cell: vtkCell, index: int ) -> None:
        r"""Split a triangle.

        Let's suppose an input triangle composed of nodes (0, 1, 2),
        the cell is splitted in 3 triangles using edge centers.

        2
        |\
        |  \
        5    4
        |      \
        |        \
        0-----3----1

        Args:
            cell (vtkCell): cell to split
            index (int): index of the cell
        """
        pt0: int = cell.GetPointId( 0 )
        pt1: int = cell.GetPointId( 1 )
        pt2: int = cell.GetPointId( 2 )
        pt3: int = self._addMidPoint( pt0, pt1 )
        pt4: int = self._addMidPoint( pt1, pt2 )
        pt5: int = self._addMidPoint( pt0, pt2 )

        self.cells.InsertNextCell( 3, [ pt0, pt3, pt5 ] )
        self.cells.InsertNextCell( 3, [ pt3, pt1, pt4 ] )
        self.cells.InsertNextCell( 3, [ pt5, pt4, pt2 ] )
        self.cells.InsertNextCell( 3, [ pt3, pt4, pt5 ] )
        for _ in range( 4 ):
            self.originalId.InsertNextValue( index )
        self.cellTypes.extend( [ VTK_TRIANGLE ] * 4 )

    def _splitQuad( self: Self, cell: vtkCell, index: int ) -> None:
        r"""Split a quad.

        Let's suppose an input quad composed of nodes (0, 1, 2, 3),
        the cell is splitted in 4 quads using edge centers.

        3-----6-----2
        |           |
        |           |
        7     8     5
        |           |
        |           |
        0-----4-----1

        Args:
            cell (vtkCell): cell to split
            index (int): index of the cell
        """
        pt0: int = cell.GetPointId( 0 )
        pt1: int = cell.GetPointId( 1 )
        pt2: int = cell.GetPointId( 2 )
        pt3: int = cell.GetPointId( 3 )
        pt4: int = self._addMidPoint( pt0, pt1 )
        pt5: int = self._addMidPoint( pt1, pt2 )
        pt6: int = self._addMidPoint( pt2, pt3 )
        pt7: int = self._addMidPoint( pt3, pt0 )
        pt8: int = self._addMidPoint( pt7, pt5 )

        self.cells.InsertNextCell( 4, [ pt0, pt4, pt8, pt7 ] )
        self.cells.InsertNextCell( 4, [ pt4, pt1, pt5, pt8 ] )
        self.cells.InsertNextCell( 4, [ pt8, pt5, pt2, pt6 ] )
        self.cells.InsertNextCell( 4, [ pt7, pt8, pt6, pt3 ] )
        for _ in range( 4 ):
            self.originalId.InsertNextValue( index )
        self.cellTypes.extend( [ VTK_QUAD ] * 4 )

    def _transferCellArrays( self: Self, splittedMesh: vtkUnstructuredGrid ) -> bool:
        """Transfer arrays from input mesh to splitted mesh.

        Args:
            splittedMesh (vtkUnstructuredGrid): splitted mesh

        Returns:
            bool: True if arrays were successfully transferred.
        """
        cellDataSplitted: vtkCellData = splittedMesh.GetCellData()
        assert cellDataSplitted is not None, "Cell data of splitted mesh should be defined."
        cellData: vtkCellData = self.inputMesh.GetCellData()
        assert cellData is not None, "Cell data of input mesh should be defined."
        # for each array of input mesh
        for i in range( cellData.GetNumberOfArrays() ):
            array: vtkDataArray = cellData.GetArray( i )
            assert array is not None, "Array should be defined."
            npArray: npt.NDArray[ np.float64 ] = vtk_to_numpy( array )
            # get number of components
            dims: tuple[ int, ...] = npArray.shape
            ny: int = 1 if len( dims ) == 1 else dims[ 1 ]
            # create new array with nb cells from splitted mesh and number of components from array to copy
            newNpArray: npt.NDArray[ np.float64 ] = np.full( ( splittedMesh.GetNumberOfCells(), ny ), np.nan )
            # for each cell, copy the values from input mesh
            for c in range( splittedMesh.GetNumberOfCells() ):
                idParent: int = int( self.originalId.GetTuple1( c ) )
                newNpArray[ c ] = npArray[ idParent ]
            # set array the splitted mesh
            newArray: vtkDataArray = numpy_to_vtk( newNpArray )
            newArray.SetName( array.GetName() )
            cellDataSplitted.AddArray( newArray )
            cellDataSplitted.Modified()
        splittedMesh.Modified()
        return True
