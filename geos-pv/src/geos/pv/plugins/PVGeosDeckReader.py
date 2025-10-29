# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
from paraview.util.vtkAlgorithm import smdomain, smhint, smproperty, smproxy  # type: ignore[import-untyped]
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkPartitionedDataSetCollection

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

__doc__ = """
`PVGeosDeckReader` is a Python-based Paraview reader that allows users to open GEOS XML files
and create mesh objects for visualization and analysis.
- The plugin is registered as `PythonGeosDeckReader` in Paraview.
- It outputs a `vtkPartitionedDataSetCollection` representing the mesh and associated regions as defined in the XML file.

Key Features

- Direct XML loading: Open GEOS XML input files (`.xml`) in Paraview as native datasets.
- Region support: The reader uses the `Region` attribute (or a user-specified attribute) to organize mesh data.
- Integration with GEOS workflows: Enables direct inspection and analysis of simulation input decks without conversion steps.

How to Use

1. Install the geos-pv package and ensure Paraview is set up to use Python plugins.
2. In Paraview, load the plugin (typically via the Python Plugin Manager or by specifying the path to `PVGeosDeckReader.py`).
3. Use the "Open" dialog in Paraview to select a GEOS XML file. Choose the `PythonGeosDeckReader` when prompted.
4. The mesh and regions defined in the XML will be loaded as a multi-block dataset for visualization and further processing.

Technical Details

- The plugin is implemented as a subclass of `VTKPythonAlgorithmBase` and uses the `create_vtk_deck` function from geos-xml-tools to build the VTK data structure.
- The plugin exposes a `FileName` property for selecting the XML file and can be extended to support additional attributes or options.

Example
    # Load the plugin in Paraview

    paraview --python-script=path/to/PVGeosDeckReader.py
    # Or load via the Paraview GUI
    Tools>Manage Plugins...>Load new>path/to/PVGeosDeckReader.py

    # In Paraview:
    # File > Open > select input.xml > choose PythonGeosDeckReader

Note: This plugin is intended for users who want to inspect or debug GEOS input decks visually,
or to prepare data for further Paraview-based workflows.
"""

paraview_plugin_version = "0.1.0"


@smproxy.reader(
    name="PythonGeosDeckReader",
    label="Python-based Deck Reader for GEOS",
    extensions="xml",
    file_description="XML files",
)
class PVGeosDeckReader( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Constructor of the reader."""
        super().__init__(
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSetCollection",
        )  # type: ignore
        self.__filename: str = ""
        self.__attributeName: str = "Region"
        from geos.xml_tools.vtk_builder import create_vtk_deck

        self.__create_vtk_deck = create_vtk_deck

    @smproperty.stringvector( name="FileName" )  # type: ignore
    @smdomain.filelist()  # type: ignore
    @smhint.filechooser( extensions="xml", file_description="GEOS XML files" )  # type: ignore
    def SetFileName( self: Self, name: str ) -> None:
        """Specify filename for the file to read.

        Args:
            name (str): filename
        """
        if self.__filename != name:
            self.__filename = name
            self.Modified()

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """RequestData function of the vtk pipeline.

        Args:
            request (vtkInformation): information about the request
            inInfoVec (list[vtkInformationVector]): input information vector
            outInfoVec (vtkInformationVector): output information vector

        Raises:
            RuntimeError: Raises an error if no filename is specified

        Returns:
            int: Returns 1 if the pipeline is successful
        """
        if not self.__filename:
            raise RuntimeError( "No filename specified" )

        output = vtkPartitionedDataSetCollection.GetData( outInfoVec, 0 )
        vtk_collection = self.__create_vtk_deck( self.__filename, self.__attributeName )
        output.ShallowCopy( vtk_collection )
        return 1
