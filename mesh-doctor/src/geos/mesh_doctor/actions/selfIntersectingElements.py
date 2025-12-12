# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersGeneral import vtkCellValidator
from vtkmodules.vtkCommonCore import vtkOutputWindow, vtkFileOutputWindow
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    minDistance: float


@dataclass( frozen=True )
class Result:
    invalidCellIds: dict[ str, list[ int ] ]


def getInvalidCellIds( mesh: vtkUnstructuredGrid, minDistance: float ) -> dict[ str, list[ int ] ]:
    """For every cell element in a vtk mesh, check if the cell is invalid regarding 8 specific criteria.

    "wrongNumberOfPoints", "intersectingEdges", "intersectingFaces", "nonContiguousEdges","nonConvex",
    "facesAreOrientedIncorrectly", "nonPlanarFacesElements" and "degenerateFacesElements".

    If any of this criteria was met, the cell index is added to a list corresponding to this specific criteria.
    The dict with the complete list of cell indices by criteria is returned.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        minDistance (float): Minimum distance in the computation.

    Returns:
        dict[ str, list[ int ] ]:
        {
            "wrongNumberOfPointsElements": [ 10, 34, ... ],
            "intersectingEdgesElements": [ ... ],
            "intersectingFacesElements": [ ... ],
            "nonContiguousEdgesElements": [ ... ],
            "nonConvexElements": [ ... ],
            "facesOrientedIncorrectlyElements": [ ... ],
            "nonPlanarFacesElements": [ ... ],
            "degenerateFacesElements": [ ... ]
        }
    """
    errOut = vtkFileOutputWindow()
    errOut.SetFileName( "/dev/null" )
    vtkStdErrOut = vtkOutputWindow()
    vtkStdErrOut.SetInstance( errOut )

    # Different types of cell invalidity are defined as hexadecimal values, specific to vtkCellValidator
    # Complete set of validity checks available in vtkCellValidator
    errorMasks: dict[ str, int ] = {
        "wrongNumberOfPointsElements": 0x01,  # 0000 0001
        "intersectingEdgesElements": 0x02,  # 0000 0010
        "intersectingFacesElements": 0x04,  # 0000 0100
        "nonContiguousEdgesElements": 0x08,  # 0000 1000
        "nonConvexElements": 0x10,  # 0001 0000
        "facesOrientedIncorrectlyElements": 0x20,  # 0010 0000
        "nonPlanarFacesElements": 0x40,  # 0100 0000
        "degenerateFacesElements": 0x80,  # 1000 0000
    }

    # The results can be stored in a dictionary where keys are the error names
    # and values are the lists of cell indices with that error.
    # We can initialize it directly from the keys of our errorMasks dictionary.
    invalidCellIds: dict[ str, list[ int ] ] = { _errorName: [] for _errorName in errorMasks }

    f = vtkCellValidator()
    f.SetTolerance( minDistance )
    f.SetInputData( mesh )
    f.Update()  # executes the filter
    output = f.GetOutput()

    validity = output.GetCellData().GetArray( "ValidityState" )
    assert validity is not None
    # array of np.int16 that combines the flags using a bitwise OR operation for each cell index.
    validity = vtk_to_numpy( validity )
    for cellIndex, validityFlag in enumerate( validity ):
        if not validityFlag:  # Skip valid cells ( validityFlag == 0 or 0000 0000 )
            continue
        for errorName, errorMask in errorMasks.items():  # Check only invalid cells against all possible errors.
            if validityFlag & errorMask:
                invalidCellIds[ errorName ].append( cellIndex )

    return invalidCellIds


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the self intersecting elements check on a vtkUnstructuredGrid.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of the self intersecting elements check.
    """
    invalidCellIds: dict[ str, list[ int ] ] = getInvalidCellIds( mesh, options.minDistance )
    return Result( invalidCellIds )


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
