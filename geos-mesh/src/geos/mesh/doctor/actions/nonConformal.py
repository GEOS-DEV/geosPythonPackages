from dataclasses import dataclass
import math
import numpy
from tqdm import tqdm
from typing import List, Tuple, Any
from vtk import reference as vtkReference
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkBoundingBox, vtkCell, vtkCellArray, vtkPointSet, vtkPolyData,
                                            vtkStaticCellLocator, vtkStaticPointLocator, vtkUnstructuredGrid,
                                            VTK_POLYHEDRON )
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkFiltersModeling import vtkCollisionDetectionFilter, vtkLinearExtrusionFilter
from geos.mesh.doctor.actions import reorientMesh, triangleDistance
from geos.mesh.utils.genericHelpers import vtkIter
from geos.mesh.io.vtkIO import read_mesh


@dataclass( frozen=True )
class Options:
    angleTolerance: float
    pointTolerance: float
    faceTolerance: float


@dataclass( frozen=True )
class Result:
    nonConformalCells: List[ Tuple[ int, int ] ]


class BoundaryMesh:
    """
    A BoundaryMesh is the envelope of the 3d mesh on which we want to perform the simulations.
    It is computed by vtk. But we want to be sure that the normals of the envelope are directed outwards.
    The `vtkDataSetSurfaceFilter` does not have the same behavior for standard vtk cells (like tets or hexs),
    and for polyhedron meshes, for which the result is a bit brittle.
    Therefore, we reorient the polyhedron cells ourselves, so we're sure that they point outwards.
    And then we compute the boundary meshes for both meshes, given that the computing options are not identical.
    """

    def __init__( self, mesh: vtkUnstructuredGrid ):
        """
        Builds a boundary mesh.
        :param mesh: The 3d mesh.
        """
        # Building the boundary meshes
        boundaryMesh, __normals, self.__originalCells = BoundaryMesh.__buildBoundaryMesh( mesh )
        cellsToReorient = filter(
            lambda c: mesh.GetCell( c ).GetCellType() == VTK_POLYHEDRON,
            map( self.__originalCells.GetValue, range( self.__originalCells.GetNumberOfValues() ) ) )
        reorientedMesh = reorientMesh.reorientMesh( mesh, cellsToReorient )
        self.reBoundaryMesh, reNormals, _ = BoundaryMesh.__buildBoundaryMesh( reorientedMesh, consistency=False )
        numCells = boundaryMesh.GetNumberOfCells()
        # Precomputing the underlying cell type
        self.__isUnderlyingCellTypeAPolyhedron = numpy.zeros( numCells, dtype=bool )
        for ic in range( numCells ):
            self.__isUnderlyingCellTypeAPolyhedron[ ic ] = mesh.GetCell(
                self.__originalCells.GetValue( ic ) ).GetCellType() == VTK_POLYHEDRON
        # Precomputing the normals
        self.__normals: numpy.ndarray = numpy.empty( ( numCells, 3 ), dtype=numpy.double,
                                                     order='C' )  # Do not modify the storage layout
        for ic in range( numCells ):
            if self.__isUnderlyingCellTypeAPolyhedron[ ic ]:
                self.__normals[ ic, : ] = reNormals.GetTuple3( ic )
            else:
                self.__normals[ ic, : ] = __normals.GetTuple3( ic )

    @staticmethod
    def __buildBoundaryMesh( mesh: vtkUnstructuredGrid, consistency=True ) -> Tuple[ vtkUnstructuredGrid, Any, Any ]:
        """
        From a 3d mesh, build the envelope meshes.
        :param mesh: The input 3d mesh.
        :param consistency: The vtk option passed to the `vtkDataSetSurfaceFilter`.
        :return: A tuple containing the boundary mesh, the normal vectors array,
                 an array that maps the id of the boundary element to the id of the 3d cell it touches.
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
        normals = n.GetOutput().GetCellData().GetArray( "Normals" )
        assert normals
        assert normals.GetNumberOfComponents() == 3
        assert normals.GetNumberOfTuples() == boundaryMesh.GetNumberOfCells()
        originalCells = boundaryMesh.GetCellData().GetArray( originalCellsKey )
        assert originalCells
        return boundaryMesh, normals, originalCells

    def GetNumberOfCells( self ) -> int:
        """
        The number of cells.
        :return: An integer.
        """
        return self.reBoundaryMesh.GetNumberOfCells()

    def GetNumberOfPoints( self ) -> int:
        """
        The number of points.
        :return: An integer.
        """
        return self.reBoundaryMesh.GetNumberOfPoints()

    def bounds( self, i ) -> Tuple[ float, float, float, float, float, float ]:
        """
        The boundrary box of cell `i`.
        :param i: The boundary cell index.
        :return: The vtk bounding box.
        """
        return self.reBoundaryMesh.GetCell( i ).GetBounds()

    def normals( self, i ) -> numpy.ndarray:
        """
        The normal of cell `i`. This normal will be directed outwards
        :param i: The boundary cell index.
        :return: The normal as a length-3 numpy array.
        """
        return self.__normals[ i ]

    def GetCell( self, i ) -> vtkCell:
        """
        Cell i of the boundary mesh. This cell will have its normal directed outwards.
        :param i: The boundary cell index.
        :return: The cell instance.
        :warning: This member function relies on the vtkUnstructuredGrid.GetCell member function which is not thread safe.
        """
        return self.reBoundaryMesh.GetCell( i )

    def GetPoint( self, i ) -> Tuple[ float, float, float ]:
        """
        Point i of the boundary mesh.
        :param i: The boundary point index.
        :return: A length-3 tuple containing the coordinates of the point.
        :warning: This member function relies on the vtkUnstructuredGrid.GetPoint member function which is not thread safe.
        """
        return self.reBoundaryMesh.GetPoint( i )

    @property
    def originalCells( self ):
        """
        Returns the 2d boundary cell to the 3d cell index of the original mesh.
        :return: A 1d array.
        """
        return self.__originalCells


def buildPolyDataForExtrusion( i: int, boundaryMesh: BoundaryMesh ) -> vtkPolyData:
    """
    Creates a vtkPolyData containing the unique cell `i` of the boundary mesh.
    This operation is needed to use the vtk extrusion filter.
    :param i: The boundary cell index that will eventually be extruded.
    :param boundaryMesh:
    :return: The created vtkPolyData.
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


