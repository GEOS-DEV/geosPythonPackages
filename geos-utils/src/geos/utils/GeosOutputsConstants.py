# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
from enum import Enum

from typing_extensions import Self
from geos.utils.pieceEnum import Piece

__doc__ = """
GeosOutputsConstants module defines useful constant names such as attribute
names, domain names, phase types, and the lists of attribute names to process.

.. WARNING::
    Names may need to be updated when modifications occur in the GEOS code.

.. todo::

    If possible, link GEOS names directly with GEOS code instead of redefining
    them here.

"""

#: Phase separator in Geos output log file.
PHASE_SEP: str = "_"
FAILURE_ENVELOPE: str = "FailureEnvelope"


class AttributeEnum( Enum ):

    def __init__( self: Self, attributeName: str, nbComponent: int, piece: Piece ) -> None:
        """Define the enumeration to store attribute properties.

        Args:
            attributeName (str): name of the attribute.
            nbComponent (int): number of component: 1 is scalar attribute, >1 is vectorial attribute.
            piece (Piece): The piece of the attribute.
        """
        self.attributeName: str = attributeName
        self.nbComponent: int = nbComponent
        self.piece: Piece = piece

    def __repr__( self: Self ) -> str:
        """Get the string of AttributeEnum.

        Returns:
            str: string of AttributeEnum.
        """
        return f"<{self.__class__.__name__}.{self.attributeName}>.{self.nbComponent}>"


################################################################################
#                          Searched keywords in geos log                       #
################################################################################
class GeosLogOutputsEnum( Enum ):
    """Define the keywords in Geos log."""

    # flow keywords
    PHASE = "phase"

    # well keywords

    # aquifer keywords

    # convergence keywords


################################################################################
#                      Attribute names in the output mesh                      #
################################################################################


# list of node names from Geos
class GeosDomainNameEnum( Enum ):
    """Name of the nodes in the MultiBlock data tree."""

    VOLUME_DOMAIN_NAME = "CellElementRegion"
    FAULT_DOMAIN_NAME = "SurfaceElementRegion"
    WELL_DOMAIN_NAME = "WellElementRegion"


# Attributes are defined according to a tuple (str, int, bool) that contains the
# name of the attribute, the number of components for vectorial attributes and
# a boolean that evaluates to True if the attribute is stored on Points, and False
# if it is stored on Cells


class GeosMeshSuffixEnum( Enum ):
    """Define the suffix of attributes in Geos output mesh."""

    # rock attributes suffix
    DENSITY_SUFFIX = "_density"
    STRESS_SUFFIX = "_stress"
    STRAIN_SUFFIX = "strain"
    PERMEABILITY_SUFFIX = "_permeability"
    POROSITY_SUFFIX = "_porosity"
    POROSITY_INIT_SUFFIX = "_initialPorosity"
    POROSITY_REF_SUFFIX = "_referencePorosity"
    BULK_MODULUS_SUFFIX = "_bulkModulus"
    SHEAR_MODULUS_SUFFIX = "_shearModulus"
    GRAIN_BULK_MODULUS_SUFFIX = "_grainBulkModulus"
    BIOT_COEFFICIENT_SUFFIX = "_biotCoefficient"

    # fluid attributes suffix multiPhases
    TOTAL_FLUID_DENSITY_SUFFIX = "_totalDensity"
    PHASE_DENSITY_SUFFIX = "_phaseDensity"
    PHASE_FRACTION_SUFFIX = "_phaseFraction"
    PHASE_MASS_DENSITY_SUFFIX = "_phaseMassDensity"
    PHASE_VISCOSITY_SUFFIX = "_phaseViscosity"
    PHASE_INTERNAL_ENERGY_SUFFIX = "_phaseInternalEnergy"
    PHASE_COMP_FRACTION_SUFFIX = "_phaseCompFraction"
    PHASE_REAL_PERM_SUFFIX = "_phaseRelPerm"
    PHASE_TRAP_VOL_FRACTION_SUFFIX = "_phaseTrappedVolFraction"

    # fluid attributes suffix singlePhase
    FLUID_DENSITY_SUFFIX = "_density"
    FLUID_VISCOSITY_SUFFIX = "_viscosity"
    FLUID_DENSITY_DERIVATE_SUFFIX = "_dDensity"
    FLUID_VISCOSITY_DERIVATE_SUFFIX = "_dViscosity"
    FLUID_INTERNAL_ENERGY_SUFFIX = "_internalEnergy"
    FLUID_INTERNAL_ENERGY_DERIVATE_SUFFIX = "_dInternalEnergy"
    FLUID_ENTHALPY_SUFFIX = "_enthalpy"
    FLUID_ENTHALPY_DERIVATE_SUFFIX = "_dEnthalpy"

    # surface attribute transfer suffix
    SURFACE_PLUS_SUFFIX = "_Plus"
    SURFACE_MINUS_SUFFIX = "_Minus"


