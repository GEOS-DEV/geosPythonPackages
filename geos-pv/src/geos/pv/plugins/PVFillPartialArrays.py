# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Any, Optional, Union
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smproperty,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet, )

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.pv.utils.details import SISOFilter, FilterCategory
from geos.processing.generic_processing_tools.FillPartialArrays import FillPartialArrays, loggerTitle

from geos.utils.Logger import addPluginLogSupport

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


@SISOFilter( category=FilterCategory.GEOS_UTILS,
             decoratedLabel="Fill Partial Arrays",
             decoratedType="vtkMultiBlockDataSet" )
@addPluginLogSupport( loggerTitle=loggerTitle )
class PVFillPartialArrays( VTKPythonAlgorithmBase ):

    def __init__( self: Self, ) -> None:
        """Fill a partial attribute with constant value per component."""
        self.clearDictAttributesValues: bool = True
        self.dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ] = {}
        #remove noisy loggers to get clean OutputMessage windows
        # self.logger = getLogger( loggerTitle )
        # for hdlr in list(filter(lambda x : not isinstance(x, GEOSHandler),  self.logger.handlers)):
        #         self.logger.removeHandler(hdlr)

    @smproperty.xml( """
        <StringVectorProperty
            name="AttributeTable"
            number_of_elements="2"
            command="setDictAttributesValues"
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
    def setDictAttributesValues( self: Self, attributeName: Optional[ str ], values: Optional[ str ] ) -> None:
        """Set the dictionary with the region indexes and its corresponding list of value for each components.

        Args:
            attributeName (Optional[str]): Name of the attribute to consider.
            values (Optional[str]): List of the filing values. If multiple components use a comma between the value of each component.
        """
        if self.clearDictAttributesValues:
            self.dictAttributesValues = {}
            self.clearDictAttributesValues = False

        if attributeName is not None:
            if values is not None:
                self.dictAttributesValues[ attributeName ] = list( values.split( "," ) )
            else:
                self.dictAttributesValues[ attributeName ] = None

        self.Modified()

    def ApplyFilter( self, inputMesh: vtkMultiBlockDataSet, outputMesh: vtkMultiBlockDataSet ) -> None:
        """Is applying FillPartialArrays to the mesh and return with the class's dictionary for attributes values.

        Args:
            inputMesh : A mesh to transform.
            outputMesh : A mesh transformed.

        """
        fillPartialArraysFilter: FillPartialArrays = FillPartialArrays(
            outputMesh,
            self.dictAttributesValues,
        )

        fillPartialArraysFilter.applyFilter()

        self.clearDictAttributesValues = True

        return