def arePointsConformal( pointTolerance: float, cellI: vtkCell, cellJ: vtkCell ) -> bool:
    """
    Checks if points of cell `i` matches, one by one, the points of cell `j`.
    :param pointTolerance: The point tolerance to consider that two points match.
    :param cellI: The first cell.
    :param cellJ: The second cell.
    :return: A boolean.
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


class Extruder:
    """
    Computes and stores all the extrusions of the boundary faces.
    The main reason for this class is to be lazy and cache the extrusions.
    """

    def __init__( self, boundaryMesh: BoundaryMesh, faceTolerance: float ):
        self.__extrusions: List[ vtkPolyData ] = [
            None,
        ] * boundaryMesh.GetNumberOfCells()
        self.__boundaryMesh = boundaryMesh
        self.__faceTolerance = faceTolerance

    def __extrude( self, polygonPolyData, normal ) -> vtkPolyData:
        """
        Extrude the polygon data to create a volume that will be used for intersection.
        :param polygonPolyData: The data to extrude
        :param normal: The (uniform) direction of the extrusion.
        :return: The extrusion.
        """
        extruder = vtkLinearExtrusionFilter()
        extruder.SetExtrusionTypeToVectorExtrusion()
        extruder.SetVector( normal )
        extruder.SetScaleFactor( self.__faceTolerance / 2. )
        extruder.SetInputData( polygonPolyData )
        extruder.Update()
        return extruder.GetOutput()

    def __getitem__( self, i ) -> vtkPolyData:
        """
        Returns the vtk extrusion for boundary element i.
        :param i: The cell index.
        :return: The vtk instance.
        """
        extrusion = self.__extrusions[ i ]
        if extrusion:
            return extrusion
        extrusion = self.__extrude( buildPolyDataForExtrusion( i, self.__boundaryMesh ),
                                    self.__boundaryMesh.normals( i ) )
        self.__extrusions[ i ] = extrusion
        return extrusion


def areFacesConformalUsingExtrusions( extrusions: Extruder, i: int, j: int, boundaryMesh: vtkUnstructuredGrid,
                                      pointTolerance: float ) -> bool:
    """
    Tests if two boundary faces are conformal, checking for intersection between their normal extruded volumes.
    :param extrusions: The extrusions cache.
    :param i: The cell index of the first cell.
    :param j: The cell index of the second cell.
    :param boundaryMesh: The boundary mesh.
    :param pointTolerance: The point tolerance to consider that two points match.
    :return: A boolean.
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
    """
    Tests if two boundary faces are conformal, checking the minimal distance between triangulated surfaces.
    :param i: The cell index of the first cell.
    :param j: The cell index of the second cell.
    :param boundaryMesh: The boundary mesh.
    :param faceTolerance: The tolerance under which we should consider the two faces "touching" each other.
    :param pointTolerance: The point tolerance to consider that two points match.
    :return: A boolean.
    """
    cpI = boundaryMesh.GetCell( i ).NewInstance()
    cpI.DeepCopy( boundaryMesh.GetCell( i ) )
    cpJ = boundaryMesh.GetCell( j ).NewInstance()
    cpJ.DeepCopy( boundaryMesh.GetCell( j ) )

    def triangulate( cell ):
        assert cell.GetCellDimension() == 2
        _pointsIds = vtkIdList()
        _points = vtkPoints()
        cell.Triangulate( 0, _pointsIds, _points )
        _pointsIds = tuple( vtkIter( _pointsIds ) )
        assert len( _pointsIds ) % 3 == 0
        assert _points.GetNumberOfPoints() % 3 == 0
        return _pointsIds, _points

    pointsIdsI, pointsI = triangulate( cpI )
    pointsIdsJ, pointsJ = triangulate( cpJ )

    def buildNumpyTriangles( pointsIds ):
        __triangles = []
        for __i in range( 0, len( pointsIds ), 3 ):
            __t = []
            for __pi in pointsIds[ __i:__i + 3 ]:
                __t.append( boundaryMesh.GetPoint( __pi ) )
            __triangles.append( numpy.array( __t, dtype=float ) )
        return __triangles

    trianglesI = buildNumpyTriangles( pointsIdsI )
    trianglesJ = buildNumpyTriangles( pointsIdsJ )

    minDist = numpy.inf
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


