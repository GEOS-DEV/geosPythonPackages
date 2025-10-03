from collections import defaultdict
from dataclasses import dataclass
import numpy
from typing import Collection, Iterable
from vtkmodules.vtkCommonCore import reference, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkIncrementalOctreePointLocator
from geos.mesh.doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import read_mesh


@dataclass( frozen=True )
class Options:
    tolerance: float


@dataclass( frozen=True )
class Result:
    nodesBuckets: Iterable[ Iterable[ int ] ]  # Each bucket contains the duplicated node indices.
    wrongSupportElements: Collection[ int ]  # Element indices with support node indices appearing more than once.


def __action( mesh, options: Options ) -> Result:
    points = mesh.GetPoints()

    locator = vtkIncrementalOctreePointLocator()
    locator.SetTolerance( options.tolerance )
    output = vtkPoints()
    locator.InitPointInsertion( output, points.GetBounds() )

    # original ids to/from filtered ids.
    filteredToOriginal = numpy.ones( points.GetNumberOfPoints(), dtype=int ) * -1

    rejectedPoints = defaultdict( list )
    pointId = reference( 0 )
    for i in range( points.GetNumberOfPoints() ):
        isInserted = locator.InsertUniquePoint( points.GetPoint( i ), pointId )
        if not isInserted:
            # If it's not inserted, `pointId` contains the node that was already at that location.
            # But in that case, `pointId` is the new numbering in the destination points array.
            # It's more useful for the user to get the old index in the original mesh, so he can look for it in his data.
            setupLogger.debug(
                f"Point {i} at {points.GetPoint(i)} has been rejected, "
                f"point {filteredToOriginal[pointId.get()]} is already inserted."
            )
            rejectedPoints[ pointId.get() ].append( i )
        else:
            # If it's inserted, `pointId` contains the new index in the destination array.
            # We store this information to be able to connect the source and destination arrays.
            # originalToFiltered[i] = pointId.get()
            filteredToOriginal[ pointId.get() ] = i

    tmp = []
    for n, ns in rejectedPoints.items():
        tmp.append( ( n, *ns ) )

    # Checking that the support node indices appear only once per element.
    wrongSupportElements = []
    for c in range( mesh.GetNumberOfCells() ):
        cell = mesh.GetCell( c )
        numPointsPerCell = cell.GetNumberOfPoints()
        if len( { cell.GetPointId( i ) for i in range( numPointsPerCell ) } ) != numPointsPerCell:
            wrongSupportElements.append( c )

    return Result( nodesBuckets=tmp, wrongSupportElements=wrongSupportElements )


def action( vtkInputFile: str, options: Options ) -> Result:
    mesh = read_mesh( vtkInputFile )
    return __action( mesh, options )
