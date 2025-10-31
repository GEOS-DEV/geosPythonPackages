# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from enum import Enum

from typing_extensions import Self

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

    def __init__( self: Self, attributeName: str, nbComponent: int, onPoints: bool ) -> None:
        """Define the enumeration to store attribute properties.

        Args:
            attributeName (str): name of the attribute
            nbComponent (int): number of component: 1 is scalar attribute, >1 is
                vectorial attribute
            onPoints (bool): location of the attribute: on Points (True) or on Cells
                (False)
        """
        self.attributeName: str = attributeName
        self.nbComponent: int = nbComponent
        self.isOnPoints: bool = onPoints

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
    POROSITY_REF_SUFFIX = "_referencePorosity"
    BULK_MODULUS_SUFFIX = "_bulkModulus"
    SHEAR_MODULUS_SUFFIX = "_shearModulus"
    GRAIN_BULK_MODULUS_SUFFIX = "_grainBulkModulus"
    BIOT_COEFFICIENT_SUFFIX = "_biotCoefficient"

    # fluid attributes suffix
    PHASE_DENSITY_SUFFIX = "_phaseDensity"
    PHASE_MASS_DENSITY_SUFFIX = "_phaseMassDensity"
    PHASE_VISCOSITY_SUFFIX = "_phaseViscosity"
    PHASE_FRACTION_SUFFIX = "_phaseFraction"

    # surface attribute transfer suffix
    SURFACE_PLUS_SUFFIX = "_Plus"
    SURFACE_MINUS_SUFFIX = "_Minus"


class GeosMeshOutputsEnum( AttributeEnum ):
    """Attribute names that come from Geos.

    Define the names of Geos outputs, the number of components
    for vectorial attributes, and the location (Point or Cell) in the mesh
    """

    # IDs
    POINTS_ID = ( "Point ID", 1, True )
    CELL_ID = ( "Cell ID", 1, False )
    VTK_ORIGINAL_CELL_ID = ( "vtkOriginalCellIds", 1, False )

    # geometry attributes
    POINT = ( "Points", 3, True )
    ELEMENT_CENTER = ( "elementCenter", 1, False )

    # flow attributes
    WATER_DENSITY = ( "water_density", 1, False )
    PRESSURE = ( "pressure", 1, False )
    DELTA_PRESSURE = ( "deltaPressure", 1, False )
    MASS = ( "mass", 1, False )

    # geomechanics attributes
    ROCK_DENSITY = ( "density", 1, False )
    PERMEABILITY = ( "permeability", 1, False )
    POROSITY = ( "porosity", 1, False )
    POROSITY_INI = ( "porosityInitial", 1, False )

    BULK_MODULUS = ( "bulkModulus", 1, False )
    GRAIN_BULK_MODULUS = ( "bulkModulusGrains", 1, False )
    SHEAR_MODULUS = ( "shearModulus", 1, False )
    STRESS_EFFECTIVE = ( "stressEffective", 6, False )
    TOTAL_DISPLACEMENT = ( "totalDisplacement", 4, True )

    TRACTION = ( "traction", 3, False )
    DISPLACEMENT_JUMP = ( "displacementJump", 3, False )


################################################################################
#                        Post-processing attribute names                       #
################################################################################


class PostProcessingOutputsEnum( AttributeEnum ):
    """Compute attributes enumeration.

    Define the names of post-processing outputs, the number of components
    for vectorial attributes, and the location (Point or Cell) in the mesh
    """

    # general outputs
    BLOCK_INDEX = ( "blockIndex", 1, False )
    ADJACENT_CELL_SIDE = ( "SurfaceAdjacentCells", 1, False )

    # basic geomechanical outputs
    BULK_MODULUS_INITIAL = ( "bulkModulusInitial", 1, False )
    SHEAR_MODULUS_INITIAL = ( "shearModulusInitial", 1, False )
    YOUNG_MODULUS = ( "youngModulus", 1, False )
    YOUNG_MODULUS_INITIAL = ( "youngModulusInitial", 1, False )
    POISSON_RATIO = ( "poissonRatio", 1, False )
    POISSON_RATIO_INITIAL = ( "poissonRatioInitial", 1, False )
    OEDOMETRIC_MODULUS = ( "oedometricModulus", 1, False )
    BIOT_COEFFICIENT = ( "biotCoefficient", 1, False )
    BIOT_COEFFICIENT_INITIAL = ( "biotCoefficientInitial", 1, False )
    COMPRESSIBILITY = ( "compressibilityCoefficient", 1, False )
    COMPRESSIBILITY_REAL = ( "compressibilityCoefficient_real", 1, False )
    COMPRESSIBILITY_OED = ( "compressibilityCoefficient_oed", 1, False )
    SPECIFIC_GRAVITY = ( "specificGravity", 1, False )
    LITHOSTATIC_STRESS = ( "stressLithostatic", 1, False )
    STRESS_EFFECTIVE_INITIAL = ( "stressEffectiveInitial", 6, False )
    STRESS_EFFECTIVE_RATIO_REAL = ( "stressEffectiveRatio_real", 1, False )
    STRESS_EFFECTIVE_RATIO_OED = ( "stressEffectiveRatio_oed", 1, False )
    STRESS_TOTAL = ( "stressTotal", 6, False )
    STRESS_TOTAL_INITIAL = ( "stressTotalInitial", 6, False )
    STRESS_TOTAL_RATIO_REAL = ( "stressTotalRatio_real", 1, False )
    STRESS_TOTAL_DELTA = ( "deltaStressTotal", 6, False )
    STRAIN_ELASTIC = ( "strainElastic", 6, False )
    RSP_OED = ( "rsp_oed", 1, False )
    RSP_REAL = ( "rsp_real", 6, False )

    # advanced geomechanical outputs
    CRITICAL_TOTAL_STRESS_RATIO = ( "totalStressRatioCritical_real", 1, False )
    TOTAL_STRESS_RATIO_THRESHOLD = ( "totalStressRatioThreshold_real", 1, False )
    CRITICAL_PORE_PRESSURE = ( "porePressureCritical_real", 1, False )
    CRITICAL_PORE_PRESSURE_THRESHOLD = ( "porePressureThreshold_real", 1, False )

    # surface outputs
    SCU = ( "SCU", 1, False )


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
            GeosMeshSuffixEnum.BULK_MODULUS_SUFFIX.value,
            GeosMeshSuffixEnum.SHEAR_MODULUS_SUFFIX.value,
            GeosMeshSuffixEnum.POROSITY_SUFFIX.value,
            GeosMeshSuffixEnum.POROSITY_REF_SUFFIX.value,
            GeosMeshSuffixEnum.PERMEABILITY_SUFFIX.value,
        ),
    )
    FLUID = (
        "Fluid",
        (
            GeosMeshSuffixEnum.PHASE_DENSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_VISCOSITY_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_FRACTION_SUFFIX.value,
            GeosMeshSuffixEnum.PHASE_MASS_DENSITY_SUFFIX.value,
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