def __action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """
    Checks if the mesh is "conformal" (i.e. if some of its boundary faces may not be too close to each other without matching nodes).
    :param mesh: The vtk mesh
    :param options: The check options.
    :return: The Result instance.
    """
    boundaryMesh = BoundaryMesh( mesh )
    cosTheta = abs( math.cos( numpy.deg2rad( options.angleTolerance ) ) )
    numCells = boundaryMesh.GetNumberOfCells()

    # Computing the exact number of cells per node
    numCellsPerNode = numpy.zeros( boundaryMesh.GetNumberOfPoints(), dtype=int )
    for ic in range( boundaryMesh.GetNumberOfCells() ):
        c = boundaryMesh.GetCell( ic )
        pointIds = c.GetPointIds()
        for pointId in vtkIter( pointIds ):
            numCellsPerNode[ pointId ] += 1

    cellLocator = vtkStaticCellLocator()
    cellLocator.Initialize()
    cellLocator.SetNumberOfCellsPerNode( numCellsPerNode.max() )
    cellLocator.SetDataSet( boundaryMesh.reBoundaryMesh )
    cellLocator.BuildLocator()

    # Precomputing the bounding boxes.
    # The options are important to directly interact with memory in C++.
    boundingBoxes = numpy.empty( ( boundaryMesh.GetNumberOfCells(), 6 ), dtype=numpy.double, order="C" )
    for i in range( boundaryMesh.GetNumberOfCells() ):
        bb = vtkBoundingBox( boundaryMesh.bounds( i ) )
        bb.Inflate( 2 * options.faceTolerance )
        assert boundingBoxes[
            i, : ].data.contiguous  # Do not modify the storage layout since vtk deals with raw memory here.
        bb.GetBounds( boundingBoxes[ i, : ] )

    nonConformalCells = []
    extrusions = Extruder( boundaryMesh, options.faceTolerance )
    closeCells = vtkIdList()
    # Looping on all the pairs of boundary cells. We'll hopefully discard most of the pairs.
    for i in tqdm( range( numCells ), desc="Non conformal elements" ):
        cellLocator.FindCellsWithinBounds( boundingBoxes[ i ], closeCells )
        for j in vtkIter( closeCells ):
            if j < i:
                continue
            # Discarding pairs that are not facing each others (with a threshold).
            normalI, normalJ = boundaryMesh.normals( i ), boundaryMesh.normals( j )
            if numpy.dot( normalI, normalJ ) > -cosTheta:  # opposite directions only (can be facing or not)
                continue
            # At this point, back-to-back and face-to-face pairs of elements are considered.
            if not areFacesConformalUsingExtrusions( extrusions, i, j, boundaryMesh, options.pointTolerance ):
                nonConformalCells.append( ( i, j ) )
    # Extracting the original 3d element index (and not the index of the boundary mesh).
    tmp = []
    for i, j in nonConformalCells:
        tmp.append( ( boundaryMesh.originalCells.GetValue( i ), boundaryMesh.originalCells.GetValue( j ) ) )

    return Result( nonConformalCells=tmp )


def action( vtkInputFile: str, options: Options ) -> Result:
    mesh = read_mesh( vtkInputFile )
    return __action( mesh, options )
