# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

from dataclasses import dataclass

import numpy as np
from xsdata.formats.converter import Converter, converter


@dataclass
class integer:
    value: np.int32


class integerConverter( Converter ):

    def deserialize( self, value: str, **kwargs ) -> integer:
        return integer( value )

    def serialize( self, value: integer, **kwargs ) -> str:
        if kwargs[ "format" ]:
            return kwargs[ "format" ].format( value )
        return str( value )


converter.register_converter( integer, integerConverter() )


@dataclass
class real32:
    value: np.float32


class real32Converter( Converter ):

    def deserialize( self, value: str, **kwargs ) -> real32:
        return real32( value )

    def serialize( self, value: real32, **kwargs ) -> str:
        if kwargs[ "format" ]:
            return kwargs[ "format" ].format( value )
        return str( value )


converter.register_converter( real32, real32Converter() )


@dataclass
class real64:
    value: np.float64


class real64Converter( Converter ):

    def deserialize( self, value: str, **kwargs ) -> real64:
        print( "deserialize" )
        return real64( value=np.float64( value ) )

    def serialize( self, value: real64, **kwargs ) -> str:
        if kwargs[ "format" ]:
            return kwargs[ "format" ].format( value )
        return str( value )


converter.register_converter( real64, real64Converter() )


@dataclass
class globalIndex:
    value: np.int64


class globalIndexConverter( Converter ):

    def deserialize( self, value: str, **kwargs ) -> globalIndex:
        return globalIndex( value )

    def serialize( self, value: globalIndex, **kwargs ) -> str:
        if kwargs[ "format" ]:
            return kwargs[ "format" ].format( value )
        return str( value )


converter.register_converter( globalIndex, globalIndexConverter() )


def custom_class_factory( clazz, params ):
    if clazz is real64:
        return clazz( **{ k: v for k, v in params.items() } )

    return clazz( **params )


# @dataclass
# class globalIndex_array:
#     value: np.ndarray[np.int64]

# class globalIndex_arrayConverter(Converter):
#     def deserialize(self, value: str, **kwargs) -> globalIndex_array:
#        return globalIndex_array(value)

#     def serialize(self, value: globalIndex_array, **kwargs) -> str:
#         if kwargs["format"]:
#             return kwargs["format"].format(value)
#         return str(value)
