from dataclasses import dataclass
import math
import numpy as np
import numpy.typing as npt
from typing import Union
from tqdm import tqdm
from vtk import reference as vtkReference
from vtkmodules.vtkCommonCore import vtkIntArray, vtkFloatArray, vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkBoundingBox, vtkCell, vtkCellArray, vtkPointSet, vtkPolyData,
                                            vtkStaticCellLocator, vtkStaticPointLocator, vtkUnstructuredGrid,
                                            VTK_POLYHEDRON )
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkFiltersModeling import vtkCollisionDetectionFilter, vtkLinearExtrusionFilter
from geos.mesh_doctor.actions import reorientMesh, triangleDistance
from geos.mesh.io.vtkIO import readUnstructuredGrid
from geos.mesh.utils.genericHelpers import vtkIter


@dataclass( frozen=True )
class Options:
    angleTolerance: float
    pointTolerance: float
    faceTolerance: float


@dataclass( frozen=True )
class Result:
    nonConformalCells: list[ tuple[ int, int ] ]


class BoundaryMesh:
    """A BoundaryMesh is the envelope of the 3d mesh on which we want to perform the simulations.

    It is computed by vtk. But we want to be sure that the normals of the envelope are directed outwards.
    The `vtkDataSetSurfaceFilter` does not have the same behavior for standard vtk cells (like tets or hexs),
    and for polyhedron meshes, for which the result is a bit brittle.
    Therefore, we reorient the polyhedron cells ourselves, so we're sure that they point outwards.
    And then we compute the boundary meshes for both meshes, given that the computing options are not identical.
    """

    def __init__( self, mesh: vtkUnstructuredGrid ) -> None:
        """Builds a boundary mesh.

        Args:
            mesh (vtkUnstructuredGrid): The 3d mesh.
        """
        # Building the boundary meshes
        boundaryMesh, __normals, self.__originalCells = BoundaryMesh.__buildBoundaryMesh( mesh )
        cellsToReorient: filter[ int ] = filter(
            lambda c: mesh.GetCell( c ).GetCellType() == VTK_POLYHEDRON,  # type: ignore[arg-type]
            map(
                self.__originalCells.GetValue,  # type: ignore[attr-defined]
                range( self.__originalCells.GetNumberOfValues() ) ) )
        reorientedMesh = reorientMesh.reorientMesh( mesh, cellsToReorient )
        self.reBoundaryMesh, reNormals, _ = BoundaryMesh.__buildBoundaryMesh( reorientedMesh, consistency=False )
        numCells = boundaryMesh.GetNumberOfCells()
        # Precomputing the underlying cell type
        self.__isUnderlyingCellTypeAPolyhedron = np.zeros( numCells, dtype=bool )
        for ic in range( numCells ):
            self.__isUnderlyingCellTypeAPolyhedron[ ic ] = mesh.GetCell(
                self.__originalCells.GetValue( ic ) ).GetCellType() == VTK_POLYHEDRON  # type: ignore[attr-defined]
        # Precomputing the normals
        self.__normals: np.ndarray = np.empty( ( numCells, 3 ), dtype=np.double,
                                               order='C' )  # Do not modify the storage layout
        for ic in range( numCells ):
            if self.__isUnderlyingCellTypeAPolyhedron[ ic ]:
                self.__normals[ ic, : ] = reNormals.GetTuple3( ic )
            else:
                self.__normals[ ic, : ] = __normals.GetTuple3( ic )

    @staticmethod
    def __buildBoundaryMesh( mesh: vtkUnstructuredGrid,
                             consistency: bool = True ) -> tuple[ vtkPolyData, vtkFloatArray, vtkIntArray ]:
        """From a 3d mesh, build the envelope meshes.

        Args:
            mesh (vtkUnstructuredGrid): The input 3d mesh.
            consistency (bool, optional): The vtk option passed to the `vtkDataSetSurfaceFilter`. Defaults to True.

        Returns:
            tuple[ vtkPolyData, vtkDataArray, vtkDataArray ]: A tuple containing the boundary mesh,
                             the normal vectors array, and an array that maps the id of the boundary element
                             to the id of the 3d cell it touches.
        """
        f = vtkDataSetSurfaceFilter()
        f.PassThroughCellIdsOn()
        f.PassThroughPointIdsOff()
        f.FastModeOff()

        # Note that we do not need the original points, but we could keep them as well if needed
        originalCellsKey = "ORIGINAL_CELLS"
        f.SetOriginalCellIdsName( originalCellsKey )

        boundaryMesh = vtkPolyData()
        f.UnstructuredGridExecute( mesh, boundaryMesh )

        n = vtkPolyDataNormals()
        n.SetConsistency( consistency )
        n.SetAutoOrientNormals( consistency )
        n.FlipNormalsOff()
        n.ComputeCellNormalsOn()
        n.SetInputData( boundaryMesh )
        n.Update()
        normals: vtkFloatArray = n.GetOutput().GetCellData().GetArray( "Normals" )
        assert normals
        assert normals.GetNumberOfComponents() == 3
        assert normals.GetNumberOfTuples() == boundaryMesh.GetNumberOfCells()
        originalCells: vtkIntArray = boundaryMesh.GetCellData().GetArray( originalCellsKey )
        assert originalCells
        return boundaryMesh, normals, originalCells

    def GetNumberOfCells( self ) -> int:
        """The number of cells.

        Returns:
            int: An integer.
        """
        return self.reBoundaryMesh.GetNumberOfCells()

    def GetNumberOfPoints( self ) -> int:
        """The number of points.

        Returns:
            int: An integer.
        """
        return self.reBoundaryMesh.GetNumberOfPoints()

    def bounds( self, i: int ) -> tuple[ float, float, float, float, float, float ]:
        """The boundrary box of cell `i`.

        Args:
            i (int): The boundary cell index.

        Returns:
            tuple[ float, float, float, float, float, float ]: The bounding box of the cell.
        """
        return self.reBoundaryMesh.GetCell( i ).GetBounds()

    def normals( self, i: int ) -> np.ndarray:
        """The normal of cell `i`. This normal will be directed outwards.

        Args:
            i (int): The boundary cell index.

        Returns:
            np.ndarray: The normal as a length-3 numpy array.
        """
        return self.__normals[ i ]

    def GetCell( self, i: int ) -> vtkCell:
        """Cell i of the boundary mesh. This cell will have its normal directed outwards.

        Args:
            i (int): The boundary cell index.

        Returns:
            vtkCell: The cell instance.
        """
        return self.reBoundaryMesh.GetCell( i )

    def GetPoint( self, i: int ) -> tuple[ float, float, float ]:
        """Point i of the boundary mesh.

        Args:
            i (int): The boundary point index.

        Returns:
            tuple[ float, float, float ]: A length-3 tuple containing the coordinates of the point.
        """
        return self.reBoundaryMesh.GetPoint( i )

    @property
    def originalCells( self ) -> vtkIntArray:
        """Returns the 2d boundary cell to the 3d cell index of the original mesh.

        Returns:
            vtkIntArray: A 1d array.
        """
        return self.__originalCells


