# SPDX-License-Identifier: Apache-2.0
# # SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
from typing import Any
import numpy as np
import numpy.typing as npt

from geos_posp.processing.MohrCoulomb import MohrCoulomb
from geos.utils.algebraFunctions import getAttributeMatrixFromVector
from geos.utils.PhysicalConstants import (
    EPSILON, )

__doc__ = """Functions to compute additional geomechanical properties."""


def specificGravity( density: npt.NDArray[ np.float64 ], specificDensity: float ) -> npt.NDArray[ np.float64 ]:
    r"""Compute the specific gravity.

    .. math::
        SG = \frac{\rho}{\rho_f}

    Args:
        density (npt.NDArray[np.float64]): density (:math:`\rho` - kg/m³)
        specificDensity (float): fluid density (:math:`\rho_f` - kg/m³)

    Returns:
        npt.NDArray[np.float64]: specific gravity (*SG* - no unit)

    """
    assert density is not None, "Density data must be defined"

    if abs( specificDensity ) < EPSILON:
        return np.full_like( density, np.nan )
    return ( density / specificDensity ).astype( np.float64 )


# https://en.wikipedia.org/wiki/Elastic_modulus
def youngModulus( bulkModulus: npt.NDArray[ np.float64 ],
                  shearModulus: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute Young modulus.

    .. math::
        E = \frac{9K.G}{3K+G}

    Args:
        bulkModulus (npt.NDArray[np.float64]): Bulk modulus (*K* - Pa)
        shearModulus (npt.NDArray[np.float64]): Shear modulus (*G* - Pa)

    Returns:
        npt.NDArray[np.float64]: Young modulus (*E* - Pa)

    """
    assert bulkModulus is not None, "Bulk modulus must be defined"
    assert shearModulus is not None, "Shear modulus must be defined"
    # manage division by 0 by replacing with nan
    assert bulkModulus.size == shearModulus.size, ( "Bulk modulus array and Shear modulus array" +
                                                    " sizes (i.e., number of cells) must be equal." )

    den: npt.NDArray[ np.float64 ] = 3.0 * bulkModulus + shearModulus
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    young: npt.NDArray[ np.float64 ] = 9.0 * bulkModulus * shearModulus / den
    young[ mask ] = np.nan
    return young


def poissonRatio( bulkModulus: npt.NDArray[ np.float64 ],
                  shearModulus: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute Poisson's ratio.

    .. math::
        \nu = \frac{3K-2G}{2(3K+G)}

    Args:
        bulkModulus (npt.NDArray[np.float64]): Bulk modulus (*K* - Pa)
        shearModulus (npt.NDArray[np.float64]): Shear modulus (*G* - Pa)

    Returns:
        npt.NDArray[np.float64]: Poisson's ratio (:math:`\nu`)

    """
    assert bulkModulus is not None, "Bulk modulus must be defined"
    assert shearModulus is not None, "Shear modulus must be defined"
    assert bulkModulus.size == shearModulus.size, ( "Bulk modulus array and Shear modulus array" +
                                                    " sizes (i.e., number of cells) must be equal." )
    # manage division by 0 by replacing with nan
    den: npt.NDArray[ np.float64 ] = 2.0 * ( 3.0 * bulkModulus + shearModulus )
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    poisson: npt.NDArray[ np.float64 ] = ( 3.0 * bulkModulus - 2.0 * shearModulus ) / den
    poisson[ mask ] = np.nan
    return poisson


def bulkModulus( youngModulus: npt.NDArray[ np.float64 ],
                 poissonRatio: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute bulk Modulus from young modulus and poisson ratio.

    .. math::
        K = \frac{E}{3(1-2\nu)}

    Args:
        youngModulus (npt.NDArray[np.float64]): Young modulus (*E* - Pa)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: Bulk modulus (*K* - Pa)

    """
    assert poissonRatio is not None, "Poisson's ratio must be defined"
    assert youngModulus is not None, "Young modulus must be defined"

    den: npt.NDArray[ np.float64 ] = 3.0 * ( 1.0 - 2.0 * poissonRatio )
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    bulkMod: npt.NDArray[ np.float64 ] = youngModulus / den
    bulkMod[ mask ] = np.nan
    return bulkMod


def shearModulus( youngModulus: npt.NDArray[ np.float64 ],
                  poissonRatio: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute shear Modulus from young modulus and poisson ratio.

    .. math::
        G = \frac{E}{2(1+\nu)}

    Args:
        youngModulus (npt.NDArray[np.float64]): Young modulus (*E* - Pa)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: Shear modulus (*G* - Pa)

    """
    assert poissonRatio is not None, "Poisson's ratio must be defined"
    assert youngModulus is not None, "Young modulus must be defined"

    den: npt.NDArray[ np.float64 ] = 2.0 * ( 1.0 + poissonRatio )
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    shearMod: npt.NDArray[ np.float64 ] = youngModulus / den
    shearMod[ mask ] = np.nan
    return shearMod


def lambdaCoefficient( youngModulus: npt.NDArray[ np.float64 ],
                       poissonRatio: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute lambda coefficient from young modulus and Poisson ratio.

    .. math::
        \lambda = \frac{E*\nu}{(1+\nu)(1-2\nu)}

    Args:
        youngModulus (npt.NDArray[np.float64]): Young modulus (*E* - Pa)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: lambda coefficient (:math:`\lambda`)

    """
    lambdaCoeff: npt.NDArray[ np.float64 ] = poissonRatio * youngModulus
    den: npt.NDArray[ np.float64 ] = ( 1.0 + poissonRatio ) * ( 1.0 - 2.0 * poissonRatio )
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    lambdaCoeff /= den
    lambdaCoeff[ mask ] = np.nan
    return lambdaCoeff


def oedometricModulus( Edef: npt.NDArray[ np.float64 ],
                       poissonRatio: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute Oedometric modulus.

    .. math::
        M_{oed} = \frac{E_{def}}{1-2\frac{\nu^2}{1-\nu}}

    Args:
        Edef (npt.NDArray[np.float64]): Deformation modulus (:math:`E_{def}` - Pa)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: Oedometric modulus (:math:`M_{oed}` - Pa)

    """
    assert poissonRatio is not None, "Poisson's ratio must be defined"
    assert Edef is not None, "Deformation modulus must be defined"

    assert Edef.size == poissonRatio.size, ( "Deformation modulus array and Poisson's" +
                                             " ratio array sizes (i.e., number of cells) must be equal." )
    den: npt.NDArray[ np.float64 ] = 1.0 - ( 2.0 * poissonRatio * poissonRatio ) / ( 1.0 - poissonRatio )

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    EodMod: npt.NDArray[ np.float64 ] = Edef / den
    EodMod[ mask ] = np.nan
    return EodMod


def biotCoefficient( Kgrain: float, bulkModulus: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute Biot coefficient.

    .. math::
        b = 1-\frac{K}{K_{grain}}

    Args:
        Kgrain (float): grain bulk modulus (:math:`K_{grain}` - Pa)
        bulkModulus (npt.NDArray[np.float64]): default bulk modulus (*K* - Pa)

    Returns:
        npt.NDArray[np.float64]: biot coefficient (*b*)

    """
    assert bulkModulus is not None, "Bulk modulus must be defined"

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( Kgrain ) < EPSILON
    den: npt.NDArray[ np.float64 ] = np.copy( Kgrain )
    den[ mask ] = 1.0
    biot: npt.NDArray[ np.float64 ] = 1.0 - bulkModulus / den
    biot[ mask ] = np.nan
    return biot


def totalStress(
    effectiveStress: npt.NDArray[ np.float64 ],
    biot: npt.NDArray[ np.float64 ],
    pressure: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute total stress from effective stress, pressure, and Biot coeff.

    .. math::
        \sigma_{tot} = \sigma_{eff}-bP

    Args:
        effectiveStress (npt.NDArray[np.float64]): effective stress
            (:math:`\sigma_{eff}` - Pa) using Geos convention
        biot (npt.NDArray[np.float64]): Biot coefficient (*b*)
        pressure (npt.NDArray[np.float64]): Pore pressure (*P* - Pa)

    Returns:
        npt.NDArray[np.float64]: total stress (:math:`\sigma_{tot}` - Pa)

    """
    assert effectiveStress is not None, "Effective stress must be defined"
    assert biot is not None, "Biot coefficient must be defined"
    assert pressure is not None, "Pressure must be defined"

    assert effectiveStress.shape[ 0 ] == biot.size, ( "Biot coefficient array and " +
                                                      "effective stress sizes (i.e., number of cells) must be equal." )
    assert biot.size == pressure.size, ( "Biot coefficient array and pressure array" +
                                         "sizes (i.e., number of cells) must be equal." )

    totalStress: npt.NDArray[ np.float64 ] = np.copy( effectiveStress )
    # pore pressure has an effect on normal stresses only
    # (cf. https://dnicolasespinoza.github.io/node5.html)
    nb: int = totalStress.shape[ 1 ] if totalStress.shape[ 1 ] < 4 else 3
    for j in range( nb ):
        totalStress[ :, j ] = effectiveStress[ :, j ] - biot * pressure
    return totalStress


def stressRatio( horizontalStress: npt.NDArray[ np.float64 ],
                 verticalStress: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute horizontal to vertical stress ratio.

    .. math::
        r = \frac{\sigma_h}{\sigma_v}

    Args:
        horizontalStress (npt.NDArray[np.float64]): horizontal stress
            (:math:`\sigma_h` - Pa)
        verticalStress (npt.NDArray[np.float64]): vertical stress
            (:math:`\sigma_v` - Pa)

    Returns:
        npt.NDArray[np.float64]: stress ratio (:math:`\sigma` - Pa)

    """
    assert horizontalStress is not None, "Horizontal stress must be defined"
    assert verticalStress is not None, "Vertical stress must be defined"

    assert horizontalStress.size == verticalStress.size, (
        "Horizontal stress array " + "and vertical stress array sizes (i.e., number of cells) must be equal." )

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( verticalStress ) < EPSILON
    verticalStress2: npt.NDArray[ np.float64 ] = np.copy( verticalStress )
    verticalStress2[ mask ] = 1.0
    ratio: npt.NDArray[ np.float64 ] = horizontalStress / verticalStress2
    ratio[ mask ] = np.nan
    return ratio


def lithostaticStress( depth: npt.NDArray[ np.float64 ], density: npt.NDArray[ np.float64 ],
                       gravity: float ) -> npt.NDArray[ np.float64 ]:
    """Compute the lithostatic stress.

    Args:
        depth (npt.NDArray[np.float64]): depth from surface - m)
        density (npt.NDArray[np.float64]): density of the overburden (kg/m³)
        gravity (float): gravity (m²/s)

    Returns:
        npt.NDArray[np.float64]: lithostatic stress (Pa)

    """
    # compute average density of the overburden of each point (replacing nan value by 0)

    # TODO: the formula should not depends on the density of the cell but the average
    # density of the overburden.
    # But how to compute the average density of the overburden in an unstructured mesh?

    # density2 = np.copy(density)
    # density2[np.isnan(density)] = 0
    # overburdenMeanDensity = np.cumsum(density) / np.arange(1, density.size+1, 1)

    # TODO: which convention? + or -?

    # TODO: Warning z coordinate may be + or - if 0 is sea level. Need to take dz from surface.
    # Is the surface always on top of the model?
    assert depth is not None, "Depth must be defined"
    assert density is not None, "Density must be defined"

    assert depth.size == density.size, ( "Depth array " +
                                         "and density array sizes (i.e., number of cells) must be equal." )
    # use -1*depth to agree with Geos convention (i.e., compression with negative stress)
    return -depth * density * gravity


def elasticStrainFromBulkShear(
    deltaEffectiveStress: npt.NDArray[ np.float64 ],
    bulkModulus: npt.NDArray[ np.float64 ],
    shearModulus: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute elastic strain from Bulk and Shear moduli.

    See documentation on https://dnicolasespinoza.github.io/node5.html.

    .. math::
        \epsilon=\Delta\sigma_{eff}.C^{-1}


        C=\begin{pmatrix}
          K+\frac{4}{3}G & K-\frac{2}{3}G & K-\frac{2}{3}G &   0 &   0 &   0\\
          K-\frac{2}{3}G & K+\frac{4}{3}G & K-\frac{2}{3}G &   0 &   0 &   0\\
          K-\frac{2}{3}G & K-\frac{2}{3}G & K+\frac{4}{3}G &   0 &   0 &   0\\
                       0 &              0 &              0 & \nu &   0 &   0\\
                       0 &              0 &              0 &   0 & \nu &   0\\
                       0 &              0 &              0 &   0 &   0 & \nu\\
          \end{pmatrix}

    where *C* is stiffness tensor.


    Args:
        deltaEffectiveStress (npt.NDArray[np.float64]): effective stress
            variation (:math:`\Delta\sigma_{eff}` - Pa) [S11, S22, S33, S23, S13, S12]
        bulkModulus (npt.NDArray[np.float64]): Bulk modulus (*K* - Pa)
        shearModulus (npt.NDArray[np.float64]): Shear modulus (*G* - Pa)

    Returns:
        npt.NDArray[np.float64]: elastic strain (:math:`\epsilon`)

    """
    assert ( deltaEffectiveStress is not None ), "Effective stress variation must be defined"
    assert bulkModulus is not None, "Bulk modulus must be defined"
    assert shearModulus is not None, "Shear modulus must be defined"

    assert deltaEffectiveStress.shape[ 0 ] == bulkModulus.size, (
        "Effective stress variation " + " and bulk modulus array sizes (i.e., number of cells) must be equal." )
    assert shearModulus.size == bulkModulus.size, (
        "Shear modulus " + "and bulk modulus array sizes (i.e., number of cells) must be equal." )
    assert deltaEffectiveStress.shape[ 1 ] == 6, ( "Effective stress variation " +
                                                   "number of components must be equal to 6." )

    elasticStrain: npt.NDArray[ np.float64 ] = np.full_like( deltaEffectiveStress, np.nan )
    for i, stressVector in enumerate( deltaEffectiveStress ):
        stiffnessTensor: npt.NDArray[ np.float64 ] = shearModulus[ i ] * np.identity( 6, dtype=float )
        for k in range( 3 ):
            for m in range( 3 ):
                val: float = ( ( bulkModulus[ i ] + 4.0 / 3.0 * shearModulus[ i ] ) if k == m else
                               ( bulkModulus[ i ] - 2.0 / 3.0 * shearModulus[ i ] ) )
                stiffnessTensor[ k, m ] = val
        elasticStrain[ i ] = stressVector @ np.linalg.inv( stiffnessTensor )
    return elasticStrain


def elasticStrainFromYoungPoisson(
    deltaEffectiveStress: npt.NDArray[ np.float64 ],
    youngModulus: npt.NDArray[ np.float64 ],
    poissonRatio: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute elastic strain from Young modulus and Poisson ratio.

    See documentation on https://dnicolasespinoza.github.io/node5.html.

    .. math::
        \epsilon=\Delta\sigma_{eff}.C^{-1}


        C=\begin{pmatrix}
          \lambda+2G &    \lambda &    \lambda &   0 &   0 &   0\\
             \lambda & \lambda+2G &    \lambda &   0 &   0 &   0\\
             \lambda &    \lambda & \lambda+2G &   0 &   0 &   0\\
                   0 &          0 &          0 & \nu &   0 &   0\\
                   0 &          0 &          0 &   0 & \nu &   0\\
                   0 &          0 &          0 &   0 &   0 & \nu\\
          \end{pmatrix}

    where *C* is stiffness tensor, :math:`\nu` is shear modulus,
    :math:`\lambda` is lambda coefficient.

    Args:
        deltaEffectiveStress (npt.NDArray[np.float64]): effective stress
            variation (:math:`\Delta\sigma_{eff}` - Pa) [S11, S22, S33, S23, S13, S12]
        youngModulus (npt.NDArray[np.float64]): Young modulus (*E* - Pa)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: elastic strain (:math:`\epsilon`)

    """
    assert ( deltaEffectiveStress is not None ), "Effective stress variation must be defined"
    assert youngModulus is not None, "Bulk modulus must be defined"
    assert poissonRatio is not None, "Shear modulus must be defined"

    assert deltaEffectiveStress.shape[ 0 ] == youngModulus.size, (
        "Effective stress variation " + " and bulk modulus array sizes (i.e., number of cells) must be equal." )
    assert poissonRatio.size == youngModulus.size, (
        "Shear modulus " + "and bulk modulus array sizes (i.e., number of cells) must be equal." )
    assert deltaEffectiveStress.shape[ 1 ] == 6, ( "Effective stress variation " +
                                                   "number of components must be equal to 6." )

    # use of Lamé's equations
    lambdaCoeff: npt.NDArray[ np.float64 ] = lambdaCoefficient( youngModulus, poissonRatio )
    shearMod: npt.NDArray[ np.float64 ] = shearModulus( youngModulus, poissonRatio )

    elasticStrain: npt.NDArray[ np.float64 ] = np.full_like( deltaEffectiveStress, np.nan )
    for i, deltaStressVector in enumerate( deltaEffectiveStress ):
        stiffnessTensor: npt.NDArray[ np.float64 ] = shearMod[ i ] * np.identity( 6, dtype=float )
        for k in range( 3 ):
            for m in range( 3 ):
                val: float = ( ( lambdaCoeff[ i ] + 2.0 * shearMod[ i ] ) if k == m else ( lambdaCoeff[ i ] ) )
                stiffnessTensor[ k, m ] = val

        elasticStrain[ i ] = deltaStressVector @ np.linalg.inv( stiffnessTensor )
    return elasticStrain


def deviatoricStressPathOed( poissonRatio: npt.NDArray[ np.float64 ], ) -> npt.NDArray[ np.float64 ]:
    r"""Compute the Deviatoric Stress Path parameter in oedometric conditions.

    This parameter corresponds to the ratio between horizontal and vertical
    stresses in oedometric conditions.

    .. math::
        DSP=\frac{\nu}{1-\nu}

    Args:
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: Deviatoric Stress Path parameter in
            oedometric conditions (*DSP*)

    """
    assert poissonRatio is not None, "Poisson's ratio must be defined"

    # manage division by 0 by replacing with nan
    den: npt.NDArray[ np.float64 ] = 1 - poissonRatio
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    ratio: npt.NDArray[ np.float64 ] = poissonRatio / den
    ratio[ mask ] = np.nan
    return ratio


def reservoirStressPathReal( deltaStress: npt.NDArray[ np.float64 ],
                             deltaPressure: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute real reservoir stress path.

    .. math::
        RSP_{real}=\frac{\Delta\sigma}{\Delta P}

    Args:
        deltaStress (npt.NDArray[np.float64]): stress difference from start
            (:math:`\Delta\sigma` - Pa)
        deltaPressure (npt.NDArray[np.float64]): pressure difference from start
            (:math:`\Delta P` - Pa)

    Returns:
        npt.NDArray[np.float64]: reservoir stress path (:math:`RSP_{real}`)

    """
    assert deltaPressure is not None, "Pressure deviation must be defined"
    assert deltaStress is not None, "Stress deviation must be defined"

    assert deltaStress.shape[ 0 ] == deltaPressure.size, ( "Total stress array and pressure variation " +
                                                           "array sizes (i.e., number of cells) must be equal." )

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( deltaPressure ) < EPSILON
    den: npt.NDArray[ np.float64 ] = np.copy( deltaPressure )
    den[ mask ] = 1.0
    # use -1 to agree with Geos convention (i.e., compression with negative stress)
    # take the xx, yy, and zz components only
    rsp: npt.NDArray[ np.float64 ] = np.copy( deltaStress[ :, :3 ] )
    for j in range( rsp.shape[ 1 ] ):
        rsp[ :, j ] /= den
        rsp[ mask, j ] = np.nan
    return rsp


def reservoirStressPathOed( biotCoefficient: npt.NDArray[ np.float64 ],
                            poissonRatio: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute reservoir stress path in oedometric conditions.

    .. math::
        RSP_{oed}=b\frac{1-2\nu}{1-\nu}

    Args:
        biotCoefficient (npt.NDArray[np.float64]): biot coefficient (*b*)
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`)

    Returns:
        npt.NDArray[np.float64]: reservoir stress path (:math:`RSP_{oed}`)

    """
    assert biotCoefficient is not None, "Biot coefficient must be defined"
    assert poissonRatio is not None, "Poisson's ratio must be defined"

    assert biotCoefficient.size == poissonRatio.size, (
        "Biot coefficient array and " + "Poisson's ratio array sizes (i.e., number of cells) must be equal." )

    # manage division by 0 by replacing with nan
    den: npt.NDArray[ np.float64 ] = 1.0 - poissonRatio
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0
    rsp: npt.NDArray[ np.float64 ] = biotCoefficient * ( 1.0 - 2.0 * poissonRatio ) / den
    rsp[ mask ] = np.nan
    return rsp


def criticalTotalStressRatio( pressure: npt.NDArray[ np.float64 ],
                              verticalStress: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute critical total stress ratio.

    Corresponds to the fracture index from Lemgruber-Traby et al (2024).
    Fracturing can occur in areas where K > Total stress ratio.
    (see Lemgruber-Traby, A., Cacas, M. C., Bonte, D., Rudkiewicz, J. L., Gout, C.,
    & Cornu, T. (2024). Basin modelling workflow applied to the screening of deep
    aquifers for potential CO2 storage. Geoenergy, geoenergy2024-010.
    https://doi.org/10.1144/geoenergy2024-010)

    .. math::
        \sigma_{Ĉr}=\frac{P}{\sigma_v}

    Args:
        pressure (npt.NDArray[np.float64]): Pressure (*P* - Pa)
        verticalStress (npt.NDArray[np.float64]): Vertical total stress
            (:math:`\sigma_v` - Pa) using Geos convention

    Returns:
        npt.NDArray[np.float64]: critical total stress ratio
            (:math:`\sigma_{Cr}`)

    """
    assert pressure is not None, "Pressure must be defined"
    assert verticalStress is not None, "Vertical stress must be defined"

    assert pressure.size == verticalStress.size, (
        "pressure array and " + "vertical stress array sizes (i.e., number of cells) must be equal." )
    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( verticalStress ) < EPSILON
    # use -1 to agree with Geos convention (i.e., compression with negative stress)
    verticalStress2: npt.NDArray[ np.float64 ] = -1.0 * np.copy( verticalStress )
    verticalStress2[ mask ] = 1.0
    fi: npt.NDArray[ np.float64 ] = pressure / verticalStress2
    fi[ mask ] = np.nan
    return fi


def totalStressRatioThreshold( pressure: npt.NDArray[ np.float64 ],
                               horizontalStress: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute total stress ratio threshold.

    Corresponds to the fracture threshold from Lemgruber-Traby et al (2024).
    Fracturing can occur in areas where FT > 1.
    Equals FractureIndex / totalStressRatio.
    (see Lemgruber-Traby, A., Cacas, M. C., Bonte, D., Rudkiewicz, J. L., Gout, C.,
    & Cornu, T. (2024). Basin modelling workflow applied to the screening of deep
    aquifers for potential CO2 storage. Geoenergy, geoenergy2024-010.
    https://doi.org/10.1144/geoenergy2024-010)

    .. math::
        \sigma_{Th}=\frac{P}{\sigma_h}

    Args:
        pressure (npt.NDArray[np.float64]): Pressure (*P* - Pa)
        horizontalStress (npt.NDArray[np.float64]): minimal horizontal total
            stress (:math:`\sigma_h` - Pa) using Geos convention

    Returns:
        npt.NDArray[np.float64]: fracture threshold (:math:`\sigma_{Th}`)

    """
    assert pressure is not None, "Pressure must be defined"
    assert horizontalStress is not None, "Horizontal stress must be defined"

    assert pressure.size == horizontalStress.size, (
        "pressure array and " + "horizontal stress array sizes (i.e., number of cells) must be equal." )

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( horizontalStress ) < EPSILON
    # use -1 to agree with Geos convention (i.e., compression with negative stress)
    horizontalStress2: npt.NDArray[ np.float64 ] = -1.0 * np.copy( horizontalStress )
    horizontalStress2[ mask ] = 1.0
    ft: npt.NDArray[ np.float64 ] = pressure / horizontalStress2
    ft[ mask ] = np.nan
    return ft


def criticalPorePressure(
    stressVector: npt.NDArray[ np.float64 ],
    rockCohesion: float,
    frictionAngle: float = 0.0,
) -> npt.NDArray[ np.float64 ]:
    r"""Compute the critical pore pressure.

    Fracturing can occur in areas where Critical pore pressure is greater than
    the pressure.
    (see Khan, S., Khulief, Y., Juanes, R., Bashmal, S., Usman, M., & Al-Shuhail, A.
    (2024). Geomechanical Modeling of CO2 Sequestration: A Review Focused on CO2
    Injection and Monitoring. Journal of Environmental Chemical Engineering, 112847.
    https://doi.org/10.1016/j.jece.2024.112847)

    .. math::
        P_{Cr}=\frac{c.\cos(\alpha)}{1-\sin(\alpha)} + \frac{3\sigma_3-\sigma_1}{2}

    Args:
        stressVector (npt.NDArray[np.float64]): stress vector
            (:math:`\sigma` - Pa).
        rockCohesion (float): rock cohesion (*c* - Pa)
        frictionAngle (float, optional): friction angle (:math:`\alpha` - rad).

            Defaults to 0 rad.

    Returns:
        npt.NDArray[np.float64]: critical pore pressure (:math:`P_{Cr}` - Pa)

    """
    assert stressVector is not None, "Stress vector must be defined"
    assert stressVector.shape[ 1 ] == 6, "Stress vector must be of size 6."

    assert ( frictionAngle >= 0.0 ) and ( frictionAngle < np.pi / 2.0 ), ( "Fristion angle " +
                                                                           "must range between 0 and pi/2." )

    minimumPrincipalStress: npt.NDArray[ np.float64 ] = np.full( stressVector.shape[ 0 ], np.nan )
    maximumPrincipalStress: npt.NDArray[ np.float64 ] = np.copy( minimumPrincipalStress )
    for i in range( minimumPrincipalStress.shape[ 0 ] ):
        p3, p2, p1 = computeStressPrincipalComponentsFromStressVector( stressVector[ i ] )
        minimumPrincipalStress[ i ] = p3
        maximumPrincipalStress[ i ] = p1

    # assertion frictionAngle < np.pi/2., so sin(frictionAngle) != 1
    cohesiveTerm: npt.NDArray[ np.float64 ] = ( rockCohesion * np.cos( frictionAngle ) /
                                                ( 1 - np.sin( frictionAngle ) ) )
    residualTerm: npt.NDArray[ np.floating[ Any ] ] = ( 3 * minimumPrincipalStress - maximumPrincipalStress ) / 2.0
    return cohesiveTerm + residualTerm


def criticalPorePressureThreshold( pressure: npt.NDArray[ np.float64 ],
                                   criticalPorePressure: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    r"""Compute the critical pore pressure threshold.

    Defined as the ratio between pressure and critical pore pressure.
    Fracturing can occur in areas where critical pore pressure threshold is >1.

    .. math::
        P_{Th}=\frac{P}{P_{Cr}}

    Args:
        pressure (npt.NDArray[np.float64]): pressure (*P* - Pa)
        criticalPorePressure (npt.NDArray[np.float64]): Critical pore pressure
            (:math:`P_{Cr}` - Pa)

    Returns:
        npt.NDArray[np.float64]: Critical pore pressure threshold (:math:`P_{Th}`)

    """
    assert pressure is not None, "Pressure must be defined"
    assert criticalPorePressure is not None, "Critical pore pressure must be defined"

    assert pressure.size == criticalPorePressure.size, (
        "Pressure array and critical" + " pore pressure array sizes (i.e., number of cells) must be equal." )

    # manage division by 0 by replacing with nan
    mask: npt.NDArray[ np.bool_ ] = np.abs( criticalPorePressure ) < EPSILON
    den = np.copy( criticalPorePressure )
    den[ mask ] = 1.0
    index: npt.NDArray[ np.float64 ] = pressure / den
    index[ mask ] = np.nan
    return index


def compressibilityOed(
    shearModulus: npt.NDArray[ np.float64 ],
    bulkModulus: npt.NDArray[ np.float64 ],
    porosity: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute compressibility from elastic moduli and porosity.

    Compressibility formula is:

    .. math::
        C = \frac{1}{\phi}.\frac{3}{3K+4G}

    Args:
        shearModulus (npt.NDArray[np.float64]): shear modulus (*G* - Pa).
        bulkModulus (npt.NDArray[np.float64]): Bulk Modulus (*K* - Pa).
        porosity (npt.NDArray[np.float64]): Rock porosity (:math:`\phi`).

    Returns:
        npt.NDArray[np.float64]: Oedometric Compressibility (*C* - Pa^-1).

    """
    assert bulkModulus is not None, "Bulk modulus must be defined"
    assert shearModulus is not None, "Shear modulus must be defined"
    assert porosity is not None, "Porosity must be defined"
    mask1: npt.NDArray[ np.bool_ ] = np.abs( porosity ) < EPSILON
    den1: npt.NDArray[ np.float64 ] = np.copy( porosity )
    den1[ mask1 ] = 1.0

    den2: npt.NDArray[ np.float64 ] = 3.0 * bulkModulus + 4.0 * shearModulus
    mask2: npt.NDArray[ np.bool_ ] = np.abs( den2 ) < EPSILON
    den2[ mask2 ] = 1.0

    comprOed: npt.NDArray[ np.float64 ] = 1.0 / den1 * 3.0 / den2
    comprOed[ mask1 ] = np.nan
    comprOed[ mask2 ] = np.nan
    return comprOed


def compressibilityReal(
    deltaPressure: npt.NDArray[ np.float64 ],
    porosity: npt.NDArray[ np.float64 ],
    porosityInitial: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute compressibility from elastic moduli and porosity.

    Compressibility formula is:

    .. math::
        C = \frac{\phi-\phi_0}{\Delta P.\phi_0}

    Args:
        deltaPressure (npt.NDArray[np.float64]): Pressure deviation
            (:math:`\Delta P` - Pa).
        porosity (npt.NDArray[np.float64]): Rock porosity (:math:`\phi`).
        porosityInitial (npt.NDArray[np.float64]): initial porosity
            (:math:`\phi_0`).

    Returns:
        npt.NDArray[np.float64]: Real compressibility (*C* - Pa^-1).

    """
    assert deltaPressure is not None, "Pressure deviation must be defined"
    assert porosity is not None, "Porosity must be defined"
    assert porosityInitial is not None, "Initial porosity must be defined"

    den: npt.NDArray[ np.float64 ] = deltaPressure * porosityInitial
    mask: npt.NDArray[ np.bool_ ] = np.abs( den ) < EPSILON
    den[ mask ] = 1.0

    comprReal: npt.NDArray[ np.float64 ] = ( porosity - porosityInitial ) / den
    comprReal[ mask ] = np.nan
    return comprReal


def compressibility(
    poissonRatio: npt.NDArray[ np.float64 ],
    bulkModulus: npt.NDArray[ np.float64 ],
    biotCoefficient: npt.NDArray[ np.float64 ],
    porosity: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    r"""Compute compressibility from elastic moduli, biot coefficient and porosity.

    Compressibility formula is:

    .. math::
        C = \frac{1-2\nu}{\phi K}\left(\frac{b²(1+\nu)}{1-\nu} + 3(b-\phi)(1-b)\right)

    Args:
        poissonRatio (npt.NDArray[np.float64]): Poisson's ratio (:math:`\nu`).
        bulkModulus (npt.NDArray[np.float64]): Bulk Modulus (*K* - Pa)
        biotCoefficient (npt.NDArray[np.float64]): Biot coefficient (*b*).
        porosity (npt.NDArray[np.float64]): Rock porosity (:math:`\phi`).

    Returns:
        npt.NDArray[np.float64]: Compressibility array (*C* - Pa^-1).

    """
    assert poissonRatio is not None, "Poisson's ratio must be defined"
    assert bulkModulus is not None, "Bulk modulus must be defined"
    assert biotCoefficient is not None, "Biot coefficient must be defined"
    assert porosity is not None, "Porosity must be defined"

    term1: npt.NDArray[ np.float64 ] = 1.0 - 2.0 * poissonRatio

    mask: npt.NDArray[ np.bool_ ] = ( np.abs( bulkModulus ) < EPSILON ) * ( np.abs( porosity ) < EPSILON )
    denFac1: npt.NDArray[ np.float64 ] = porosity * bulkModulus
    term1[ mask ] = 1.0
    term1 /= denFac1

    term2M1: npt.NDArray[ np.float64 ] = ( biotCoefficient * biotCoefficient * ( 1 + poissonRatio ) )
    denTerm2M1: npt.NDArray[ np.float64 ] = 1 - poissonRatio
    mask2: npt.NDArray[ np.bool_ ] = np.abs( denTerm2M1 ) < EPSILON
    denTerm2M1[ mask2 ] = 1.0
    term2M1 /= denTerm2M1
    term2M1[ mask2 ] = np.nan

    term2M2: npt.NDArray[ np.float64 ] = ( 3.0 * ( biotCoefficient - porosity ) * ( 1 - biotCoefficient ) )
    term2: npt.NDArray[ np.float64 ] = term2M1 + term2M2
    return term1 * term2


def shearCapacityUtilization( traction: npt.NDArray[ np.float64 ], rockCohesion: float,
                              frictionAngle: float ) -> npt.NDArray[ np.float64 ]:
    r"""Compute shear capacity utilization (SCU).

    .. math::
        SCU = \frac{abs(\tau_1)}{\tau_{max}}

    where \tau_{max} is the Mohr-Coulomb failure threshold.

    Args:
        traction (npt.NDArray[np.float64]): traction vector
            (:math:`(\sigma, \tau_1, \tau2)` - Pa)
        rockCohesion (float): rock cohesion (*c* - Pa).
        frictionAngle (float): friction angle (:math:`\alpha` - rad).

    Returns:
        npt.NDArray[np.float64]: *SCU*

    """
    assert traction is not None, "Traction must be defined"
    assert traction.shape[ 1 ] == 3, "Traction vector must have 3 components."

    scu: npt.NDArray[ np.float64 ] = np.full( traction.shape[ 0 ], np.nan )
    for i in range( traction.shape[ 0 ] ):
        tractionVec: npt.NDArray[ np.float64 ] = traction[ i ]
        # use -1 to agree with Geos convention (i.e., compression with negative stress)
        stressNormal: npt.NDArray[ np.float64 ] = -1.0 * tractionVec[ 0 ]

        # compute failure envelope
        mohrCoulomb: MohrCoulomb = MohrCoulomb( rockCohesion, frictionAngle )
        tauFailure: float = float( mohrCoulomb.computeShearStress( stressNormal ) )
        scu_i: float = np.nan
        if tauFailure > 0:
            scu_i = np.abs( tractionVec[ 1 ] ) / tauFailure
        # compute SCU
        scu[ i ] = scu_i
    return scu


def computeStressPrincipalComponentsFromStressVector(
    stressVector: npt.NDArray[ np.float64 ], ) -> tuple[ float, float, float ]:
    """Compute stress principal components from stress vector.

    Args:
        stressVector (npt.NDArray[np.float64]): stress vector.

    Returns:
        tuple[float, float, float]: Principal components sorted in ascending
            order.

    """
    assert stressVector.size == 6, "Stress vector dimension is wrong."
    stressTensor: npt.NDArray[ np.float64 ] = getAttributeMatrixFromVector( stressVector )
    return computeStressPrincipalComponents( stressTensor )


def computeStressPrincipalComponents( stressTensor: npt.NDArray[ np.float64 ], ) -> tuple[ float, float, float ]:
    """Compute stress principal components.

    Args:
        stressTensor (npt.NDArray[np.float64]): stress tensor.

    Returns:
        tuple[float, float, float]: Principal components sorted in ascending
            order.

    """
    # get eigen values
    e_val, e_vec = np.linalg.eig( stressTensor )
    # sort principal stresses from smallest to largest
    p3, p2, p1 = np.sort( e_val )
    return ( p3, p2, p1 )


def computeNormalShearStress( stressTensor: npt.NDArray[ np.float64 ],
                              directionVector: npt.NDArray[ np.float64 ] ) -> tuple[ float, float ]:
    """Compute normal and shear stress according to stress tensor and direction.

    Args:
        stressTensor (npt.NDArray[np.float64]): 3x3 stress tensor
        directionVector (npt.NDArray[np.float64]): direction vector

    Returns:
        tuple[float, float]: normal and shear stresses.

    """
    assert stressTensor.shape == ( 3, 3 ), "Stress tensor must be 3x3 matrix."
    assert directionVector.size == 3, "Direction vector must have 3 components"

    # normalization of direction vector
    directionVector = directionVector / np.linalg.norm( directionVector )
    # stress vector
    T: npt.NDArray[ np.float64 ] = np.dot( stressTensor, directionVector )
    # normal stress
    sigmaN: float = np.dot( T, directionVector )
    # shear stress
    tauVec: npt.NDArray[ np.float64 ] = T - np.dot( sigmaN, directionVector )
    tau: float = float( np.linalg.norm( tauVec ) )
    return ( sigmaN, tau )
