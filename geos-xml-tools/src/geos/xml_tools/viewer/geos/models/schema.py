# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

from dataclasses import dataclass, field
from typing import Optional

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
    value: np.float64 = field( metadata={ "decoder": np.float64 } )


class real64Converter( Converter ):

    def deserialize( self, value: str, **kwargs ) -> real64:
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


@dataclass
class AquiferType:
    allow_all_phases_into_aquifer: str = field(
        default="0",
        metadata={
            "name": "allowAllPhasesIntoAquifer",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    aquifer_angle: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferAngle",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_elevation: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_initial_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferInitialPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_inner_radius: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferInnerRadius",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_permeability: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferPermeability",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_porosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferPorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_thickness: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferThickness",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_total_compressibility: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferTotalCompressibility",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_water_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferWaterDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    aquifer_water_phase_component_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "aquiferWaterPhaseComponentFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    aquifer_water_phase_component_names: str = field(
        default="{}",
        metadata={
            "name": "aquiferWaterPhaseComponentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    aquifer_water_viscosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "aquiferWaterViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_condition: str = field(
        default="0",
        metadata={
            "name": "initialCondition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    pressure_influence_function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "pressureInfluenceFunctionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BiotPorosityType:
    default_porosity_tec: str = field(
        default="0",
        metadata={
            "name": "defaultPorosityTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_reference_porosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    grain_bulk_modulus: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "grainBulkModulus",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BlackOilFluidType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    hydrocarbon_formation_vol_factor_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonFormationVolFactorTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    hydrocarbon_viscosity_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonViscosityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    surface_densities: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "surfaceDensities",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    table_files: str = field(
        default="{}",
        metadata={
            "name": "tableFiles",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    water_compressibility: str = field(
        default="0",
        metadata={
            "name": "waterCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_formation_volume_factor: str = field(
        default="0",
        metadata={
            "name": "waterFormationVolumeFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_reference_pressure: str = field(
        default="0",
        metadata={
            "name": "waterReferencePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_viscosity: str = field(
        default="0",
        metadata={
            "name": "waterViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BlueprintType:
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    output_full_quadrature_data: str = field(
        default="0",
        metadata={
            "name": "outputFullQuadratureData",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    plot_level: str = field(
        default="1",
        metadata={
            "name": "plotLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BoxType:
    strike: str = field(
        default="-90",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    x_max: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "xMax",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    x_min: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "xMin",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BrooksCoreyBakerRelativePermeabilityType:
    gas_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name":
            "gasOilRelPermExponent",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "gasOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name":
            "waterOilRelPermExponent",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "waterOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BrooksCoreyCapillaryPressureType:
    cap_pressure_epsilon: str = field(
        default="1e-06",
        metadata={
            "name": "capPressureEpsilon",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_cap_pressure_exponent_inv: str = field(
        default="{2}",
        metadata={
            "name":
            "phaseCapPressureExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_entry_pressure: str = field(
        default="{1}",
        metadata={
            "name":
            "phaseEntryPressure",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BrooksCoreyRelativePermeabilityType:
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name":
            "phaseRelPermExponent",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class BrooksCoreyStone2RelativePermeabilityType:
    gas_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name":
            "gasOilRelPermExponent",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "gasOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name":
            "waterOilRelPermExponent",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "waterOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Co2BrineEzrokhiFluidType:

    class Meta:
        name = "CO2BrineEzrokhiFluidType"

    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    flash_model_para_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Co2BrineEzrokhiThermalFluidType:

    class Meta:
        name = "CO2BrineEzrokhiThermalFluidType"

    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    flash_model_para_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Co2BrinePhillipsFluidType:

    class Meta:
        name = "CO2BrinePhillipsFluidType"

    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    flash_model_para_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Co2BrinePhillipsThermalFluidType:

    class Meta:
        name = "CO2BrinePhillipsThermalFluidType"

    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    flash_model_para_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CarmanKozenyPermeabilityType:
    anisotropy: str = field(
        default="{1,1,1}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    particle_diameter: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "particleDiameter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    sphericity: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CellElementRegionType:
    cell_blocks: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "cellBlocks",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    coarsening_ratio: str = field(
        default="0",
        metadata={
            "name": "coarseningRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    material_list: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    mesh_body: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CeramicDamageType:
    compressive_strength: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "compressiveStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    crack_speed: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "crackSpeed",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    maximum_strength: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maximumStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tensile_strength: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "tensileStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ChomboIotype:

    class Meta:
        name = "ChomboIOType"

    begin_cycle: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "beginCycle",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    input_path: str = field(
        default="/INVALID_INPUT_PATH",
        metadata={
            "name": "inputPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    output_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "outputPath",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_chombo_pressures: str = field(
        default="0",
        metadata={
            "name": "useChomboPressures",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    wait_for_input: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "waitForInput",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositeFunctionType:
    expression: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    function_names: str = field(
        default="{}",
        metadata={
            "name": "functionNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    variable_names: str = field(
        default="{}",
        metadata={
            "name": "variableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseFluidType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentAcentricFactor",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name":
            "componentBinaryCoeff",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalPressure",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_critical_temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalTemperature",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name":
            "componentVolumeShift",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseReservoirPoromechanicsInitializationType:
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    perform_stress_initialization: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "performStressInitialization",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseStatisticsType:
    compute_cflnumbers: str = field(
        default="0",
        metadata={
            "name": "computeCFLNumbers",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    compute_region_statistics: str = field(
        default="1",
        metadata={
            "name": "computeRegionStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    relperm_threshold: str = field(
        default="1e-06",
        metadata={
            "name": "relpermThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositonalTwoPhaseFluidPengRobinsonType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentAcentricFactor",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name":
            "componentBinaryCoeff",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalPressure",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_critical_temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalTemperature",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name":
            "componentCriticalVolume",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name":
            "componentVolumeShift",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositonalTwoPhaseFluidSoaveRedlichKwongType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentAcentricFactor",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name":
            "componentBinaryCoeff",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalPressure",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_critical_temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentCriticalTemperature",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name":
            "componentCriticalVolume",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name":
            "componentVolumeShift",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSinglePhaseFluidType:
    compressibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_viscosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    density_model_type: str = field(
        default="linear",
        metadata={
            "name": "densityModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|exponential|linear|quadratic",
        },
    )
    reference_density: str = field(
        default="1000",
        metadata={
            "name": "referenceDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_pressure: str = field(
        default="0",
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_viscosity: str = field(
        default="0.001",
        metadata={
            "name": "referenceViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosity_model_type: str = field(
        default="linear",
        metadata={
            "name": "viscosityModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|exponential|linear|quadratic",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidCarmanKozenyPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidConstantPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidExponentialDecayPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidParallelPlatesPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidSlipDependentPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompressibleSolidWillisRichardsPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ConstantDiffusionType:
    default_phase_diffusivity_multipliers: str = field(
        default="{1}",
        metadata={
            "name":
            "defaultPhaseDiffusivityMultipliers",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    diffusivity_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "diffusivityComponents",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ConstantPermeabilityType:
    permeability_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "permeabilityComponents",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CoulombType:
    aperture_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "apertureTableName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    aperture_tolerance: str = field(
        default="1e-09",
        metadata={
            "name": "apertureTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    cohesion: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    friction_coefficient: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "frictionCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "penaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    shear_stiffness: str = field(
        default="0",
        metadata={
            "name": "shearStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CustomPolarObjectType:
    center: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    coefficients: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    length_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "lengthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    normal: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "widthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CylinderType:
    first_face_center: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "firstFaceCenter",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    inner_radius: str = field(
        default="-1",
        metadata={
            "name": "innerRadius",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    outer_radius: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "outerRadius",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    second_face_center: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "secondFaceCenter",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DamageElasticIsotropicType:
    compressive_strength: str = field(
        default="0",
        metadata={
            "name": "compressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_fracture_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_strain_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    degradation_lower_limit: str = field(
        default="0",
        metadata={
            "name": "degradationLowerLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "deltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tensile_strength: str = field(
        default="0",
        metadata={
            "name": "tensileStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DamageSpectralElasticIsotropicType:
    compressive_strength: str = field(
        default="0",
        metadata={
            "name": "compressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_fracture_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_strain_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    degradation_lower_limit: str = field(
        default="0",
        metadata={
            "name": "degradationLowerLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "deltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tensile_strength: str = field(
        default="0",
        metadata={
            "name": "tensileStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DamageVolDevElasticIsotropicType:
    compressive_strength: str = field(
        default="0",
        metadata={
            "name": "compressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_fracture_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_strain_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    degradation_lower_limit: str = field(
        default="0",
        metadata={
            "name": "degradationLowerLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "deltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tensile_strength: str = field(
        default="0",
        metadata={
            "name": "tensileStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DeadOilFluidType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    hydrocarbon_formation_vol_factor_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonFormationVolFactorTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    hydrocarbon_viscosity_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonViscosityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    surface_densities: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "surfaceDensities",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    table_files: str = field(
        default="{}",
        metadata={
            "name": "tableFiles",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    water_compressibility: str = field(
        default="0",
        metadata={
            "name": "waterCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_formation_volume_factor: str = field(
        default="0",
        metadata={
            "name": "waterFormationVolumeFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_reference_pressure: str = field(
        default="0",
        metadata={
            "name": "waterReferencePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_viscosity: str = field(
        default="0",
        metadata={
            "name": "waterViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DelftEggType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_csl_slope: str = field(
        default="1",
        metadata={
            "name": "defaultCslSlope",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_pre_consolidation_pressure: str = field(
        default="-1.5",
        metadata={
            "name": "defaultPreConsolidationPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_recompression_index: str = field(
        default="0.002",
        metadata={
            "name": "defaultRecompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shape_parameter: str = field(
        default="1",
        metadata={
            "name": "defaultShapeParameter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_virgin_compression_index: str = field(
        default="0.005",
        metadata={
            "name": "defaultVirginCompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DirichletType:
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    field_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_condition: str = field(
        default="0",
        metadata={
            "name": "initialCondition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DiscType:
    center: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    length_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "lengthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    normal: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    radius: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "widthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class DruckerPragerType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_cohesion: str = field(
        default="0",
        metadata={
            "name": "defaultCohesion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_dilation_angle: str = field(
        default="30",
        metadata={
            "name": "defaultDilationAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_hardening_rate: str = field(
        default="0",
        metadata={
            "name": "defaultHardeningRate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElasticIsotropicPressureDependentType:
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_recompression_index: str = field(
        default="0.002",
        metadata={
            "name": "defaultRecompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_pressure: str = field(
        default="-1",
        metadata={
            "name": "defaultRefPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_strain_vol: str = field(
        default="0",
        metadata={
            "name": "defaultRefStrainVol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElasticIsotropicType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElasticOrthotropicType:
    default_c11: str = field(
        default="-1",
        metadata={
            "name": "defaultC11",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c12: str = field(
        default="-1",
        metadata={
            "name": "defaultC12",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c13: str = field(
        default="-1",
        metadata={
            "name": "defaultC13",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c22: str = field(
        default="-1",
        metadata={
            "name": "defaultC22",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c23: str = field(
        default="-1",
        metadata={
            "name": "defaultC23",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c33: str = field(
        default="-1",
        metadata={
            "name": "defaultC33",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c44: str = field(
        default="-1",
        metadata={
            "name": "defaultC44",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c55: str = field(
        default="-1",
        metadata={
            "name": "defaultC55",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c66: str = field(
        default="-1",
        metadata={
            "name": "defaultC66",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_e1: str = field(
        default="-1",
        metadata={
            "name": "defaultE1",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_e2: str = field(
        default="-1",
        metadata={
            "name": "defaultE2",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_e3: str = field(
        default="-1",
        metadata={
            "name": "defaultE3",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_g12: str = field(
        default="-1",
        metadata={
            "name": "defaultG12",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_g13: str = field(
        default="-1",
        metadata={
            "name": "defaultG13",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_g23: str = field(
        default="-1",
        metadata={
            "name": "defaultG23",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_nu12: str = field(
        default="-1",
        metadata={
            "name": "defaultNu12",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_nu13: str = field(
        default="-1",
        metadata={
            "name": "defaultNu13",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_nu23: str = field(
        default="-1",
        metadata={
            "name": "defaultNu23",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElasticTransverseIsotropicType:
    default_c11: str = field(
        default="-1",
        metadata={
            "name": "defaultC11",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c13: str = field(
        default="-1",
        metadata={
            "name": "defaultC13",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c33: str = field(
        default="-1",
        metadata={
            "name": "defaultC33",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c44: str = field(
        default="-1",
        metadata={
            "name": "defaultC44",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_c66: str = field(
        default="-1",
        metadata={
            "name": "defaultC66",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio_axial_transverse: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatioAxialTransverse",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio_transverse: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatioTransverse",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus_axial_transverse: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulusAxialTransverse",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus_axial: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulusAxial",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus_transverse: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulusTransverse",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ExponentialDecayPermeabilityType:
    empirical_constant: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "empiricalConstant",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_permeability: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "initialPermeability",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ExtendedDruckerPragerType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_cohesion: str = field(
        default="0",
        metadata={
            "name": "defaultCohesion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_dilation_ratio: str = field(
        default="1",
        metadata={
            "name": "defaultDilationRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_hardening: str = field(
        default="0",
        metadata={
            "name": "defaultHardening",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_initial_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultInitialFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_residual_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultResidualFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class FieldSpecificationType:
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    field_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_condition: str = field(
        default="0",
        metadata={
            "name": "initialCondition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class FileType:
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )


@dataclass
class FiniteElementSpaceType:
    formulation: str = field(
        default="default",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|SEM",
        },
    )
    order: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_virtual_elements: str = field(
        default="0",
        metadata={
            "name": "useVirtualElements",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class FrictionlessContactType:
    aperture_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "apertureTableName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    aperture_tolerance: str = field(
        default="1e-09",
        metadata={
            "name": "apertureTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "penaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    shear_stiffness: str = field(
        default="0",
        metadata={
            "name": "shearStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class HybridMimeticDiscretizationType:
    inner_product_type: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "innerProductType",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class HydrostaticEquilibriumType:
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component_fraction_vs_elevation_table_names: str = field(
        default="{}",
        metadata={
            "name": "componentFractionVsElevationTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    datum_elevation: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "datumElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    datum_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "datumPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    elevation_increment_in_hydrostatic_pressure_table: str = field(
        default="0.6096",
        metadata={
            "name": "elevationIncrementInHydrostaticPressureTable",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    equilibration_tolerance: str = field(
        default="0.001",
        metadata={
            "name": "equilibrationTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_phase_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "initialPhaseName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_number_of_equilibration_iterations: str = field(
        default="5",
        metadata={
            "name": "maxNumberOfEquilibrationIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature_vs_elevation_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "temperatureVsElevationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class JfunctionCapillaryPressureType:

    class Meta:
        name = "JFunctionCapillaryPressureType"

    non_wetting_intermediate_jfunction_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "nonWettingIntermediateJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    non_wetting_intermediate_surface_tension: str = field(
        default="0",
        metadata={
            "name": "nonWettingIntermediateSurfaceTension",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    permeability_direction: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityDirection",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|XY|X|Y|Z",
        },
    )
    permeability_exponent: str = field(
        default="0.5",
        metadata={
            "name": "permeabilityExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    porosity_exponent: str = field(
        default="0.5",
        metadata={
            "name": "porosityExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    wetting_intermediate_jfunction_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wettingIntermediateJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    wetting_intermediate_surface_tension: str = field(
        default="0",
        metadata={
            "name": "wettingIntermediateSurfaceTension",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    wetting_non_wetting_jfunction_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wettingNonWettingJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    wetting_non_wetting_surface_tension: str = field(
        default="0",
        metadata={
            "name": "wettingNonWettingSurfaceTension",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class LinearIsotropicDispersionType:
    longitudinal_dispersivity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "longitudinalDispersivity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class LinearSolverParametersType:
    amg_aggressive_coarsening_levels: str = field(
        default="0",
        metadata={
            "name": "amgAggressiveCoarseningLevels",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_aggressive_coarsening_paths: str = field(
        default="1",
        metadata={
            "name": "amgAggressiveCoarseningPaths",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_aggressive_interp_type: str = field(
        default="multipass",
        metadata={
            "name":
            "amgAggressiveInterpType",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|default|extendedIStage2|standardStage2|extendedStage2|multipass|modifiedExtended|modifiedExtendedI|modifiedExtendedE|modifiedMultipass",
        },
    )
    amg_coarse_solver: str = field(
        default="direct",
        metadata={
            "name": "amgCoarseSolver",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|direct|bgs",
        },
    )
    amg_coarsening_type: str = field(
        default="HMIS",
        metadata={
            "name": "amgCoarseningType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|CLJP|RugeStueben|Falgout|PMIS|HMIS",
        },
    )
    amg_interpolation_max_non_zeros: str = field(
        default="4",
        metadata={
            "name": "amgInterpolationMaxNonZeros",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_interpolation_type: str = field(
        default="extendedI",
        metadata={
            "name":
            "amgInterpolationType",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|default|modifiedClassical|direct|multipass|extendedI|standard|extended|directBAMG|modifiedExtended|modifiedExtendedI|modifiedExtendedE",
        },
    )
    amg_null_space_type: str = field(
        default="constantModes",
        metadata={
            "name": "amgNullSpaceType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|constantModes|rigidBodyModes",
        },
    )
    amg_num_functions: str = field(
        default="1",
        metadata={
            "name": "amgNumFunctions",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_num_sweeps: str = field(
        default="1",
        metadata={
            "name": "amgNumSweeps",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_relax_weight: str = field(
        default="1",
        metadata={
            "name": "amgRelaxWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    amg_separate_components: str = field(
        default="0",
        metadata={
            "name": "amgSeparateComponents",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    amg_smoother_type: str = field(
        default="l1sgs",
        metadata={
            "name": "amgSmootherType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|jacobi|l1jacobi|fgs|bgs|sgs|l1sgs|chebyshev|ilu0|ilut|ic0|ict",
        },
    )
    amg_threshold: str = field(
        default="0",
        metadata={
            "name": "amgThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    direct_check_residual: str = field(
        default="0",
        metadata={
            "name": "directCheckResidual",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direct_col_perm: str = field(
        default="metis",
        metadata={
            "name": "directColPerm",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|MMD_AtplusA|MMD_AtA|colAMD|metis|parmetis",
        },
    )
    direct_equil: str = field(
        default="1",
        metadata={
            "name": "directEquil",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direct_iter_ref: str = field(
        default="1",
        metadata={
            "name": "directIterRef",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direct_parallel: str = field(
        default="1",
        metadata={
            "name": "directParallel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direct_repl_tiny_pivot: str = field(
        default="1",
        metadata={
            "name": "directReplTinyPivot",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direct_row_perm: str = field(
        default="mc64",
        metadata={
            "name": "directRowPerm",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|mc64",
        },
    )
    ilu_fill: str = field(
        default="0",
        metadata={
            "name": "iluFill",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    ilu_threshold: str = field(
        default="0",
        metadata={
            "name": "iluThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    krylov_adaptive_tol: str = field(
        default="0",
        metadata={
            "name": "krylovAdaptiveTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    krylov_max_iter: str = field(
        default="200",
        metadata={
            "name": "krylovMaxIter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    krylov_max_restart: str = field(
        default="200",
        metadata={
            "name": "krylovMaxRestart",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    krylov_tol: str = field(
        default="1e-06",
        metadata={
            "name": "krylovTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    krylov_weakest_tol: str = field(
        default="0.001",
        metadata={
            "name": "krylovWeakestTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    preconditioner_type: str = field(
        default="iluk",
        metadata={
            "name":
            "preconditionerType",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|none|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|iluk|ilut|icc|ict|amg|mgr|block|direct|bgs",
        },
    )
    solver_type: str = field(
        default="direct",
        metadata={
            "name": "solverType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|direct|cg|gmres|fgmres|bicgstab|preconditioner",
        },
    )
    stop_if_error: str = field(
        default="1",
        metadata={
            "name": "stopIfError",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


@dataclass
class ModifiedCamClayType:
    default_csl_slope: str = field(
        default="1",
        metadata={
            "name": "defaultCslSlope",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_pre_consolidation_pressure: str = field(
        default="-1.5",
        metadata={
            "name": "defaultPreConsolidationPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_recompression_index: str = field(
        default="0.002",
        metadata={
            "name": "defaultRecompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_pressure: str = field(
        default="-1",
        metadata={
            "name": "defaultRefPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_strain_vol: str = field(
        default="0",
        metadata={
            "name": "defaultRefStrainVol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_virgin_compression_index: str = field(
        default="0.005",
        metadata={
            "name": "defaultVirginCompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultiPhaseConstantThermalConductivityType:
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    thermal_conductivity_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "thermalConductivityComponents",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultiPhaseVolumeWeightedThermalConductivityType:
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_thermal_conductivity: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "phaseThermalConductivity",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    rock_thermal_conductivity_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "rockThermalConductivityComponents",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultiphasePoromechanicsInitializationType:
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    perform_stress_initialization: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "performStressInitialization",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultivariableTableFunctionType:
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class NonlinearSolverParametersType:
    allow_non_converged: str = field(
        default="0",
        metadata={
            "name": "allowNonConverged",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    coupling_type: str = field(
        default="FullyImplicit",
        metadata={
            "name": "couplingType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|FullyImplicit|Sequential",
        },
    )
    line_search_action: str = field(
        default="Attempt",
        metadata={
            "name": "lineSearchAction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|None|Attempt|Require",
        },
    )
    line_search_cut_factor: str = field(
        default="0.5",
        metadata={
            "name": "lineSearchCutFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    line_search_interpolation_type: str = field(
        default="Linear",
        metadata={
            "name": "lineSearchInterpolationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|Linear|Parabolic",
        },
    )
    line_search_max_cuts: str = field(
        default="4",
        metadata={
            "name": "lineSearchMaxCuts",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_allowed_residual_norm: str = field(
        default="1e+09",
        metadata={
            "name": "maxAllowedResidualNorm",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_num_configuration_attempts: str = field(
        default="10",
        metadata={
            "name": "maxNumConfigurationAttempts",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_sub_steps: str = field(
        default="10",
        metadata={
            "name": "maxSubSteps",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_time_step_cuts: str = field(
        default="2",
        metadata={
            "name": "maxTimeStepCuts",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    min_normalizer: str = field(
        default="1e-12",
        metadata={
            "name": "minNormalizer",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    newton_max_iter: str = field(
        default="5",
        metadata={
            "name": "newtonMaxIter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    newton_min_iter: str = field(
        default="1",
        metadata={
            "name": "newtonMinIter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    newton_tol: str = field(
        default="1e-06",
        metadata={
            "name": "newtonTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    nonlinear_acceleration_type: str = field(
        default="None",
        metadata={
            "name": "nonlinearAccelerationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|None|Aitken",
        },
    )
    sequential_convergence_criterion: str = field(
        default="ResidualNorm",
        metadata={
            "name": "sequentialConvergenceCriterion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ResidualNorm|NumberOfNonlinearIterations",
        },
    )
    subcycling: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    time_step_cut_factor: str = field(
        default="0.5",
        metadata={
            "name": "timeStepCutFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_step_decrease_factor: str = field(
        default="0.5",
        metadata={
            "name": "timeStepDecreaseFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_step_decrease_iter_limit: str = field(
        default="0.7",
        metadata={
            "name": "timeStepDecreaseIterLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_step_increase_factor: str = field(
        default="2",
        metadata={
            "name": "timeStepIncreaseFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_step_increase_iter_limit: str = field(
        default="0.4",
        metadata={
            "name": "timeStepIncreaseIterLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    norm_type: str = field(
        default="Linfinity",
        metadata={
            "name": "normType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|Linfinity|L2",
        },
    )


@dataclass
class NullModelType:
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Pmltype:

    class Meta:
        name = "PMLType"

    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    reflectivity: real32 = field(
        default="0.001",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    thickness_max_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name":
            "thicknessMaxXYZ",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    thickness_min_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name":
            "thicknessMinXYZ",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    wave_speed_max_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name":
            "waveSpeedMaxXYZ",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    wave_speed_min_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name":
            "waveSpeedMinXYZ",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    x_max: str = field(
        default="{3.40282e+38,3.40282e+38,3.40282e+38}",
        metadata={
            "name":
            "xMax",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    x_min: str = field(
        default="{-3.40282e+38,-3.40282e+38,-3.40282e+38}",
        metadata={
            "name":
            "xMin",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PvtdriverType:

    class Meta:
        name = "PVTDriverType"

    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    feed_composition: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "feedComposition",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    fluid: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    output_compressibility: str = field(
        default="0",
        metadata={
            "name": "outputCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_phase_composition: str = field(
        default="0",
        metadata={
            "name": "outputPhaseComposition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    pressure_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "pressureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    steps: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    temperature_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "temperatureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PackCollectionType:
    disable_coord_collection: str = field(
        default="0",
        metadata={
            "name": "disableCoordCollection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    field_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    only_on_set_change: str = field(
        default="0",
        metadata={
            "name": "onlyOnSetChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    set_names: str = field(
        default="{}",
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ParallelPlatesPermeabilityType:
    transversal_permeability: str = field(
        default="-1",
        metadata={
            "name": "transversalPermeability",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ParameterType:
    value: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ParticleFluidType:
    collision_alpha: str = field(
        default="1.27",
        metadata={
            "name": "collisionAlpha",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    collision_beta: str = field(
        default="1.5",
        metadata={
            "name": "collisionBeta",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    fluid_viscosity: str = field(
        default="0.001",
        metadata={
            "name": "fluidViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    hindered_settling_coefficient: str = field(
        default="5.9",
        metadata={
            "name": "hinderedSettlingCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_collisional_slip: str = field(
        default="0",
        metadata={
            "name": "isCollisionalSlip",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_proppant_concentration: str = field(
        default="0.6",
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    particle_settling_model: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "particleSettlingModel",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|Stokes|Intermediate|Turbulence",
        },
    )
    proppant_density: str = field(
        default="1400",
        metadata={
            "name": "proppantDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    proppant_diameter: str = field(
        default="0.0002",
        metadata={
            "name": "proppantDiameter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    slip_concentration: str = field(
        default="0.1",
        metadata={
            "name": "slipConcentration",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    sphericity: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ParticleMeshType:
    header_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "headerFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    particle_block_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "particleBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    particle_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "particleFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    particle_types: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "particleTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ParticleRegionType:
    material_list: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    mesh_body: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    particle_blocks: str = field(
        default="{}",
        metadata={
            "name": "particleBlocks",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PerfectlyPlasticType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_yield_stress: str = field(
        default="1.79769e+308",
        metadata={
            "name": "defaultYieldStress",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PerforationType:
    distance_from_head: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "distanceFromHead",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    skin_factor: str = field(
        default="0",
        metadata={
            "name": "skinFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    transmissibility: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PermeabilityBaseType:
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousDelftEggType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousDruckerPragerType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousElasticIsotropicType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousElasticOrthotropicType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousElasticTransverseIsotropicType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousExtendedDruckerPragerType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PorousModifiedCamClayType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PressurePorosityType:
    compressibility: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_reference_porosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_pressure: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ProppantPermeabilityType:
    max_proppant_concentration: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    proppant_diameter: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "proppantDiameter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ProppantPorosityType:
    default_reference_porosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_proppant_concentration: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ProppantSlurryFluidType:
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    compressibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_component_density: str = field(
        default="{0}",
        metadata={
            "name":
            "defaultComponentDensity",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    default_component_viscosity: str = field(
        default="{0}",
        metadata={
            "name":
            "defaultComponentViscosity",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    default_compressibility: str = field(
        default="{0}",
        metadata={
            "name":
            "defaultCompressibility",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    flow_behavior_index: str = field(
        default="{0}",
        metadata={
            "name":
            "flowBehaviorIndex",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    flow_consistency_index: str = field(
        default="{0}",
        metadata={
            "name":
            "flowConsistencyIndex",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    max_proppant_concentration: str = field(
        default="0.6",
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_density: str = field(
        default="1000",
        metadata={
            "name": "referenceDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_pressure: str = field(
        default="100000",
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_proppant_density: str = field(
        default="1400",
        metadata={
            "name": "referenceProppantDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_viscosity: str = field(
        default="0.001",
        metadata={
            "name": "referenceViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ProppantSolidProppantPermeabilityType:
    permeability_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    porosity_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_internal_energy_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_model_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PythonType:
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ReactiveBrineThermalType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ReactiveBrineType:
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name":
            "componentMolarWeight",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ReactiveFluidDriverType:
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    feed_composition: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "feedComposition",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    fluid: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    pressure_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "pressureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    steps: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    temperature_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "temperatureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class RectangleType:
    dimensions: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    length_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "lengthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    normal: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    origin: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "widthVector",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class RelpermDriverType:
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    relperm: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    steps: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class RestartType:
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class RunType:
    args: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    auto_partition: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "autoPartition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    mesh_sizes: str = field(
        default="{0}",
        metadata={
            "name": "meshSizes",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    nodes: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    scale_list: str = field(
        default="{0}",
        metadata={
            "name": "scaleList",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    scaling: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    tasks_per_node: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "tasksPerNode",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    threads_per_task: str = field(
        default="0",
        metadata={
            "name": "threadsPerTask",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    time_limit: str = field(
        default="0",
        metadata={
            "name": "timeLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


@dataclass
class SiloType:
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    field_names: str = field(
        default="{}",
        metadata={
            "name": "fieldNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    only_plot_specified_field_names: str = field(
        default="0",
        metadata={
            "name": "onlyPlotSpecifiedFieldNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    plot_file_root: str = field(
        default="plot",
        metadata={
            "name": "plotFileRoot",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    plot_level: str = field(
        default="1",
        metadata={
            "name": "plotLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_cell_element_mesh: str = field(
        default="1",
        metadata={
            "name": "writeCellElementMesh",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_edge_mesh: str = field(
        default="0",
        metadata={
            "name": "writeEdgeMesh",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_femfaces: str = field(
        default="0",
        metadata={
            "name": "writeFEMFaces",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_face_element_mesh: str = field(
        default="1",
        metadata={
            "name": "writeFaceElementMesh",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseConstantThermalConductivityType:
    thermal_conductivity_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "thermalConductivityComponents",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhasePoromechanicsInitializationType:
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    perform_stress_initialization: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "performStressInitialization",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseReservoirPoromechanicsInitializationType:
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    perform_stress_initialization: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "performStressInitialization",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseStatisticsType:
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SlipDependentPermeabilityType:
    initial_permeability: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "initialPermeability",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    max_perm_multiplier: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maxPermMultiplier",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    shear_disp_threshold: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "shearDispThreshold",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidInternalEnergyType:
    reference_internal_energy: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "referenceInternalEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "referenceTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    volumetric_heat_capacity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "volumetricHeatCapacity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsStateResetType:
    disable_inelasticity: str = field(
        default="0",
        metadata={
            "name": "disableInelasticity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    reset_displacements: str = field(
        default="1",
        metadata={
            "name": "resetDisplacements",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsStatisticsType:
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SoloEventType:
    halt_event: list[ "HaltEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[ "PeriodicEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list[ "SoloEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "SoloEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    begin_time: str = field(
        default="0",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    end_time: str = field(
        default="1e+100",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    final_dt_stretch: str = field(
        default="0.001",
        metadata={
            "name": "finalDtStretch",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    force_dt: str = field(
        default="-1",
        metadata={
            "name": "forceDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_event_dt: str = field(
        default="-1",
        metadata={
            "name": "maxEventDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_cycle: str = field(
        default="-1",
        metadata={
            "name": "targetCycle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_exact_start_stop: str = field(
        default="1",
        metadata={
            "name": "targetExactStartStop",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_exact_timestep: str = field(
        default="1",
        metadata={
            "name": "targetExactTimestep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_time: str = field(
        default="-1",
        metadata={
            "name": "targetTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SourceFluxType:
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_condition: str = field(
        default="0",
        metadata={
            "name": "initialCondition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SurfaceElementRegionType:
    default_aperture: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultAperture",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    face_block: str = field(
        default="FractureSubRegion",
        metadata={
            "name": "faceBlock",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    material_list: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    mesh_body: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    sub_region_type: str = field(
        default="faceElement",
        metadata={
            "name": "subRegionType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|faceElement|embeddedElement",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SymbolicFunctionType:
    expression: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    variable_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "variableNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TableCapillaryPressureType:
    non_wetting_intermediate_cap_pressure_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "nonWettingIntermediateCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    wetting_intermediate_cap_pressure_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wettingIntermediateCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    wetting_non_wetting_cap_pressure_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wettingNonWettingCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TableFunctionType:
    coordinate_files: str = field(
        default="{}",
        metadata={
            "name": "coordinateFiles",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^*?<>\|:\";,\s]+\s*,\s*)*[^*?<>\|:\";,\s]+\s*)?\}\s*",
        },
    )
    coordinates: str = field(
        default="{0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    interpolation: str = field(
        default="linear",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|linear|nearest|upper|lower",
        },
    )
    values: str = field(
        default="{0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    voxel_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "voxelFile",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TableRelativePermeabilityHysteresisType:
    drainage_non_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageNonWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    drainage_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    drainage_wetting_non_wetting_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageWettingNonWettingRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    imbibition_non_wetting_rel_perm_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "imbibitionNonWettingRelPermTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    imbibition_wetting_rel_perm_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "imbibitionWettingRelPermTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    jerauld_parameter_a: str = field(
        default="0.1",
        metadata={
            "name": "jerauldParameterA",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    jerauld_parameter_b: str = field(
        default="0",
        metadata={
            "name": "jerauldParameterB",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    killough_curvature_parameter: str = field(
        default="1",
        metadata={
            "name": "killoughCurvatureParameter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    three_phase_interpolator: str = field(
        default="BAKER",
        metadata={
            "name": "threePhaseInterpolator",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|BAKER|STONEII",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TableRelativePermeabilityType:
    non_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "nonWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    three_phase_interpolator: str = field(
        default="BAKER",
        metadata={
            "name": "threePhaseInterpolator",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|BAKER|STONEII",
        },
    )
    wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "wettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    wetting_non_wetting_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "wettingNonWettingRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ThermalCompressibleSinglePhaseFluidType:
    compressibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_viscosity: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    density_model_type: str = field(
        default="linear",
        metadata={
            "name": "densityModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|exponential|linear|quadratic",
        },
    )
    internal_energy_model_type: str = field(
        default="linear",
        metadata={
            "name": "internalEnergyModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|exponential|linear|quadratic",
        },
    )
    reference_density: str = field(
        default="1000",
        metadata={
            "name": "referenceDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_internal_energy: str = field(
        default="0.001",
        metadata={
            "name": "referenceInternalEnergy",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_pressure: str = field(
        default="0",
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_temperature: str = field(
        default="0",
        metadata={
            "name": "referenceTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_viscosity: str = field(
        default="0.001",
        metadata={
            "name": "referenceViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    thermal_expansion_coeff: str = field(
        default="0",
        metadata={
            "name": "thermalExpansionCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosity_model_type: str = field(
        default="linear",
        metadata={
            "name": "viscosityModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|exponential|linear|quadratic",
        },
    )
    volumetric_heat_capacity: str = field(
        default="0",
        metadata={
            "name": "volumetricHeatCapacity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ThickPlaneType:
    normal: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    origin: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    thickness: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TimeHistoryType:
    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    filename: str = field(
        default="TimeHistory",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    format: str = field(
        default="hdf",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    sources: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TractionType:
    bc_application_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    begin_time: str = field(
        default="-1e+99",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    end_time: str = field(
        default="1e+99",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_condition: str = field(
        default="0",
        metadata={
            "name": "initialCondition",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    input_stress: str = field(
        default="{0,0,0,0,0,0}",
        metadata={
            "name":
            "inputStress",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){5}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    traction_type: str = field(
        default="vector",
        metadata={
            "name": "tractionType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|vector|normal|stress",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TriaxialDriverType:
    axial_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "axialControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    initial_stress: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "initialStress",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    material: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    mode: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|mixedControl|strainControl|stressControl",
        },
    )
    output: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    radial_control: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "radialControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    steps: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TwoPointFluxApproximationType:
    area_rel_tol: str = field(
        default="1e-08",
        metadata={
            "name": "areaRelTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    mean_perm_coefficient: str = field(
        default="1",
        metadata={
            "name": "meanPermCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    upwinding_scheme: str = field(
        default="PPU",
        metadata={
            "name": "upwindingScheme",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|PPU|C1PPU",
        },
    )
    use_pedfm: str = field(
        default="0",
        metadata={
            "name": "usePEDFM",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class Vtktype:

    class Meta:
        name = "VTKType"

    child_directory: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    field_names: str = field(
        default="{}",
        metadata={
            "name": "fieldNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    format: str = field(
        default="binary",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|binary|ascii",
        },
    )
    level_names: str = field(
        default="{}",
        metadata={
            "name": "levelNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    only_plot_specified_field_names: str = field(
        default="0",
        metadata={
            "name": "onlyPlotSpecifiedFieldNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_region_type: str = field(
        default="all",
        metadata={
            "name": "outputRegionType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|cell|well|surface|particle|all",
        },
    )
    parallel_threads: str = field(
        default="1",
        metadata={
            "name": "parallelThreads",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    plot_file_root: str = field(
        default="VTK",
        metadata={
            "name": "plotFileRoot",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    plot_level: str = field(
        default="1",
        metadata={
            "name": "plotLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_femfaces: str = field(
        default="0",
        metadata={
            "name": "writeFEMFaces",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_ghost_cells: str = field(
        default="0",
        metadata={
            "name": "writeGhostCells",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class VanGenuchtenBakerRelativePermeabilityType:
    gas_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name":
            "gasOilRelPermExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "gasOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name":
            "waterOilRelPermExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "waterOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class VanGenuchtenCapillaryPressureType:
    cap_pressure_epsilon: str = field(
        default="1e-06",
        metadata={
            "name": "capPressureEpsilon",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_cap_pressure_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name":
            "phaseCapPressureExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_cap_pressure_multiplier: str = field(
        default="{1}",
        metadata={
            "name":
            "phaseCapPressureMultiplier",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class VanGenuchtenStone2RelativePermeabilityType:
    gas_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name":
            "gasOilRelPermExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "gasOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name":
            "phaseMinVolumeFraction",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name":
            "waterOilRelPermExponentInv",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name":
            "waterOilRelPermMaxValue",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ViscoDruckerPragerType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_cohesion: str = field(
        default="0",
        metadata={
            "name": "defaultCohesion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_dilation_angle: str = field(
        default="30",
        metadata={
            "name": "defaultDilationAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_hardening_rate: str = field(
        default="0",
        metadata={
            "name": "defaultHardeningRate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    relaxation_time: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ViscoExtendedDruckerPragerType:
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_cohesion: str = field(
        default="0",
        metadata={
            "name": "defaultCohesion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_dilation_ratio: str = field(
        default="1",
        metadata={
            "name": "defaultDilationRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_hardening: str = field(
        default="0",
        metadata={
            "name": "defaultHardening",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_initial_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultInitialFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_poisson_ratio: str = field(
        default="-1",
        metadata={
            "name": "defaultPoissonRatio",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_residual_friction_angle: str = field(
        default="30",
        metadata={
            "name": "defaultResidualFrictionAngle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_young_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultYoungModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    relaxation_time: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ViscoModifiedCamClayType:
    default_csl_slope: str = field(
        default="1",
        metadata={
            "name": "defaultCslSlope",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_drained_linear_tec: str = field(
        default="0",
        metadata={
            "name": "defaultDrainedLinearTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_pre_consolidation_pressure: str = field(
        default="-1.5",
        metadata={
            "name": "defaultPreConsolidationPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_recompression_index: str = field(
        default="0.002",
        metadata={
            "name": "defaultRecompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_pressure: str = field(
        default="-1",
        metadata={
            "name": "defaultRefPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_ref_strain_vol: str = field(
        default="0",
        metadata={
            "name": "defaultRefStrainVol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_shear_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultShearModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_virgin_compression_index: str = field(
        default="0.005",
        metadata={
            "name": "defaultVirginCompressionIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    relaxation_time: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class WellControlsType:
    control: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|BHP|phaseVolRate|totalVolRate|uninitialized",
        },
    )
    enable_crossflow: str = field(
        default="1",
        metadata={
            "name": "enableCrossflow",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_pressure_coefficient: str = field(
        default="0.1",
        metadata={
            "name": "initialPressureCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    injection_stream: str = field(
        default="{-1}",
        metadata={
            "name":
            "injectionStream",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    injection_temperature: str = field(
        default="-1",
        metadata={
            "name": "injectionTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    reference_elevation: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "referenceElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    status_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "statusTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    surface_pressure: str = field(
        default="0",
        metadata={
            "name": "surfacePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    surface_temperature: str = field(
        default="0",
        metadata={
            "name": "surfaceTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_bhp: str = field(
        default="0",
        metadata={
            "name": "targetBHP",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_bhptable_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetBHPTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_phase_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetPhaseName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_phase_rate: str = field(
        default="0",
        metadata={
            "name": "targetPhaseRate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_phase_rate_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetPhaseRateTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_total_rate: str = field(
        default="0",
        metadata={
            "name": "targetTotalRate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_total_rate_table_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetTotalRateTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    type_value: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|producer|injector",
        },
    )
    use_surface_conditions: str = field(
        default="0",
        metadata={
            "name": "useSurfaceConditions",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class WellElementRegionType:
    material_list: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    mesh_body: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class WillisRichardsPermeabilityType:
    dilation_coefficient: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "dilationCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_frac_aperture: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maxFracAperture",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    ref_closure_stress: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "refClosureStress",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class AcousticFirstOrderSemtype:

    class Meta:
        name = "AcousticFirstOrderSEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    dt_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "dtSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    enable_lifo: str = field(
        default="0",
        metadata={
            "name": "enableLifo",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    forward: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    lifo_on_device: str = field(
        default="-80",
        metadata={
            "name": "lifoOnDevice",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_on_host: str = field(
        default="-80",
        metadata={
            "name": "lifoOnHost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_size: str = field(
        default="2147483647",
        metadata={
            "name": "lifoSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    linear_dasgeometry: str = field(
        default="{{0}}",
        metadata={
            "name":
            "linearDASGeometry",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "outputSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    receiver_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "receiverCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    ricker_order: str = field(
        default="2",
        metadata={
            "name": "rickerOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    save_fields: str = field(
        default="0",
        metadata={
            "name": "saveFields",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    shot_index: str = field(
        default="0",
        metadata={
            "name": "shotIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "sourceCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_source_delay: real32 = field(
        default="-1",
        metadata={
            "name": "timeSourceDelay",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_source_frequency: real32 = field(
        default="0",
        metadata={
            "name": "timeSourceFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class AcousticSemtype:

    class Meta:
        name = "AcousticSEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    dt_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "dtSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    enable_lifo: str = field(
        default="0",
        metadata={
            "name": "enableLifo",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    forward: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    lifo_on_device: str = field(
        default="-80",
        metadata={
            "name": "lifoOnDevice",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_on_host: str = field(
        default="-80",
        metadata={
            "name": "lifoOnHost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_size: str = field(
        default="2147483647",
        metadata={
            "name": "lifoSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    linear_dasgeometry: str = field(
        default="{{0}}",
        metadata={
            "name":
            "linearDASGeometry",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "outputSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    receiver_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "receiverCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    ricker_order: str = field(
        default="2",
        metadata={
            "name": "rickerOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    save_fields: str = field(
        default="0",
        metadata={
            "name": "saveFields",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    shot_index: str = field(
        default="0",
        metadata={
            "name": "shotIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "sourceCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_source_delay: str = field(
        default="-1",
        metadata={
            "name": "timeSourceDelay",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_source_frequency: str = field(
        default="0",
        metadata={
            "name": "timeSourceFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class AcousticVtisemtype:

    class Meta:
        name = "AcousticVTISEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    dt_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "dtSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    enable_lifo: str = field(
        default="0",
        metadata={
            "name": "enableLifo",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    forward: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    lifo_on_device: str = field(
        default="-80",
        metadata={
            "name": "lifoOnDevice",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_on_host: str = field(
        default="-80",
        metadata={
            "name": "lifoOnHost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_size: str = field(
        default="2147483647",
        metadata={
            "name": "lifoSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    linear_dasgeometry: str = field(
        default="{{0}}",
        metadata={
            "name":
            "linearDASGeometry",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "outputSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    receiver_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "receiverCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    ricker_order: str = field(
        default="2",
        metadata={
            "name": "rickerOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    save_fields: str = field(
        default="0",
        metadata={
            "name": "saveFields",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    shot_index: str = field(
        default="0",
        metadata={
            "name": "shotIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "sourceCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_source_delay: str = field(
        default="-1",
        metadata={
            "name": "timeSourceDelay",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_source_frequency: str = field(
        default="0",
        metadata={
            "name": "timeSourceFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseFvmtype:

    class Meta:
        name = "CompositionalMultiphaseFVMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_local_comp_density_chopping: str = field(
        default="1",
        metadata={
            "name": "allowLocalCompDensityChopping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    cont_multiplier_dbc: str = field(
        default="0.5",
        metadata={
            "name": "contMultiplierDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    continuation_dbc: str = field(
        default="1",
        metadata={
            "name": "continuationDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    kappamin_dbc: str = field(
        default="1e-20",
        metadata={
            "name": "kappaminDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_comp_fraction_change: str = field(
        default="0.5",
        metadata={
            "name": "maxCompFractionChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_relative_pressure_change: str = field(
        default="0.5",
        metadata={
            "name": "maxRelativePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_relative_temperature_change: str = field(
        default="0.5",
        metadata={
            "name": "maxRelativeTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_comp_dens: str = field(
        default="1e-10",
        metadata={
            "name": "minCompDens",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    miscible_dbc: str = field(
        default="0",
        metadata={
            "name": "miscibleDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    omega_dbc: str = field(
        default="1",
        metadata={
            "name": "omegaDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    scaling_type: str = field(
        default="Global",
        metadata={
            "name": "scalingType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|Global|Local",
        },
    )
    solution_change_scaling_factor: str = field(
        default="0.5",
        metadata={
            "name": "solutionChangeScalingFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_flow_cfl: str = field(
        default="-1",
        metadata={
            "name": "targetFlowCFL",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_phase_vol_fraction_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetPhaseVolFractionChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    target_relative_pressure_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetRelativePressureChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_relative_temperature_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetRelativeTemperatureChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_dbc: str = field(
        default="0",
        metadata={
            "name": "useDBC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_mass: str = field(
        default="0",
        metadata={
            "name": "useMass",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_simple_accumulation: str = field(
        default="0",
        metadata={
            "name": "useSimpleAccumulation",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_total_mass_equation: str = field(
        default="1",
        metadata={
            "name": "useTotalMassEquation",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseHybridFvmtype:

    class Meta:
        name = "CompositionalMultiphaseHybridFVMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_local_comp_density_chopping: str = field(
        default="1",
        metadata={
            "name": "allowLocalCompDensityChopping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_comp_fraction_change: str = field(
        default="0.5",
        metadata={
            "name": "maxCompFractionChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_relative_pressure_change: str = field(
        default="0.5",
        metadata={
            "name": "maxRelativePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_relative_temperature_change: str = field(
        default="0.5",
        metadata={
            "name": "maxRelativeTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_comp_dens: str = field(
        default="1e-10",
        metadata={
            "name": "minCompDens",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    solution_change_scaling_factor: str = field(
        default="0.5",
        metadata={
            "name": "solutionChangeScalingFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_flow_cfl: str = field(
        default="-1",
        metadata={
            "name": "targetFlowCFL",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_phase_vol_fraction_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetPhaseVolFractionChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    target_relative_pressure_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetRelativePressureChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_relative_temperature_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetRelativeTemperatureChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_mass: str = field(
        default="0",
        metadata={
            "name": "useMass",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_simple_accumulation: str = field(
        default="0",
        metadata={
            "name": "useSimpleAccumulation",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_total_mass_equation: str = field(
        default="1",
        metadata={
            "name": "useTotalMassEquation",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseReservoirPoromechanicsType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    reservoir_and_wells_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    stabilization_multiplier: str = field(
        default="1",
        metadata={
            "name": "stabilizationMultiplier",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stabilization_region_names: str = field(
        default="{}",
        metadata={
            "name": "stabilizationRegionNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    stabilization_type: str = field(
        default="None",
        metadata={
            "name": "stabilizationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|None|Global|Local",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseReservoirType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    well_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class CompositionalMultiphaseWellType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    well_controls: list[ WellControlsType ] = field(
        default_factory=list,
        metadata={
            "name": "WellControls",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_local_comp_density_chopping: str = field(
        default="1",
        metadata={
            "name": "allowLocalCompDensityChopping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_comp_fraction_change: str = field(
        default="1",
        metadata={
            "name": "maxCompFractionChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_relative_pressure_change: str = field(
        default="1",
        metadata={
            "name": "maxRelativePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    use_mass: str = field(
        default="0",
        metadata={
            "name": "useMass",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ConstitutiveType:
    biot_porosity: list[ BiotPorosityType ] = field(
        default_factory=list,
        metadata={
            "name": "BiotPorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    black_oil_fluid: list[ BlackOilFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "BlackOilFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_baker_relative_permeability: list[ BrooksCoreyBakerRelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyBakerRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_capillary_pressure: list[ BrooksCoreyCapillaryPressureType ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_relative_permeability: list[ BrooksCoreyRelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_stone2_relative_permeability: list[ BrooksCoreyStone2RelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyStone2RelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_ezrokhi_fluid: list[ Co2BrineEzrokhiFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrineEzrokhiFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_ezrokhi_thermal_fluid: list[ Co2BrineEzrokhiThermalFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrineEzrokhiThermalFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_phillips_fluid: list[ Co2BrinePhillipsFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrinePhillipsFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_phillips_thermal_fluid: list[ Co2BrinePhillipsThermalFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrinePhillipsThermalFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    carman_kozeny_permeability: list[ CarmanKozenyPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    ceramic_damage: list[ CeramicDamageType ] = field(
        default_factory=list,
        metadata={
            "name": "CeramicDamage",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_fluid: list[ CompositionalMultiphaseFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    compositonal_two_phase_fluid_peng_robinson: list[ CompositonalTwoPhaseFluidPengRobinsonType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositonalTwoPhaseFluidPengRobinson",
            "type": "Element",
            "namespace": "",
        },
    )
    compositonal_two_phase_fluid_soave_redlich_kwong: list[ CompositonalTwoPhaseFluidSoaveRedlichKwongType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositonalTwoPhaseFluidSoaveRedlichKwong",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_single_phase_fluid: list[ CompressibleSinglePhaseFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSinglePhaseFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_carman_kozeny_permeability: list[ CompressibleSolidCarmanKozenyPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_constant_permeability: list[ CompressibleSolidConstantPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidConstantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_exponential_decay_permeability: list[
        CompressibleSolidExponentialDecayPermeabilityType ] = field(
            default_factory=list,
            metadata={
                "name": "CompressibleSolidExponentialDecayPermeability",
                "type": "Element",
                "namespace": "",
            },
        )
    compressible_solid_parallel_plates_permeability: list[ CompressibleSolidParallelPlatesPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidParallelPlatesPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_slip_dependent_permeability: list[ CompressibleSolidSlipDependentPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidSlipDependentPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_willis_richards_permeability: list[ CompressibleSolidWillisRichardsPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidWillisRichardsPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    constant_diffusion: list[ ConstantDiffusionType ] = field(
        default_factory=list,
        metadata={
            "name": "ConstantDiffusion",
            "type": "Element",
            "namespace": "",
        },
    )
    constant_permeability: list[ ConstantPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "ConstantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    coulomb: list[ CoulombType ] = field(
        default_factory=list,
        metadata={
            "name": "Coulomb",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_elastic_isotropic: list[ DamageElasticIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "DamageElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_spectral_elastic_isotropic: list[ DamageSpectralElasticIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "DamageSpectralElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_vol_dev_elastic_isotropic: list[ DamageVolDevElasticIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "DamageVolDevElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    dead_oil_fluid: list[ DeadOilFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "DeadOilFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    delft_egg: list[ DelftEggType ] = field(
        default_factory=list,
        metadata={
            "name": "DelftEgg",
            "type": "Element",
            "namespace": "",
        },
    )
    drucker_prager: list[ DruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "DruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_isotropic: list[ ElasticIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_isotropic_pressure_dependent: list[ ElasticIsotropicPressureDependentType ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticIsotropicPressureDependent",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_orthotropic: list[ ElasticOrthotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticOrthotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_transverse_isotropic: list[ ElasticTransverseIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticTransverseIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    exponential_decay_permeability: list[ ExponentialDecayPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "ExponentialDecayPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    extended_drucker_prager: list[ ExtendedDruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "ExtendedDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    frictionless_contact: list[ FrictionlessContactType ] = field(
        default_factory=list,
        metadata={
            "name": "FrictionlessContact",
            "type": "Element",
            "namespace": "",
        },
    )
    jfunction_capillary_pressure: list[ JfunctionCapillaryPressureType ] = field(
        default_factory=list,
        metadata={
            "name": "JFunctionCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    linear_isotropic_dispersion: list[ LinearIsotropicDispersionType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearIsotropicDispersion",
            "type": "Element",
            "namespace": "",
        },
    )
    modified_cam_clay: list[ ModifiedCamClayType ] = field(
        default_factory=list,
        metadata={
            "name": "ModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    multi_phase_constant_thermal_conductivity: list[ MultiPhaseConstantThermalConductivityType ] = field(
        default_factory=list,
        metadata={
            "name": "MultiPhaseConstantThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    multi_phase_volume_weighted_thermal_conductivity: list[ MultiPhaseVolumeWeightedThermalConductivityType ] = field(
        default_factory=list,
        metadata={
            "name": "MultiPhaseVolumeWeightedThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    null_model: list[ NullModelType ] = field(
        default_factory=list,
        metadata={
            "name": "NullModel",
            "type": "Element",
            "namespace": "",
        },
    )
    parallel_plates_permeability: list[ ParallelPlatesPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "ParallelPlatesPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_fluid: list[ ParticleFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "ParticleFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    perfectly_plastic: list[ PerfectlyPlasticType ] = field(
        default_factory=list,
        metadata={
            "name": "PerfectlyPlastic",
            "type": "Element",
            "namespace": "",
        },
    )
    permeability_base: list[ PermeabilityBaseType ] = field(
        default_factory=list,
        metadata={
            "name": "PermeabilityBase",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_delft_egg: list[ PorousDelftEggType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDelftEgg",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_drucker_prager: list[ PorousDruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_isotropic: list[ PorousElasticIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_orthotropic: list[ PorousElasticOrthotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticOrthotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_transverse_isotropic: list[ PorousElasticTransverseIsotropicType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticTransverseIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_extended_drucker_prager: list[ PorousExtendedDruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousExtendedDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_modified_cam_clay: list[ PorousModifiedCamClayType ] = field(
        default_factory=list,
        metadata={
            "name": "PorousModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    pressure_porosity: list[ PressurePorosityType ] = field(
        default_factory=list,
        metadata={
            "name": "PressurePorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_permeability: list[ ProppantPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_porosity: list[ ProppantPorosityType ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantPorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_slurry_fluid: list[ ProppantSlurryFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantSlurryFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_solid_proppant_permeability: list[ ProppantSolidProppantPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantSolidProppantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_brine: list[ ReactiveBrineType ] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveBrine",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_brine_thermal: list[ ReactiveBrineThermalType ] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveBrineThermal",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_constant_thermal_conductivity: list[ SinglePhaseConstantThermalConductivityType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseConstantThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    slip_dependent_permeability: list[ SlipDependentPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "SlipDependentPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_internal_energy: list[ SolidInternalEnergyType ] = field(
        default_factory=list,
        metadata={
            "name": "SolidInternalEnergy",
            "type": "Element",
            "namespace": "",
        },
    )
    table_capillary_pressure: list[ TableCapillaryPressureType ] = field(
        default_factory=list,
        metadata={
            "name": "TableCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    table_relative_permeability: list[ TableRelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "TableRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    table_relative_permeability_hysteresis: list[ TableRelativePermeabilityHysteresisType ] = field(
        default_factory=list,
        metadata={
            "name": "TableRelativePermeabilityHysteresis",
            "type": "Element",
            "namespace": "",
        },
    )
    thermal_compressible_single_phase_fluid: list[ ThermalCompressibleSinglePhaseFluidType ] = field(
        default_factory=list,
        metadata={
            "name": "ThermalCompressibleSinglePhaseFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_baker_relative_permeability: list[ VanGenuchtenBakerRelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenBakerRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_capillary_pressure: list[ VanGenuchtenCapillaryPressureType ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_stone2_relative_permeability: list[ VanGenuchtenStone2RelativePermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenStone2RelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    visco_drucker_prager: list[ ViscoDruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "ViscoDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    visco_extended_drucker_prager: list[ ViscoExtendedDruckerPragerType ] = field(
        default_factory=list,
        metadata={
            "name": "ViscoExtendedDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    visco_modified_cam_clay: list[ ViscoModifiedCamClayType ] = field(
        default_factory=list,
        metadata={
            "name": "ViscoModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    willis_richards_permeability: list[ WillisRichardsPermeabilityType ] = field(
        default_factory=list,
        metadata={
            "name": "WillisRichardsPermeability",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class ElasticFirstOrderSemtype:

    class Meta:
        name = "ElasticFirstOrderSEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    dt_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "dtSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    enable_lifo: str = field(
        default="0",
        metadata={
            "name": "enableLifo",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    forward: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    lifo_on_device: str = field(
        default="-80",
        metadata={
            "name": "lifoOnDevice",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_on_host: str = field(
        default="-80",
        metadata={
            "name": "lifoOnHost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_size: str = field(
        default="2147483647",
        metadata={
            "name": "lifoSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    linear_dasgeometry: str = field(
        default="{{0}}",
        metadata={
            "name":
            "linearDASGeometry",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "outputSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    receiver_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "receiverCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    ricker_order: str = field(
        default="2",
        metadata={
            "name": "rickerOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    save_fields: str = field(
        default="0",
        metadata={
            "name": "saveFields",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    shot_index: str = field(
        default="0",
        metadata={
            "name": "shotIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "sourceCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_source_delay: str = field(
        default="-1",
        metadata={
            "name": "timeSourceDelay",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_source_frequency: str = field(
        default="0",
        metadata={
            "name": "timeSourceFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElasticSemtype:

    class Meta:
        name = "ElasticSEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    dt_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "dtSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    enable_lifo: str = field(
        default="0",
        metadata={
            "name": "enableLifo",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    forward: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    lifo_on_device: str = field(
        default="-80",
        metadata={
            "name": "lifoOnDevice",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_on_host: str = field(
        default="-80",
        metadata={
            "name": "lifoOnHost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    lifo_size: str = field(
        default="2147483647",
        metadata={
            "name": "lifoSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    linear_dasgeometry: str = field(
        default="{{0}}",
        metadata={
            "name":
            "linearDASGeometry",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_seismo_trace: str = field(
        default="0",
        metadata={
            "name": "outputSeismoTrace",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    receiver_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "receiverCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    ricker_order: str = field(
        default="2",
        metadata={
            "name": "rickerOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    save_fields: str = field(
        default="0",
        metadata={
            "name": "saveFields",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    shot_index: str = field(
        default="0",
        metadata={
            "name": "shotIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name":
            "sourceCoordinates",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_force: str = field(
        default="{0,0,0}",
        metadata={
            "name":
            "sourceForce",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    source_moment: str = field(
        default="{1,1,1,0,0,0}",
        metadata={
            "name":
            "sourceMoment",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){5}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_source_delay: str = field(
        default="-1",
        metadata={
            "name": "timeSourceDelay",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_source_frequency: str = field(
        default="0",
        metadata={
            "name": "timeSourceFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ElementRegionsType:
    cell_element_region: list[ CellElementRegionType ] = field(
        default_factory=list,
        metadata={
            "name": "CellElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )
    surface_element_region: list[ SurfaceElementRegionType ] = field(
        default_factory=list,
        metadata={
            "name": "SurfaceElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )
    well_element_region: list[ WellElementRegionType ] = field(
        default_factory=list,
        metadata={
            "name": "WellElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class EmbeddedSurfaceGeneratorType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    fracture_region: str = field(
        default="FractureRegion",
        metadata={
            "name": "fractureRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    mpi_comm_order: str = field(
        default="0",
        metadata={
            "name": "mpiCommOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_objects: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetObjects",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class FieldSpecificationsType:
    aquifer: list[ AquiferType ] = field(
        default_factory=list,
        metadata={
            "name": "Aquifer",
            "type": "Element",
            "namespace": "",
        },
    )
    dirichlet: list[ DirichletType ] = field(
        default_factory=list,
        metadata={
            "name": "Dirichlet",
            "type": "Element",
            "namespace": "",
        },
    )
    field_specification: list[ FieldSpecificationType ] = field(
        default_factory=list,
        metadata={
            "name": "FieldSpecification",
            "type": "Element",
            "namespace": "",
        },
    )
    hydrostatic_equilibrium: list[ HydrostaticEquilibriumType ] = field(
        default_factory=list,
        metadata={
            "name": "HydrostaticEquilibrium",
            "type": "Element",
            "namespace": "",
        },
    )
    pml: list[ Pmltype ] = field(
        default_factory=list,
        metadata={
            "name": "PML",
            "type": "Element",
            "namespace": "",
        },
    )
    source_flux: list[ SourceFluxType ] = field(
        default_factory=list,
        metadata={
            "name": "SourceFlux",
            "type": "Element",
            "namespace": "",
        },
    )
    traction: list[ TractionType ] = field(
        default_factory=list,
        metadata={
            "name": "Traction",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class FiniteElementsType:
    finite_element_space: list[ FiniteElementSpaceType ] = field(
        default_factory=list,
        metadata={
            "name": "FiniteElementSpace",
            "type": "Element",
            "namespace": "",
        },
    )
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class FiniteVolumeType:
    hybrid_mimetic_discretization: list[ HybridMimeticDiscretizationType ] = field(
        default_factory=list,
        metadata={
            "name": "HybridMimeticDiscretization",
            "type": "Element",
            "namespace": "",
        },
    )
    two_point_flux_approximation: list[ TwoPointFluxApproximationType ] = field(
        default_factory=list,
        metadata={
            "name": "TwoPointFluxApproximation",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class FlowProppantTransportType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    proppant_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "proppantSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class FunctionsType:
    composite_function: list[ CompositeFunctionType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositeFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    multivariable_table_function: list[ MultivariableTableFunctionType ] = field(
        default_factory=list,
        metadata={
            "name": "MultivariableTableFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    symbolic_function: list[ SymbolicFunctionType ] = field(
        default_factory=list,
        metadata={
            "name": "SymbolicFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    table_function: list[ TableFunctionType ] = field(
        default_factory=list,
        metadata={
            "name": "TableFunction",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class GeometryType:
    box: list[ BoxType ] = field(
        default_factory=list,
        metadata={
            "name": "Box",
            "type": "Element",
            "namespace": "",
        },
    )
    custom_polar_object: list[ CustomPolarObjectType ] = field(
        default_factory=list,
        metadata={
            "name": "CustomPolarObject",
            "type": "Element",
            "namespace": "",
        },
    )
    cylinder: list[ CylinderType ] = field(
        default_factory=list,
        metadata={
            "name": "Cylinder",
            "type": "Element",
            "namespace": "",
        },
    )
    disc: list[ DiscType ] = field(
        default_factory=list,
        metadata={
            "name": "Disc",
            "type": "Element",
            "namespace": "",
        },
    )
    rectangle: list[ RectangleType ] = field(
        default_factory=list,
        metadata={
            "name": "Rectangle",
            "type": "Element",
            "namespace": "",
        },
    )
    thick_plane: list[ ThickPlaneType ] = field(
        default_factory=list,
        metadata={
            "name": "ThickPlane",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class HydrofractureType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_matrix_poroelastic: str = field(
        default="0",
        metadata={
            "name": "isMatrixPoroelastic",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_num_resolves: str = field(
        default="10",
        metadata={
            "name": "maxNumResolves",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    surface_generator_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "surfaceGeneratorName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class IncludedType:
    file: list[ FileType ] = field(
        default_factory=list,
        metadata={
            "name": "File",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class InternalWellType:
    perforation: list[ PerforationType ] = field(
        default_factory=list,
        metadata={
            "name": "Perforation",
            "type": "Element",
            "namespace": "",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    min_element_length: str = field(
        default="0.001",
        metadata={
            "name": "minElementLength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_segment_length: str = field(
        default="0.01",
        metadata={
            "name": "minSegmentLength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    num_elements_per_segment: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "numElementsPerSegment",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    polyline_node_coords: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "polylineNodeCoords",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    polyline_segment_conn: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "polylineSegmentConn",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*\}\s*",
        },
    )
    radius: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    well_controls_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellControlsName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    well_region_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellRegionName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class LagrangianContactType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    fracture_region_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fractureRegionName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    stabilization_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "stabilizationName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class LaplaceFemtype:

    class Meta:
        name = "LaplaceFEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    field_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_integration_option: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|SteadyState|ImplicitTransient",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultiphasePoromechanicsReservoirType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    well_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class MultiphasePoromechanicsType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    stabilization_multiplier: str = field(
        default="1",
        metadata={
            "name": "stabilizationMultiplier",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stabilization_region_names: str = field(
        default="{}",
        metadata={
            "name": "stabilizationRegionNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    stabilization_type: str = field(
        default="None",
        metadata={
            "name": "stabilizationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|None|Global|Local",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class OutputsType:
    blueprint: list[ BlueprintType ] = field(
        default_factory=list,
        metadata={
            "name": "Blueprint",
            "type": "Element",
            "namespace": "",
        },
    )
    chombo_io: list[ ChomboIotype ] = field(
        default_factory=list,
        metadata={
            "name": "ChomboIO",
            "type": "Element",
            "namespace": "",
        },
    )
    python: list[ PythonType ] = field(
        default_factory=list,
        metadata={
            "name": "Python",
            "type": "Element",
            "namespace": "",
        },
    )
    restart: list[ RestartType ] = field(
        default_factory=list,
        metadata={
            "name": "Restart",
            "type": "Element",
            "namespace": "",
        },
    )
    silo: list[ SiloType ] = field(
        default_factory=list,
        metadata={
            "name": "Silo",
            "type": "Element",
            "namespace": "",
        },
    )
    time_history: list[ TimeHistoryType ] = field(
        default_factory=list,
        metadata={
            "name": "TimeHistory",
            "type": "Element",
            "namespace": "",
        },
    )
    vtk: list[ Vtktype ] = field(
        default_factory=list,
        metadata={
            "name": "VTK",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class ParametersType:
    parameter: list[ ParameterType ] = field(
        default_factory=list,
        metadata={
            "name": "Parameter",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class ParticleRegionsType:
    particle_region: list[ ParticleRegionType ] = field(
        default_factory=list,
        metadata={
            "name": "ParticleRegion",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class PeriodicEventType:
    halt_event: list[ "HaltEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[ "PeriodicEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list[ SoloEventType ] = field(
        default_factory=list,
        metadata={
            "name": "SoloEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    begin_time: str = field(
        default="0",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    cycle_frequency: str = field(
        default="1",
        metadata={
            "name": "cycleFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    end_time: str = field(
        default="1e+100",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    final_dt_stretch: str = field(
        default="0.001",
        metadata={
            "name": "finalDtStretch",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    force_dt: str = field(
        default="-1",
        metadata={
            "name": "forceDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    function: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_event_dt: str = field(
        default="-1",
        metadata={
            "name": "maxEventDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    object_value: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "object",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    set: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    stat: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_exact_start_stop: str = field(
        default="1",
        metadata={
            "name": "targetExactStartStop",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_exact_timestep: str = field(
        default="1",
        metadata={
            "name": "targetExactTimestep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    threshold: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_frequency: str = field(
        default="-1",
        metadata={
            "name": "timeFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PhaseFieldDamageFemtype:

    class Meta:
        name = "PhaseFieldDamageFEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    damage_upper_bound: str = field(
        default="1.5",
        metadata={
            "name": "damageUpperBound",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    field_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    irreversibility_flag: str = field(
        default="0",
        metadata={
            "name": "irreversibilityFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    local_dissipation: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "localDissipation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|Linear|Quadratic",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_integration_option: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|SteadyState|ImplicitTransient|ExplicitTransient",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class PhaseFieldFractureType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    damage_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "damageSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ProppantTransportType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    bridging_factor: str = field(
        default="0",
        metadata={
            "name": "bridgingFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    critical_shields_number: str = field(
        default="0",
        metadata={
            "name": "criticalShieldsNumber",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    friction_coefficient: str = field(
        default="0.03",
        metadata={
            "name": "frictionCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_proppant_concentration: str = field(
        default="0.6",
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    proppant_density: str = field(
        default="2500",
        metadata={
            "name": "proppantDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    proppant_diameter: str = field(
        default="0.0004",
        metadata={
            "name": "proppantDiameter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    update_proppant_packing: str = field(
        default="0",
        metadata={
            "name": "updateProppantPacking",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class ReactiveCompositionalMultiphaseObltype:

    class Meta:
        name = "ReactiveCompositionalMultiphaseOBLType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    obloperators_table_file: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "OBLOperatorsTableFile",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    allow_local_oblchopping: str = field(
        default="1",
        metadata={
            "name": "allowLocalOBLChopping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    component_names: str = field(
        default="{}",
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    enable_energy_balance: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "enableEnergyBalance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_comp_fraction_change: str = field(
        default="1",
        metadata={
            "name": "maxCompFractionChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    num_components: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "numComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    num_phases: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "numPhases",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    trans_mult_exp: str = field(
        default="1",
        metadata={
            "name": "transMultExp",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_dartsl2_norm: str = field(
        default="1",
        metadata={
            "name": "useDARTSL2Norm",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseFvmtype:

    class Meta:
        name = "SinglePhaseFVMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseHybridFvmtype:

    class Meta:
        name = "SinglePhaseHybridFVMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhasePoromechanicsConformingFracturesType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    lagrangian_contact_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "LagrangianContactSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhasePoromechanicsEmbeddedFracturesType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    fractures_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fracturesSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhasePoromechanicsReservoirType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    well_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhasePoromechanicsType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseProppantFvmtype:

    class Meta:
        name = "SinglePhaseProppantFVMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="1",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_absolute_pressure_change: str = field(
        default="-1",
        metadata={
            "name": "maxAbsolutePressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseReservoirPoromechanicsType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_thermal: str = field(
        default="0",
        metadata={
            "name": "isThermal",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    reservoir_and_wells_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseReservoirType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    flow_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    well_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SinglePhaseWellType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    well_controls: list[ WellControlsType ] = field(
        default_factory=list,
        metadata={
            "name": "WellControls",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsEmbeddedFracturesType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    fracture_region_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fractureRegionName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    use_static_condensation: str = field(
        default="0",
        metadata={
            "name": "useStaticCondensation",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsLagrangianSsletype:

    class Meta:
        name = "SolidMechanicsLagrangianSSLEType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: str = field(
        default="NOCONTACT",
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    mass_damping: str = field(
        default="0",
        metadata={
            "name": "massDamping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_num_resolves: str = field(
        default="10",
        metadata={
            "name": "maxNumResolves",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    newmark_beta: str = field(
        default="0.25",
        metadata={
            "name": "newmarkBeta",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    newmark_gamma: str = field(
        default="0.5",
        metadata={
            "name": "newmarkGamma",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stiffness_damping: str = field(
        default="0",
        metadata={
            "name": "stiffnessDamping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    strain_theory: str = field(
        default="0",
        metadata={
            "name": "strainTheory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    surface_generator_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "surfaceGeneratorName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_integration_option: str = field(
        default="ExplicitDynamic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsLagrangianFemtype:

    class Meta:
        name = "SolidMechanics_LagrangianFEMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: str = field(
        default="NOCONTACT",
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    mass_damping: str = field(
        default="0",
        metadata={
            "name": "massDamping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_num_resolves: str = field(
        default="10",
        metadata={
            "name": "maxNumResolves",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    newmark_beta: str = field(
        default="0.25",
        metadata={
            "name": "newmarkBeta",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    newmark_gamma: str = field(
        default="0.5",
        metadata={
            "name": "newmarkGamma",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stiffness_damping: str = field(
        default="0",
        metadata={
            "name": "stiffnessDamping",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    strain_theory: str = field(
        default="0",
        metadata={
            "name": "strainTheory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    surface_generator_name: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "surfaceGeneratorName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_integration_option: str = field(
        default="ExplicitDynamic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SolidMechanicsMpmtype:

    class Meta:
        name = "SolidMechanics_MPMType"

    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    boundary_condition_types: str = field(
        default="{0}",
        metadata={
            "name": "boundaryConditionTypes",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    box_average_history: str = field(
        default="0",
        metadata={
            "name": "boxAverageHistory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_gap_correction: str = field(
        default="0",
        metadata={
            "name": "contactGapCorrection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    cpdi_domain_scaling: str = field(
        default="0",
        metadata={
            "name": "cpdiDomainScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    damage_field_partitioning: str = field(
        default="0",
        metadata={
            "name": "damageFieldPartitioning",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    discretization: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    f_table_interp_type: str = field(
        default="0",
        metadata={
            "name": "fTableInterpType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    f_table_path: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "fTablePath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    friction_coefficient: str = field(
        default="0",
        metadata={
            "name": "frictionCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    needs_neighbor_list: str = field(
        default="0",
        metadata={
            "name": "needsNeighborList",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    neighbor_radius: str = field(
        default="-1",
        metadata={
            "name": "neighborRadius",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    plane_strain: str = field(
        default="0",
        metadata={
            "name": "planeStrain",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    prescribed_bc_table: str = field(
        default="0",
        metadata={
            "name": "prescribedBcTable",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    prescribed_boundary_ftable: str = field(
        default="0",
        metadata={
            "name": "prescribedBoundaryFTable",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    reaction_history: str = field(
        default="0",
        metadata={
            "name": "reactionHistory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    separability_min_damage: str = field(
        default="0.5",
        metadata={
            "name": "separabilityMinDamage",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    solver_profiling: str = field(
        default="0",
        metadata={
            "name": "solverProfiling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    surface_detection: str = field(
        default="0",
        metadata={
            "name": "surfaceDetection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    time_integration_option: str = field(
        default="ExplicitDynamic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    treat_fully_damaged_as_single_field: str = field(
        default="1",
        metadata={
            "name": "treatFullyDamagedAsSingleField",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_damage_as_surface_flag: str = field(
        default="0",
        metadata={
            "name": "useDamageAsSurfaceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class SurfaceGeneratorType:
    linear_solver_parameters: list[ LinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[ NonlinearSolverParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    fracture_region: str = field(
        default="Fracture",
        metadata={
            "name": "fractureRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    mpi_comm_order: str = field(
        default="0",
        metadata={
            "name": "mpiCommOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    node_based_sif: str = field(
        default="0",
        metadata={
            "name": "nodeBasedSIF",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    rock_toughness: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "rockToughness",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class TasksType:
    compositional_multiphase_reservoir_poromechanics_initialization: list[
        CompositionalMultiphaseReservoirPoromechanicsInitializationType ] = field(
            default_factory=list,
            metadata={
                "name": "CompositionalMultiphaseReservoirPoromechanicsInitialization",
                "type": "Element",
                "namespace": "",
            },
        )
    compositional_multiphase_statistics: list[ CompositionalMultiphaseStatisticsType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics_initialization: list[ MultiphasePoromechanicsInitializationType ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    pvtdriver: list[ PvtdriverType ] = field(
        default_factory=list,
        metadata={
            "name": "PVTDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    pack_collection: list[ PackCollectionType ] = field(
        default_factory=list,
        metadata={
            "name": "PackCollection",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_fluid_driver: list[ ReactiveFluidDriverType ] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveFluidDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    relperm_driver: list[ RelpermDriverType ] = field(
        default_factory=list,
        metadata={
            "name": "RelpermDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_initialization: list[ SinglePhasePoromechanicsInitializationType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_initialization: list[
        SinglePhaseReservoirPoromechanicsInitializationType ] = field(
            default_factory=list,
            metadata={
                "name": "SinglePhaseReservoirPoromechanicsInitialization",
                "type": "Element",
                "namespace": "",
            },
        )
    single_phase_statistics: list[ SinglePhaseStatisticsType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_state_reset: list[ SolidMechanicsStateResetType ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsStateReset",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_statistics: list[ SolidMechanicsStatisticsType ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    triaxial_driver: list[ TriaxialDriverType ] = field(
        default_factory=list,
        metadata={
            "name": "TriaxialDriver",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class CrusherType:

    class Meta:
        name = "crusherType"

    run: list[ RunType ] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class LassenType:

    class Meta:
        name = "lassenType"

    run: list[ RunType ] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class QuartzType:

    class Meta:
        name = "quartzType"

    run: list[ RunType ] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class BenchmarksType:
    crusher: list[ CrusherType ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    lassen: list[ LassenType ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    quartz: list[ QuartzType ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class HaltEventType:
    halt_event: list[ "HaltEventType" ] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[ PeriodicEventType ] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list[ SoloEventType ] = field(
        default_factory=list,
        metadata={
            "name": "SoloEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    begin_time: str = field(
        default="0",
        metadata={
            "name": "beginTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    end_time: str = field(
        default="1e+100",
        metadata={
            "name": "endTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    final_dt_stretch: str = field(
        default="0.001",
        metadata={
            "name": "finalDtStretch",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    force_dt: str = field(
        default="-1",
        metadata={
            "name": "forceDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_event_dt: str = field(
        default="-1",
        metadata={
            "name": "maxEventDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_runtime: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "maxRuntime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    target_exact_start_stop: str = field(
        default="1",
        metadata={
            "name": "targetExactStartStop",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class InternalMeshType:
    internal_well: list[ InternalWellType ] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    cell_block_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "cellBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    element_types: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "elementTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    nx: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    ny: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    nz: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    position_tolerance: str = field(
        default="1e-10",
        metadata={
            "name": "positionTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    triangle_pattern: str = field(
        default="0",
        metadata={
            "name": "trianglePattern",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    x_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "xBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    x_coords: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "xCoords",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    y_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "yBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    y_coords: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "yCoords",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "zBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_coords: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "zCoords",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class InternalWellboreType:
    internal_well: list[ InternalWellType ] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    auto_space_radial_elems: str = field(
        default="{-1}",
        metadata={
            "name":
            "autoSpaceRadialElems",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    cartesian_mapping_inner_radius: str = field(
        default="1e+99",
        metadata={
            "name": "cartesianMappingInnerRadius",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    cell_block_names: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "cellBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    element_types: Optional[ str ] = field(
        default=None,
        metadata={
            "name": "elementTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    hard_radial_coords: str = field(
        default="{0}",
        metadata={
            "name":
            "hardRadialCoords",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    nr: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    nt: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    nz: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        },
    )
    position_tolerance: str = field(
        default="1e-10",
        metadata={
            "name": "positionTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    r_bias: str = field(
        default="{-0.8}",
        metadata={
            "name":
            "rBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    radius: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    theta: Optional[ str ] = field(
        default=None,
        metadata={
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    trajectory: str = field(
        default="{{0}}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    triangle_pattern: str = field(
        default="0",
        metadata={
            "name": "trianglePattern",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_cartesian_outer_boundary: str = field(
        default="1000000",
        metadata={
            "name": "useCartesianOuterBoundary",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    x_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "xBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    y_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "yBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_bias: str = field(
        default="{1}",
        metadata={
            "name":
            "zBias",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_coords: Optional[ str ] = field(
        default=None,
        metadata={
            "name":
            "zCoords",
            "type":
            "Attribute",
            "required":
            True,
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class NumericalMethodsType:
    finite_elements: list[ FiniteElementsType ] = field(
        default_factory=list,
        metadata={
            "name": "FiniteElements",
            "type": "Element",
            "namespace": "",
        },
    )
    finite_volume: list[ FiniteVolumeType ] = field(
        default_factory=list,
        metadata={
            "name": "FiniteVolume",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class SolversType:
    acoustic_first_order_sem: list[ AcousticFirstOrderSemtype ] = field(
        default_factory=list,
        metadata={
            "name": "AcousticFirstOrderSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_sem: list[ AcousticSemtype ] = field(
        default_factory=list,
        metadata={
            "name": "AcousticSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_vtisem: list[ AcousticVtisemtype ] = field(
        default_factory=list,
        metadata={
            "name": "AcousticVTISEM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_fvm: list[ CompositionalMultiphaseFvmtype ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_hybrid_fvm: list[ CompositionalMultiphaseHybridFvmtype ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseHybridFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir: list[ CompositionalMultiphaseReservoirType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir_poromechanics: list[ CompositionalMultiphaseReservoirPoromechanicsType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoirPoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_well: list[ CompositionalMultiphaseWellType ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseWell",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_first_order_sem: list[ ElasticFirstOrderSemtype ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticFirstOrderSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_sem: list[ ElasticSemtype ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    embedded_surface_generator: list[ EmbeddedSurfaceGeneratorType ] = field(
        default_factory=list,
        metadata={
            "name": "EmbeddedSurfaceGenerator",
            "type": "Element",
            "namespace": "",
        },
    )
    flow_proppant_transport: list[ FlowProppantTransportType ] = field(
        default_factory=list,
        metadata={
            "name": "FlowProppantTransport",
            "type": "Element",
            "namespace": "",
        },
    )
    hydrofracture: list[ HydrofractureType ] = field(
        default_factory=list,
        metadata={
            "name": "Hydrofracture",
            "type": "Element",
            "namespace": "",
        },
    )
    lagrangian_contact: list[ LagrangianContactType ] = field(
        default_factory=list,
        metadata={
            "name": "LagrangianContact",
            "type": "Element",
            "namespace": "",
        },
    )
    laplace_fem: list[ LaplaceFemtype ] = field(
        default_factory=list,
        metadata={
            "name": "LaplaceFEM",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics: list[ MultiphasePoromechanicsType ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics_reservoir: list[ MultiphasePoromechanicsReservoirType ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    phase_field_damage_fem: list[ PhaseFieldDamageFemtype ] = field(
        default_factory=list,
        metadata={
            "name": "PhaseFieldDamageFEM",
            "type": "Element",
            "namespace": "",
        },
    )
    phase_field_fracture: list[ PhaseFieldFractureType ] = field(
        default_factory=list,
        metadata={
            "name": "PhaseFieldFracture",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_transport: list[ ProppantTransportType ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantTransport",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_compositional_multiphase_obl: list[ ReactiveCompositionalMultiphaseObltype ] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveCompositionalMultiphaseOBL",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_fvm: list[ SinglePhaseFvmtype ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_hybrid_fvm: list[ SinglePhaseHybridFvmtype ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseHybridFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics: list[ SinglePhasePoromechanicsType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures: list[ SinglePhasePoromechanicsConformingFracturesType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_embedded_fractures: list[ SinglePhasePoromechanicsEmbeddedFracturesType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsEmbeddedFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_reservoir: list[ SinglePhasePoromechanicsReservoirType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_proppant_fvm: list[ SinglePhaseProppantFvmtype ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseProppantFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir: list[ SinglePhaseReservoirType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics: list[ SinglePhaseReservoirPoromechanicsType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_well: list[ SinglePhaseWellType ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseWell",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_embedded_fractures: list[ SolidMechanicsEmbeddedFracturesType ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsEmbeddedFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_lagrangian_ssle: list[ SolidMechanicsLagrangianSsletype ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsLagrangianSSLE",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_lagrangian_fem: list[ SolidMechanicsLagrangianFemtype ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanics_LagrangianFEM",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_mpm: list[ SolidMechanicsMpmtype ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanics_MPM",
            "type": "Element",
            "namespace": "",
        },
    )
    surface_generator: list[ SurfaceGeneratorType ] = field(
        default_factory=list,
        metadata={
            "name": "SurfaceGenerator",
            "type": "Element",
            "namespace": "",
        },
    )
    gravity_vector: str = field(
        default="{0,0,-9.81}",
        metadata={
            "name":
            "gravityVector",
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )


@dataclass
class VtkmeshType:

    class Meta:
        name = "VTKMeshType"

    internal_well: list[ InternalWellType ] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    face_blocks: str = field(
        default="{}",
        metadata={
            "name": "faceBlocks",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    field_names_in_geosx: str = field(
        default="{}",
        metadata={
            "name": "fieldNamesInGEOSX",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    fields_to_import: str = field(
        default="{}",
        metadata={
            "name": "fieldsToImport",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    file: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^*?<>\|:\";,\s]*\s*",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    main_block_name: str = field(
        default="main",
        metadata={
            "name": "mainBlockName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    nodeset_names: str = field(
        default="{}",
        metadata={
            "name": "nodesetNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    partition_method: str = field(
        default="parmetis",
        metadata={
            "name": "partitionMethod",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|parmetis|ptscotch",
        },
    )
    partition_refinement: str = field(
        default="1",
        metadata={
            "name": "partitionRefinement",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    region_attribute: str = field(
        default="attribute",
        metadata={
            "name": "regionAttribute",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/]*",
        },
    )
    scale: str = field(
        default="{1,1,1}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    surfacic_fields_in_geosx: str = field(
        default="{}",
        metadata={
            "name": "surfacicFieldsInGEOSX",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    surfacic_fields_to_import: str = field(
        default="{}",
        metadata={
            "name": "surfacicFieldsToImport",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/]*\s*,\s*)*[a-zA-Z0-9.\-_/]*\s*)?\}\s*",
        },
    )
    translate: str = field(
        default="{0,0,0}",
        metadata={
            "type":
            "Attribute",
            "pattern":
            r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    use_global_ids: str = field(
        default="0",
        metadata={
            "name": "useGlobalIds",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: Optional[ str ] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        },
    )


@dataclass
class EventsType:
    halt_event: list[ HaltEventType ] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[ PeriodicEventType ] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list[ SoloEventType ] = field(
        default_factory=list,
        metadata={
            "name": "SoloEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_cycle: str = field(
        default="2147483647",
        metadata={
            "name": "maxCycle",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_time: real64 = field(
        default=1.79769e308,
        metadata={
            "name": "maxTime",
            "type": "Attribute",
            # "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_time: str = field(
        default="0",
        metadata={
            "name": "minTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    time_output_format: str = field(
        default="seconds",
        metadata={
            "name": "timeOutputFormat",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|seconds|minutes|hours|days|years|full",
        },
    )


@dataclass
class MeshType:
    internal_mesh: list[ InternalMeshType ] = field(
        default_factory=list,
        metadata={
            "name": "InternalMesh",
            "type": "Element",
            "namespace": "",
        },
    )
    internal_wellbore: list[ InternalWellboreType ] = field(
        default_factory=list,
        metadata={
            "name": "InternalWellbore",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_mesh: list[ ParticleMeshType ] = field(
        default_factory=list,
        metadata={
            "name": "ParticleMesh",
            "type": "Element",
            "namespace": "",
        },
    )
    vtkmesh: list[ VtkmeshType ] = field(
        default_factory=list,
        metadata={
            "name": "VTKMesh",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class ProblemType:
    events: list[ EventsType ] = field(
        default_factory=list,
        metadata={
            "name": "Events",
            "type": "Element",
            "namespace": "",
        },
    )
    field_specifications: list[ FieldSpecificationsType ] = field(
        default_factory=list,
        metadata={
            "name": "FieldSpecifications",
            "type": "Element",
            "namespace": "",
        },
    )
    functions: list[ FunctionsType ] = field(
        default_factory=list,
        metadata={
            "name": "Functions",
            "type": "Element",
            "namespace": "",
        },
    )
    geometry: list[ GeometryType ] = field(
        default_factory=list,
        metadata={
            "name": "Geometry",
            "type": "Element",
            "namespace": "",
        },
    )
    mesh: list[ MeshType ] = field(
        default_factory=list,
        metadata={
            "name": "Mesh",
            "type": "Element",
            "namespace": "",
        },
    )
    numerical_methods: list[ NumericalMethodsType ] = field(
        default_factory=list,
        metadata={
            "name": "NumericalMethods",
            "type": "Element",
            "namespace": "",
        },
    )
    outputs: list[ OutputsType ] = field(
        default_factory=list,
        metadata={
            "name": "Outputs",
            "type": "Element",
            "namespace": "",
        },
    )
    solvers: list[ SolversType ] = field(
        default_factory=list,
        metadata={
            "name": "Solvers",
            "type": "Element",
            "namespace": "",
        },
    )
    tasks: list[ TasksType ] = field(
        default_factory=list,
        metadata={
            "name": "Tasks",
            "type": "Element",
            "namespace": "",
        },
    )
    constitutive: list[ ConstitutiveType ] = field(
        default_factory=list,
        metadata={
            "name": "Constitutive",
            "type": "Element",
            "namespace": "",
        },
    )
    element_regions: list[ ElementRegionsType ] = field(
        default_factory=list,
        metadata={
            "name": "ElementRegions",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_regions: list[ ParticleRegionsType ] = field(
        default_factory=list,
        metadata={
            "name": "ParticleRegions",
            "type": "Element",
            "namespace": "",
        },
    )
    included: list[ IncludedType ] = field(
        default_factory=list,
        metadata={
            "name": "Included",
            "type": "Element",
            "namespace": "",
        },
    )
    parameters: list[ ParametersType ] = field(
        default_factory=list,
        metadata={
            "name": "Parameters",
            "type": "Element",
            "namespace": "",
        },
    )
    benchmarks: list[ BenchmarksType ] = field(
        default_factory=list,
        metadata={
            "name": "Benchmarks",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class Problem( ProblemType ):
    pass
