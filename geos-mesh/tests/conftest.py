# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union, Any, Tuple, Dict
import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLGenericDataObjectReader


@pytest.fixture
def arrayExpected( request: pytest.FixtureRequest ) -> npt.NDArray[ np.float64 ]:
    """Get an array from a file."""
    reference_data = "data/data.npz"
    reference_data_path = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), reference_data )
    data = np.load( reference_data_path )

    return data[ request.param ]


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
        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset


@pytest.fixture
def getElementMap() -> Any:
    """Get the element indexes mapping dictionary using the function _get_elementMap() between two meshes.

    Returns:
        elementMap (Dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary.
    """

    def _get_elementMap( meshFromName: str, meshToName: str, points: bool ) -> Dict[ int, npt.NDArray[ np.int64 ] ]:
        """Get the element indexes mapping dictionary between two meshes.

        Args:
            meshFromName (str): The name of the meshFrom.
            meshToName (str): The name of the meshTo.
            points (bool): True if elements to map is points, False if it is cells.

        Returns:
            elementMap (Dict[int, npt.NDArray[np.int64]]): The element mapping dictionary.
        """
        ShareCells2D3DId: npt.NDArray[ np.int64 ] = np.array(
            [ [ 0, 0 ], [ 1, 1 ], [ 2, 2 ], [ 3, 3 ], [ 4, 4 ], [ 5, 5 ], [ 6, 6 ], [ 7, 7 ], [ 8, 8 ], [ 9, 9 ],
              [ 10, 10 ], [ 11, 11 ], [ 12, 12 ], [ 13, 13 ], [ 14, 14 ], [ 15, 15 ], [ 16, 16 ], [ 17, 17 ],
              [ 18, 18 ], [ 19, 19 ], [ 20, 20 ], [ 21, 21 ], [ 22, 22 ], [ 23, 23 ], [ 24, 48 ], [ 25, 50 ],
              [ 26, 51 ], [ 27, 54 ], [ 28, 56 ], [ 29, 57 ], [ 30, 58 ], [ 31, 59 ], [ 32, 60 ], [ 33, 61 ],
              [ 34, 62 ], [ 35, 63 ], [ 36, 64 ], [ 37, 65 ], [ 38, 66 ], [ 39, 67 ], [ 40, 68 ], [ 41, 69 ],
              [ 42, 70 ], [ 43, 71 ], [ 44, 72 ], [ 45, 73 ], [ 46, 74 ], [ 47, 75 ], [ 48, 76 ], [ 49, 77 ],
              [ 50, 78 ], [ 51, 79 ], [ 52, 580 ], [ 53, 581 ], [ 54, 582 ], [ 55, 583 ], [ 56, 584 ], [ 57, 585 ],
              [ 58, 586 ], [ 59, 587 ], [ 60, 588 ], [ 61, 589 ], [ 62, 590 ], [ 63, 591 ], [ 64, 592 ], [ 65, 593 ],
              [ 66, 594 ], [ 67, 595 ], [ 68, 596 ], [ 69, 597 ], [ 70, 598 ], [ 71, 599 ], [ 72, 600 ], [ 73, 601 ],
              [ 74, 602 ], [ 75, 603 ], [ 76, 628 ], [ 77, 630 ], [ 78, 631 ], [ 79, 634 ], [ 80, 636 ], [ 81, 637 ],
              [ 82, 638 ], [ 83, 639 ], [ 84, 640 ], [ 85, 641 ], [ 86, 642 ], [ 87, 643 ], [ 88, 644 ], [ 89, 645 ],
              [ 90, 646 ], [ 91, 647 ], [ 92, 648 ], [ 93, 649 ], [ 94, 650 ], [ 95, 651 ], [ 96, 652 ], [ 97, 653 ],
              [ 98, 654 ], [ 99, 655 ], [ 100, 656 ], [ 101, 657 ], [ 102, 658 ], [ 103, 659 ], [ 104, 1160 ],
              [ 105, 1161 ], [ 106, 1162 ], [ 107, 1163 ], [ 108, 1164 ], [ 109, 1165 ], [ 110, 1166 ], [ 111, 1167 ],
              [ 112, 1168 ], [ 113, 1169 ], [ 114, 1170 ], [ 115, 1171 ], [ 116, 1172 ], [ 117, 1173 ], [ 118, 1174 ],
              [ 119, 1175 ], [ 120, 1176 ], [ 121, 1177 ], [ 122, 1178 ], [ 123, 1179 ], [ 124, 1180 ], [ 125, 1181 ],
              [ 126, 1182 ], [ 127, 1183 ], [ 128, 1208 ], [ 129, 1210 ], [ 130, 1211 ], [ 131, 1214 ], [ 132, 1216 ],
              [ 133, 1217 ], [ 134, 1218 ], [ 135, 1219 ], [ 136, 1220 ], [ 137, 1221 ], [ 138, 1222 ], [ 139, 1223 ],
              [ 140, 1224 ], [ 141, 1225 ], [ 142, 1226 ], [ 143, 1227 ], [ 144, 1228 ], [ 145, 1229 ], [ 146, 1230 ],
              [ 147, 1231 ], [ 148, 1232 ], [ 149, 1233 ], [ 150, 1234 ], [ 151, 1235 ], [ 152, 1236 ], [ 153, 1237 ],
              [ 154, 1238 ], [ 155, 1239 ] ],
            dtype=np.int64,
        )
        SharePoints1D2DId: npt.NDArray[ np.int64 ] = np.array( [ [ 0, 26 ] ], dtype=np.int64 )
        SharePoints1D3DId: npt.NDArray[ np.int64 ] = np.array( [ [ 0, 475 ] ], dtype=np.int64 )
        elementMap: Dict[ int, npt.NDArray[ np.int64 ] ] = {}
        nbElements: Tuple[ int, int, int ] = ( 4092, 212, 11 ) if points else ( 1740, 156, 10 )
        if meshFromName == "well":
            if meshToName == "emptyWell":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 2 ] ) ] )
            if meshToName == "emptyFracture" or meshToName == "emptypolydata":
                elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 1 ] ):
                    for test in SharePoints1D2DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, test[ 0 ] ]
            elif meshToName == "emptydataset":
                elementMap[ 0 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for test in SharePoints1D3DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, test[ 0 ] ]
            elif meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for test in SharePoints1D3DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 1 ][ id3DElem ] = [ 0, test[ 0 ] ]
                elementMap[ 3 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 1 ] ):
                    for test in SharePoints1D2DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 3 ][ id3DElem ] = [ 0, test[ 0 ] ]
        elif meshFromName == "fracture" or meshFromName == "polydata":
            if meshToName == "emptyFracture" or meshToName == "emptypolydata":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
            elif meshToName == "emptyWell":
                elementMap[ 0 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 2 ] ):
                    for test in SharePoints1D2DId:
                        if id3DElem == test[ 0 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, test[ 1 ] ]
            elif meshToName == "emptydataset":
                elementMap[ 0 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for test in ShareCells2D3DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, test[ 0 ] ]
            elif meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 0 ] ):
                    for test in ShareCells2D3DId:
                        if id3DElem == test[ 1 ]:
                            elementMap[ 1 ][ id3DElem ] = [ 0, test[ 0 ] ]
                elementMap[ 3 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "dataset":
            if meshToName == "emptydataset":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
            elif meshToName == "emptyWell":
                elementMap[ 0 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 2 ] ):
                    for test in SharePoints1D3DId:
                        if id3DElem == test[ 0 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 0, test[ 1 ] ]
            elif meshToName == "emptypolydata" or meshToName == "emptyFracture":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in ShareCells2D3DId[ :, 1 ] ] )
            elif meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
                elementMap[ 3 ] = np.array( [ [ 0, element ] for element in ShareCells2D3DId[ :, 1 ] ] )
        elif meshFromName == "multiblock":
            if meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 0 ] ) ] )
                elementMap[ 3 ] = np.array( [ [ 1, element ] for element in ShareCells2D3DId[ :, 1 ] ] )
            elif meshToName == "emptyWell":
                elementMap[ 0 ] = np.full( ( nbElements[ 2 ], 2 ), -1, np.int64 )
                for id3DElem in range( nbElements[ 2 ] ):
                    for test in SharePoints1D3DId:
                        if id3DElem == test[ 0 ]:
                            elementMap[ 0 ][ id3DElem ] = [ 1, test[ 1 ] ]
            elif meshToName == "emptyFracture" or meshToName == "emptypolydata":
                elementMap[ 0 ] = np.array( [ [ 1, element ] for element in ShareCells2D3DId[ :, 1 ] ] )
            elif meshToName == "emptydataset":
                elementMap[ 0 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 0 ] ) ] )

        return elementMap

    return _get_elementMap