class GeosMeshOutputsEnum( AttributeEnum ):
    """Attribute names that come from Geos.

    Define the names of Geos outputs, the number of components
    for vectorial attributes, and the location (Points or Cells) in the mesh.
    """

    # IDs
    POINTS_ID = ( "Point ID", 1, Piece.POINTS )
    CELL_ID = ( "Cell ID", 1, Piece.CELLS )
    VTK_ORIGINAL_CELL_ID = ( "vtkOriginalCellIds", 1, Piece.CELLS )

    # geometry attributes
    POINT = ( "Points", 3, Piece.POINTS )
    ELEMENT_CENTER = ( "elementCenter", 1, Piece.CELLS )

    # flow attributes
    WATER_DENSITY = ( "water_density", 1, Piece.CELLS )
    PRESSURE = ( "pressure", 1, Piece.CELLS )
    DELTA_PRESSURE = ( "deltaPressure", 1, Piece.CELLS )
    MASS = ( "mass", 1, Piece.CELLS )

    # geomechanics attributes
    ROCK_DENSITY = ( "density", 1, Piece.CELLS )
    PERMEABILITY = ( "permeability", 1, Piece.CELLS )
    POROSITY = ( "porosity", 1, Piece.CELLS )
    POROSITY_INI = ( "porosityInitial", 1, Piece.CELLS )

    BULK_MODULUS = ( "bulkModulus", 1, Piece.CELLS )
    GRAIN_BULK_MODULUS = ( "bulkModulusGrains", 1, Piece.CELLS )
    SHEAR_MODULUS = ( "shearModulus", 1, Piece.CELLS )
    STRESS_EFFECTIVE = ( "stressEffective", 6, Piece.CELLS )
    TOTAL_DISPLACEMENT = ( "totalDisplacement", 4, Piece.POINTS )

    TRACTION = ( "traction", 3, Piece.CELLS )
    DISPLACEMENT_JUMP = ( "displacementJump", 3, Piece.CELLS )


################################################################################
#                        Post-processing attribute names                       #
################################################################################


