# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union, Any
import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData, vtkUnstructuredGrid, VTK_LINE, VTK_QUAD, VTK_HEXAHEDRON
from vtkmodules.vtkIOXML import vtkXMLGenericDataObjectReader

from geos.utils.pieceEnum import Piece
from geos.mesh.utils.genericHelpers import createMultiCellMesh


@pytest.fixture
def arrayTest( request: pytest.FixtureRequest ) -> npt.NDArray[ np.float64 ]:
    """Get a random array of float64."""
    np.random.seed( 42 )
    array: npt.NDArray[ np.float64 ] = np.random.rand(
        request.param,
        3,
    )
    return array


@pytest.fixture
def getArrayWithSpeTypeValue() -> Any:
    """Get a random array of input type with the function _getarray().

    Returns:
        npt.NDArray[Any]: Random array of input type.
    """

    def _getarray( nb_component: int, nb_elements: int, valueType: str ) -> Any:
        """Get a random array of input type.

        Args:
            nb_component (int): Number of components.
            nb_elements (int): Number of elements.
            valueType (str): The type of the value.

        Returns:
            npt.NDArray[Any]: Random array of input type.
        """
        np.random.seed( 28 )
        if valueType == "int8":
            if nb_component == 1:
                return np.array( [ np.int8( 10 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int8( 10 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "int16":
            if nb_component == 1:
                return np.array( [ np.int16( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int16( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "int32":
            if nb_component == 1:
                return np.array( [ np.int32( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int32( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "int64":
            if nb_component == 1:
                return np.array( [ np.int64( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int64( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        if valueType == "uint8":
            if nb_component == 1:
                return np.array( [ np.uint8( 10 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.uint8( 10 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "uint16":
            if nb_component == 1:
                return np.array( [ np.uint16( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.uint16( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "uint32":
            if nb_component == 1:
                return np.array( [ np.uint32( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.uint32( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "uint64":
            if nb_component == 1:
                return np.array( [ np.uint64( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.uint64( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "int":
            if nb_component == 1:
                return np.array( [ int( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ int( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "float":
            if nb_component == 1:
                return np.array( [ float( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ float( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "float32":
            if nb_component == 1:
                return np.array( [ np.float32( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.float32( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

        elif valueType == "float64":
            if nb_component == 1:
                return np.array( [ np.float64( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.float64( 1000 * np.random.random() ) for _ in range( nb_component ) ]
                                   for _ in range( nb_elements ) ] )

    return _getarray


@pytest.fixture
def dataSetTest() -> Any:
    """Get a vtkObject from a file with the function _get_dataset().

    Returns:
        (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
    """

    def _get_dataset( datasetType: str ) -> Union[ vtkMultiBlockDataSet, vtkPolyData, vtkDataSet ]:
        """Get a vtkObject from a file.

        Args:
            datasetType (str): The type of vtk object wanted.

        Returns:
            (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
        """
        reader: vtkXMLGenericDataObjectReader = vtkXMLGenericDataObjectReader()
        if datasetType == "multiblock":
            vtkFilename = "data/displacedFault.vtm"
        elif datasetType == "emptymultiblock":
            vtkFilename = "data/displacedFaultempty.vtm"
        elif datasetType == "multiblockGeosOutput":
            # adapted from example GEOS/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_smoke.xml
            vtkFilename = "data/simpleReservoirViz_small_000478.vtm"
        elif datasetType == "fracture":
            vtkFilename = "data/fracture_res5_id.vtu"
        elif datasetType == "emptyFracture":
            vtkFilename = "data/fracture_res5_id_empty.vtu"
        elif datasetType == "dataset":
            vtkFilename = "data/domain_res5_id.vtu"
        elif datasetType == "emptydataset":
            vtkFilename = "data/domain_res5_id_empty.vtu"
        elif datasetType == "polydata":
            vtkFilename = "data/fracture_res5_id.vtp"
        elif datasetType == "emptypolydata":
            vtkFilename = "data/fracture_res5_id_empty.vtp"
        elif datasetType == "meshGeosExtractBlockTmp":
            vtkFilename = "data/meshGeosExtractBlockTmp.vtm"
        elif datasetType == "well":
            vtkFilename = "data/well.vtu"
        elif datasetType == "emptyWell":
            vtkFilename = "data/well_empty.vtu"

        if datasetType == "2Ranks":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/cellElementRegion2Ranks.vtm"
        elif datasetType == "geosOutput2Ranks":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/geosOutput2Ranks.vtm"
        elif datasetType == "extractAndMergeVolume":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeVolume.vtu"
        elif datasetType == "extractAndMergeFault":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFault.vtu"
        elif datasetType == "extractAndMergeFaultVtp":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFault.vtp"
        elif datasetType == "extractAndMergeWell1":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeWell1.vtu"
        elif datasetType == "extractAndMergeVolumeWell1":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeVolumeWell1.vtm"
        elif datasetType == "extractAndMergeFaultWell1":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFaultWell1.vtm"

        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset


@pytest.fixture
def internMeshTest() -> Any:
    """Get an intern mesh.

    Returns:
        mesh (vtkUnstructuredGrid | vtkMultiBlockDataSet): An internal mesh.
    """
    ## mesh 3D
    coordPts3D: list[ list[ float ] ] = [ [ -1., 0., 0. ], [ 0., 0., 0. ], [ 0., 1., 0. ], [ -1., 1., 0. ],
                                          [ -1., 0., 1. ], [ 0., 0., 1. ], [ 0., 1., 1. ], [ -1., 1., 1. ],
                                          [ 1., 0., 0. ], [ 1., 1., 0. ], [ 1., 0., 1. ], [ 1., 1., 1. ],
                                          [ 2., 0., 0. ], [ 2., 1., 0. ], [ 2., 0., 1. ], [ 2., 1., 1. ] ]
    cellsMesh3D: list[ tuple[ int, ...] ] = [ ( 0, 1, 2, 3, 4, 5, 6, 7 ), ( 1, 8, 9, 2, 5, 10, 11, 6 ),
                                              ( 8, 12, 13, 9, 10, 14, 15, 11 ) ]
    coordCells3D: list[ npt.NDArray[ np.float64 ] ] = [
        np.array( [ coordPts3D[ i ] for i in cellMesh3D ] ) for cellMesh3D in cellsMesh3D
    ]
    list3DCellType: list[ int ] = [ VTK_HEXAHEDRON, VTK_HEXAHEDRON, VTK_HEXAHEDRON ]

    ## mesh 2D
    coordPts2D: list[ list[ float ] ] = [ [ 0., 0., 0. ], [ 1., 0., 0. ], [ 1., 0., 1. ], [ 0., 0., 1. ],
                                          [ 2., 0., 0. ], [ 2., 0., 1. ], [ 3., 0., 0. ], [ 3., 0., 1. ] ]
    cellsMesh2D: list[ tuple[ int, ...] ] = [ ( 0, 1, 2, 3 ), ( 1, 4, 5, 2 ), ( 4, 6, 7, 5 ) ]
    coordCells2D: list[ npt.NDArray[ np.float64 ] ] = [
        np.array( [ coordPts2D[ i ] for i in cellMesh2D ] ) for cellMesh2D in cellsMesh2D
    ]
    list2DCellType: list[ int ] = [ VTK_QUAD, VTK_QUAD, VTK_QUAD ]

    ## mesh 1D
    coordPts1D: list[ list[ float ] ] = [ [ 1., 0., 0. ], [ 1., 0., 1. ], [ 1.5, 0., 0. ], [ 1.5, 0., 1. ] ]
    cellsMesh1D: list[ tuple[ int, ...] ] = [ ( 0, 1 ), ( 2, 3 ) ]
    coordCells1D: list[ npt.NDArray[ np.float64 ] ] = [
        np.array( [ coordPts1D[ i ] for i in cellMesh1D ] ) for cellMesh1D in cellsMesh1D
    ]
    list1DCellType: list[ int ] = [ VTK_LINE, VTK_LINE ]

    testCase: dict[ str, tuple[ list[ npt.NDArray[ np.float64 ] ], list[ int ] ] ] = {
        "vtu1D": ( coordCells1D, list1DCellType ),
        "vtu2D": ( coordCells2D, list2DCellType ),
        "vtu3D": ( coordCells3D, list3DCellType )
    }

    def _get_mesh( meshType: str ) -> vtkUnstructuredGrid | vtkMultiBlockDataSet:
        """Create and return a mesh with the right type.

        Args:
            meshType (str): The type of mesh wanted.

        Returns:
            (vtkUnstructuredGrid | vtkMultiBlockDataSet): The mesh created.
        """
        cellType: list[ int ]
        cellPtsCoord: list[ npt.NDArray[ np.float64 ] ]
        if meshType == 'vtm':
            mesh = vtkMultiBlockDataSet()
            mesh.SetNumberOfBlocks( 3 )
            for i, key in enumerate( testCase ):
                cellPtsCoord, cellType = testCase[ key ]
                mesh.SetBlock( i, createMultiCellMesh( cellType, cellPtsCoord ) )
        else:
            cellPtsCoord, cellType = testCase[ meshType ]
            mesh = createMultiCellMesh( cellType, cellPtsCoord )

        return mesh

    return _get_mesh


@pytest.fixture
def getElementMap() -> Any:
    """Get the element indexes mapping dictionary using the function _get_elementMap() between two meshes.

    Returns:
        elementMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary.
    """

    def _get_elementMap( meshFromName: str, meshToName: str, piece: Piece ) -> dict[ int, npt.NDArray[ np.int64 ] ]:
        """Get the element indexes mapping dictionary between two meshes.

        Args:
            meshFromName (str): The name of the meshFrom.
            meshToName (str): The name of the meshTo.
            piece (Piece): The element to map.

        Returns:
            elementMap (dict[int, npt.NDArray[np.int64]]): The element mapping dictionary.
        """
        sharedElem2D3DIds: dict[ Piece, npt.NDArray[ np.int64 ] ] = {
            Piece.CELLS: np.array( [ [ 0, 1 ], [ 1, 2 ] ], dtype=np.int64 ),
            Piece.POINTS: np.array( [ [ 0, 1 ], [ 1, 8 ], [ 2, 10 ], [ 3, 5 ], [ 4, 12 ], [ 5, 14 ] ], dtype=np.int64 )
        }

        sharedElem1D2DIds: dict[ Piece, npt.NDArray[ np.int64 ] ] = {
            Piece.CELLS: np.array( [ [ 0, 0 ] ], dtype=np.int64 ),
            Piece.POINTS: np.array( [ [ 0, 1 ], [ 1, 2 ] ], dtype=np.int64 )
        }

        sharedElem1D3DIds: dict[ Piece, npt.NDArray[ np.int64 ] ] = {
            Piece.CELLS: np.array( [ [ 0, 1 ] ], dtype=np.int64 ),
            Piece.POINTS: np.array( [ [ 0, 8 ], [ 1, 10 ] ], dtype=np.int64 )
        }

        elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = {}
        nbElements: tuple[ int, int, int ] = ( 16, 8, 4 ) if piece == Piece.POINTS else ( 3, 3, 2 )
        if meshFromName == "vtu1D":
            if meshToName == "vtu1D":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 2 ] ) ] )
            elif meshToName == "vtu2D":
                elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id2DElem in range( nbElements[ 1 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if id2DElem == sharedElem1D2DId[ 1 ]:
                            elementMap[ 0 ][ id2DElem ] = [ 0, sharedElem1D2DId[ 0 ] ]
            elif meshToName == "vtu3D":
                elementMap[ 0 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if id3DElem == sharedElem1D3DId[ 1 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, sharedElem1D3DId[ 0 ] ]
            elif meshToName == "vtm":
                elementMap[ 1 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 2 ] ) ] )
                elementMap[ 2 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id2DElem in range( nbElements[ 1 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if id2DElem == sharedElem1D2DId[ 1 ]:
                            elementMap[ 2 ][ id2DElem ] = [ 0, sharedElem1D2DId[ 0 ] ]
                elementMap[ 3 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if id3DElem == sharedElem1D3DId[ 1 ]:
                            elementMap[ 3 ][ id3DElem ] = [ 0, sharedElem1D3DId[ 0 ] ]
        elif meshFromName == "vtu2D":
            if meshToName == "vtu2D":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
            elif meshToName == "vtu1D":
                elementMap[ 0 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id1DElem in range( nbElements[ 2 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if id1DElem == sharedElem1D2DId[ 0 ]:
                            elementMap[ 0 ][ id1DElem ] = [ 0, sharedElem1D2DId[ 1 ] ]
            elif meshToName == "vtu3D":
                elementMap[ 0 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                        if id3DElem == sharedElem2D3DId[ 1 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, sharedElem2D3DId[ 0 ] ]
            elif meshToName == "vtm":
                elementMap[ 1 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id1DElem in range( nbElements[ 2 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if id1DElem == sharedElem1D2DId[ 0 ]:
                            elementMap[ 1 ][ id1DElem ] = [ 0, sharedElem1D2DId[ 1 ] ]
                elementMap[ 2 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
                elementMap[ 3 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                        if id3DElem == sharedElem2D3DId[ 1 ]:
                            elementMap[ 3 ][ id3DElem ] = [ 0, sharedElem2D3DId[ 0 ] ]
        elif meshFromName == "vtu3D":
            if meshToName == "vtu3D":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
            elif meshToName == "vtu1D":
                elementMap[ 0 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id1DElem in range( nbElements[ 2 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if id1DElem == sharedElem1D3DId[ 0 ]:
                            elementMap[ 0 ][ id1DElem ] = [ 0, sharedElem1D3DId[ 1 ] ]
            elif meshToName == "vtu2D":
                elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id2DElem in range( nbElements[ 1 ] ):
                    for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                        if id2DElem == sharedElem2D3DId[ 0 ]:
                            elementMap[ 0 ][ id2DElem ] = [ 0, sharedElem2D3DId[ 1 ] ]
            elif meshToName == "vtm":
                elementMap[ 1 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id1DElem in range( nbElements[ 2 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if id1DElem == sharedElem1D3DId[ 0 ]:
                            elementMap[ 1 ][ id1DElem ] = [ 0, sharedElem1D3DId[ 1 ] ]
                elementMap[ 2 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id2DElem in range( nbElements[ 1 ] ):
                    for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                        if id2DElem == sharedElem2D3DId[ 0 ]:
                            elementMap[ 2 ][ id2DElem ] = [ 0, sharedElem2D3DId[ 1 ] ]
                elementMap[ 3 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
        elif meshFromName == "vtm":
            if meshToName == "vtm":
                elementMap[ 1 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 2 ] ) ] )
                elementMap[ 2 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for idElem in range( nbElements[ 1 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if idElem == sharedElem1D2DId[ 1 ]:
                            elementMap[ 2 ][ idElem ] = [ 1, sharedElem1D2DId[ 0 ] ]
                    if ( elementMap[ 2 ][ idElem ] == [ -1, -1 ] ).all():
                        elementMap[ 2 ][ idElem ] = [ 2, idElem ]
                elementMap[ 3 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for idElem in range( nbElements[ 0 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if idElem == sharedElem1D3DId[ 1 ]:
                            elementMap[ 3 ][ idElem ] = [ 1, sharedElem1D3DId[ 0 ] ]
                    if ( elementMap[ 3 ][ idElem ] == [ -1, -1 ] ).all():
                        for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                            if idElem == sharedElem2D3DId[ 1 ]:
                                elementMap[ 3 ][ idElem ] = [ 2, sharedElem2D3DId[ 0 ] ]
                    if ( elementMap[ 3 ][ idElem ] == [ -1, -1 ] ).all():
                        elementMap[ 3 ][ idElem ] = [ 3, idElem ]
            elif meshToName == "vtu1D":
                elementMap[ 0 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 2 ] ) ] )
            elif meshToName == "vtu2D":
                elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for idElem in range( nbElements[ 1 ] ):
                    for sharedElem1D2DId in sharedElem1D2DIds[ piece ]:
                        if idElem == sharedElem1D2DId[ 1 ]:
                            elementMap[ 0 ][ idElem ] = [ 1, sharedElem1D2DId[ 0 ] ]
                    if ( elementMap[ 0 ][ idElem ] == [ -1, -1 ] ).all():
                        elementMap[ 0 ][ idElem ] = [ 2, idElem ]
            elif meshToName == "vtu3D":
                elementMap[ 0 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for idElem in range( nbElements[ 0 ] ):
                    for sharedElem1D3DId in sharedElem1D3DIds[ piece ]:
                        if idElem == sharedElem1D3DId[ 1 ]:
                            elementMap[ 0 ][ idElem ] = [ 1, sharedElem1D3DId[ 0 ] ]
                    if ( elementMap[ 0 ][ idElem ] == [ -1, -1 ] ).all():
                        for sharedElem2D3DId in sharedElem2D3DIds[ piece ]:
                            if idElem == sharedElem2D3DId[ 1 ]:
                                elementMap[ 0 ][ idElem ] = [ 2, sharedElem2D3DId[ 0 ] ]
                    if ( elementMap[ 0 ][ idElem ] == [ -1, -1 ] ).all():
                        elementMap[ 0 ][ idElem ] = [ 3, idElem ]

        return elementMap

    return _get_elementMap
