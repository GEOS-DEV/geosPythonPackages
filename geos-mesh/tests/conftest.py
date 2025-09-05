# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union, Any
import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader, vtkXMLMultiBlockDataReader


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
        reader: Union[ vtkXMLMultiBlockDataReader, vtkXMLUnstructuredGridReader ]
        if datasetType == "multiblock":
            reader = vtkXMLMultiBlockDataReader()
            vtkFilename = "data/displacedFault.vtm"
        elif datasetType == "emptymultiblock":
            reader = vtkXMLMultiBlockDataReader()
            vtkFilename = "data/displacedFaultempty.vtm"
        elif datasetType == "fracture":
            reader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/fracture_res5_id.vtu"
        elif datasetType == "emptyFracture":
            reader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/fracture_res5_id_empty.vtu"
        elif datasetType == "dataset":
            reader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/domain_res5_id.vtu"
        elif datasetType == "emptydataset":
            reader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/domain_res5_id_empty.vtu"
        elif datasetType == "polydata":
            reader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/triangulatedSurface.vtu"
        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset


@pytest.fixture
def getElementMap() -> Any:
    """Get the element indexes mapping dictionary using the function _get_elementMap() between two meshes.

    Returns:
        elementMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary.
    """

    def _get_elementMap( meshFromName: str, meshToName: str, points: bool ) -> dict[ int, npt.NDArray[ np.int64 ] ]:
        """Get the element indexes mapping dictionary between two meshes

        Args:
            meshFromName (str): The name of the meshFrom.
            meshToName (str): The name of the meshTo.
            points (bool): True if elements to map is points, False if it is cells.

        Returns:
            elementMap (dict[int, npt.NDArray[np.int64]]): The element mapping dictionary.
        """
        elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = {}
        nbElements: tuple[ int, int ] = ( 4092, 212 ) if points else ( 1740, 156 )
        if meshFromName == "multiblock" and meshToName == "emptymultiblock":
            elementMap[ 1 ] = np.array( [ [ 1, element ] for element in range( nbElements[ 0 ] ) ] )
            elementMap[ 2 ] = np.array( [ [ 2, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "multiblock" and meshToName == "emptyFracture":
            elementMap[ 0 ] = np.array( [ [ 2, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "dataset" and meshToName == "emptyFracture":
            elementMap[ 0 ] = np.full( ( nbElements[ 1 ], 2), -1, np.int64 )
        elif meshFromName == "fracture" and meshToName == "emptyFracture":
            elementMap[ 0 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )
        elif meshFromName == "fracture" and meshToName == "emptymultiblock":
            elementMap[ 1 ] = np.full( ( nbElements[ 0 ], 2 ), -1, np.int64 )
            elementMap[ 2 ] = np.array( [ [ 0, element ] for element in range( nbElements[ 1 ] ) ] )

        return elementMap

    return _get_elementMap
