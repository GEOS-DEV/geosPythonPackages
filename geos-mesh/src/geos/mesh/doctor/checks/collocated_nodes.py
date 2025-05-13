from collections import defaultdict
from dataclasses import dataclass
import logging
import numpy
from vtkmodules.vtkCommonCore import reference, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkIncrementalOctreePointLocator, vtkPointSet, vtkCell
from geos.mesh.vtk.io import read_mesh


@dataclass( frozen=True )
class Options:
    tolerance: float


@dataclass( frozen=True )
class Result:
    nodes_buckets: list[ tuple[ int ] ]  # Each bucket contains the duplicated node indices.
    wrong_support_elements: list[ int ]  # Element indices with support node indices appearing more than once.


def find_collocated_nodes_buckets( mesh: vtkPointSet, tolerance: float ) -> list[ tuple[ int ] ]:
    points: vtkPoints = mesh.GetPoints()

    locator = vtkIncrementalOctreePointLocator()
    locator.SetTolerance( tolerance )
    output = vtkPoints()
    locator.InitPointInsertion( output, points.GetBounds() )

    # original ids to/from filtered ids.
    filtered_to_original = numpy.ones( points.GetNumberOfPoints(), dtype=int ) * -1

    rejected_points: dict[ int, list[ int ] ] = defaultdict( list )
    point_id: int = reference( 0 )
    for i in range( points.GetNumberOfPoints() ):
        is_inserted = locator.InsertUniquePoint( points.GetPoint( i ), point_id )
        if not is_inserted:
            # If it's not inserted, `point_id` contains the node that was already at that location.
            # But in that case, `point_id` is the new numbering in the destination points array.
            # It's more useful for the user to get the old index in the original mesh, so he can look for it in his data.
            logging.debug(
                f"Point {i} at {points.GetPoint(i)} has been rejected, point {filtered_to_original[point_id.get()]} is already inserted."
            )
            rejected_points[ point_id.get() ].append( i )
        else:
            # If it's inserted, `point_id` contains the new index in the destination array.
            # We store this information to be able to connect the source and destination arrays.
            # original_to_filtered[i] = point_id.get()
            filtered_to_original[ point_id.get() ] = i

    collocated_nodes_buckets: list[ tuple[ int ] ] = list()
    for n, ns in rejected_points.items():
        collocated_nodes_buckets.append( ( n, *ns ) )
    return collocated_nodes_buckets


def find_wrong_support_elements( mesh: vtkPointSet ) -> list[ int ]:
    # Checking that the support node indices appear only once per element.
    wrong_support_elements: list[ int ] = list()
    for c in range( mesh.GetNumberOfCells() ):
        cell: vtkCell = mesh.GetCell( c )
        num_points_per_cell: int = cell.GetNumberOfPoints()
        if len( { cell.GetPointId( i ) for i in range( num_points_per_cell ) } ) != num_points_per_cell:
            wrong_support_elements.append( c )
    return wrong_support_elements


def __check( mesh: vtkPointSet, options: Options ) -> Result:
    collocated_nodes_buckets = find_collocated_nodes_buckets( mesh, options.tolerance )
    wrong_support_elements = find_wrong_support_elements( mesh )
    return Result( nodes_buckets=collocated_nodes_buckets, wrong_support_elements=wrong_support_elements )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh: vtkPointSet = read_mesh( vtk_input_file )
    return __check( mesh, options )
