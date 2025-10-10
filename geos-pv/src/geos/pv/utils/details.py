# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from functools import update_wrapper
from typing import Protocol
from abc import abstractmethod
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


# def SISOFilter(decorated_name, decorated_label, decorated_type):
#     """
#         Decorate single input single output filter
#     """
#     def decorated_class(cls):

#         # @dataclass
#         # class WrappingClass(cls):
#         @smproxy.filter( name=decorated_name, label=decorated_label )
#         @smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
#         @smproperty.input( name="Input", port_index=0 )
#         @smdomain.datatype(
#             dataTypes=[ decorated_type ],
#             composite_data_supported=True,
#             )
#         class WrappingClass(cls,VTKPythonAlgorithmBase):

#             def __init__(self,*ar,**kw):
#                 VTKPythonAlgorithmBase.__init__(self, nInputPorts=1,
#                             nOutputPorts=1,
#                             inputType=decorated_type,
#                             outputType=decorated_type )
#                 cls.__init__(self,*ar,**kw)

#        # IMPORTANT: Set the wrapper's name to match the original class
#         WrappingClass.__name__ = cls.__name__
#         WrappingClass.__qualname__ = cls.__qualname__
#         WrappingClass.__module__ = cls.__module__
#         update_wrapper(WrappingClass, cls, updated=[])
#         # # Copy metada        
#         # import sys
#         # original_module = sys.modules.get(cls.__module__)
#         # print(f"Registering {cls.__name__} in module {cls.__module__}")
#         # print(f"Module found: {original_module is not None}")

#         # if original_module is not None:
#         #     setattr(original_module, cls.__name__, WrappingClass)
#         #     # Verify registration
#         #     print(f"Successfully registered: {hasattr(original_module, cls.__name__)}")

#         return WrappingClass

#     return decorated_class

# def IsSISOFilter(Protocol):    

#     @abstractmethod
#     def RequestData(
#         self,
#         request: vtkInformation,  # noqa: F841
#         inInfoVec: list[ vtkInformationVector ],
#         outInfoVec: vtkInformationVector,
#     ) -> int:
#         raise NotImplementedError


def SISOFilter(category, decorated_label, decorated_type):
    """
    Decorate single input single output filter
    """
    print(f"Is using decorator")

    def decorated_class(cls):
        original_init = cls.__init__
        # Créer une fonction __init__ personnalisée
        def new_init(self, *ar, **kw):
            VTKPythonAlgorithmBase.__init__(
                self, 
                nInputPorts=1,
                nOutputPorts=1,
                inputType=decorated_type,
                outputType=decorated_type
            )

            if original_init is not object.__init__:
                original_init(self, *ar, **kw)

        def RequestDataObject(
            self,
            request: vtkInformation,
            inInfoVec: list[ vtkInformationVector ],
            outInfoVec: vtkInformationVector, ) -> int:
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
            return VTKPythonAlgorithmBase.RequestDataObject(self, request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]
        
        # to be inserted in the class
        class_dict = {
                '__init__': new_init,
                '__module__': cls.__module__,
                '__qualname__': cls.__qualname__,
                'RequestDataObject' : RequestDataObject,
                # 'RequestData': cls.RequestData,
            }

        # if hasattr(cls,'RequestData'):
            # class_dict['RequestData'] = cls.RequestData

        # dynamically creates a class
        WrappingClass = type(
            cls.__name__,  # Nom de la classe
            (cls,VTKPythonAlgorithmBase),  # Bases
            class_dict
        )
        
        # Copy metadata
        update_wrapper(WrappingClass, cls, updated=[])

        #decorate it old fashion way
        WrappingClass = smdomain. datatype(dataTypes=[ decorated_type ],
                                            composite_data_supported=True,
                                              )(WrappingClass)
        WrappingClass = smproperty.input( name="Input", port_index=0 )(WrappingClass)
        WrappingClass = smhint.xml( category )(WrappingClass)
        WrappingClass = smproxy.filter( name=cls.__name__, 
                                       label=decorated_label)(WrappingClass)
        
        return WrappingClass
    return decorated_class