class PostProcessingOutputsEnum( AttributeEnum ):
    """Compute attributes enumeration.

    Define the names of post-processing outputs, the number of components
    for vectorial attributes, and the location (Point or Cell) in the mesh
    """

    # general outputs
    BLOCK_INDEX = ( "blockIndex", 1, Piece.CELLS )
    ADJACENT_CELL_SIDE = ( "SurfaceAdjacentCells", 1, Piece.CELLS )

    # basic geomechanical outputs
    BULK_MODULUS_INITIAL = ( "bulkModulusInitial", 1, Piece.CELLS )
    SHEAR_MODULUS_INITIAL = ( "shearModulusInitial", 1, Piece.CELLS )
    YOUNG_MODULUS = ( "youngModulus", 1, Piece.CELLS )
    YOUNG_MODULUS_INITIAL = ( "youngModulusInitial", 1, Piece.CELLS )
    POISSON_RATIO = ( "poissonRatio", 1, Piece.CELLS )
    POISSON_RATIO_INITIAL = ( "poissonRatioInitial", 1, Piece.CELLS )
    OEDOMETRIC_MODULUS = ( "oedometricModulus", 1, Piece.CELLS )
    BIOT_COEFFICIENT = ( "biotCoefficient", 1, Piece.CELLS )
    BIOT_COEFFICIENT_INITIAL = ( "biotCoefficientInitial", 1, Piece.CELLS )
    COMPRESSIBILITY = ( "compressibilityCoefficient", 1, Piece.CELLS )
    COMPRESSIBILITY_REAL = ( "compressibilityCoefficient_real", 1, Piece.CELLS )
    COMPRESSIBILITY_OED = ( "compressibilityCoefficient_oed", 1, Piece.CELLS )
    SPECIFIC_GRAVITY = ( "specificGravity", 1, Piece.CELLS )
    LITHOSTATIC_STRESS = ( "stressLithostatic", 1, Piece.CELLS )
    STRESS_EFFECTIVE_INITIAL = ( "stressEffectiveInitial", 6, Piece.CELLS )
    STRESS_EFFECTIVE_RATIO_REAL = ( "stressEffectiveRatio_real", 1, Piece.CELLS )
    STRESS_EFFECTIVE_RATIO_OED = ( "stressEffectiveRatio_oed", 1, Piece.CELLS )
    STRESS_TOTAL = ( "stressTotal", 6, Piece.CELLS )
    STRESS_TOTAL_INITIAL = ( "stressTotalInitial", 6, Piece.CELLS )
    STRESS_TOTAL_RATIO_REAL = ( "stressTotalRatio_real", 1, Piece.CELLS )
    STRESS_TOTAL_DELTA = ( "deltaStressTotal", 6, Piece.CELLS )
    STRAIN_ELASTIC = ( "strainElastic", 6, Piece.CELLS )
    RSP_OED = ( "rsp_oed", 1, Piece.CELLS )
    RSP_REAL = ( "rsp_real", 6, Piece.CELLS )

    # advanced geomechanical outputs
    CRITICAL_TOTAL_STRESS_RATIO = ( "totalStressRatioCritical_real", 1, Piece.CELLS )
    TOTAL_STRESS_RATIO_THRESHOLD = ( "totalStressRatioThreshold_real", 1, Piece.CELLS )
    CRITICAL_PORE_PRESSURE = ( "porePressureCritical_real", 1, Piece.CELLS )
    CRITICAL_PORE_PRESSURE_THRESHOLD = ( "porePressureThreshold_real", 1, Piece.CELLS )

    # surface outputs
    SCU = ( "SCU", 1, Piece.CELLS )


class PhaseTypeEnum( Enum ):

    def __init__( self: Self, phaseType: str, attributes: tuple[ str, ...] ) -> None:
        """Define the main phases and associated property suffix.

        Args:
            phaseType (str): name of the type of phase

            attributes (tuple[str,...]): list of attributes
        """
        self.type: str = phaseType
        self.attributes: tuple[ str, ...] = attributes

    ROCK = (
        "Rock",
        (
            GeosMeshSuffixEnum.DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.STRESS_SUFFIX.value,
            GeosMeshSuffixEnum.PERMEABILITY_SUFFIX.value,
            GeosMeshSuffixEnum.POROSITY_SUFFIX.value,
            GeosMeshSuffixEnum.POROSITY_INIT_SUFFIX.value,
            GeosMeshSuffixEnum.POROSITY_REF_SUFFIX.value,
            GeosMeshSuffixEnum.BULK_MODULUS_SUFFIX.value,
            GeosMeshSuffixEnum.SHEAR_MODULUS_SUFFIX.value,
            GeosMeshSuffixEnum.GRAIN_BULK_MODULUS_SUFFIX.value,
            GeosMeshSuffixEnum.BIOT_COEFFICIENT_SUFFIX.value,
        ),
    )
    FLUID = (
        "Fluid",
        (
            GeosMeshSuffixEnum.TOTAL_FLUID_DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_FRACTION_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_MASS_DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_VISCOSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_INTERNAL_ENERGY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_COMP_FRACTION_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_REAL_PERM_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_TRAP_VOL_FRACTION_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_VISCOSITY_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_DENSITY_DERIVATE_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_VISCOSITY_DERIVATE_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_INTERNAL_ENERGY_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_INTERNAL_ENERGY_DERIVATE_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_ENTHALPY_SUFFIX.value,
            GeosMeshSuffixEnum.FLUID_ENTHALPY_DERIVATE_SUFFIX.value,
        ),
    )
    UNKNOWN = ( "Other", () )


