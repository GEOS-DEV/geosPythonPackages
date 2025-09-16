# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union, Any
from typing_extensions import Self

# from functools import wraps
# from dataclasses import dataclass

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

__doc__ = """
Set of decorators that allow:
    - quicker generation of MultiBlockDataSet to MultiBlockDataSet filters
    - more stable logger strategy

Usage is:

    @SISO(name='MyFilter',label='This is my filter',dtype='vtkMultiBlockDataSet')
    class PVMyFilter:
        ...
        def __hidden_layer(self):
            

"""

def SISOFilter(decorated_name, decorated_label, decorated_type):
    """
        Decorate single input single output filter
    """
    def decorated_class(cls):
        @smproxy.filter( name=decorated_name, label=decorated_label )
        @smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
        @smproperty.input( name="Input", port_index=0 )
        @smdomain.datatype(
            dataTypes=[ decorated_type ],
            composite_data_supported=True,
            )
        # @dataclass
        # class WrappingClass(cls):
        class WrappingClass(cls,VTKPythonAlgorithmBase):

            def __init__(self,*ar,**kw):
                VTKPythonAlgorithmBase.__init__(self, nInputPorts=1,
                            nOutputPorts=1,
                            inputType=decorated_type,
                            outputType=decorated_type )
                cls.___init__(self,*ar,**kw)
        WrappingClass.__name__ = cls.__name__
        WrappingClass.__module__ = cls.__module__
                
        return WrappingClass
    return decorated_class



