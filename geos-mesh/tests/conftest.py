# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union, Any, Tuple, Dict
import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLGenericDataObjectReader, vtkXMLMultiBlockDataReader


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
        elementMap: Dict[ int, npt.NDArray[ np.int64 ] ] = {}
        nbElements: Tuple[ int, int ] = ( 4092, 212 ) if points else ( 1740, 156 )
        if meshFromName == "multiblock":
            if meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 0 ] ) ] )
                elementMap[ 3 ] = np.array( [ [ 3, element ] for element in range( nbElements[ 1 ] ) ] )
            elif meshToName == "emptyFracture":
                elementMap[ 0 ] = np.array( [ [ 3, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "dataset":
            if meshToName == "emptydataset":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
            elif meshToName == "emptyFracture":
                elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
            elif meshToName == "emptypolydata":
                elementMap[ 0 ] = np.array( [ [ 0, 0 ], [ 0, 1 ], [ 0, 2 ], [ 0, 3 ], [ 0, 4 ], [ 0, 5 ], [ 0, 6 ],
                                              [ 0, 7 ], [ 0, 8 ], [ 0, 9 ], [ 0, 10 ], [ 0, 11 ], [ 0, 12 ], [ 0, 13 ],
                                              [ 0, 14 ], [ 0, 15 ], [ 0, 16 ], [ 0, 17 ], [ 0, 18 ], [ 0,
                                                                                                       19 ], [ 0, 20 ],
                                              [ 0, 21 ], [ 0, 22 ], [ 0, 23 ], [ 0, 48 ], [ 0, 50 ], [ 0,
                                                                                                       51 ], [ 0, 54 ],
                                              [ 0, 56 ], [ 0, 57 ], [ 0, 58 ], [ 0, 59 ], [ 0, 60 ], [ 0,
                                                                                                       61 ], [ 0, 62 ],
                                              [ 0, 63 ], [ 0, 64 ], [ 0, 65 ], [ 0, 66 ], [ 0, 67 ], [ 0,
                                                                                                       68 ], [ 0, 69 ],
                                              [ 0, 70 ], [ 0, 71 ], [ 0, 72 ], [ 0, 73 ], [ 0, 74 ],
                                              [ 0, 75 ], [ 0, 76 ], [ 0, 77 ], [ 0, 78 ], [ 0, 79 ], [ 0, 580 ],
                                              [ 0, 581 ], [ 0, 582 ], [ 0, 583 ], [ 0, 584 ], [ 0, 585 ], [ 0, 586 ],
                                              [ 0, 587 ], [ 0, 588 ], [ 0, 589 ], [ 0, 590 ], [ 0, 591 ], [ 0, 592 ],
                                              [ 0, 593 ], [ 0, 594 ], [ 0, 595 ], [ 0, 596 ], [ 0, 597 ], [ 0, 598 ],
                                              [ 0, 599 ], [ 0, 600 ], [ 0, 601 ], [ 0, 602 ], [ 0, 603 ], [ 0, 628 ],
                                              [ 0, 630 ], [ 0, 631 ], [ 0, 634 ], [ 0, 636 ], [ 0, 637 ], [ 0, 638 ],
                                              [ 0, 639 ], [ 0, 640 ], [ 0, 641 ], [ 0, 642 ], [ 0, 643 ], [ 0, 644 ],
                                              [ 0, 645 ], [ 0, 646 ], [ 0, 647 ], [ 0, 648 ], [ 0, 649 ], [ 0, 650 ],
                                              [ 0, 651 ], [ 0, 652 ], [ 0, 653 ], [ 0, 654 ], [ 0, 655 ], [ 0, 656 ],
                                              [ 0, 657 ], [ 0, 658 ], [ 0, 659 ], [ 0, 1160 ], [ 0, 1161 ], [ 0, 1162 ],
                                              [ 0, 1163 ], [ 0, 1164 ], [ 0, 1165 ], [ 0, 1166 ], [ 0, 1167 ],
                                              [ 0, 1168 ], [ 0, 1169 ], [ 0, 1170 ], [ 0, 1171 ], [ 0, 1172 ],
                                              [ 0, 1173 ], [ 0, 1174 ], [ 0, 1175 ], [ 0, 1176 ], [ 0, 1177 ],
                                              [ 0, 1178 ], [ 0, 1179 ], [ 0, 1180 ], [ 0, 1181 ], [ 0, 1182 ],
                                              [ 0, 1183 ], [ 0, 1208 ], [ 0, 1210 ], [ 0, 1211 ], [ 0, 1214 ],
                                              [ 0, 1216 ], [ 0, 1217 ], [ 0, 1218 ], [ 0, 1219 ], [ 0, 1220 ],
                                              [ 0, 1221 ], [ 0, 1222 ], [ 0, 1223 ], [ 0, 1224 ], [ 0, 1225 ],
                                              [ 0, 1226 ], [ 0, 1227 ], [ 0, 1228 ], [ 0, 1229 ], [ 0, 1230 ],
                                              [ 0, 1231 ], [ 0, 1232 ], [ 0, 1233 ], [ 0, 1234 ], [ 0, 1235 ],
                                              [ 0, 1236 ], [ 0, 1237 ], [ 0, 1238 ], [ 0, 1239 ] ] )
            elif meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 0 ] ) ] )
                elementMap[ 3 ] = np.full( ( nbElements[ 1 ], 2 ), -1, np.int64 )
        elif meshFromName == "fracture":
            if meshToName == "emptyFracture":
                elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
            elif meshToName == "emptymultiblock":
                elementMap[ 1 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
                elementMap[ 3 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "polydata" and meshToName == "emptypolydata":
            elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )

        return elementMap

    return _get_elementMap
