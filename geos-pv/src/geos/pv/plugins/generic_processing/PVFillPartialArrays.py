# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
from pathlib import Path
from typing import Any, Optional, Union
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.Logger import isHandlerInLogger
from geos.pv.utils.details import ( SISOFilter, FilterCategory )
from geos.processing.generic_processing_tools.FillPartialArrays import FillPartialArrays

__doc__ = f"""
Fill partial arrays of input mesh.

Input and output are vtkMultiBlockDataSet.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/generic_processing/PVFillPartialArrays
* Select the input mesh to process
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } > Fill Partial Arrays
* Set the partial attribute to fill and its filling values
* Apply

"""


@SISOFilter( category=FilterCategory.GENERIC_PROCESSING,
             decoratedLabel="Fill Partial Arrays",
             decoratedType="vtkMultiBlockDataSet" )
class PVFillPartialArrays( VTKPythonAlgorithmBase ):

    def __init__( self: Self, ) -> None:
        """Fill a partial attribute with constant value per component."""
        self.clearDictAttributesValues: bool = True
        self.dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ] = {}
        self.handler: logging.Handler = VTKHandler()

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
            speHandler=True,
        )

        if not isHandlerInLogger( self.handler, fillPartialArraysFilter.logger ):
            fillPartialArraysFilter.setLoggerHandler( self.handler )

        try:
            fillPartialArraysFilter.applyFilter()
        except ( ValueError, AttributeError ) as e:
            fillPartialArraysFilter.logger.error(
                f"The filter { fillPartialArraysFilter.logger.name } failed due to:\n{ e }" )
        except Exception as e:
            mess: str = f"The filter { fillPartialArraysFilter.logger.name } failed due to:\n{ e }"
            fillPartialArraysFilter.logger.critical( mess, exc_info=True )

        self.clearDictAttributesValues = True

        return
