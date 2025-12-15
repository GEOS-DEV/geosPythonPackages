#------------------------------------------------------------------
#
#  Generated on 2025-12-15 10:51
#  GEOS version: d5d87a5
#
#-------------------------------------------------------------------
from typing import Optional

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field


class AquiferType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    allow_all_phases_into_aquifer: str = field(
        default="0",
        metadata={
            "name": "allowAllPhasesIntoAquifer",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    aquifer_angle: str = field(
        metadata={
            "name": "aquiferAngle",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_elevation: str = field(
        metadata={
            "name": "aquiferElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_initial_pressure: str = field(
        metadata={
            "name": "aquiferInitialPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_inner_radius: str = field(
        metadata={
            "name": "aquiferInnerRadius",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_permeability: str = field(
        metadata={
            "name": "aquiferPermeability",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_porosity: str = field(
        metadata={
            "name": "aquiferPorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_thickness: str = field(
        metadata={
            "name": "aquiferThickness",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_total_compressibility: str = field(
        metadata={
            "name": "aquiferTotalCompressibility",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_water_density: str = field(
        metadata={
            "name": "aquiferWaterDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    aquifer_water_phase_component_fraction: str = field(
        default="{0}",
        metadata={
            "name": "aquiferWaterPhaseComponentFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    aquifer_water_viscosity: str = field(
        metadata={
            "name": "aquiferWaterViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    pressure_influence_function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "pressureInfluenceFunctionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BartonBandisType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    reference_aperture: str = field(
        default="1e-06",
        metadata={
            "name": "referenceAperture",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_normal_stress: str = field(
        metadata={
            "name": "referenceNormalStress",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BiotPorosityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_grain_bulk_modulus: str = field(
        metadata={
            "name": "defaultGrainBulkModulus",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_porosity_tec: str = field(
        default="0",
        metadata={
            "name": "defaultPorosityTEC",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_reference_porosity: str = field(
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    use_uniaxial_fixed_stress: str = field(
        default="0",
        metadata={
            "name": "useUniaxialFixedStress",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BlackOilFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    hydrocarbon_viscosity_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonViscosityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    surface_densities: str = field(
        metadata={
            "name": "surfaceDensities",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    table_files: str = field(
        default="{}",
        metadata={
            "name": "tableFiles",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BlockType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    scaling: str = field(
        default="frobenius",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|frobenius|user",
        },
    )
    schur_type: str = field(
        default="probing",
        metadata={
            "name": "schurType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|diagonal|probing|user",
        },
    )
    shape: str = field(
        default="DU",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|D|DU|LD|LDU",
        },
    )


class BlueprintType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
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
    output_full_quadrature_data: str = field(
        default="0",
        metadata={
            "name": "outputFullQuadratureData",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BoxType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    strike: str = field(
        default="-90",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    x_max: str = field(
        metadata={
            "name": "xMax",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    x_min: str = field(
        metadata={
            "name": "xMin",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BrooksCoreyBakerRelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    gas_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name": "gasOilRelPermExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "gasOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    water_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name": "waterOilRelPermExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "waterOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BrooksCoreyCapillaryPressureType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "name": "phaseCapPressureExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_entry_pressure: str = field(
        default="{1}",
        metadata={
            "name": "phaseEntryPressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BrooksCoreyRelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    phase_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name": "phaseRelPermExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "phaseRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class BrooksCoreyStone2RelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    gas_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name": "gasOilRelPermExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "gasOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    water_oil_rel_perm_exponent: str = field(
        default="{1}",
        metadata={
            "name": "waterOilRelPermExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "waterOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Co2BrineEzrokhiFluidType(BaseModel):
    class Meta:
        name = "CO2BrineEzrokhiFluidType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    check_phase_presence: str = field(
        default="0",
        metadata={
            "name": "checkPhasePresence",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    flash_model_para_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    solubility_table_names: str = field(
        default="{}",
        metadata={
            "name": "solubilityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Co2BrineEzrokhiThermalFluidType(BaseModel):
    class Meta:
        name = "CO2BrineEzrokhiThermalFluidType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    check_phase_presence: str = field(
        default="0",
        metadata={
            "name": "checkPhasePresence",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    flash_model_para_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    solubility_table_names: str = field(
        default="{}",
        metadata={
            "name": "solubilityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Co2BrinePhillipsFluidType(BaseModel):
    class Meta:
        name = "CO2BrinePhillipsFluidType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    check_phase_presence: str = field(
        default="0",
        metadata={
            "name": "checkPhasePresence",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    flash_model_para_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    solubility_table_names: str = field(
        default="{}",
        metadata={
            "name": "solubilityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Co2BrinePhillipsThermalFluidType(BaseModel):
    class Meta:
        name = "CO2BrinePhillipsThermalFluidType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    check_phase_presence: str = field(
        default="0",
        metadata={
            "name": "checkPhasePresence",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        default="{0}",
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    flash_model_para_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "flashModelParaFile",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    solubility_table_names: str = field(
        default="{}",
        metadata={
            "name": "solubilityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    anisotropy: str = field(
        default="{1,1,1}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    particle_diameter: str = field(
        metadata={
            "name": "particleDiameter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    sphericity: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CellElementRegionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    cell_blocks: str = field(
        metadata={
            "name": "cellBlocks",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    material_list: str = field(
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    mesh_body: Optional[str] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CellToCellDataCollectionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    mesh_body: str = field(
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CeramicDamageType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    compressive_strength: str = field(
        metadata={
            "name": "compressiveStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    crack_speed: str = field(
        metadata={
            "name": "crackSpeed",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    maximum_strength: str = field(
        metadata={
            "name": "maximumStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    tensile_strength: str = field(
        metadata={
            "name": "tensileStrength",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ChomboIotype(BaseModel):
    class Meta:
        name = "ChomboIOType"

    model_config = ConfigDict(defer_build=True)
    begin_cycle: str = field(
        metadata={
            "name": "beginCycle",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    child_directory: Optional[str] = field(
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
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    output_path: str = field(
        metadata={
            "name": "outputPath",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    use_chombo_pressures: str = field(
        default="0",
        metadata={
            "name": "useChomboPressures",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    wait_for_input: str = field(
        metadata={
            "name": "waitForInput",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositeFunctionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    expression: Optional[str] = field(
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    input_var_scale: str = field(
        default="{1}",
        metadata={
            "name": "inputVarScale",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    variable_names: str = field(
        default="{}",
        metadata={
            "name": "variableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    constant_phase_viscosity: str = field(
        default="{0}",
        metadata={
            "name": "constantPhaseViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseReservoirPoromechanicsConformingFracturesInitializationType(
    BaseModel
):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseReservoirPoromechanicsInitializationType(
    BaseModel
):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseStatisticsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalThreePhaseFluidLohrenzBrayClarkType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    flash_max_iterations: str = field(
        default="300",
        metadata={
            "name": "flashMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flash_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "flashTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    stability_max_iterations: str = field(
        default="300",
        metadata={
            "name": "stabilityMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    stability_threshold: str = field(
        default="-1e-08",
        metadata={
            "name": "stabilityThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stability_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "stabilityTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosity_mixing_rule: str = field(
        default="HerningZipperer",
        metadata={
            "name": "viscosityMixingRule",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    water_compressibility: str = field(
        metadata={
            "name": "waterCompressibility",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    water_density: str = field(
        metadata={
            "name": "waterDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    water_expansion_coefficient: str = field(
        default="0",
        metadata={
            "name": "waterExpansionCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_reference_pressure: str = field(
        metadata={
            "name": "waterReferencePressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    water_reference_temperature: str = field(
        default="293.15",
        metadata={
            "name": "waterReferenceTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_viscosity: str = field(
        metadata={
            "name": "waterViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    water_viscosity_compressibility: str = field(
        default="0",
        metadata={
            "name": "waterViscosityCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    water_viscosity_expansion_coefficient: str = field(
        default="0",
        metadata={
            "name": "waterViscosityExpansionCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalTwoPhaseFluidLohrenzBrayClarkType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    flash_max_iterations: str = field(
        default="300",
        metadata={
            "name": "flashMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flash_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "flashTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    stability_max_iterations: str = field(
        default="300",
        metadata={
            "name": "stabilityMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    stability_threshold: str = field(
        default="-1e-08",
        metadata={
            "name": "stabilityThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stability_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "stabilityTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    viscosity_mixing_rule: str = field(
        default="HerningZipperer",
        metadata={
            "name": "viscosityMixingRule",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalTwoPhaseFluidPhillipsBrineType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    flash_max_iterations: str = field(
        default="300",
        metadata={
            "name": "flashMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flash_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "flashTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    pressure_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "pressureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    salinity: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    salt_molar_weight: str = field(
        default="0.05844",
        metadata={
            "name": "saltMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stability_max_iterations: str = field(
        default="300",
        metadata={
            "name": "stabilityMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    stability_threshold: str = field(
        default="-1e-08",
        metadata={
            "name": "stabilityThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stability_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "stabilityTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "temperatureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    viscosity_mixing_rule: str = field(
        default="HerningZipperer",
        metadata={
            "name": "viscosityMixingRule",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    water_compressibility: str = field(
        default="4.5e-10",
        metadata={
            "name": "waterCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalTwoPhaseFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    constant_phase_viscosity: str = field(
        default="{0}",
        metadata={
            "name": "constantPhaseViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    flash_max_iterations: str = field(
        default="300",
        metadata={
            "name": "flashMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flash_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "flashTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    stability_max_iterations: str = field(
        default="300",
        metadata={
            "name": "stabilityMaxIterations",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    stability_threshold: str = field(
        default="-1e-08",
        metadata={
            "name": "stabilityThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    stability_tolerance: str = field(
        default="1e-08",
        metadata={
            "name": "stabilityTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalTwoPhaseKvalueFluidLohrenzBrayClarkType(BaseModel):
    class Meta:
        name = "CompositionalTwoPhaseKValueFluidLohrenzBrayClarkType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    k_value_tables: str = field(
        metadata={
            "name": "kValueTables",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    pressure_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "pressureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    temperature_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "temperatureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    viscosity_mixing_rule: str = field(
        default="HerningZipperer",
        metadata={
            "name": "viscosityMixingRule",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalTwoPhaseKvalueFluidPhillipsBrineType(BaseModel):
    class Meta:
        name = "CompositionalTwoPhaseKValueFluidPhillipsBrineType"

    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_acentric_factor: str = field(
        metadata={
            "name": "componentAcentricFactor",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_binary_coeff: str = field(
        default="{{0}}",
        metadata={
            "name": "componentBinaryCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    component_critical_pressure: str = field(
        metadata={
            "name": "componentCriticalPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_temperature: str = field(
        metadata={
            "name": "componentCriticalTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_critical_volume: str = field(
        default="{0}",
        metadata={
            "name": "componentCriticalVolume",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    component_volume_shift: str = field(
        default="{0}",
        metadata={
            "name": "componentVolumeShift",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    equations_of_state: str = field(
        metadata={
            "name": "equationsOfState",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    k_value_tables: str = field(
        metadata={
            "name": "kValueTables",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    pressure_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "pressureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    salinity: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    salt_molar_weight: str = field(
        default="0.05844",
        metadata={
            "name": "saltMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature_coordinates: str = field(
        default="{0}",
        metadata={
            "name": "temperatureCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    viscosity_mixing_rule: str = field(
        default="HerningZipperer",
        metadata={
            "name": "viscosityMixingRule",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    water_compressibility: str = field(
        default="4.5e-10",
        metadata={
            "name": "waterCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSinglePhaseFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    compressibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_viscosity: str = field(
        metadata={
            "name": "defaultViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    density_model_type: str = field(
        default="exponential",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidConstantPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidExponentialDecayPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidParallelPlatesPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidPressurePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidSlipDependentPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompressibleSolidWillisRichardsPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ConstantDiffusionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_phase_diffusivity_multipliers: str = field(
        default="{1}",
        metadata={
            "name": "defaultPhaseDiffusivityMultipliers",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    diffusivity_components: str = field(
        metadata={
            "name": "diffusivityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ConstantPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_components: str = field(
        metadata={
            "name": "permeabilityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CoulombType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    cohesion: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    friction_coefficient: str = field(
        metadata={
            "name": "frictionCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    shear_stiffness: str = field(
        default="0",
        metadata={
            "name": "shearStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CoupledType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    use_block_smoother: str = field(
        default="1",
        metadata={
            "name": "useBlockSmoother",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class CustomPolarObjectType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    center: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    coefficients: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    length_vector: str = field(
        metadata={
            "name": "lengthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    normal: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: str = field(
        metadata={
            "name": "widthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CylinderType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    first_face_center: str = field(
        metadata={
            "name": "firstFaceCenter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    inner_radius: str = field(
        default="-1",
        metadata={
            "name": "innerRadius",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    outer_radius: str = field(
        metadata={
            "name": "outerRadius",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    second_face_center: str = field(
        metadata={
            "name": "secondFaceCenter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DamageElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    critical_strain_energy: str = field(
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_compressive_strength: str = field(
        default="0",
        metadata={
            "name": "defaultCompressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_critical_fracture_energy: str = field(
        metadata={
            "name": "defaultCriticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "defaultDeltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    default_tensile_strength: str = field(
        default="0",
        metadata={
            "name": "defaultTensileStrength",
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
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: str = field(
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DamagePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bulk_permeability: str = field(
        metadata={
            "name": "bulkPermeability",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    damage_dependence_constant: str = field(
        metadata={
            "name": "damageDependenceConstant",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DamageSpectralElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    critical_strain_energy: str = field(
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_compressive_strength: str = field(
        default="0",
        metadata={
            "name": "defaultCompressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_critical_fracture_energy: str = field(
        metadata={
            "name": "defaultCriticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "defaultDeltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    default_tensile_strength: str = field(
        default="0",
        metadata={
            "name": "defaultTensileStrength",
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
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: str = field(
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DamageVolDevElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    critical_strain_energy: str = field(
        metadata={
            "name": "criticalStrainEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_compressive_strength: str = field(
        default="0",
        metadata={
            "name": "defaultCompressiveStrength",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_critical_fracture_energy: str = field(
        metadata={
            "name": "defaultCriticalFractureEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_delta_coefficient: str = field(
        default="-1",
        metadata={
            "name": "defaultDeltaCoefficient",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    default_tensile_strength: str = field(
        default="0",
        metadata={
            "name": "defaultTensileStrength",
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
    ext_driving_force_flag: str = field(
        default="0",
        metadata={
            "name": "extDrivingForceFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    length_scale: str = field(
        metadata={
            "name": "lengthScale",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DeadOilFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    hydrocarbon_viscosity_table_names: str = field(
        default="{}",
        metadata={
            "name": "hydrocarbonViscosityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    surface_densities: str = field(
        metadata={
            "name": "surfaceDensities",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    table_files: str = field(
        default="{}",
        metadata={
            "name": "tableFiles",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DelftEggType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DirichletType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    field_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DiscType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    center: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    length_vector: str = field(
        metadata={
            "name": "lengthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    normal: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    radius: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: str = field(
        metadata={
            "name": "widthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class DruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticIsotropicPressureDependentType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticOrthotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticTransverseIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ExponentialDecayPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    empirical_constant: str = field(
        metadata={
            "name": "empiricalConstant",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    initial_permeability: str = field(
        metadata={
            "name": "initialPermeability",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ExtendedDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class FieldSpecificationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    field_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class FileType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        }
    )


class FiniteElementSpaceType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    formulation: str = field(
        default="default",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|SEM|DG",
        },
    )
    order: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    use_high_order_quadrature_rule: str = field(
        default="0",
        metadata={
            "name": "useHighOrderQuadratureRule",
            "type": "Attribute",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class FrictionlessContactType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HaltEventType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    halt_event: list["HaltEventType"] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list["PeriodicEventType"] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list["SoloEventType"] = field(
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
    max_runtime: str = field(
        metadata={
            "name": "maxRuntime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    target: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HybridMimeticDiscretizationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    inner_product_type: str = field(
        metadata={
            "name": "innerProductType",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HydraulicApertureTableType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    aperture_table_name: str = field(
        metadata={
            "name": "apertureTableName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    aperture_tolerance: str = field(
        default="1e-09",
        metadata={
            "name": "apertureTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_aperture: str = field(
        default="1e-06",
        metadata={
            "name": "referenceAperture",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HydrofractureInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HydrostaticEquilibriumType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    datum_elevation: str = field(
        metadata={
            "name": "datumElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    datum_pressure: str = field(
        metadata={
            "name": "datumPressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    direction: str = field(
        default="{0,0,0}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    initial_phase_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "initialPhaseName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature_vs_elevation_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "temperatureVsElevationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class InvariantImmiscibleFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    check_pvttables_ranges: str = field(
        default="1",
        metadata={
            "name": "checkPVTTablesRanges",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    component_molar_weight: str = field(
        metadata={
            "name": "componentMolarWeight",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    component_names: str = field(
        metadata={
            "name": "componentNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    densities: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    viscosities: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class JfunctionCapillaryPressureType(BaseModel):
    class Meta:
        name = "JFunctionCapillaryPressureType"

    model_config = ConfigDict(defer_build=True)
    non_wetting_intermediate_jfunction_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "nonWettingIntermediateJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    permeability_direction: str = field(
        metadata={
            "name": "permeabilityDirection",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|XY|X|Y|Z",
        }
    )
    permeability_exponent: str = field(
        default="0.5",
        metadata={
            "name": "permeabilityExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    porosity_exponent: str = field(
        default="0.5",
        metadata={
            "name": "porosityExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    wetting_intermediate_jfunction_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "wettingIntermediateJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    wetting_non_wetting_jfunction_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "wettingNonWettingJFunctionTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class LinearIsotropicDispersionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    longitudinal_dispersivity: str = field(
        metadata={
            "name": "longitudinalDispersivity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MemoryStatsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    log_level: str = field(
        default="1",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_csv: str = field(
        default="1",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MetisType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    method: str = field(
        default="kway",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|kway|recursive",
        },
    )
    seed: str = field(
        default="2020",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    ufactor: str = field(
        default="30",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class ModifiedCamClayType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_csl_slope: str = field(
        default="1",
        metadata={
            "name": "defaultCslSlope",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MsRsbtype(BaseModel):
    class Meta:
        name = "MsRSBType"

    model_config = ConfigDict(defer_build=True)
    check_frequency: str = field(
        default="10",
        metadata={
            "name": "checkFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_iter: str = field(
        default="100",
        metadata={
            "name": "maxIter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    num_layers: str = field(
        default="3",
        metadata={
            "name": "numLayers",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    relaxation: str = field(
        default="0.666667",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    support_type: str = field(
        default="matching",
        metadata={
            "name": "supportType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|layers|matching",
        },
    )
    tolerance: str = field(
        default="0.001",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    update_frequency: str = field(
        default="10",
        metadata={
            "name": "updateFrequency",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class MultiPhaseConstantThermalConductivityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thermal_conductivity_components: str = field(
        metadata={
            "name": "thermalConductivityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiPhaseVolumeWeightedThermalConductivityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    phase_thermal_conductivity: str = field(
        metadata={
            "name": "phaseThermalConductivity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    rock_thermal_conductivity_components: str = field(
        metadata={
            "name": "rockThermalConductivityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiphasePoromechanicsConformingFracturesInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiphasePoromechanicsInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultivariableTableFunctionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    input_var_scale: str = field(
        default="{1}",
        metadata={
            "name": "inputVarScale",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class NonlinearSolverParametersType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    allow_non_converged: str = field(
        default="0",
        metadata={
            "name": "allowNonConverged",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    configuration_tolerance: str = field(
        default="0",
        metadata={
            "name": "configurationTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    line_search_residual_factor: str = field(
        default="1",
        metadata={
            "name": "lineSearchResidualFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    line_search_starting_iteration: str = field(
        default="0",
        metadata={
            "name": "lineSearchStartingIteration",
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
    min_time_step_increase_interval: str = field(
        default="10",
        metadata={
            "name": "minTimeStepIncreaseInterval",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    oscillation_check_depth: str = field(
        default="3",
        metadata={
            "name": "oscillationCheckDepth",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    oscillation_fraction: str = field(
        default="0.05",
        metadata={
            "name": "oscillationFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    oscillation_scaling: str = field(
        default="0",
        metadata={
            "name": "oscillationScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    oscillation_scaling_factor: str = field(
        default="0.5",
        metadata={
            "name": "oscillationScalingFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    oscillation_tolerance: str = field(
        default="0.01",
        metadata={
            "name": "oscillationTolerance",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    sequential_convergence_criterion: str = field(
        default="ResidualNorm",
        metadata={
            "name": "sequentialConvergenceCriterion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ResidualNorm|NumberOfNonlinearIterations|SolutionIncrements",
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


class NullModelType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Pmltype(BaseModel):
    class Meta:
        name = "PMLType"

    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    reflectivity: str = field(
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
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_max_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name": "thicknessMaxXYZ",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    thickness_min_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name": "thicknessMinXYZ",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    wave_speed_max_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name": "waveSpeedMaxXYZ",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    wave_speed_min_xyz: str = field(
        default="{-1,-1,-1}",
        metadata={
            "name": "waveSpeedMinXYZ",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    x_max: str = field(
        default="{3.40282e+38,3.40282e+38,3.40282e+38}",
        metadata={
            "name": "xMax",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    x_min: str = field(
        default="{-3.40282e+38,-3.40282e+38,-3.40282e+38}",
        metadata={
            "name": "xMin",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PvtdriverType(BaseModel):
    class Meta:
        name = "PVTDriverType"

    model_config = ConfigDict(defer_build=True)
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        },
    )
    feed_composition: str = field(
        metadata={
            "name": "feedComposition",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    fluid: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    output_mass_density: str = field(
        default="0",
        metadata={
            "name": "outputMassDensity",
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
    precision: str = field(
        default="4",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    pressure_control: str = field(
        metadata={
            "name": "pressureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    steps: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    temperature_control: str = field(
        metadata={
            "name": "temperatureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PackCollectionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    disable_coord_collection: str = field(
        default="0",
        metadata={
            "name": "disableCoordCollection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    field_name: str = field(
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    object_path: str = field(
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ParallelPlatesPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    transversal_permeability: str = field(
        default="-1",
        metadata={
            "name": "transversalPermeability",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ParameterType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    value: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ParticleFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    particle_settling_model: str = field(
        metadata={
            "name": "particleSettlingModel",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|Stokes|Intermediate|Turbulence",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ParticleMeshType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    header_file: str = field(
        metadata={
            "name": "headerFile",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        }
    )
    particle_block_names: str = field(
        metadata={
            "name": "particleBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    particle_file: str = field(
        metadata={
            "name": "particleFile",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        }
    )
    particle_types: str = field(
        metadata={
            "name": "particleTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ParticleRegionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    material_list: str = field(
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    mesh_body: Optional[str] = field(
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PerfectlyPlasticType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_bulk_modulus: str = field(
        default="-1",
        metadata={
            "name": "defaultBulkModulus",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PerforationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    distance_from_head: str = field(
        metadata={
            "name": "distanceFromHead",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    perf_status_table: str = field(
        default="{{0}}",
        metadata={
            "name": "perfStatusTable",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    perf_status_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "perfStatusTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    target_region: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    transmissibility: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDamageElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDamageSpectralElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDamageVolDevElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDelftEggCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDelftEggType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDruckerPragerCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticIsotropicCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticOrthotropicCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticOrthotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticTransverseIsotropicCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousElasticTransverseIsotropicType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousExtendedDruckerPragerCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousExtendedDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousModifiedCamClayCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousModifiedCamClayType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoDruckerPragerCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoExtendedDruckerPragerCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoExtendedDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoModifiedCamClayCarmanKozenyPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PorousViscoModifiedCamClayType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PressurePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    max_permeability: str = field(
        default="1",
        metadata={
            "name": "maxPermeability",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    pressure_dependence_constants: str = field(
        metadata={
            "name": "pressureDependenceConstants",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    pressure_model_type: str = field(
        default="Hyperbolic",
        metadata={
            "name": "pressureModelType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|Exponential|Hyperbolic",
        },
    )
    reference_permeability_components: str = field(
        metadata={
            "name": "referencePermeabilityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    reference_pressure: str = field(
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PressurePorosityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    compressibility: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_reference_porosity: str = field(
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    reference_pressure: str = field(
        metadata={
            "name": "referencePressure",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ProppantPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    max_proppant_concentration: str = field(
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    proppant_diameter: str = field(
        metadata={
            "name": "proppantDiameter",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ProppantPorosityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_reference_porosity: str = field(
        metadata={
            "name": "defaultReferencePorosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    max_proppant_concentration: str = field(
        metadata={
            "name": "maxProppantConcentration",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ProppantSlurryFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "name": "defaultComponentDensity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    default_component_viscosity: str = field(
        default="{0}",
        metadata={
            "name": "defaultComponentViscosity",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    default_compressibility: str = field(
        default="{0}",
        metadata={
            "name": "defaultCompressibility",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    flow_behavior_index: str = field(
        default="{0}",
        metadata={
            "name": "flowBehaviorIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    flow_consistency_index: str = field(
        default="{0}",
        metadata={
            "name": "flowConsistencyIndex",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ProppantSolidProppantPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    permeability_model_name: str = field(
        metadata={
            "name": "permeabilityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    porosity_model_name: str = field(
        metadata={
            "name": "porosityModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_internal_energy_model_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidInternalEnergyModelName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    solid_model_name: str = field(
        metadata={
            "name": "solidModelName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PythonType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RateAndStateFrictionAgingLawType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_a: str = field(
        metadata={
            "name": "defaultA",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_b: str = field(
        metadata={
            "name": "defaultB",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_dc: str = field(
        metadata={
            "name": "defaultDc",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_reference_friction_coefficient: str = field(
        metadata={
            "name": "defaultReferenceFrictionCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_reference_velocity: str = field(
        metadata={
            "name": "defaultReferenceVelocity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RateAndStateFrictionSlipLawType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_a: str = field(
        metadata={
            "name": "defaultA",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_b: str = field(
        metadata={
            "name": "defaultB",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_dc: str = field(
        metadata={
            "name": "defaultDc",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_reference_friction_coefficient: str = field(
        metadata={
            "name": "defaultReferenceFrictionCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_reference_velocity: str = field(
        metadata={
            "name": "defaultReferenceVelocity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    displacement_jump_threshold: str = field(
        default="2.22045e-16",
        metadata={
            "name": "displacementJumpThreshold",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ReactiveBrineThermalType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ReactiveBrineType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "name": "componentMolarWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_pvtpara_files: str = field(
        metadata={
            "name": "phasePVTParaFiles",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        }
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ReactiveFluidDriverType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        },
    )
    feed_composition: str = field(
        metadata={
            "name": "feedComposition",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    fluid: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    pressure_control: str = field(
        metadata={
            "name": "pressureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    steps: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    temperature_control: str = field(
        metadata={
            "name": "temperatureControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RectangleType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    dimensions: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    length_vector: str = field(
        metadata={
            "name": "lengthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    normal: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    origin: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    tolerance: str = field(
        default="1e-05",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    width_vector: str = field(
        metadata={
            "name": "widthVector",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RegionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    path_in_repository: str = field(
        metadata={
            "name": "pathInRepository",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RelpermDriverType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
    relperm: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    steps: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RestartType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
        default=None,
        metadata={
            "name": "childDirectory",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class RunType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    args: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    auto_partition: Optional[str] = field(
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
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
    scaling: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    tasks_per_node: str = field(
        metadata={
            "name": "tasksPerNode",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
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


class SiloType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsConformingFracturesAlminitializationType(
    BaseModel
):
    class Meta:
        name = (
            "SinglePhasePoromechanicsConformingFracturesALMInitializationType"
        )

    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsConformingFracturesInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsEmbeddedFracturesInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsConformingFracturesAlminitializationType(
    BaseModel
):
    class Meta:
        name = "SinglePhaseReservoirPoromechanicsConformingFracturesALMInitializationType"

    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsConformingFracturesInitializationType(
    BaseModel
):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsInitializationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_mechanics_statistics_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "solidMechanicsStatisticsName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseStatisticsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseThermalConductivityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_thermal_conductivity_components: str = field(
        metadata={
            "name": "defaultThermalConductivityComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    reference_temperature: str = field(
        default="0",
        metadata={
            "name": "referenceTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    thermal_conductivity_gradient_components: str = field(
        default="{0,0,0}",
        metadata={
            "name": "thermalConductivityGradientComponents",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SlipDependentPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    initial_permeability: str = field(
        metadata={
            "name": "initialPermeability",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    max_perm_multiplier: str = field(
        metadata={
            "name": "maxPermMultiplier",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    shear_disp_threshold: str = field(
        metadata={
            "name": "shearDispThreshold",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SmootherType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    num_sweeps: str = field(
        default="1",
        metadata={
            "name": "numSweeps",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    pre_or_post: str = field(
        default="both",
        metadata={
            "name": "preOrPost",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|pre|post|both",
        },
    )
    type_value: str = field(
        default="sgs",
        metadata={
            "name": "type",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|iluk|ilut|ick|ict|amg|mgr|block|direct|bgs|multiscale",
        },
    )


class SolidInternalEnergyType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    d_volumetric_heat_capacity_d_temperature: str = field(
        default="0",
        metadata={
            "name": "dVolumetricHeatCapacity_dTemperature",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reference_internal_energy: str = field(
        metadata={
            "name": "referenceInternalEnergy",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    reference_temperature: str = field(
        metadata={
            "name": "referenceTemperature",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    reference_volumetric_heat_capacity: str = field(
        metadata={
            "name": "referenceVolumetricHeatCapacity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsStateResetType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsStatisticsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SourceFluxStatisticsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    flux_names: str = field(
        default="{*}",
        metadata={
            "name": "fluxNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SourceFluxType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class StructuredType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    semicoarsening: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class SurfaceElementRegionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_aperture: str = field(
        metadata={
            "name": "defaultAperture",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    face_block: str = field(
        default="FractureSubRegion",
        metadata={
            "name": "faceBlock",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    material_list: str = field(
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    mesh_body: Optional[str] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SymbolicFunctionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    expression: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    input_var_scale: str = field(
        default="{1}",
        metadata={
            "name": "inputVarScale",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    variable_names: str = field(
        metadata={
            "name": "variableNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TableCapillaryPressureType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    non_wetting_intermediate_cap_pressure_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "nonWettingIntermediateCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    wetting_intermediate_cap_pressure_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "wettingIntermediateCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    wetting_non_wetting_cap_pressure_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "wettingNonWettingCapPressureTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TableFunctionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    coordinate_files: str = field(
        default="{}",
        metadata={
            "name": "coordinateFiles",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        },
    )
    coordinates: str = field(
        default="{0}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    input_var_names: str = field(
        default="{}",
        metadata={
            "name": "inputVarNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    input_var_scale: str = field(
        default="{1}",
        metadata={
            "name": "inputVarScale",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    interpolation: str = field(
        default="linear",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|linear|nearest|upper|lower",
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
    values: str = field(
        default="{0}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    voxel_file: Optional[str] = field(
        default=None,
        metadata={
            "name": "voxelFile",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TableRelativePermeabilityHysteresisType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    drainage_non_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageNonWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    drainage_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    drainage_wetting_non_wetting_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "drainageWettingNonWettingRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    imbibition_non_wetting_rel_perm_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "imbibitionNonWettingRelPermTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    imbibition_wetting_rel_perm_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "imbibitionWettingRelPermTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    three_phase_interpolator: str = field(
        default="BAKER",
        metadata={
            "name": "threePhaseInterpolator",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|BAKER|STONEII",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TableRelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    non_wetting_intermediate_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "nonWettingIntermediateRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    wetting_non_wetting_rel_perm_table_names: str = field(
        default="{}",
        metadata={
            "name": "wettingNonWettingRelPermTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ThermalCompressibleSinglePhaseFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    compressibility: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    default_viscosity: str = field(
        metadata={
            "name": "defaultViscosity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    density_model_type: str = field(
        default="exponential",
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
    specific_heat_capacity: str = field(
        default="0",
        metadata={
            "name": "specificHeatCapacity",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ThickPlaneType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    epsilon: str = field(
        default="-1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    normal: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    origin: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        }
    )
    thickness: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TimeHistoryType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
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
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    sources: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TractionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    bc_application_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "bcApplicationTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    error_set_mode: str = field(
        default="error",
        metadata={
            "name": "errorSetMode",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|silent|error|warning",
        },
    )
    function_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "functionName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
            "name": "inputStress",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){5}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    nodal_scale_flag: str = field(
        default="0",
        metadata={
            "name": "nodalScaleFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    object_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "objectPath",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    scale_set: str = field(
        default="{0}",
        metadata={
            "name": "scaleSet",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    set_names: str = field(
        metadata={
            "name": "setNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    traction_type: str = field(
        default="vector",
        metadata={
            "name": "tractionType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|vector|normal|stress",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TriaxialDriverType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    axial_control: str = field(
        metadata={
            "name": "axialControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    baseline: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        },
    )
    initial_stress: str = field(
        metadata={
            "name": "initialStress",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    material: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    mode: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|mixedControl|strainControl|stressControl",
        }
    )
    output: str = field(
        default="none",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    radial_control: str = field(
        metadata={
            "name": "radialControl",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    steps: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TwoPhaseImmiscibleFluidType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    density_table_names: str = field(
        default="{}",
        metadata={
            "name": "densityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    table_files: str = field(
        default="{}",
        metadata={
            "name": "tableFiles",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|\s*\{\s*(([^*?<>\|:";,\s]+\s*,\s*)*[^*?<>\|:";,\s]+\s*)?\}\s*',
        },
    )
    viscosity_table_names: str = field(
        default="{}",
        metadata={
            "name": "viscosityTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TwoPointFluxApproximationType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "pattern": r".*[\[\]`$].*|PPU|C1PPU|IHU|HU2PH",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class VtkhierarchicalDataSourceType(BaseModel):
    class Meta:
        name = "VTKHierarchicalDataSourceType"

    model_config = ConfigDict(defer_build=True)
    vtkhierarchical_data_source: list["VtkhierarchicalDataSourceType"] = field(
        default_factory=list,
        metadata={
            "name": "VTKHierarchicalDataSource",
            "type": "Element",
            "namespace": "",
        },
    )
    file: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class Vtktype(BaseModel):
    class Meta:
        name = "VTKType"

    model_config = ConfigDict(defer_build=True)
    child_directory: Optional[str] = field(
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    number_of_target_processes: str = field(
        default="1",
        metadata={
            "name": "numberOfTargetProcesses",
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
    write_face_elements_as3_d: str = field(
        default="0",
        metadata={
            "name": "writeFaceElementsAs3D",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class VanGenuchtenBakerRelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    gas_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name": "gasOilRelPermExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "gasOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    water_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name": "waterOilRelPermExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "waterOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class VanGenuchtenCapillaryPressureType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
            "name": "phaseCapPressureExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_cap_pressure_multiplier: str = field(
        default="{1}",
        metadata={
            "name": "phaseCapPressureMultiplier",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class VanGenuchtenStone2RelativePermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    gas_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name": "gasOilRelPermExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    gas_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "gasOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_min_volume_fraction: str = field(
        default="{0}",
        metadata={
            "name": "phaseMinVolumeFraction",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    phase_names: str = field(
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    water_oil_rel_perm_exponent_inv: str = field(
        default="{0.5}",
        metadata={
            "name": "waterOilRelPermExponentInv",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    water_oil_rel_perm_max_value: str = field(
        default="{0}",
        metadata={
            "name": "waterOilRelPermMaxValue",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ViscoDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    relaxation_time: str = field(
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ViscoExtendedDruckerPragerType(BaseModel):
    model_config = ConfigDict(defer_build=True)
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
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    relaxation_time: str = field(
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ViscoModifiedCamClayType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    default_csl_slope: str = field(
        default="1",
        metadata={
            "name": "defaultCslSlope",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    default_density: str = field(
        metadata={
            "name": "defaultDensity",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    relaxation_time: str = field(
        metadata={
            "name": "relaxationTime",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class WellControlsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    control: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|BHP|phaseVolRate|totalVolRate|massRate|uninitialized",
        }
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
            "name": "injectionStream",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    reference_elevation: str = field(
        metadata={
            "name": "referenceElevation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    reference_reservoir_region: Optional[str] = field(
        default=None,
        metadata={
            "name": "referenceReservoirRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    status_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "statusTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    target_bhptable_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetBHPTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    target_mass_rate: str = field(
        default="0",
        metadata={
            "name": "targetMassRate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_mass_rate_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetMassRateTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    target_phase_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetPhaseName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    target_phase_rate_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetPhaseRateTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    target_total_rate_table_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "targetTotalRateTableName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    type_value: str = field(
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|producer|injector",
        }
    )
    use_surface_conditions: str = field(
        default="0",
        metadata={
            "name": "useSurfaceConditions",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class WellElementRegionType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    material_list: str = field(
        metadata={
            "name": "materialList",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    mesh_body: Optional[str] = field(
        default=None,
        metadata={
            "name": "meshBody",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class WillisRichardsPermeabilityType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    dilation_coefficient: str = field(
        metadata={
            "name": "dilationCoefficient",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    max_frac_aperture: str = field(
        metadata={
            "name": "maxFracAperture",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    ref_closure_stress: str = field(
        metadata={
            "name": "refClosureStress",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ConstitutiveType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    barton_bandis: list[BartonBandisType] = field(
        default_factory=list,
        metadata={
            "name": "BartonBandis",
            "type": "Element",
            "namespace": "",
        },
    )
    biot_porosity: list[BiotPorosityType] = field(
        default_factory=list,
        metadata={
            "name": "BiotPorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    black_oil_fluid: list[BlackOilFluidType] = field(
        default_factory=list,
        metadata={
            "name": "BlackOilFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_baker_relative_permeability: list[
        BrooksCoreyBakerRelativePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyBakerRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_capillary_pressure: list[BrooksCoreyCapillaryPressureType] = (
        field(
            default_factory=list,
            metadata={
                "name": "BrooksCoreyCapillaryPressure",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    brooks_corey_relative_permeability: list[
        BrooksCoreyRelativePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    brooks_corey_stone2_relative_permeability: list[
        BrooksCoreyStone2RelativePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "BrooksCoreyStone2RelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_ezrokhi_fluid: list[Co2BrineEzrokhiFluidType] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrineEzrokhiFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_ezrokhi_thermal_fluid: list[Co2BrineEzrokhiThermalFluidType] = (
        field(
            default_factory=list,
            metadata={
                "name": "CO2BrineEzrokhiThermalFluid",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    co2_brine_phillips_fluid: list[Co2BrinePhillipsFluidType] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrinePhillipsFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    co2_brine_phillips_thermal_fluid: list[
        Co2BrinePhillipsThermalFluidType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CO2BrinePhillipsThermalFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    carman_kozeny_permeability: list[CarmanKozenyPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "CarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    ceramic_damage: list[CeramicDamageType] = field(
        default_factory=list,
        metadata={
            "name": "CeramicDamage",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_fluid: list[CompositionalMultiphaseFluidType] = (
        field(
            default_factory=list,
            metadata={
                "name": "CompositionalMultiphaseFluid",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    compositional_three_phase_fluid_lohrenz_bray_clark: list[
        CompositionalThreePhaseFluidLohrenzBrayClarkType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalThreePhaseFluidLohrenzBrayClark",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_two_phase_fluid: list[CompositionalTwoPhaseFluidType] = (
        field(
            default_factory=list,
            metadata={
                "name": "CompositionalTwoPhaseFluid",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    compositional_two_phase_fluid_lohrenz_bray_clark: list[
        CompositionalTwoPhaseFluidLohrenzBrayClarkType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalTwoPhaseFluidLohrenzBrayClark",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_two_phase_fluid_phillips_brine: list[
        CompositionalTwoPhaseFluidPhillipsBrineType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalTwoPhaseFluidPhillipsBrine",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_two_phase_kvalue_fluid_lohrenz_bray_clark: list[
        CompositionalTwoPhaseKvalueFluidLohrenzBrayClarkType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalTwoPhaseKValueFluidLohrenzBrayClark",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_two_phase_kvalue_fluid_phillips_brine: list[
        CompositionalTwoPhaseKvalueFluidPhillipsBrineType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalTwoPhaseKValueFluidPhillipsBrine",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_single_phase_fluid: list[CompressibleSinglePhaseFluidType] = (
        field(
            default_factory=list,
            metadata={
                "name": "CompressibleSinglePhaseFluid",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    compressible_solid_carman_kozeny_permeability: list[
        CompressibleSolidCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_constant_permeability: list[
        CompressibleSolidConstantPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidConstantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_exponential_decay_permeability: list[
        CompressibleSolidExponentialDecayPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidExponentialDecayPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_parallel_plates_permeability: list[
        CompressibleSolidParallelPlatesPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidParallelPlatesPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_pressure_permeability: list[
        CompressibleSolidPressurePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidPressurePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_slip_dependent_permeability: list[
        CompressibleSolidSlipDependentPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidSlipDependentPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    compressible_solid_willis_richards_permeability: list[
        CompressibleSolidWillisRichardsPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompressibleSolidWillisRichardsPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    constant_diffusion: list[ConstantDiffusionType] = field(
        default_factory=list,
        metadata={
            "name": "ConstantDiffusion",
            "type": "Element",
            "namespace": "",
        },
    )
    constant_permeability: list[ConstantPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "ConstantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    coulomb: list[CoulombType] = field(
        default_factory=list,
        metadata={
            "name": "Coulomb",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_elastic_isotropic: list[DamageElasticIsotropicType] = field(
        default_factory=list,
        metadata={
            "name": "DamageElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_permeability: list[DamagePermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "DamagePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_spectral_elastic_isotropic: list[
        DamageSpectralElasticIsotropicType
    ] = field(
        default_factory=list,
        metadata={
            "name": "DamageSpectralElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    damage_vol_dev_elastic_isotropic: list[
        DamageVolDevElasticIsotropicType
    ] = field(
        default_factory=list,
        metadata={
            "name": "DamageVolDevElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    dead_oil_fluid: list[DeadOilFluidType] = field(
        default_factory=list,
        metadata={
            "name": "DeadOilFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    delft_egg: list[DelftEggType] = field(
        default_factory=list,
        metadata={
            "name": "DelftEgg",
            "type": "Element",
            "namespace": "",
        },
    )
    drucker_prager: list[DruckerPragerType] = field(
        default_factory=list,
        metadata={
            "name": "DruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_isotropic: list[ElasticIsotropicType] = field(
        default_factory=list,
        metadata={
            "name": "ElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_isotropic_pressure_dependent: list[
        ElasticIsotropicPressureDependentType
    ] = field(
        default_factory=list,
        metadata={
            "name": "ElasticIsotropicPressureDependent",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_orthotropic: list[ElasticOrthotropicType] = field(
        default_factory=list,
        metadata={
            "name": "ElasticOrthotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_transverse_isotropic: list[ElasticTransverseIsotropicType] = field(
        default_factory=list,
        metadata={
            "name": "ElasticTransverseIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    exponential_decay_permeability: list[ExponentialDecayPermeabilityType] = (
        field(
            default_factory=list,
            metadata={
                "name": "ExponentialDecayPermeability",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    extended_drucker_prager: list[ExtendedDruckerPragerType] = field(
        default_factory=list,
        metadata={
            "name": "ExtendedDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    frictionless_contact: list[FrictionlessContactType] = field(
        default_factory=list,
        metadata={
            "name": "FrictionlessContact",
            "type": "Element",
            "namespace": "",
        },
    )
    hydraulic_aperture_table: list[HydraulicApertureTableType] = field(
        default_factory=list,
        metadata={
            "name": "HydraulicApertureTable",
            "type": "Element",
            "namespace": "",
        },
    )
    invariant_immiscible_fluid: list[InvariantImmiscibleFluidType] = field(
        default_factory=list,
        metadata={
            "name": "InvariantImmiscibleFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    jfunction_capillary_pressure: list[JfunctionCapillaryPressureType] = field(
        default_factory=list,
        metadata={
            "name": "JFunctionCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    linear_isotropic_dispersion: list[LinearIsotropicDispersionType] = field(
        default_factory=list,
        metadata={
            "name": "LinearIsotropicDispersion",
            "type": "Element",
            "namespace": "",
        },
    )
    modified_cam_clay: list[ModifiedCamClayType] = field(
        default_factory=list,
        metadata={
            "name": "ModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    multi_phase_constant_thermal_conductivity: list[
        MultiPhaseConstantThermalConductivityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiPhaseConstantThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    multi_phase_volume_weighted_thermal_conductivity: list[
        MultiPhaseVolumeWeightedThermalConductivityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiPhaseVolumeWeightedThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    null_model: list[NullModelType] = field(
        default_factory=list,
        metadata={
            "name": "NullModel",
            "type": "Element",
            "namespace": "",
        },
    )
    parallel_plates_permeability: list[ParallelPlatesPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "ParallelPlatesPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_fluid: list[ParticleFluidType] = field(
        default_factory=list,
        metadata={
            "name": "ParticleFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    perfectly_plastic: list[PerfectlyPlasticType] = field(
        default_factory=list,
        metadata={
            "name": "PerfectlyPlastic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_damage_elastic_isotropic: list[PorousDamageElasticIsotropicType] = (
        field(
            default_factory=list,
            metadata={
                "name": "PorousDamageElasticIsotropic",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    porous_damage_spectral_elastic_isotropic: list[
        PorousDamageSpectralElasticIsotropicType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDamageSpectralElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_damage_vol_dev_elastic_isotropic: list[
        PorousDamageVolDevElasticIsotropicType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDamageVolDevElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_delft_egg: list[PorousDelftEggType] = field(
        default_factory=list,
        metadata={
            "name": "PorousDelftEgg",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_delft_egg_carman_kozeny_permeability: list[
        PorousDelftEggCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDelftEggCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_drucker_prager: list[PorousDruckerPragerType] = field(
        default_factory=list,
        metadata={
            "name": "PorousDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_drucker_prager_carman_kozeny_permeability: list[
        PorousDruckerPragerCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousDruckerPragerCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_isotropic: list[PorousElasticIsotropicType] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_isotropic_carman_kozeny_permeability: list[
        PorousElasticIsotropicCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticIsotropicCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_orthotropic: list[PorousElasticOrthotropicType] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticOrthotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_orthotropic_carman_kozeny_permeability: list[
        PorousElasticOrthotropicCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticOrthotropicCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_transverse_isotropic: list[
        PorousElasticTransverseIsotropicType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticTransverseIsotropic",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_elastic_transverse_isotropic_carman_kozeny_permeability: list[
        PorousElasticTransverseIsotropicCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousElasticTransverseIsotropicCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_extended_drucker_prager: list[PorousExtendedDruckerPragerType] = (
        field(
            default_factory=list,
            metadata={
                "name": "PorousExtendedDruckerPrager",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    porous_extended_drucker_prager_carman_kozeny_permeability: list[
        PorousExtendedDruckerPragerCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousExtendedDruckerPragerCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_modified_cam_clay: list[PorousModifiedCamClayType] = field(
        default_factory=list,
        metadata={
            "name": "PorousModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_modified_cam_clay_carman_kozeny_permeability: list[
        PorousModifiedCamClayCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousModifiedCamClayCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_visco_drucker_prager: list[PorousViscoDruckerPragerType] = field(
        default_factory=list,
        metadata={
            "name": "PorousViscoDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_visco_drucker_prager_carman_kozeny_permeability: list[
        PorousViscoDruckerPragerCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousViscoDruckerPragerCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_visco_extended_drucker_prager: list[
        PorousViscoExtendedDruckerPragerType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousViscoExtendedDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_visco_extended_drucker_prager_carman_kozeny_permeability: list[
        PorousViscoExtendedDruckerPragerCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousViscoExtendedDruckerPragerCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    porous_visco_modified_cam_clay: list[PorousViscoModifiedCamClayType] = (
        field(
            default_factory=list,
            metadata={
                "name": "PorousViscoModifiedCamClay",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    porous_visco_modified_cam_clay_carman_kozeny_permeability: list[
        PorousViscoModifiedCamClayCarmanKozenyPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "PorousViscoModifiedCamClayCarmanKozenyPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    pressure_permeability: list[PressurePermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "PressurePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    pressure_porosity: list[PressurePorosityType] = field(
        default_factory=list,
        metadata={
            "name": "PressurePorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_permeability: list[ProppantPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "ProppantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_porosity: list[ProppantPorosityType] = field(
        default_factory=list,
        metadata={
            "name": "ProppantPorosity",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_slurry_fluid: list[ProppantSlurryFluidType] = field(
        default_factory=list,
        metadata={
            "name": "ProppantSlurryFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_solid_proppant_permeability: list[
        ProppantSolidProppantPermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "ProppantSolidProppantPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    rate_and_state_friction_aging_law: list[
        RateAndStateFrictionAgingLawType
    ] = field(
        default_factory=list,
        metadata={
            "name": "RateAndStateFrictionAgingLaw",
            "type": "Element",
            "namespace": "",
        },
    )
    rate_and_state_friction_slip_law: list[RateAndStateFrictionSlipLawType] = (
        field(
            default_factory=list,
            metadata={
                "name": "RateAndStateFrictionSlipLaw",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    reactive_brine: list[ReactiveBrineType] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveBrine",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_brine_thermal: list[ReactiveBrineThermalType] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveBrineThermal",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_thermal_conductivity: list[
        SinglePhaseThermalConductivityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseThermalConductivity",
            "type": "Element",
            "namespace": "",
        },
    )
    slip_dependent_permeability: list[SlipDependentPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "SlipDependentPermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_internal_energy: list[SolidInternalEnergyType] = field(
        default_factory=list,
        metadata={
            "name": "SolidInternalEnergy",
            "type": "Element",
            "namespace": "",
        },
    )
    table_capillary_pressure: list[TableCapillaryPressureType] = field(
        default_factory=list,
        metadata={
            "name": "TableCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    table_relative_permeability: list[TableRelativePermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "TableRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    table_relative_permeability_hysteresis: list[
        TableRelativePermeabilityHysteresisType
    ] = field(
        default_factory=list,
        metadata={
            "name": "TableRelativePermeabilityHysteresis",
            "type": "Element",
            "namespace": "",
        },
    )
    thermal_compressible_single_phase_fluid: list[
        ThermalCompressibleSinglePhaseFluidType
    ] = field(
        default_factory=list,
        metadata={
            "name": "ThermalCompressibleSinglePhaseFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    two_phase_immiscible_fluid: list[TwoPhaseImmiscibleFluidType] = field(
        default_factory=list,
        metadata={
            "name": "TwoPhaseImmiscibleFluid",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_baker_relative_permeability: list[
        VanGenuchtenBakerRelativePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenBakerRelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_capillary_pressure: list[
        VanGenuchtenCapillaryPressureType
    ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenCapillaryPressure",
            "type": "Element",
            "namespace": "",
        },
    )
    van_genuchten_stone2_relative_permeability: list[
        VanGenuchtenStone2RelativePermeabilityType
    ] = field(
        default_factory=list,
        metadata={
            "name": "VanGenuchtenStone2RelativePermeability",
            "type": "Element",
            "namespace": "",
        },
    )
    visco_drucker_prager: list[ViscoDruckerPragerType] = field(
        default_factory=list,
        metadata={
            "name": "ViscoDruckerPrager",
            "type": "Element",
            "namespace": "",
        },
    )
    visco_extended_drucker_prager: list[ViscoExtendedDruckerPragerType] = (
        field(
            default_factory=list,
            metadata={
                "name": "ViscoExtendedDruckerPrager",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    visco_modified_cam_clay: list[ViscoModifiedCamClayType] = field(
        default_factory=list,
        metadata={
            "name": "ViscoModifiedCamClay",
            "type": "Element",
            "namespace": "",
        },
    )
    willis_richards_permeability: list[WillisRichardsPermeabilityType] = field(
        default_factory=list,
        metadata={
            "name": "WillisRichardsPermeability",
            "type": "Element",
            "namespace": "",
        },
    )


class ElementRegionsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    cell_element_region: list[CellElementRegionType] = field(
        default_factory=list,
        metadata={
            "name": "CellElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )
    surface_element_region: list[SurfaceElementRegionType] = field(
        default_factory=list,
        metadata={
            "name": "SurfaceElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )
    well_element_region: list[WellElementRegionType] = field(
        default_factory=list,
        metadata={
            "name": "WellElementRegion",
            "type": "Element",
            "namespace": "",
        },
    )


class ExternalDataSourceType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    vtkhierarchical_data_source: list[VtkhierarchicalDataSourceType] = field(
        default_factory=list,
        metadata={
            "name": "VTKHierarchicalDataSource",
            "type": "Element",
            "namespace": "",
        },
    )


class FieldSpecificationsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    aquifer: list[AquiferType] = field(
        default_factory=list,
        metadata={
            "name": "Aquifer",
            "type": "Element",
            "namespace": "",
        },
    )
    dirichlet: list[DirichletType] = field(
        default_factory=list,
        metadata={
            "name": "Dirichlet",
            "type": "Element",
            "namespace": "",
        },
    )
    field_specification: list[FieldSpecificationType] = field(
        default_factory=list,
        metadata={
            "name": "FieldSpecification",
            "type": "Element",
            "namespace": "",
        },
    )
    hydrostatic_equilibrium: list[HydrostaticEquilibriumType] = field(
        default_factory=list,
        metadata={
            "name": "HydrostaticEquilibrium",
            "type": "Element",
            "namespace": "",
        },
    )
    pml: list[Pmltype] = field(
        default_factory=list,
        metadata={
            "name": "PML",
            "type": "Element",
            "namespace": "",
        },
    )
    source_flux: list[SourceFluxType] = field(
        default_factory=list,
        metadata={
            "name": "SourceFlux",
            "type": "Element",
            "namespace": "",
        },
    )
    traction: list[TractionType] = field(
        default_factory=list,
        metadata={
            "name": "Traction",
            "type": "Element",
            "namespace": "",
        },
    )


class FiniteVolumeType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    hybrid_mimetic_discretization: list[HybridMimeticDiscretizationType] = (
        field(
            default_factory=list,
            metadata={
                "name": "HybridMimeticDiscretization",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    two_point_flux_approximation: list[TwoPointFluxApproximationType] = field(
        default_factory=list,
        metadata={
            "name": "TwoPointFluxApproximation",
            "type": "Element",
            "namespace": "",
        },
    )


class FunctionsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    composite_function: list[CompositeFunctionType] = field(
        default_factory=list,
        metadata={
            "name": "CompositeFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    multivariable_table_function: list[MultivariableTableFunctionType] = field(
        default_factory=list,
        metadata={
            "name": "MultivariableTableFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    symbolic_function: list[SymbolicFunctionType] = field(
        default_factory=list,
        metadata={
            "name": "SymbolicFunction",
            "type": "Element",
            "namespace": "",
        },
    )
    table_function: list[TableFunctionType] = field(
        default_factory=list,
        metadata={
            "name": "TableFunction",
            "type": "Element",
            "namespace": "",
        },
    )


class GeometryType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    box: list[BoxType] = field(
        default_factory=list,
        metadata={
            "name": "Box",
            "type": "Element",
            "namespace": "",
        },
    )
    custom_polar_object: list[CustomPolarObjectType] = field(
        default_factory=list,
        metadata={
            "name": "CustomPolarObject",
            "type": "Element",
            "namespace": "",
        },
    )
    cylinder: list[CylinderType] = field(
        default_factory=list,
        metadata={
            "name": "Cylinder",
            "type": "Element",
            "namespace": "",
        },
    )
    disc: list[DiscType] = field(
        default_factory=list,
        metadata={
            "name": "Disc",
            "type": "Element",
            "namespace": "",
        },
    )
    rectangle: list[RectangleType] = field(
        default_factory=list,
        metadata={
            "name": "Rectangle",
            "type": "Element",
            "namespace": "",
        },
    )
    thick_plane: list[ThickPlaneType] = field(
        default_factory=list,
        metadata={
            "name": "ThickPlane",
            "type": "Element",
            "namespace": "",
        },
    )


class GraphType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    metis: list[MetisType] = field(
        default_factory=list,
        metadata={
            "name": "Metis",
            "type": "Element",
            "namespace": "",
        },
    )
    matrix_weights: str = field(
        default="0",
        metadata={
            "name": "matrixWeights",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    method: str = field(
        default="metis",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|metis|scotch",
        },
    )
    min_common_nodes: str = field(
        default="3",
        metadata={
            "name": "minCommonNodes",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    preserve_regions: str = field(
        default="0",
        metadata={
            "name": "preserveRegions",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class IncludedType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    file: list[FileType] = field(
        default_factory=list,
        metadata={
            "name": "File",
            "type": "Element",
            "namespace": "",
        },
    )


class InternalWellType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    perforation: list[PerforationType] = field(
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
    num_elements_per_segment: str = field(
        metadata={
            "name": "numElementsPerSegment",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    polyline_node_coords: str = field(
        metadata={
            "name": "polylineNodeCoords",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        }
    )
    polyline_segment_conn: str = field(
        metadata={
            "name": "polylineSegmentConn",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*\}\s*",
        }
    )
    radius: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    well_controls_name: str = field(
        metadata={
            "name": "wellControlsName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    well_region_name: str = field(
        metadata={
            "name": "wellRegionName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class OutputsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    blueprint: list[BlueprintType] = field(
        default_factory=list,
        metadata={
            "name": "Blueprint",
            "type": "Element",
            "namespace": "",
        },
    )
    chombo_io: list[ChomboIotype] = field(
        default_factory=list,
        metadata={
            "name": "ChomboIO",
            "type": "Element",
            "namespace": "",
        },
    )
    memory_stats: list[MemoryStatsType] = field(
        default_factory=list,
        metadata={
            "name": "MemoryStats",
            "type": "Element",
            "namespace": "",
        },
    )
    python: list[PythonType] = field(
        default_factory=list,
        metadata={
            "name": "Python",
            "type": "Element",
            "namespace": "",
        },
    )
    restart: list[RestartType] = field(
        default_factory=list,
        metadata={
            "name": "Restart",
            "type": "Element",
            "namespace": "",
        },
    )
    silo: list[SiloType] = field(
        default_factory=list,
        metadata={
            "name": "Silo",
            "type": "Element",
            "namespace": "",
        },
    )
    time_history: list[TimeHistoryType] = field(
        default_factory=list,
        metadata={
            "name": "TimeHistory",
            "type": "Element",
            "namespace": "",
        },
    )
    vtk: list[Vtktype] = field(
        default_factory=list,
        metadata={
            "name": "VTK",
            "type": "Element",
            "namespace": "",
        },
    )


class ParametersType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    parameter: list[ParameterType] = field(
        default_factory=list,
        metadata={
            "name": "Parameter",
            "type": "Element",
            "namespace": "",
        },
    )


class ParticleRegionsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    particle_region: list[ParticleRegionType] = field(
        default_factory=list,
        metadata={
            "name": "ParticleRegion",
            "type": "Element",
            "namespace": "",
        },
    )


class PeriodicEventType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    halt_event: list[HaltEventType] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list["PeriodicEventType"] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list["SoloEventType"] = field(
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
    function: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    object_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "object",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    set: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    stat: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class TasksType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    cell_to_cell_data_collection: list[CellToCellDataCollectionType] = field(
        default_factory=list,
        metadata={
            "name": "CellToCellDataCollection",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir_poromechanics_conforming_fractures_initialization: list[
        CompositionalMultiphaseReservoirPoromechanicsConformingFracturesInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoirPoromechanicsConformingFracturesInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir_poromechanics_initialization: list[
        CompositionalMultiphaseReservoirPoromechanicsInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoirPoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_statistics: list[
        CompositionalMultiphaseStatisticsType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    hydrofracture_initialization: list[HydrofractureInitializationType] = (
        field(
            default_factory=list,
            metadata={
                "name": "HydrofractureInitialization",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    multiphase_poromechanics_conforming_fractures_initialization: list[
        MultiphasePoromechanicsConformingFracturesInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsConformingFracturesInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics_initialization: list[
        MultiphasePoromechanicsInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    pvtdriver: list[PvtdriverType] = field(
        default_factory=list,
        metadata={
            "name": "PVTDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    pack_collection: list[PackCollectionType] = field(
        default_factory=list,
        metadata={
            "name": "PackCollection",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_fluid_driver: list[ReactiveFluidDriverType] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveFluidDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    relperm_driver: list[RelpermDriverType] = field(
        default_factory=list,
        metadata={
            "name": "RelpermDriver",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures_alminitialization: list[
        SinglePhasePoromechanicsConformingFracturesAlminitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFracturesALMInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures_initialization: list[
        SinglePhasePoromechanicsConformingFracturesInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFracturesInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_embedded_fractures_initialization: list[
        SinglePhasePoromechanicsEmbeddedFracturesInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsEmbeddedFracturesInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_initialization: list[
        SinglePhasePoromechanicsInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_conforming_fractures_alminitialization: list[
        SinglePhaseReservoirPoromechanicsConformingFracturesAlminitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanicsConformingFracturesALMInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_conforming_fractures_initialization: list[
        SinglePhaseReservoirPoromechanicsConformingFracturesInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanicsConformingFracturesInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_initialization: list[
        SinglePhaseReservoirPoromechanicsInitializationType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanicsInitialization",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_statistics: list[SinglePhaseStatisticsType] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_state_reset: list[SolidMechanicsStateResetType] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsStateReset",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_statistics: list[SolidMechanicsStatisticsType] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    source_flux_statistics: list[SourceFluxStatisticsType] = field(
        default_factory=list,
        metadata={
            "name": "SourceFluxStatistics",
            "type": "Element",
            "namespace": "",
        },
    )
    triaxial_driver: list[TriaxialDriverType] = field(
        default_factory=list,
        metadata={
            "name": "TriaxialDriver",
            "type": "Element",
            "namespace": "",
        },
    )


class VtkwellType(BaseModel):
    class Meta:
        name = "VTKWellType"

    model_config = ConfigDict(defer_build=True)
    perforation: list[PerforationType] = field(
        default_factory=list,
        metadata={
            "name": "Perforation",
            "type": "Element",
            "namespace": "",
        },
    )
    file: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        }
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
    num_elements_per_segment: str = field(
        metadata={
            "name": "numElementsPerSegment",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    radius: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    well_controls_name: str = field(
        metadata={
            "name": "wellControlsName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    well_region_name: str = field(
        metadata={
            "name": "wellRegionName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CrusherType(BaseModel):
    class Meta:
        name = "crusherType"

    model_config = ConfigDict(defer_build=True)
    run: list[RunType] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


class LassenType(BaseModel):
    class Meta:
        name = "lassenType"

    model_config = ConfigDict(defer_build=True)
    run: list[RunType] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


class QuartzType(BaseModel):
    class Meta:
        name = "quartzType"

    model_config = ConfigDict(defer_build=True)
    run: list[RunType] = field(
        default_factory=list,
        metadata={
            "name": "Run",
            "type": "Element",
            "namespace": "",
        },
    )


class BenchmarksType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    crusher: list[CrusherType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    lassen: list[LassenType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    quartz: list[QuartzType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


class CoarseningType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    graph: list[GraphType] = field(
        default_factory=list,
        metadata={
            "name": "Graph",
            "type": "Element",
            "namespace": "",
        },
    )
    structured: list[StructuredType] = field(
        default_factory=list,
        metadata={
            "name": "Structured",
            "type": "Element",
            "namespace": "",
        },
    )
    max_coarse_dof: str = field(
        default="0",
        metadata={
            "name": "maxCoarseDof",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    partition_type: str = field(
        default="graph",
        metadata={
            "name": "partitionType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|graph|cartesian|semistructured",
        },
    )
    ratio: str = field(
        default="{0}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )


class InternalMeshType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    internal_well: list[InternalWellType] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    region: list[RegionType] = field(
        default_factory=list,
        metadata={
            "name": "Region",
            "type": "Element",
            "namespace": "",
        },
    )
    vtkwell: list[VtkwellType] = field(
        default_factory=list,
        metadata={
            "name": "VTKWell",
            "type": "Element",
            "namespace": "",
        },
    )
    cell_block_names: str = field(
        metadata={
            "name": "cellBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    element_types: str = field(
        metadata={
            "name": "elementTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    nx: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
    )
    ny: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
    )
    nz: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
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
            "name": "xBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    x_coords: str = field(
        metadata={
            "name": "xCoords",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    y_bias: str = field(
        default="{1}",
        metadata={
            "name": "yBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    y_coords: str = field(
        metadata={
            "name": "yCoords",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    z_bias: str = field(
        default="{1}",
        metadata={
            "name": "zBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_coords: str = field(
        metadata={
            "name": "zCoords",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class InternalWellboreType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    internal_well: list[InternalWellType] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    region: list[RegionType] = field(
        default_factory=list,
        metadata={
            "name": "Region",
            "type": "Element",
            "namespace": "",
        },
    )
    vtkwell: list[VtkwellType] = field(
        default_factory=list,
        metadata={
            "name": "VTKWell",
            "type": "Element",
            "namespace": "",
        },
    )
    auto_space_radial_elems: str = field(
        default="{-1}",
        metadata={
            "name": "autoSpaceRadialElems",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
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
    cell_block_names: str = field(
        metadata={
            "name": "cellBlockNames",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    element_types: str = field(
        metadata={
            "name": "elementTypes",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        }
    )
    hard_radial_coords: str = field(
        default="{0}",
        metadata={
            "name": "hardRadialCoords",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    nr: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
    )
    nt: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
    )
    nz: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]+\s*,\s*)*[+-]?[\d]+\s*)?\}\s*",
        }
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
            "name": "rBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    radius: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    theta: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    trajectory: str = field(
        default="{{0}}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
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
            "name": "xBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    y_bias: str = field(
        default="{1}",
        metadata={
            "name": "yBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_bias: str = field(
        default="{1}",
        metadata={
            "name": "zBias",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    z_coords: str = field(
        metadata={
            "name": "zCoords",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SoloEventType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    halt_event: list[HaltEventType] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[PeriodicEventType] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list["SoloEventType"] = field(
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
    target: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class VtkmeshType(BaseModel):
    class Meta:
        name = "VTKMeshType"

    model_config = ConfigDict(defer_build=True)
    internal_well: list[InternalWellType] = field(
        default_factory=list,
        metadata={
            "name": "InternalWell",
            "type": "Element",
            "namespace": "",
        },
    )
    region: list[RegionType] = field(
        default_factory=list,
        metadata={
            "name": "Region",
            "type": "Element",
            "namespace": "",
        },
    )
    vtkwell: list[VtkwellType] = field(
        default_factory=list,
        metadata={
            "name": "VTKWell",
            "type": "Element",
            "namespace": "",
        },
    )
    data_source_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataSourceName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    face_blocks: str = field(
        default="{}",
        metadata={
            "name": "faceBlocks",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    field_names_in_geos: str = field(
        default="{}",
        metadata={
            "name": "fieldNamesInGEOS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    fields_to_import: str = field(
        default="{}",
        metadata={
            "name": "fieldsToImport",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    file: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    nodeset_names: str = field(
        default="{}",
        metadata={
            "name": "nodesetNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    scale: str = field(
        default="{1,1,1}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    structured_index_attribute: Optional[str] = field(
        default=None,
        metadata={
            "name": "structuredIndexAttribute",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    surfacic_fields_in_geos: str = field(
        default="{}",
        metadata={
            "name": "surfacicFieldsInGEOS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    surfacic_fields_to_import: str = field(
        default="{}",
        metadata={
            "name": "surfacicFieldsToImport",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    translate: str = field(
        default="{0,0,0}",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class EventsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    halt_event: list[HaltEventType] = field(
        default_factory=list,
        metadata={
            "name": "HaltEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    periodic_event: list[PeriodicEventType] = field(
        default_factory=list,
        metadata={
            "name": "PeriodicEvent",
            "type": "Element",
            "namespace": "",
        },
    )
    solo_event: list[SoloEventType] = field(
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
    max_time: str = field(
        default="3.1557e+11",
        metadata={
            "name": "maxTime",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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


class MeshType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    internal_mesh: list[InternalMeshType] = field(
        default_factory=list,
        metadata={
            "name": "InternalMesh",
            "type": "Element",
            "namespace": "",
        },
    )
    internal_wellbore: list[InternalWellboreType] = field(
        default_factory=list,
        metadata={
            "name": "InternalWellbore",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_mesh: list[ParticleMeshType] = field(
        default_factory=list,
        metadata={
            "name": "ParticleMesh",
            "type": "Element",
            "namespace": "",
        },
    )
    vtkmesh: list[VtkmeshType] = field(
        default_factory=list,
        metadata={
            "name": "VTKMesh",
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


class MultiscaleType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    coarsening: list[CoarseningType] = field(
        default_factory=list,
        metadata={
            "name": "Coarsening",
            "type": "Element",
            "namespace": "",
        },
    )
    coupled: list[CoupledType] = field(
        default_factory=list,
        metadata={
            "name": "Coupled",
            "type": "Element",
            "namespace": "",
        },
    )
    ms_rsb: list[MsRsbtype] = field(
        default_factory=list,
        metadata={
            "name": "MsRSB",
            "type": "Element",
            "namespace": "",
        },
    )
    smoother: list[SmootherType] = field(
        default_factory=list,
        metadata={
            "name": "Smoother",
            "type": "Element",
            "namespace": "",
        },
    )
    basis_type: str = field(
        default="msrsb",
        metadata={
            "name": "basisType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|msrsb",
        },
    )
    boundary_sets: str = field(
        default="{}",
        metadata={
            "name": "boundarySets",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    coarse_type: str = field(
        default="direct",
        metadata={
            "name": "coarseType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|iluk|ilut|ick|ict|amg|mgr|block|direct|bgs|multiscale",
        },
    )
    debug_level: str = field(
        default="0",
        metadata={
            "name": "debugLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    droptol: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    galerkin: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    max_levels: str = field(
        default="5",
        metadata={
            "name": "maxLevels",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    separate_components: str = field(
        default="0",
        metadata={
            "name": "separateComponents",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )


class LinearSolverParametersType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    block: list[BlockType] = field(
        default_factory=list,
        metadata={
            "name": "Block",
            "type": "Element",
            "namespace": "",
        },
    )
    multiscale: list[MultiscaleType] = field(
        default_factory=list,
        metadata={
            "name": "Multiscale",
            "type": "Element",
            "namespace": "",
        },
    )
    adaptive_exponent: str = field(
        default="1",
        metadata={
            "name": "adaptiveExponent",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    adaptive_gamma: str = field(
        default="0.1",
        metadata={
            "name": "adaptiveGamma",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
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
            "name": "amgAggressiveInterpType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|extendedIStage2|standardStage2|extendedStage2|multipass|modifiedExtended|modifiedExtendedI|modifiedExtendedE|modifiedMultipass",
        },
    )
    amg_coarse_solver: str = field(
        default="direct",
        metadata={
            "name": "amgCoarseSolver",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|direct|bgs|gsElimWPivoting|gsElimWInverse",
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
            "name": "amgInterpolationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|default|modifiedClassical|direct|multipass|extendedI|standard|extended|directBAMG|modifiedExtended|modifiedExtendedI|modifiedExtendedE",
        },
    )
    amg_max_coarse_size: str = field(
        default="9",
        metadata={
            "name": "amgMaxCoarseSize",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    amg_num_cycles: str = field(
        default="1",
        metadata={
            "name": "amgNumCycles",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
            "pattern": r".*[\[\]`$].*|default|jacobi|l1jacobi|fgs|bgs|sgs|l1sgs|chebyshev|iluk|ilut|ick|ict",
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
    chebyshev_eig_num_iter: str = field(
        default="10",
        metadata={
            "name": "chebyshevEigNumIter",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    chebyshev_order: str = field(
        default="2",
        metadata={
            "name": "chebyshevOrder",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    krylov_strongest_tol: str = field(
        default="1e-08",
        metadata={
            "name": "krylovStrongestTol",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
            "name": "preconditionerType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|jacobi|l1jacobi|fgs|sgs|l1sgs|chebyshev|iluk|ilut|ick|ict|amg|mgr|block|direct|bgs|multiscale",
        },
    )
    relaxation_weight: str = field(
        default="0.666667",
        metadata={
            "name": "relaxationWeight",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    reuse_factorization: str = field(
        default="0",
        metadata={
            "name": "reuseFactorization",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    solver_type: str = field(
        default="direct",
        metadata={
            "name": "solverType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|direct|cg|gmres|fgmres|bicgstab|richardson|preconditioner",
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


class AcousticDgtype(BaseModel):
    class Meta:
        name = "AcousticDGType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class AcousticElasticSemtype(BaseModel):
    class Meta:
        name = "AcousticElasticSEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_solver_name: str = field(
        metadata={
            "name": "acousticSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    elastic_solver_name: str = field(
        metadata={
            "name": "elasticSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class AcousticFirstOrderSemtype(BaseModel):
    class Meta:
        name = "AcousticFirstOrderSEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class AcousticSemtype(BaseModel):
    class Meta:
        name = "AcousticSEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class AcousticVtisemtype(BaseModel):
    class Meta:
        name = "AcousticVTISEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseFvmtype(BaseModel):
    class Meta:
        name = "CompositionalMultiphaseFVMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
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
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    formulation_type: str = field(
        default="ComponentDensities",
        metadata={
            "name": "formulationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ComponentDensities|OverallComposition",
        },
    )
    gravity_density_scheme: str = field(
        default="ArithmeticAverage",
        metadata={
            "name": "gravityDensityScheme",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ArithmeticAverage|PhasePresence",
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
    max_relative_comp_dens_change: str = field(
        default="1.79769e+208",
        metadata={
            "name": "maxRelativeCompDensChange",
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
    max_sequential_comp_dens_change: str = field(
        default="1",
        metadata={
            "name": "maxSequentialCompDensChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
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
    min_comp_frac: str = field(
        default="0",
        metadata={
            "name": "minCompFrac",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_scaling_factor: str = field(
        default="0.01",
        metadata={
            "name": "minScalingFactor",
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
    target_comp_frac_change_in_time_step: str = field(
        default="1.79769e+308",
        metadata={
            "name": "targetCompFracChangeInTimeStep",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_relative_comp_dens_change_in_time_step: str = field(
        default="1.79769e+308",
        metadata={
            "name": "targetRelativeCompDensChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    temperature: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
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
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_simple_accumulation: str = field(
        default="1",
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
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseHybridFvmtype(BaseModel):
    class Meta:
        name = "CompositionalMultiphaseHybridFVMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
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
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    formulation_type: str = field(
        default="ComponentDensities",
        metadata={
            "name": "formulationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ComponentDensities|OverallComposition",
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
    max_relative_comp_dens_change: str = field(
        default="1.79769e+208",
        metadata={
            "name": "maxRelativeCompDensChange",
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
    max_sequential_comp_dens_change: str = field(
        default="1",
        metadata={
            "name": "maxSequentialCompDensChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
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
    min_comp_frac: str = field(
        default="0",
        metadata={
            "name": "minCompFrac",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    min_scaling_factor: str = field(
        default="0.01",
        metadata={
            "name": "minScalingFactor",
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
    target_comp_frac_change_in_time_step: str = field(
        default="1.79769e+308",
        metadata={
            "name": "targetCompFracChangeInTimeStep",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_relative_comp_dens_change_in_time_step: str = field(
        default="1.79769e+308",
        metadata={
            "name": "targetRelativeCompDensChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    temperature: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    use_mass: str = field(
        default="0",
        metadata={
            "name": "useMass",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_simple_accumulation: str = field(
        default="1",
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
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseReservoirPoromechanicsConformingFracturesType(
    BaseModel
):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    reservoir_and_wells_solver_name: str = field(
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseReservoirPoromechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    reservoir_and_wells_solver_name: str = field(
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseReservoirType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    well_solver_name: str = field(
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class CompositionalMultiphaseWellType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    well_controls: list[WellControlsType] = field(
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
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    max_relative_comp_dens_change: str = field(
        default="1.79769e+208",
        metadata={
            "name": "maxRelativeCompDensChange",
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
    max_relative_temperature_change: str = field(
        default="1",
        metadata={
            "name": "maxRelativeTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_step_from_tables: str = field(
        default="0",
        metadata={
            "name": "timeStepFromTables",
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
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
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
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticFirstOrderSemtype(BaseModel):
    class Meta:
        name = "ElasticFirstOrderSEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ElasticSemtype(BaseModel):
    class Meta:
        name = "ElasticSEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    attenuation_type: str = field(
        default="none",
        metadata={
            "name": "attenuationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|sls",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "name": "linearDASGeometry",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    linear_dassamples: str = field(
        default="5",
        metadata={
            "name": "linearDASSamples",
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
            "name": "receiverCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    reflectivity_coeff: str = field(
        default="0.001",
        metadata={
            "name": "reflectivityCoeff",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    sls_anelasticity_coefficients: str = field(
        default="{0}",
        metadata={
            "name": "slsAnelasticityCoefficients",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    sls_reference_angular_frequencies: str = field(
        default="{0}",
        metadata={
            "name": "slsReferenceAngularFrequencies",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*",
        },
    )
    source_coordinates: str = field(
        default="{{0}}",
        metadata={
            "name": "sourceCoordinates",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*,\s*)*\{\s*(([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*)*[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*)?\}\s*\}\s*",
        },
    )
    source_force: str = field(
        default="{0,0,0}",
        metadata={
            "name": "sourceForce",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    source_moment: str = field(
        default="{1,1,1,0,0,0}",
        metadata={
            "name": "sourceMoment",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){5}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    source_wavelet_table_names: str = field(
        default="{}",
        metadata={
            "name": "sourceWaveletTableNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([^,\{\}\s]+\s*,\s*)*[^,\{\}\s]+\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    thickness_taper: str = field(
        default="0",
        metadata={
            "name": "thicknessTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
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
    timestep_stability_limit: str = field(
        default="0",
        metadata={
            "name": "timestepStabilityLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_das: str = field(
        default="none",
        metadata={
            "name": "useDAS",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|dipole|strainIntegration",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_tti: str = field(
        default="0",
        metadata={
            "name": "useTTI",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_taper: str = field(
        default="0",
        metadata={
            "name": "useTaper",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_vti: str = field(
        default="0",
        metadata={
            "name": "useVTI",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class EmbeddedSurfaceGeneratorType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    fracture_region: str = field(
        default="FractureRegion",
        metadata={
            "name": "fractureRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    target_objects: str = field(
        metadata={
            "name": "targetObjects",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ExplicitQuasiDynamicEqtype(BaseModel):
    class Meta:
        name = "ExplicitQuasiDynamicEQType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    shear_impedance: str = field(
        metadata={
            "name": "shearImpedance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    stress_solver_name: str = field(
        metadata={
            "name": "stressSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ExplicitSpringSliderType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    shear_impedance: str = field(
        metadata={
            "name": "shearImpedance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class FiniteElementsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    finite_element_space: list[FiniteElementSpaceType] = field(
        default_factory=list,
        metadata={
            "name": "FiniteElementSpace",
            "type": "Element",
            "namespace": "",
        },
    )
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )


class FlowProppantTransportType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    proppant_solver_name: str = field(
        metadata={
            "name": "proppantSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class HydrofractureType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    is_lagging_fracture_stencil_weights_update: str = field(
        default="0",
        metadata={
            "name": "isLaggingFractureStencilWeightsUpdate",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    leakoff_coefficient: str = field(
        default="-1",
        metadata={
            "name": "leakoffCoefficient",
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
    max_num_resolves: str = field(
        default="10",
        metadata={
            "name": "maxNumResolves",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    new_fracture_initialization_type: str = field(
        default="Pressure",
        metadata={
            "name": "newFractureInitializationType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|Pressure|Displacement",
        },
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    surface_generator_name: str = field(
        metadata={
            "name": "surfaceGeneratorName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_quasi_newton: str = field(
        default="0",
        metadata={
            "name": "useQuasiNewton",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ImmiscibleMultiphaseFlowType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    gravity_density_scheme: str = field(
        default="ArithmeticAverage",
        metadata={
            "name": "gravityDensityScheme",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|ArithmeticAverage|PhasePresence",
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
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
    target_phase_vol_fraction_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetPhaseVolFractionChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_relative_pressure_change_in_time_step: str = field(
        default="0.2",
        metadata={
            "name": "targetRelativePressureChangeInTimeStep",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    temperature: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
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
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ImplicitQuasiDynamicEqtype(BaseModel):
    class Meta:
        name = "ImplicitQuasiDynamicEQType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    shear_impedance: str = field(
        metadata={
            "name": "shearImpedance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    stress_solver_name: str = field(
        metadata={
            "name": "stressSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_slip_increment: str = field(
        default="1e-07",
        metadata={
            "name": "targetSlipIncrement",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ImplicitSpringSliderType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    shear_impedance: str = field(
        metadata={
            "name": "shearImpedance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    target_slip_increment: str = field(
        default="1e-07",
        metadata={
            "name": "targetSlipIncrement",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class LaplaceFemtype(BaseModel):
    class Meta:
        name = "LaplaceFEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    field_name: str = field(
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|SteadyState|ImplicitTransient",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiphasePoromechanicsConformingFracturesType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiphasePoromechanicsReservoirType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    well_solver_name: str = field(
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class MultiphasePoromechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class OneWayCoupledFractureFlowContactMechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PhaseFieldDamageFemtype(BaseModel):
    class Meta:
        name = "PhaseFieldDamageFEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_upper_bound: str = field(
        default="1.5",
        metadata={
            "name": "damageUpperBound",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    field_name: str = field(
        metadata={
            "name": "fieldName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    fracture_pressure_term_flag: str = field(
        default="0",
        metadata={
            "name": "fracturePressureTermFlag",
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
    irreversibility_flag: str = field(
        default="0",
        metadata={
            "name": "irreversibilityFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    local_dissipation: str = field(
        metadata={
            "name": "localDissipation",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|Linear|Quadratic",
        }
    )
    log_level: str = field(
        default="0",
        metadata={
            "name": "logLevel",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|SteadyState|ImplicitTransient|ExplicitTransient",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PhaseFieldFractureType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_solver_name: str = field(
        metadata={
            "name": "damageSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class PhaseFieldPoromechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_solver_name: str = field(
        metadata={
            "name": "damageSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ProppantTransportType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    update_proppant_packing: str = field(
        default="0",
        metadata={
            "name": "updateProppantPacking",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class ReactiveCompositionalMultiphaseObltype(BaseModel):
    class Meta:
        name = "ReactiveCompositionalMultiphaseOBLType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    obloperators_table_file: str = field(
        metadata={
            "name": "OBLOperatorsTableFile",
            "type": "Attribute",
            "required": True,
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
        }
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
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    enable_energy_balance: str = field(
        metadata={
            "name": "enableEnergyBalance",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    num_components: str = field(
        metadata={
            "name": "numComponents",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    num_phases: str = field(
        metadata={
            "name": "numPhases",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        }
    )
    phase_names: str = field(
        default="{}",
        metadata={
            "name": "phaseNames",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
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
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SeismicityRateType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    background_stressing_rate: str = field(
        metadata={
            "name": "backgroundStressingRate",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    cfl_factor: str = field(
        default="0.5",
        metadata={
            "name": "cflFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    direct_effect: str = field(
        metadata={
            "name": "directEffect",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    fault_normal_direction: str = field(
        default="{0,0,0}",
        metadata={
            "name": "faultNormalDirection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    fault_shear_direction: str = field(
        default="{0,0,0}",
        metadata={
            "name": "faultShearDirection",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
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
    stress_solver_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "stressSolverName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseFvmtype(BaseModel):
    class Meta:
        name = "SinglePhaseFVMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseHybridFvmtype(BaseModel):
    class Meta:
        name = "SinglePhaseHybridFVMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsConformingFracturesAlmtype(BaseModel):
    class Meta:
        name = "SinglePhasePoromechanicsConformingFracturesALMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsConformingFracturesReservoirType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    poromechanics_conforming_fractures_solver_name: str = field(
        metadata={
            "name": "poromechanicsConformingFracturesSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    well_solver_name: str = field(
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsConformingFracturesType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsEmbeddedFracturesType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsReservoirType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    poromechanics_solver_name: str = field(
        metadata={
            "name": "poromechanicsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    well_solver_name: str = field(
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhasePoromechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseProppantFvmtype(BaseModel):
    class Meta:
        name = "SinglePhaseProppantFVMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_negative_pressure: str = field(
        default="0",
        metadata={
            "name": "allowNegativePressure",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    max_sequential_pressure_change: str = field(
        default="100000",
        metadata={
            "name": "maxSequentialPressureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    max_sequential_temperature_change: str = field(
        default="0.1",
        metadata={
            "name": "maxSequentialTemperatureChange",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    temperature: str = field(
        default="0",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsConformingFracturesAlmtype(BaseModel):
    class Meta:
        name = "SinglePhaseReservoirPoromechanicsConformingFracturesALMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
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
    reservoir_and_wells_solver_name: str = field(
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsConformingFracturesType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
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
    reservoir_and_wells_solver_name: str = field(
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirPoromechanicsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    damage_flag: str = field(
        default="0",
        metadata={
            "name": "damageFlag",
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
    reservoir_and_wells_solver_name: str = field(
        metadata={
            "name": "reservoirAndWellsSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    solid_solver_name: str = field(
        metadata={
            "name": "solidSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseReservoirType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    flow_solver_name: str = field(
        metadata={
            "name": "flowSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    well_solver_name: str = field(
        metadata={
            "name": "wellSolverName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SinglePhaseWellType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    well_controls: list[WellControlsType] = field(
        default_factory=list,
        metadata={
            "name": "WellControls",
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
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_step_from_tables: str = field(
        default="0",
        metadata={
            "name": "timeStepFromTables",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_csv: str = field(
        default="0",
        metadata={
            "name": "writeCSV",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsAugmentedLagrangianContactType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    contact_penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "contactPenaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    iter_penalty_n: str = field(
        default="10",
        metadata={
            "name": "iterPenaltyN",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    iter_penalty_t: str = field(
        default="0.1",
        metadata={
            "name": "iterPenaltyT",
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
    simultaneous: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    symmetric: str = field(
        default="1",
        metadata={
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        default="QuasiStatic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    tol_jump_n: str = field(
        default="1e-07",
        metadata={
            "name": "tolJumpN",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tol_jump_t: str = field(
        default="1e-05",
        metadata={
            "name": "tolJumpT",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tol_normal_trac: str = field(
        default="0.5",
        metadata={
            "name": "tolNormalTrac",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    tol_tau_limit: str = field(
        default="0.05",
        metadata={
            "name": "tolTauLimit",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsEmbeddedFracturesType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    contact_penalty_stiffness: str = field(
        metadata={
            "name": "contactPenaltyStiffness",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        default="QuasiStatic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsLagrangeContactBubbleStabType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    contact_penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "contactPenaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        default="QuasiStatic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsLagrangeContactType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    contact_penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "contactPenaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    initial_dt: str = field(
        default="1e+99",
        metadata={
            "name": "initialDt",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    local_yield_acceleration_buffer: str = field(
        default="0.1",
        metadata={
            "name": "localYieldAccelerationBuffer",
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
    stabilization_name: str = field(
        metadata={
            "name": "stabilizationName",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    stabilization_scaling_coefficient: str = field(
        default="1",
        metadata={
            "name": "stabilizationScalingCoefficient",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        default="QuasiStatic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    use_local_yield_acceleration: str = field(
        default="0",
        metadata={
            "name": "useLocalYieldAcceleration",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsLagrangianFemtype(BaseModel):
    class Meta:
        name = "SolidMechanicsLagrangianFEMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    contact_penalty_stiffness: str = field(
        default="0",
        metadata={
            "name": "contactPenaltyStiffness",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    contact_relation_name: str = field(
        default="NOCONTACT",
        metadata={
            "name": "contactRelationName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        },
    )
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
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
    surface_generator_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "surfaceGeneratorName",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[^,\{\}\s]*\s*",
        },
    )
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    time_integration_option: str = field(
        default="QuasiStatic",
        metadata={
            "name": "timeIntegrationOption",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|QuasiStatic|ImplicitDynamic|ExplicitDynamic",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SolidMechanicsMpmtype(BaseModel):
    class Meta:
        name = "SolidMechanics_MPMType"

    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
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
    discretization: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
        }
    )
    f_table_interp_type: str = field(
        default="0",
        metadata={
            "name": "fTableInterpType",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    f_table_path: Optional[str] = field(
        default=None,
        metadata={
            "name": "fTablePath",
            "type": "Attribute",
            "pattern": r'.*[\[\]`$].*|[^*?<>\|:";,\s]*\s*',
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
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
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class SurfaceGeneratorType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    linear_solver_parameters: list[LinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "LinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    nonlinear_solver_parameters: list[NonlinearSolverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "NonlinearSolverParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    allow_non_converged_linear_solver_solution: str = field(
        default="1",
        metadata={
            "name": "allowNonConvergedLinearSolverSolution",
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
    fracture_origin: str = field(
        default="{0,0,0}",
        metadata={
            "name": "fractureOrigin",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )
    fracture_region: str = field(
        default="Fracture",
        metadata={
            "name": "fractureRegion",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_/*\[\]]*",
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
    initial_rock_toughness: str = field(
        metadata={
            "name": "initialRockToughness",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        }
    )
    is_poroelastic: str = field(
        default="0",
        metadata={
            "name": "isPoroelastic",
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
    target_regions: str = field(
        metadata={
            "name": "targetRegions",
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|\s*\{\s*(([a-zA-Z0-9.\-_/*\[\]]*\s*,\s*)*[a-zA-Z0-9.\-_/*\[\]]*\s*)?\}\s*",
        }
    )
    toughness_scaling_factor: str = field(
        default="0",
        metadata={
            "name": "toughnessScalingFactor",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)",
        },
    )
    use_physics_scaling: str = field(
        default="1",
        metadata={
            "name": "usePhysicsScaling",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_linear_system: str = field(
        default="0",
        metadata={
            "name": "writeLinearSystem",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|[+-]?[\d]+",
        },
    )
    write_statistics: str = field(
        default="none",
        metadata={
            "name": "writeStatistics",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|none|iteration|convergence|all",
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
            "pattern": r".*[\[\]`$].*|[a-zA-Z0-9.\-_]+",
        }
    )


class NumericalMethodsType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    finite_elements: list[FiniteElementsType] = field(
        default_factory=list,
        metadata={
            "name": "FiniteElements",
            "type": "Element",
            "namespace": "",
        },
    )
    finite_volume: list[FiniteVolumeType] = field(
        default_factory=list,
        metadata={
            "name": "FiniteVolume",
            "type": "Element",
            "namespace": "",
        },
    )


class SolversType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    acoustic_dg: list[AcousticDgtype] = field(
        default_factory=list,
        metadata={
            "name": "AcousticDG",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_elastic_sem: list[AcousticElasticSemtype] = field(
        default_factory=list,
        metadata={
            "name": "AcousticElasticSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_first_order_sem: list[AcousticFirstOrderSemtype] = field(
        default_factory=list,
        metadata={
            "name": "AcousticFirstOrderSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_sem: list[AcousticSemtype] = field(
        default_factory=list,
        metadata={
            "name": "AcousticSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    acoustic_vtisem: list[AcousticVtisemtype] = field(
        default_factory=list,
        metadata={
            "name": "AcousticVTISEM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_fvm: list[CompositionalMultiphaseFvmtype] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_hybrid_fvm: list[
        CompositionalMultiphaseHybridFvmtype
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseHybridFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir: list[
        CompositionalMultiphaseReservoirType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir_poromechanics: list[
        CompositionalMultiphaseReservoirPoromechanicsType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoirPoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_reservoir_poromechanics_conforming_fractures: list[
        CompositionalMultiphaseReservoirPoromechanicsConformingFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "CompositionalMultiphaseReservoirPoromechanicsConformingFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    compositional_multiphase_well: list[CompositionalMultiphaseWellType] = (
        field(
            default_factory=list,
            metadata={
                "name": "CompositionalMultiphaseWell",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    elastic_first_order_sem: list[ElasticFirstOrderSemtype] = field(
        default_factory=list,
        metadata={
            "name": "ElasticFirstOrderSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    elastic_sem: list[ElasticSemtype] = field(
        default_factory=list,
        metadata={
            "name": "ElasticSEM",
            "type": "Element",
            "namespace": "",
        },
    )
    embedded_surface_generator: list[EmbeddedSurfaceGeneratorType] = field(
        default_factory=list,
        metadata={
            "name": "EmbeddedSurfaceGenerator",
            "type": "Element",
            "namespace": "",
        },
    )
    explicit_quasi_dynamic_eq: list[ExplicitQuasiDynamicEqtype] = field(
        default_factory=list,
        metadata={
            "name": "ExplicitQuasiDynamicEQ",
            "type": "Element",
            "namespace": "",
        },
    )
    explicit_spring_slider: list[ExplicitSpringSliderType] = field(
        default_factory=list,
        metadata={
            "name": "ExplicitSpringSlider",
            "type": "Element",
            "namespace": "",
        },
    )
    flow_proppant_transport: list[FlowProppantTransportType] = field(
        default_factory=list,
        metadata={
            "name": "FlowProppantTransport",
            "type": "Element",
            "namespace": "",
        },
    )
    hydrofracture: list[HydrofractureType] = field(
        default_factory=list,
        metadata={
            "name": "Hydrofracture",
            "type": "Element",
            "namespace": "",
        },
    )
    immiscible_multiphase_flow: list[ImmiscibleMultiphaseFlowType] = field(
        default_factory=list,
        metadata={
            "name": "ImmiscibleMultiphaseFlow",
            "type": "Element",
            "namespace": "",
        },
    )
    implicit_quasi_dynamic_eq: list[ImplicitQuasiDynamicEqtype] = field(
        default_factory=list,
        metadata={
            "name": "ImplicitQuasiDynamicEQ",
            "type": "Element",
            "namespace": "",
        },
    )
    implicit_spring_slider: list[ImplicitSpringSliderType] = field(
        default_factory=list,
        metadata={
            "name": "ImplicitSpringSlider",
            "type": "Element",
            "namespace": "",
        },
    )
    laplace_fem: list[LaplaceFemtype] = field(
        default_factory=list,
        metadata={
            "name": "LaplaceFEM",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics: list[MultiphasePoromechanicsType] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics_conforming_fractures: list[
        MultiphasePoromechanicsConformingFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsConformingFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    multiphase_poromechanics_reservoir: list[
        MultiphasePoromechanicsReservoirType
    ] = field(
        default_factory=list,
        metadata={
            "name": "MultiphasePoromechanicsReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    one_way_coupled_fracture_flow_contact_mechanics: list[
        OneWayCoupledFractureFlowContactMechanicsType
    ] = field(
        default_factory=list,
        metadata={
            "name": "OneWayCoupledFractureFlowContactMechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    phase_field_damage_fem: list[PhaseFieldDamageFemtype] = field(
        default_factory=list,
        metadata={
            "name": "PhaseFieldDamageFEM",
            "type": "Element",
            "namespace": "",
        },
    )
    phase_field_fracture: list[PhaseFieldFractureType] = field(
        default_factory=list,
        metadata={
            "name": "PhaseFieldFracture",
            "type": "Element",
            "namespace": "",
        },
    )
    phase_field_poromechanics: list[PhaseFieldPoromechanicsType] = field(
        default_factory=list,
        metadata={
            "name": "PhaseFieldPoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    proppant_transport: list[ProppantTransportType] = field(
        default_factory=list,
        metadata={
            "name": "ProppantTransport",
            "type": "Element",
            "namespace": "",
        },
    )
    reactive_compositional_multiphase_obl: list[
        ReactiveCompositionalMultiphaseObltype
    ] = field(
        default_factory=list,
        metadata={
            "name": "ReactiveCompositionalMultiphaseOBL",
            "type": "Element",
            "namespace": "",
        },
    )
    seismicity_rate: list[SeismicityRateType] = field(
        default_factory=list,
        metadata={
            "name": "SeismicityRate",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_fvm: list[SinglePhaseFvmtype] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_hybrid_fvm: list[SinglePhaseHybridFvmtype] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseHybridFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics: list[SinglePhasePoromechanicsType] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures: list[
        SinglePhasePoromechanicsConformingFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures_alm: list[
        SinglePhasePoromechanicsConformingFracturesAlmtype
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFracturesALM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_conforming_fractures_reservoir: list[
        SinglePhasePoromechanicsConformingFracturesReservoirType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsConformingFracturesReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_embedded_fractures: list[
        SinglePhasePoromechanicsEmbeddedFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsEmbeddedFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_poromechanics_reservoir: list[
        SinglePhasePoromechanicsReservoirType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhasePoromechanicsReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_proppant_fvm: list[SinglePhaseProppantFvmtype] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseProppantFVM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir: list[SinglePhaseReservoirType] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoir",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics: list[
        SinglePhaseReservoirPoromechanicsType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanics",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_conforming_fractures: list[
        SinglePhaseReservoirPoromechanicsConformingFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanicsConformingFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_reservoir_poromechanics_conforming_fractures_alm: list[
        SinglePhaseReservoirPoromechanicsConformingFracturesAlmtype
    ] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseReservoirPoromechanicsConformingFracturesALM",
            "type": "Element",
            "namespace": "",
        },
    )
    single_phase_well: list[SinglePhaseWellType] = field(
        default_factory=list,
        metadata={
            "name": "SinglePhaseWell",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_augmented_lagrangian_contact: list[
        SolidMechanicsAugmentedLagrangianContactType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsAugmentedLagrangianContact",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_embedded_fractures: list[
        SolidMechanicsEmbeddedFracturesType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsEmbeddedFractures",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_lagrange_contact: list[
        SolidMechanicsLagrangeContactType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsLagrangeContact",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_lagrange_contact_bubble_stab: list[
        SolidMechanicsLagrangeContactBubbleStabType
    ] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanicsLagrangeContactBubbleStab",
            "type": "Element",
            "namespace": "",
        },
    )
    solid_mechanics_lagrangian_fem: list[SolidMechanicsLagrangianFemtype] = (
        field(
            default_factory=list,
            metadata={
                "name": "SolidMechanicsLagrangianFEM",
                "type": "Element",
                "namespace": "",
            },
        )
    )
    solid_mechanics_mpm: list[SolidMechanicsMpmtype] = field(
        default_factory=list,
        metadata={
            "name": "SolidMechanics_MPM",
            "type": "Element",
            "namespace": "",
        },
    )
    surface_generator: list[SurfaceGeneratorType] = field(
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
            "name": "gravityVector",
            "type": "Attribute",
            "pattern": r".*[\[\]`$].*|\s*\{\s*([+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*,\s*){2}[+-]?[\d]*([\d]\.?|\.[\d])[\d]*([eE][-+]?[\d]+|\s*)\s*\}\s*",
        },
    )


class ProblemType(BaseModel):
    model_config = ConfigDict(defer_build=True)
    events: list[EventsType] = field(
        default_factory=list,
        metadata={
            "name": "Events",
            "type": "Element",
            "namespace": "",
        },
    )
    external_data_source: list[ExternalDataSourceType] = field(
        default_factory=list,
        metadata={
            "name": "ExternalDataSource",
            "type": "Element",
            "namespace": "",
        },
    )
    field_specifications: list[FieldSpecificationsType] = field(
        default_factory=list,
        metadata={
            "name": "FieldSpecifications",
            "type": "Element",
            "namespace": "",
        },
    )
    functions: list[FunctionsType] = field(
        default_factory=list,
        metadata={
            "name": "Functions",
            "type": "Element",
            "namespace": "",
        },
    )
    geometry: list[GeometryType] = field(
        default_factory=list,
        metadata={
            "name": "Geometry",
            "type": "Element",
            "namespace": "",
        },
    )
    mesh: list[MeshType] = field(
        default_factory=list,
        metadata={
            "name": "Mesh",
            "type": "Element",
            "namespace": "",
        },
    )
    numerical_methods: list[NumericalMethodsType] = field(
        default_factory=list,
        metadata={
            "name": "NumericalMethods",
            "type": "Element",
            "namespace": "",
        },
    )
    outputs: list[OutputsType] = field(
        default_factory=list,
        metadata={
            "name": "Outputs",
            "type": "Element",
            "namespace": "",
        },
    )
    solvers: list[SolversType] = field(
        default_factory=list,
        metadata={
            "name": "Solvers",
            "type": "Element",
            "namespace": "",
        },
    )
    tasks: list[TasksType] = field(
        default_factory=list,
        metadata={
            "name": "Tasks",
            "type": "Element",
            "namespace": "",
        },
    )
    constitutive: list[ConstitutiveType] = field(
        default_factory=list,
        metadata={
            "name": "Constitutive",
            "type": "Element",
            "namespace": "",
        },
    )
    element_regions: list[ElementRegionsType] = field(
        default_factory=list,
        metadata={
            "name": "ElementRegions",
            "type": "Element",
            "namespace": "",
        },
    )
    particle_regions: list[ParticleRegionsType] = field(
        default_factory=list,
        metadata={
            "name": "ParticleRegions",
            "type": "Element",
            "namespace": "",
        },
    )
    included: list[IncludedType] = field(
        default_factory=list,
        metadata={
            "name": "Included",
            "type": "Element",
            "namespace": "",
        },
    )
    parameters: list[ParametersType] = field(
        default_factory=list,
        metadata={
            "name": "Parameters",
            "type": "Element",
            "namespace": "",
        },
    )
    benchmarks: list[BenchmarksType] = field(
        default_factory=list,
        metadata={
            "name": "Benchmarks",
            "type": "Element",
            "namespace": "",
        },
    )


class Problem(ProblemType):
    pass
    model_config = ConfigDict(defer_build=True)
