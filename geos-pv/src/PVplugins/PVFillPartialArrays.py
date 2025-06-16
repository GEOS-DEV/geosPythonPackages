# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self


from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smhint, smproperty, smproxy,
)

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.FillPartialArrays import FillPartialArrays
from geos.pv.utils.AbstractPVPluginVtkWrapper import AbstractPVPluginVtkWrapper

__doc__ = """
Fill partial arrays of input mesh.

Input and output are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVFillPartialArrays.
* Select the input mesh.
* Select the partial arrays to fill.
* Apply.

"""


@smproxy.filter( name="PVFillPartialArrays", label="Fill Partial Arrays" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
class PVFillPartialArrays( AbstractPVPluginVtkWrapper ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__()

        self._clearSelectedAttributeMulti: bool = True
        self._selectedAttributeMulti: list[ str ] = []

    @smproperty.stringvector(
        name="SelectMultipleAttribute",
        label="Select Multiple Attribute",
        repeat_command=1,
        number_of_elements_per_command="1",
        element_types="2",
        default_values="",
        panel_visibility="default",
    )
    @smdomain.xml( """
                <ArrayListDomain
                    name="array_list"
                    attribute_type="Vectors"
                    input_domain_name="cells_vector_array">
                    <RequiredProperties>
                        <Property name="Input" function="Input"/>
                    </RequiredProperties>
                </ArrayListDomain>
                <Documentation>
                    Select a unique attribute from all the scalars cell attributes from input object.
                    Input object is defined by its name Input that must corresponds to the name in @smproperty.input
                    Attribute support is defined by input_domain_name: inputs_array (all arrays) or user defined
                    function from <InputArrayDomain/> tag from filter @smdomain.xml.
                    Attribute type is defined by keyword `attribute_type`: Scalars or Vectors
                </Documentation>
                  """ )
    
    def a02SelectMultipleAttribute( self: Self, name: str ) -> None:
        """Set selected attribute name.

        Args:
            name (str): Input value
        """
        if self._clearSelectedAttributeMulti:
            self._selectedAttributeMulti.clear()
        self._clearSelectedAttributeMulti = False
        self._selectedAttributeMulti.append( name )
        self.Modified()

    def applyVtkFilter(
        self: Self,
        input: vtkMultiBlockDataSet,
    ) -> vtkMultiBlockDataSet:
        """Apply vtk filter.

        Args:
            input (vtkMultiBlockDataSet): input mesh

        Returns:
            vtkMultiBlockDataSet: output mesh
        """
        filter: FillPartialArrays = FillPartialArrays()
        filter.SetInputDataObject( input )
        filter.Update()
        return filter.GetOutputDataObject( 0 )
