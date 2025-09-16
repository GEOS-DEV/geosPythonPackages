# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union, Any
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet, )

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.FillPartialArrays import FillPartialArrays
import geos.pv.utils.details
__doc__ = """
Fill partial arrays of input mesh.

Input and output are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVFillPartialArrays.
* Select the input mesh.
* Select the partial arrays to fill.
* Set the filling value (defaults to nan).
* Apply.

"""


# @smproxy.filter( name="PVFillPartialArrays", label="Fill Partial Arrays" )
# @smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
# @smproperty.input( name="Input", port_index=0 )
# @smdomain.datatype(
#     dataTypes=[ "vtkMultiBlockDataSet" ],
#     composite_data_supported=True,
# )
@geos.pv.utils.details.SISOFilter(decorated_name="PVFillPartialArrays", decorated_label="Fill Partial Arrays",decorated_type="vtkMultiBlockDataSet")
class PVFillPartialArrays:

    def __init__( self: Self, ) -> None:
        """Fill a partial attribute with constant value per component."""
        # super().__init__( nInputPorts=1,
        #                   nOutputPorts=1,
        #                   inputType="vtkMultiBlockDataSet",
        #                   outputType="vtkMultiBlockDataSet" )

        self.clearDictAttributesValues: bool = True
        self.dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ] = {}


    @smproperty.xml("""
        <StringVectorProperty
            name="AttributeTable"
            number_of_elements="2"
            command="_setDictAttributesValues"
            repeat_command="1"
            number_of_elements_per_command="2">
            <Documentation>
                Set the filling values for each partial attribute, use a coma between the value of each components:\n
                    attributeName | fillingValueComponent1 fillingValueComponent2 ...\n
                To fill the attribute with the default value, live a blanc. The default value is:\n
                    0 for uint type, -1 for int type and nan for float type.
            </Documentation>     
            <Hints>
                <AllowRestoreDefaults />
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Attribute name"/>
                    <ComponentLabel component="1" label="Filling values"/>
                </ShowComponentLabels>
            </Hints>
        </StringVectorProperty>
    """ )
    def _setDictAttributesValues( self: Self, attributeName: str, values: str ) -> None:
        """Set the dictionary with the region indexes and its corresponding list of value for each components.

        Args:
            attributeName (str): Name of the attribute to consider.
            values (str): List of the filing values. If multiple components use a comma between the value of each component.
        """
        if self.clearDictAttributesValues:
            self.dictAttributesValues = {}
            self.clearDictAttributesValues = False

        if attributeName is not None:
            if values is not None :
                self.dictAttributesValues[ attributeName ] = list( values.split( "," ) )
            else:
                self.dictAttributesValues[ attributeName ] = None

        self.Modified()

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
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
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: vtkMultiBlockDataSet = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        outputMesh.ShallowCopy( inputMesh )

        filter: FillPartialArrays = FillPartialArrays( outputMesh,
                                                       self.dictAttributesValues,
                                                       True,
        )

        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        filter.applyFilter()

        self.clearDictAttributesValues = True

        return 1
