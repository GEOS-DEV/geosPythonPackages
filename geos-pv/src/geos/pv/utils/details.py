# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville, Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="misc"
import sys
from pathlib import Path
# Add Enum for filter categories
from functools import update_wrapper
from typing import Protocol, Any, Type, TypeVar, Callable, runtime_checkable, Union
from abc import abstractmethod
from enum import Enum

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataObject,
)

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
Set of decorators that allows quicker generation of DataSet derived to the same DataSet derived filters. If it a list of type is provided, then the unique output type is set to vtkDataObject.

Usage is:

    from geos.pv.utils.details import SISOFilter, FilterCategory

    @SISO(category=FilterCategory.GEOS_UTILS,decoratedLabel='Awesome Filter',decoratedType='vtkMultiBlockDataSet')
    class PVMyFilter:
        ...

"""


# Enum for filter categories
class FilterCategory( str, Enum ):
    """String Enum to sort into category in PV task bar under Plugins."""
    GEOS_PROP = '0- Geos Pre-processing'
    GEOS_MESH = '1- Geos Mesh'
    GEOS_GEOMECHANICS = '2- Geos Geomechanics'
    GEOS_PV = '3- Geos PV'
    GEOS_UTILS = '4- Geos Utils'
    GEOS_QC = '5- Geos QC'
    # Add more as needed


U = TypeVar( 'U', bound='vtkDataObject' )

@runtime_checkable
class IsSISOFilter( Protocol[ U ] ):
    """Protocol to ensure that the wrapped filter defines the correct Filter core function."""

    @abstractmethod
    def ApplyFilter(
        self,
        inputMesh: U,
        outputMesh: U,
    ) -> None:
        """Define filter here.

        Args:
            inputMesh : A mesh to transform
            outputMesh : A mesh transformed

        """
        raise NotImplementedError


T = TypeVar( 'T', bound='IsSISOFilter' )


def SISOFilter( category: FilterCategory, decoratedLabel: str,
                decoratedType: Union[ str, list ] ) -> Callable[ [ Type[ T ] ], Type[ T ] ]:
    """Decorate Single Input Single Output (SISO) filter."""

    def decoratedClass( cls: Type[ T ] ) -> Type[ T ]:
        """Outer wrapper function. All is in the WrappingClass below."""
        originalInit = cls.__init__

        class WrappingClass( cls ):  # type: ignore[valid-type]

            def __init__( self, *ar: Any, **kw: Any ) -> None:
                """Pre-init the filter with the Base algo and I/O single type (usually vtkMultiBlockDataSet).

                Args:
                    ar : Fowarded arguments
                    kw : Forwarded keywords args
                """
                VTKPythonAlgorithmBase.__init__(
                    self,
                    nInputPorts=1,
                    nOutputPorts=1,
                    inputType=decoratedType if isinstance( decoratedType, str ) else "vtkDataObject",
                    outputType=decoratedType if isinstance( decoratedType, str ) else "vtkDataObject" )

                #If wrapped class has more to init there it is applied
                #avoid the overwritten init by decorator taking place of the cls
                if originalInit is not object.__init__:
                    originalInit( self, *ar, **kw )

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

                cls.ApplyFilter( self, inputMesh, outputMesh )
                return 1

        # Copy all methods and attributes from cls, including decorator metadata
        for attrName in dir( cls ):
            if attrName.startswith( '_' ):
                continue  # Skip private/magic methods (already handled or inherited)

            attr = getattr( cls, attrName )
            # Copy methods with their decorators
            if callable( attr ) and attrName not in WrappingClass.__dict__:
                setattr( WrappingClass, attrName, attr )

        # Copy metadata
        WrappingClass.__name__ = cls.__name__
        WrappingClass.__qualname__ = cls.__qualname__
        WrappingClass.__module__ = cls.__module__
        WrappingClass.__doc__ = cls.__doc__
        update_wrapper( WrappingClass, cls, updated=[] )

        #decorate it old fashion way
        WrappingClass = smdomain.datatype(
            dataTypes=[ decoratedType ] if isinstance( decoratedType, str ) else decoratedType,
            composite_data_supported=True,
        )( WrappingClass )
        WrappingClass = smproperty.input( name="Input", port_index=0 )( WrappingClass )
        # Use enum value for category
        WrappingClass = smhint.xml( f'<ShowInMenu category="{category.value}"/>' )( WrappingClass )
        WrappingClass = smproxy.filter( name=getattr( cls, '__name__', str( cls ) ),
                                        label=decoratedLabel )( WrappingClass )
        return WrappingClass

    return decoratedClass
