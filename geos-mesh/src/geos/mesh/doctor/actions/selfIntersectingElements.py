from dataclasses import dataclass
from typing import Collection
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
    wrongNumberOfPointsElements: Collection[ int ]
    intersectingEdgesElements: Collection[ int ]
    intersectingFacesElements: Collection[ int ]
    nonContiguousEdgesElements: Collection[ int ]
    nonConvexElements: Collection[ int ]
    facesAreOrientedIncorrectlyElements: Collection[ int ]


def __action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    errOut = vtkFileOutputWindow()
    errOut.SetFileName( "/dev/null" )  # vtkCellValidator outputs loads for each cell...
    vtkStdErrOut = vtkOutputWindow()
    vtkStdErrOut.SetInstance( errOut )

    valid = 0x0
    wrongNumberOfPoints = 0x01
    intersectingEdges = 0x02
    intersectingFaces = 0x04
    nonContiguousEdges = 0x08
    nonConvex = 0x10
    facesAreOrientedIncorrectly = 0x20

    wrongNumberOfPointsElements: list[ int ] = []
    intersectingEdgesElements: list[ int ] = []
    intersectingFacesElements: list[ int ] = []
    nonContiguousEdgesElements: list[ int ] = []
    nonConvexElements: list[ int ] = []
    facesAreOrientedIncorrectlyElements: list[ int ] = []

    f = vtkCellValidator()
    f.SetTolerance( options.minDistance )

    f.SetInputData( mesh )
    f.Update()
    output = f.GetOutput()

    validity = output.GetCellData().GetArray( "ValidityState" )  # Could not change name using the vtk interface.
    assert validity is not None
    validity = vtk_to_numpy( validity )
    for i, v in enumerate( validity ):
        if not v & valid:
            if v & wrongNumberOfPoints:
                wrongNumberOfPointsElements.append( i )
            if v & intersectingEdges:
                intersectingEdgesElements.append( i )
            if v & intersectingFaces:
                intersectingFacesElements.append( i )
            if v & nonContiguousEdges:
                nonContiguousEdgesElements.append( i )
            if v & nonConvex:
                nonConvexElements.append( i )
            if v & facesAreOrientedIncorrectly:
                facesAreOrientedIncorrectlyElements.append( i )
    return Result( wrongNumberOfPointsElements=wrongNumberOfPointsElements,
                   intersectingEdgesElements=intersectingEdgesElements,
                   intersectingFacesElements=intersectingFacesElements,
                   nonContiguousEdgesElements=nonContiguousEdgesElements,
                   nonConvexElements=nonConvexElements,
                   facesAreOrientedIncorrectlyElements=facesAreOrientedIncorrectlyElements )


def action( vtkInputFile: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtkInputFile )
    return __action( mesh, options )