def arePointsConformal( pointTolerance: float, cellI: vtkCell, cellJ: vtkCell ) -> bool:
    """Checks if points of cell `i` matches, one by one, the points of cell `j`.

    Args:
        pointTolerance (float): The point tolerance to consider that two points match.
        cellI (vtkCell): The first cell.
        cellJ (vtkCell): The second cell.

    Returns:
        bool: True if the points are conformal, False otherwise.
    """
    # In this last step, we check that the nodes are (or not) matching each other.
    if cellI.GetNumberOfPoints() != cellJ.GetNumberOfPoints():
        return True

    pointLocator = vtkStaticPointLocator()
    points = vtkPointSet()
    points.SetPoints( cellI.GetPoints() )
    pointLocator.SetDataSet( points )
    pointLocator.BuildLocator()
    foundPoints = set()
    for ip in range( cellJ.GetNumberOfPoints() ):
        p = cellJ.GetPoints().GetPoint( ip )
        squaredDist = vtkReference( 0. )  # unused
        foundPoint = pointLocator.FindClosestPointWithinRadius( pointTolerance, p, squaredDist )
        foundPoints.add( foundPoint )
    return foundPoints == set( range( cellI.GetNumberOfPoints() ) )


def buildPolyDataForExtrusion( i: int, boundaryMesh: BoundaryMesh ) -> vtkPolyData:
    """Creates a vtkPolyData containing the unique cell `i` of the boundary mesh.

    Args:
        i (int): The boundary cell index that will eventually be extruded.
        boundaryMesh (BoundaryMesh): The boundary mesh containing the cell.

    Returns:
        vtkPolyData: The created vtkPolyData.
    """
    cell = boundaryMesh.GetCell( i )
    copiedCell = cell.NewInstance()
    copiedCell.DeepCopy( cell )
    pointsIdsMapping = []
    for i in range( copiedCell.GetNumberOfPoints() ):
        copiedCell.GetPointIds().SetId( i, i )
        pointsIdsMapping.append( cell.GetPointId( i ) )
    polygons = vtkCellArray()
    polygons.InsertNextCell( copiedCell )
    points = vtkPoints()
    points.SetNumberOfPoints( len( pointsIdsMapping ) )
    for i, v in enumerate( pointsIdsMapping ):
        points.SetPoint( i, boundaryMesh.GetPoint( v ) )
    polygonPolyData = vtkPolyData()
    polygonPolyData.SetPoints( points )
    polygonPolyData.SetPolys( polygons )
    return polygonPolyData


