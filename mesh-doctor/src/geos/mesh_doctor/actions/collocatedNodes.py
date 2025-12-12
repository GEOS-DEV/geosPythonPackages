# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from collections import defaultdict
from dataclasses import dataclass
import numpy
from typing import Collection, Iterable
from vtkmodules.vtkCommonCore import reference, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCell, vtkIncrementalOctreePointLocator, vtkUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    tolerance: float


@dataclass( frozen=True )
class Result:
    nodesBuckets: Iterable[ Iterable[ int ] ]  # Each bucket contains the duplicated node indices.
    wrongSupportElements: Collection[ int ]  # Element indices with support node indices appearing more than once.


def findCollocatedNodesBuckets( mesh: vtkUnstructuredGrid, tolerance: float ) -> list[ tuple[ int, ...] ]:
    """Check all the nodes of a mesh and returns every bucket of nodes that are collocated within a tolerance.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        tolerance (float): The distance tolerance within which nodes are considered collocated.

    Returns:
        list[ tuple[ int, ... ] ]: A list of tuples, each containing indices of nodes that are collocated.
    """
    points: vtkPoints = mesh.GetPoints()
    locator = vtkIncrementalOctreePointLocator()
    locator.SetTolerance( tolerance )
    output = vtkPoints()
    locator.InitPointInsertion( output, points.GetBounds() )

    # original ids to/from filtered ids.
    filteredToOriginal = numpy.ones( points.GetNumberOfPoints(), dtype=int ) * -1

    rejectedPoints: defaultdict[ int, list[ int ] ] = defaultdict( list )
    pointId = reference( 0 )
    for i in range( points.GetNumberOfPoints() ):
        isInserted = locator.InsertUniquePoint( points.GetPoint( i ), pointId )  # type: ignore[arg-type]
        if not isInserted:
            # If it's not inserted, `pointId` contains the node that was already at that location.
            # But in that case, `pointId` is the new numbering in the destination points array.
            # It's more useful for the user to get the old index in the original mesh so he can look for it in his data.
            setupLogger.debug(
                f"Point {i} at {points.GetPoint(i)} has been rejected, " +
                f"point {filteredToOriginal[pointId.get()]} is already inserted.",  # type: ignore[misc, call-overload]
            )
            rejectedPoints[ pointId.get() ].append( i )  # type: ignore[misc, index]
        else:
            # If it's inserted, `pointId` contains the new index in the destination array.
            # We store this information to be able to connect the source and destination arrays.
            # originalToFiltered[i] = pointId.get()
            filteredToOriginal[ pointId.get() ] = i  # type: ignore[misc, call-overload]

    collocatedNodesBuckets: list[ tuple[ int, ...] ] = []
    for n, ns in rejectedPoints.items():
        collocatedNodesBuckets.append( ( n, *ns ) )
    return collocatedNodesBuckets


def findWrongSupportElements( mesh: vtkUnstructuredGrid ) -> list[ int ]:
    """Checking that the support node indices appear only once per element.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.

    Returns:
        list[ int ]: A list of cell indices with support node indices appearing more than once.
    """
    wrongSupportElements: list[ int ] = []
    for c in range( mesh.GetNumberOfCells() ):
        cell: vtkCell = mesh.GetCell( c )
        numPointsPerCell: int = cell.GetNumberOfPoints()
        if len( { cell.GetPointId( i ) for i in range( numPointsPerCell ) } ) != numPointsPerCell:
            wrongSupportElements.append( c )
    return wrongSupportElements


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the collocated nodes check on a vtkUnstructuredGrid.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of the collocated nodes check.
    """
    nodesBuckets = findCollocatedNodesBuckets( mesh, options.tolerance )
    wrongSupportElements = findWrongSupportElements( mesh )
    return Result( nodesBuckets=nodesBuckets, wrongSupportElements=wrongSupportElements )  # type: ignore[arg-type]


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs the element volumes check on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the element volumes check.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