class FluidPrefixEnum( Enum ):
    """Define usual names used for the fluid phase."""

    WATER = "water"
    FLUID = "fluid"
    GAS = "gas"


class OutputObjectEnum( Enum ):
    """Kind of objects present in GEOS pvd output."""

    VOLUME = "Volume"
    FAULTS = "Faults"
    WELLS = "Wells"


class ComponentNameEnum( Enum ):
    NONE = ( "", )
    XYZ = ( "XX", "YY", "ZZ", "YZ", "XZ", "XY" )
    NORMAL_TANGENTS = ( "normal", "tangent1", "tangent2", "T1T2", "NT2", "NT1" )


def getRockSuffixRenaming() -> dict[ str, str ]:
    """Get the list of attributes to rename according to suffix.

    Returns:
         dict[str,str]: dictionary where suffix are keys and new names are values
    """
    return {
        GeosMeshSuffixEnum.DENSITY_SUFFIX.value: GeosMeshOutputsEnum.ROCK_DENSITY.attributeName,
        GeosMeshSuffixEnum.STRESS_SUFFIX.value: GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName,
        GeosMeshSuffixEnum.PERMEABILITY_SUFFIX.value: GeosMeshOutputsEnum.PERMEABILITY.attributeName,
        GeosMeshSuffixEnum.POROSITY_SUFFIX.value: GeosMeshOutputsEnum.POROSITY.attributeName,
        GeosMeshSuffixEnum.POROSITY_REF_SUFFIX.value: GeosMeshOutputsEnum.POROSITY_INI.attributeName,
        GeosMeshSuffixEnum.BULK_MODULUS_SUFFIX.value: GeosMeshOutputsEnum.BULK_MODULUS.attributeName,
        GeosMeshSuffixEnum.SHEAR_MODULUS_SUFFIX.value: GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName,
        GeosMeshSuffixEnum.GRAIN_BULK_MODULUS_SUFFIX.value: GeosMeshOutputsEnum.GRAIN_BULK_MODULUS.attributeName,
        GeosMeshSuffixEnum.BIOT_COEFFICIENT_SUFFIX.value: PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName,
        GeosMeshSuffixEnum.STRAIN_SUFFIX.value: PostProcessingOutputsEnum.STRAIN_ELASTIC.attributeName,
    }


def getAttributeToTransferFromInitialTime() -> dict[ str, str ]:
    """Get the list of attributes to copy from initial time step.

    Returns:
         dict[str,str]: dictionary where attribute names are keys and copied
         names are values
    """
    return {
        GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName:
        PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.attributeName,
        GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName:
        PostProcessingOutputsEnum.SHEAR_MODULUS_INITIAL.attributeName,
        GeosMeshOutputsEnum.BULK_MODULUS.attributeName:
        PostProcessingOutputsEnum.BULK_MODULUS_INITIAL.attributeName,
        PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName:
        PostProcessingOutputsEnum.YOUNG_MODULUS_INITIAL.attributeName,
        PostProcessingOutputsEnum.POISSON_RATIO.attributeName:
        PostProcessingOutputsEnum.POISSON_RATIO_INITIAL.attributeName,
    }