class Extruder:
    """Computes and stores all the extrusions of the boundary faces.

    The main reason for this class is to be lazy and cache the extrusions.
    """

    def __init__( self, boundaryMesh: BoundaryMesh, faceTolerance: float ) -> None:
        """Initializes the extruder.

        Args:
            boundaryMesh (BoundaryMesh): Boundary mesh.
            faceTolerance (float): Tolerance value.
        """
        self.__extrusions: list[ Union[ vtkPolyData, None ] ] = [
            None,
        ] * boundaryMesh.GetNumberOfCells()
        self.__boundaryMesh = boundaryMesh
        self.__faceTolerance = faceTolerance

    def __extrude( self, polygonPolyData: vtkPolyData, normal: np.ndarray ) -> vtkPolyData:
        """Extrude the polygon data to create a surface that will be used for intersection.

        Args:
            polygonPolyData (vtkPolyData): The data to extrude
            normal (np.ndarray): The (uniform) direction of the extrusion.

        Returns:
            vtkPolyData: The extruded surface.
        """
        extruder = vtkLinearExtrusionFilter()
        extruder.SetExtrusionTypeToVectorExtrusion()
        extruder.SetVector( float( normal[ 0 ] ), float( normal[ 1 ] ), float( normal[ 2 ] ) )
        extruder.SetScaleFactor( self.__faceTolerance / 2. )
        extruder.SetInputData( polygonPolyData )
        extruder.Update()
        return extruder.GetOutput()

    def __getitem__( self, i: int ) -> vtkPolyData:
        """Returns the vtk extrusion for boundary element i.

        Args:
            i (int): The cell index.

        Returns:
            vtkPolyData: The vtk extrusion.
        """
        extrusion = self.__extrusions[ i ]
        if extrusion:
            return extrusion
        extrusion = self.__extrude( buildPolyDataForExtrusion( i, self.__boundaryMesh ),
                                    self.__boundaryMesh.normals( i ) )
        self.__extrusions[ i ] = extrusion
        return extrusion


def areFacesConformalUsingExtrusions( extrusions: Extruder, i: int, j: int, boundaryMesh: BoundaryMesh,
                                      pointTolerance: float ) -> bool:
    """Tests if two boundary faces are conformal, checking for intersection between their normal extruded volumes.

    Args:
        extrusions (Extruder): The extrusions cache.
        i (int): The cell index of the first cell.
        j (int): The cell index of the second cell.
        boundaryMesh (BoundaryMesh): The boundary mesh.
        pointTolerance (float): The point tolerance to consider that two points match.

    Returns:
        bool: True if the faces are conformal, False otherwise.
    """
    collision = vtkCollisionDetectionFilter()
    collision.SetCollisionModeToFirstContact()
    collision.SetInputData( 0, extrusions[ i ] )
    collision.SetInputData( 1, extrusions[ j ] )
    mI = vtkTransform()
    mJ = vtkTransform()
    collision.SetTransform( 0, mI )
    collision.SetTransform( 1, mJ )
    collision.Update()

    if collision.GetNumberOfContacts() == 0:
        return True

    # Duplicating data not to risk anything w.r.t. thread safety of the GetCell function.
    cellI = boundaryMesh.GetCell( i )
    copiedCellI = cellI.NewInstance()
    copiedCellI.DeepCopy( cellI )

    return arePointsConformal( pointTolerance, copiedCellI, boundaryMesh.GetCell( j ) )


