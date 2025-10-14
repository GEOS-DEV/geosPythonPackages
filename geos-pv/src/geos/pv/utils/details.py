# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="misc"
import sys
from pathlib import Path
# Add Enum for filter categories
from functools import update_wrapper
from typing import Protocol, Any, Type, TypeVar, Callable, runtime_checkable
from abc import abstractmethod
from enum import Enum


# Enum for filter categories
class FilterCategory( str, Enum ):
    GEOS_UTILS = '4- Geos Utils'
    GEOS_MESH = '1- Geos Mesh'
    GEOS_GEOMECHANICS = '2- Geos Geomechanics'
    GEOS_PV = '3- Geos PV'
    GEOS_QC = '5- Geos QC'
    # Add more as needed


# from functools import wraps
# from dataclasses import dataclass

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py

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
Set of decorators that allows quicker generation of MultiBlockDataSet to MultiBlockDataSet filters

Usage is:

    @SISO(name='MyFilter',label='This is my filter',dtype='vtkMultiBlockDataSet')
    class PVMyFilter:
        ...

"""

U = TypeVar('U')
@runtime_checkable
class IsSISOFilter( Protocol[U] ):
    """Protocol to ensure that the wrapped filter defines the correct Filter core function."""

    @abstractmethod
    def Filter(
        self,
        inputMesh: U, 
        outputMesh: U,
    ) -> None:
        """Define filter here.

        Args:
            inputMesh : a mesh to transform
            outputMesh : a mesh transformed

        """
        raise NotImplementedError


T = TypeVar( 'T', bound='IsSISOFilter' )


def SISOFilter( category: FilterCategory, decorated_label: str,
                decorated_type: str ) -> Callable[ [ Type[ T ] ], Type[ T ] ]:
    """Decorate single input single output filter."""

    def decorated_class( cls: Type[ T ] ) -> Type[ T ]:
        """Outer wrapper function. All is in the WrappingClass below."""
        original_init = cls.__init__

        class WrappingClass( cls, VTKPythonAlgorithmBase ):  # type: ignore[valid-type]

            def __init__( self, *ar: Any, **kw: Any ) -> None:
                """Pre-init the filter with the Base algo and I/O single type (usually vtkMultiBlockDataSet).

                Args:
                    ar : fowarded arguments
                    kw : forwarded keywords args
                """
                VTKPythonAlgorithmBase.__init__( self,
                                                 nInputPorts=1,
                                                 nOutputPorts=1,
                                                 inputType=decorated_type,
                                                 outputType=decorated_type )

                #If wrapped class has more to init there it is applied
                #avoid the overwritten init by decorator taking place of the cls
                if original_init is not object.__init__:
                    original_init( self, *ar, **kw )

            def RequestDataObject(
                self,
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
                return VTKPythonAlgorithmBase.RequestDataObject( self, request, inInfoVec,
                                                                 outInfoVec )  # type: ignore[no-any-return]

            def RequestData(
                self,
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

                cls.Filter( self, inputMesh, outputMesh )
                return 1

        # Copy metadata
        WrappingClass.__name__ = cls.__name__
        WrappingClass.__qualname__ = cls.__qualname__
        WrappingClass.__module__ = cls.__module__
        WrappingClass.__doc__ = cls.__doc__
        update_wrapper( WrappingClass, cls, updated=[] )

        #decorate it old fashion way
        WrappingClass = smdomain.datatype(
            dataTypes=[ decorated_type ],
            composite_data_supported=True,
        )( WrappingClass )
        WrappingClass = smproperty.input( name="Input", port_index=0 )( WrappingClass )
        # Use enum value for category
        WrappingClass = smhint.xml( f'<ShowInMenu category="{category}"/>' )( WrappingClass )
        WrappingClass = smproxy.filter( name=getattr( cls, '__name__', str( cls ) ),
                                        label=decorated_label )( WrappingClass )
        return WrappingClass

    return decorated_class
