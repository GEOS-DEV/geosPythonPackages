# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import numpy as np
from pathlib import Path
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smproperty, smproxy, smhint
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkDoubleArray,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkUnstructuredGrid,
    vtkFieldData,
    vtkMultiBlockDataSet,
)

__doc__ = """
This file defines multiple Paraview plugins with various configurations.

Examples of Source, Reader and Writer can be found on `Paraview documentation page <https://www.paraview.org/paraview-docs/nightly/python/paraview.util.vtkAlgorithm.html>`_.

Additional examples are here defined:

* PVPreserveInputTypeFilter is an example of a Paraview plugin where output is of same type as input data.

  .. Note::
    if input data is a composite data set, the RequestData method is applied to each part of input object.
    Results are concatenated to output object. Point data and cell data are added to each block,
    a new line per block is added to output Field data or output vtkTable.

* PVCompositeDataSetFilter is an example of a Paraview plugin that treats composite data sets as a single object conversely to PVPreserveInputTypeFilter.

* PVMultipleInputFilter is an example of a Paraview plugin using 2 inputs of different type.

  The output is here of same type as input 1.

  .. Note:: inputs are ordered in the reverse order compared to their definition using decorators.



"""


@smproxy.filter( name="PVPreserveInputTypeFilter", label="Preserve Input Type Filter" )
@smhint.xml("""<ShowInMenu category="Filter Examples"/>""")
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVPreserveInputTypeFilter( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )


    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        print("RequestDataObject")
        inData1 = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData is None or ( not outData.IsA( inData1.GetClassName() ) ):
            outData = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        print("RequestData")
        input: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outData: vtkPointSet = self.GetOutputData( outInfoVec, 0 )

        assert input is not None, "input 0 server mesh is null."
        assert outData is not None, "Output pipeline is null."

        # do something...
        # for instance copy input and create a Field data in output object

        outData.ShallowCopy(input)

        # add Field data attribute
        nbArrays: int = 3
        fieldData: vtkFieldData = outData.GetFieldData()
        fieldData.AllocateArrays(nbArrays)
        for i in range(nbArrays):
            newArray: vtkDoubleArray = vtkDoubleArray()
            newArray.SetName(f"Column{i}")
            newArray.SetNumberOfComponents(1)
            newArray.SetNumberOfTuples(1)
            val: float = i + np.random.rand(1)[0]
            newArray.SetValue(0, val)
            fieldData.AddArray(newArray)
        fieldData.Modified()

        # add Point attribute

        # add Cell attribute

        outData.Modified()
        return 1

@smproxy.filter( name="PVCompositeDataSetFilter", label="Composite Data Set Filter" )
@smhint.xml("""<ShowInMenu category="Filter Examples"/>""")
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
class PVCompositeDataSetFilter( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=2, nOutputPorts=1, outputType="vtkMultiBlockDataSet" )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData1 = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData is None or ( not outData.IsA( inData1.GetClassName() ) ):
            outData = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        input: vtkMultiBlockDataSet = self.GetInputData( inInfoVec, 0, 0 )
        outData: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )

        assert input is not None, "input 0 server mesh is null."
        assert outData is not None, "Output pipeline is null."

        # do something...
        # for instance copy input and create a Field data in output object

        outData.ShallowCopy(input)
        nbArrays: int = 3
        fieldData: vtkFieldData = outData.GetFieldData()
        fieldData.AllocateArrays(nbArrays)
        for i in range(nbArrays):
            newArray: vtkDoubleArray = vtkDoubleArray()
            newArray.SetName(f"Column{i}")
            newArray.SetNumberOfComponents(1)
            val: float = i + np.random.rand(1)[0]
            newArray.SetValue(val)
            fieldData.AddArray(newArray)

        fieldData.Modified()
        outData.Modified()
        return 1


@smproxy.filter( name="PVMultiInputFilter", label="Multiple Input Filter" )
@smhint.xml("""<ShowInMenu category="Filter Examples"/>""")
@smproperty.input( name="Input1", port_index=1, label="Input 1" )
@smdomain.datatype(
    dataTypes=[ "vtkPointSet", ],
    composite_data_supported=False,
)
@smproperty.input( name="Input0", port_index=0, label="Input 0" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=False,
)
class PVMultipleInputFilter( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=2, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        # here output data is of same type as input 1
        inData1 = self.GetInputData( inInfoVec, 1, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData is None or ( not outData.IsA( inData1.GetClassName() ) ):
            outData = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        input0: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        input1: vtkPointSet = self.GetInputData( inInfoVec, 1, 0 )
        outData: vtkPointSet = self.GetOutputData( outInfoVec, 0 )

        assert input0 is not None, "input 0 server mesh is null."
        assert input1 is not None, "input 1 client mesh is null."
        assert outData is not None, "Output pipeline is null."

        # do something...

        return 1

@smproxy.filter( name="PVMultiOutputFilter", label="Multiple Output Filter" )
@smhint.xml("""
                <ShowInMenu category="Filter Examples"/>
                <OutputPort index="0" name="Output0"/>
                <OutputPort index="1" name="Output1"/>
            """)
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=False,
)
class PVMultipleOutputFilter( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=2, outputType="vtkUnstructuredGrid" )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        # here output data is of same type as input 1
        inData1 = self.GetInputData( inInfoVec, 1, 0 )
        outData0 = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData0 is None or ( not outData0.IsA( inData1.GetClassName() ) ):
            outData0 = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData0.DATA_OBJECT(), outData0 )
        outData1 = self.GetOutputData( outInfoVec, 1 )
        if outData1 is None or ( not outData1.IsA( inData1.GetClassName() ) ):
            outData1 = inData1.NewInstance()
            outInfoVec.GetInformationObject( 1 ).Set( outData1.DATA_OBJECT(), outData1)
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        input: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outData0: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 0 )
        outData1: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 1 )

        assert input is not None, "input 0 server mesh is null."
        assert outData0 is not None, "Output pipeline 0 is null."
        assert outData1 is not None, "Output pipeline 1 is null."

        # do something...

        return 1