def areFacesConformalUsingDistances( i: int, j: int, boundaryMesh: vtkUnstructuredGrid, faceTolerance: float,
                                     pointTolerance: float ) -> bool:
    """Tests if two boundary faces are conformal, checking the minimal distance between triangulated surfaces.

    Args:
        i (int): The cell index of the first cell.
        j (int): The cell index of the second cell.
        boundaryMesh (vtkUnstructuredGrid): The boundary mesh.
        faceTolerance (float): The tolerance under which we should consider the two faces "touching" each other.
        pointTolerance (float): The point tolerance to consider that two points match.

    Returns:
        bool: True if the faces are conformal, False otherwise.
    """
    cpI: vtkCell = boundaryMesh.GetCell( i ).NewInstance()
    cpI.DeepCopy( boundaryMesh.GetCell( i ) )
    cpJ: vtkCell = boundaryMesh.GetCell( j ).NewInstance()
    cpJ.DeepCopy( boundaryMesh.GetCell( j ) )

    def triangulate( cell: vtkCell ) -> tuple[ tuple[ int, ...], vtkPoints ]:
        assert cell.GetCellDimension() == 2
        _pointsIdsList = vtkIdList()
        _points = vtkPoints()
        cell.Triangulate( 0, _pointsIdsList, _points )
        _pointsIds: tuple[ int, ...] = tuple( vtkIter( _pointsIdsList ) )
        assert len( _pointsIds ) % 3 == 0
        assert _points.GetNumberOfPoints() % 3 == 0
        return _pointsIds, _points

    pointsIdsI, pointsI = triangulate( cpI )
    pointsIdsJ, pointsJ = triangulate( cpJ )

    def buildNumpyTriangles( pointsIds: tuple[ int, ...] ) -> list[ npt.NDArray[ np.float64 ] ]:
        __triangles = []
        for __i in range( 0, len( pointsIds ), 3 ):
            __t = []
            for __pi in pointsIds[ __i:__i + 3 ]:
                __t.append( boundaryMesh.GetPoint( __pi ) )
            __triangles.append( np.array( __t, dtype=float ) )
        return __triangles

    trianglesI = buildNumpyTriangles( pointsIdsI )
    trianglesJ = buildNumpyTriangles( pointsIdsJ )

    minDist = np.inf
    for ti, tj in [ ( ti, tj ) for ti in trianglesI for tj in trianglesJ ]:
        # Note that here, we compute the exact distance to compare with the threshold.
        # We could improve by exiting the iterative distance computation as soon as
        # we're sure we're smaller than the threshold. No need of the exact solution.
        dist, _, _ = triangleDistance.distanceBetweenTwoTriangles( ti, tj )
        if dist < minDist:
            minDist = dist
        if minDist < faceTolerance:
            break
    if minDist > faceTolerance:
        return True

    return arePointsConformal( pointTolerance, cpI, cpJ )


def computeBoundingBox( boundaryMesh: BoundaryMesh, faceTolerance: float ) -> npt.NDArray:
    """Computes the bounding boxes of all boundary cells, inflated by 2 * faceTolerance.

    Args:
        boundaryMesh (BoundaryMesh): The boundary mesh.
        faceTolerance (float): The tolerance for face proximity.

    Returns:
        npt.NDArray[ np.float64 ]: An array of bounding boxes for each cell.
    """
    # The options are important to directly interact with memory in C++.
    boundingBoxes = np.empty( ( boundaryMesh.GetNumberOfCells(), 6 ), dtype=np.double, order="C" )
    for i in range( boundaryMesh.GetNumberOfCells() ):
        bb = vtkBoundingBox( boundaryMesh.bounds( i ) )
        bb.Inflate( 2 * faceTolerance )
        assert boundingBoxes[
            i, : ].data.contiguous  # Do not modify the storage layout since vtk deals with raw memory here.
        boundsList: list[ float ] = [ 0.0 ] * 6
        bb.GetBounds( boundsList )
        boundingBoxes[ i, : ] = boundsList
    return boundingBoxes


