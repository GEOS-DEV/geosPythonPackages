# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdTypeArray,
    vtkDataArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellArray,
    vtkCellData,
    vtkCell,
    vtkCellTypes,
    VTK_TRIANGLE,
    VTK_QUAD,
    VTK_TETRA,
    VTK_HEXAHEDRON,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_POLYHEDRON,
    VTK_POLYGON,
)

from vtkmodules.util.numpy_support import ( numpy_to_vtk, vtk_to_numpy )

from geos.processing.pre_processing.CellTypeCounterEnhanced import CellTypeCounterEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts

__doc__ = """
SplitMesh module is a vtk filter that split cells of a mesh composed of Tetrahedra, pyramids, and hexahedra.

Filter input and output types are vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from geos.processing.generic_processing_tools.SplitMesh import SplitMesh

    # Filter inputs
    input: vtkUnstructuredGrid

    # Instantiate the filter
    splitMeshFilter: SplitMesh = SplitMesh()

    # Set input data object
    splitMeshFilter.SetInputDataObject( input )

    # Do calculations
    splitMeshFilter.Update()

    # Get output object
    output :vtkUnstructuredGrid = splitMeshFilter.GetOutputDataObject( 0 )
"""


class SplitMesh( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """SplitMesh filter splits each cell using edge centers."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        self.inData: vtkUnstructuredGrid
        self.cells: vtkCellArray
        self.points: vtkPoints
        self.originalId: vtkIdTypeArray
        self.cellTypes: list[ int ]

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
        return 1

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
        self.inData = self.GetInputData( inInfoVec, 0, 0 )
        output: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 0 )

        assert self.inData is not None, "Input mesh is undefined."
        assert output is not None, "Output mesh is undefined."

        nb_cells: int = self.inData.GetNumberOfCells()
        counts: CellTypeCounts = self._get_cell_counts()
        nb_tet: int = counts.getTypeCount( VTK_TETRA )
        nb_pyr: int = counts.getTypeCount( VTK_PYRAMID )
        nb_hex: int = counts.getTypeCount( VTK_HEXAHEDRON )
        nb_triangles: int = counts.getTypeCount( VTK_TRIANGLE )
        nb_quad: int = counts.getTypeCount( VTK_QUAD )
        nb_polygon = counts.getTypeCount( VTK_POLYGON )
        nb_polyhedra = counts.getTypeCount( VTK_POLYHEDRON )
        assert counts.getTypeCount( VTK_WEDGE ) == 0, "Input mesh contains wedges that are not currently supported."
        assert nb_polyhedra * nb_polygon == 0, "Input mesh is composed of both polygons and polyhedra, but it must contains only one of the two."
        nbNewPoints: int = 0
        nbNewPoints = nb_hex * 19 + nb_tet * 6 + nb_pyr * 9 if nb_polyhedra > 0 else nb_triangles * 3 + nb_quad * 5
        nbNewCells: int = nb_hex * 8 + nb_tet * 8 + nb_pyr * 10 * nb_triangles * 4 + nb_quad * 4

        self.points = vtkPoints()
        self.points.DeepCopy( self.inData.GetPoints() )
        self.points.Resize( self.inData.GetNumberOfPoints() + nbNewPoints )

        self.cells = vtkCellArray()
        self.cells.AllocateExact( nbNewCells, 8 )
        self.originalId = vtkIdTypeArray()
        self.originalId.SetName( "OriginalID" )
        self.originalId.Allocate( nbNewCells )
        self.cellTypes = []
        for c in range( nb_cells ):
            cell: vtkCell = self.inData.GetCell( c )
            cellType: int = cell.GetCellType()
            if cellType == VTK_HEXAHEDRON:
                self._split_hexahedron( cell, c )
            elif cellType == VTK_TETRA:
                self._split_tetrahedron( cell, c )
            elif cellType == VTK_PYRAMID:
                self._split_pyramid( cell, c )
            elif cellType == VTK_TRIANGLE:
                self._split_triangle( cell, c )
            elif cellType == VTK_QUAD:
                self._split_quad( cell, c )
            else:
                raise TypeError( f"Cell type {vtkCellTypes.GetClassNameFromTypeId(cellType)} is not supported." )
        # add points and cells
        output.SetPoints( self.points )
        output.SetCells( self.cellTypes, self.cells )
        # add attribute saving original cell ids
        cellArrays: vtkCellData = output.GetCellData()
        assert cellArrays is not None, "Cell data is undefined."
        cellArrays.AddArray( self.originalId )
        # transfer all cell arrays
        self._transferCellArrays( output )
        return 1

    def _get_cell_counts( self: Self ) -> CellTypeCounts:
        """Get the number of cells of each type.

        Returns:
            CellTypeCounts: cell type counts
        """
        cellTypeCounterEnhancedFilter: CellTypeCounterEnhanced = CellTypeCounterEnhanced()
        cellTypeCounterEnhancedFilter.SetInputDataObject( self.inData )
        cellTypeCounterEnhancedFilter.Update()
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

    def _split_tetrahedron( self: Self, cell: vtkCell, index: int ) -> None:
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

    def _split_pyramid( self: Self, cell: vtkCell, index: int ) -> None:
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

    def _split_hexahedron( self: Self, cell: vtkCell, index: int ) -> None:
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

    def _split_triangle( self: Self, cell: vtkCell, index: int ) -> None:
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

    def _split_quad( self: Self, cell: vtkCell, index: int ) -> None:
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
            bool: True if arrays were successfully transfered.
        """
        cellDataSplitted: vtkCellData = splittedMesh.GetCellData()
        assert cellDataSplitted is not None, "Cell data of splitted mesh should be defined."
        cellData: vtkCellData = self.inData.GetCellData()
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