def computeNumberCellsPerNode( boundaryMesh: BoundaryMesh ) -> npt.NDArray[ np.int64 ]:
    """Computes the number of cells connected to each node in the boundary mesh.

    Args:
        boundaryMesh (BoundaryMesh): The boundary mesh.

    Returns:
        npt.NDArray[ np.int64 ]: The number of cells per node.
    """
    # Computing the exact number of cells per node
    numCellsPerNode = np.zeros( boundaryMesh.GetNumberOfPoints(), dtype=int )
    for ic in range( boundaryMesh.GetNumberOfCells() ):
        c = boundaryMesh.GetCell( ic )
        pointIds = c.GetPointIds()
        for pointId in vtkIter( pointIds ):
            numCellsPerNode[ pointId ] += 1
    return numCellsPerNode


def buildCellLocator( reBoundaryMesh: vtkPolyData, numberMaxCellPerNode: int ) -> vtkStaticCellLocator:
    """Builds a vtkStaticCellLocator for the boundary mesh.

    Args:
        reBoundaryMesh (vtkPolyData): The reBoundary mesh.
        numberMaxCellPerNode (int): The maximum number of cells per node.

    Returns:
        vtkStaticCellLocator: The built cell locator.
    """
    cellLocator = vtkStaticCellLocator()
    cellLocator.Initialize()
    cellLocator.SetNumberOfCellsPerNode( numberMaxCellPerNode )
    cellLocator.SetDataSet( reBoundaryMesh )
    cellLocator.BuildLocator()
    return cellLocator


def findNonConformalCells( mesh: vtkUnstructuredGrid, options: Options ) -> list[ tuple[ int, int ] ]:
    """Finds all pairs of non-conformal boundary faces in the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        options (Options): The options for the non-conformal check.

    Returns:
        list[ tuple[ int, int ] ]: A list of pairs of non-conformal cell indices.
    """
    # Extracts the outer surface of the 3D mesh.
    # Ensures that face normals are consistently oriented outward.
    boundaryMesh = BoundaryMesh( mesh )
    numCells: int = boundaryMesh.GetNumberOfCells()

    # Used to filter out face pairs that are not facing each other.
    cosTheta: float = abs( math.cos( np.deg2rad( options.angleTolerance ) ) )

    # Prepares extruded volumes of boundary faces for intersection testing.
    extrusions = Extruder( boundaryMesh, options.faceTolerance )

    numCellsPerNode = computeNumberCellsPerNode( boundaryMesh )
    boundingBoxes = computeBoundingBox( boundaryMesh, options.faceTolerance )
    cellLocator = buildCellLocator( boundaryMesh.reBoundaryMesh, numCellsPerNode.max() )

    closeCells = vtkIdList()
    nonConformalCellsBoundaryId: list[ tuple[ int, int ] ] = []
    # Looping on all the pairs of boundary cells. We'll hopefully discard most of the pairs.
    for i in tqdm( range( numCells ), desc="Non conformal elements" ):
        cellLocator.FindCellsWithinBounds( boundingBoxes[ i ], closeCells )
        for j in vtkIter( closeCells ):
            if j < i:
                continue
            # Discarding pairs that are not facing each others (with a threshold).
            normalI, normalJ = boundaryMesh.normals( i ), boundaryMesh.normals( j )
            if np.dot( normalI, normalJ ) > -cosTheta:  # opposite directions only (can be facing or not)
                continue
            # At this point, back-to-back and face-to-face pairs of elements are considered.
            if not areFacesConformalUsingExtrusions( extrusions, i, j, boundaryMesh, options.pointTolerance ):
                nonConformalCellsBoundaryId.append( ( i, j ) )
    # Extracting the original 3d element index (and not the index of the boundary mesh).
    nonConformalCells: list[ tuple[ int, int ] ] = []
    for i, j in nonConformalCellsBoundaryId:
        nonConformalCells.append(
            ( boundaryMesh.originalCells.GetValue( i ), boundaryMesh.originalCells.GetValue( j ) ) )
    return nonConformalCells


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Checks if the mesh is "conformal" (i.e. if some of its boundary faces may not be too close to each other without matching nodes).

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The check options.

    Returns:
        Result: The Result instance.
    """
    nonConformalCells = findNonConformalCells( mesh, options )
    return Result( nonConformalCells=nonConformalCells )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs the self intersecting elements check on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the self intersecting elements check.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
