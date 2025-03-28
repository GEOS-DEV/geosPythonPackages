# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay

__doc__ = """Define default values of usefull physical constants."""

import numpy as np

EPSILON: float = 1e-6  #: epsilon

GRAVITY: float = 9.81  #: gravity (m/s)

WATER_DENSITY: float = 1000.0  #: water density (kg/m³)
WATER_DYNAMIC_VISCOSITY: float = 1e-3  #: water dynamic viscosity (kg.m^-1/s^-1 = Pa.s)
WATER_KINEMATIC_VISCOSITY: float = 1e-6  #: water kinematic viscosity (m²/s)

#: default grain bulk modulus is that of Quartz (Pa)
DEFAULT_GRAIN_BULK_MODULUS: float = 38e9
#: default rock cohesion - fractured case - (Pa)
DEFAULT_ROCK_COHESION: float = 0.0
#: default friction angle (rad)
DEFAULT_FRICTION_ANGLE_RAD: float = 10.0 / 180.0 * np.pi
#: default friction angle (deg)
DEFAULT_FRICTION_ANGLE_DEG: float = DEFAULT_FRICTION_ANGLE_RAD * 180.0 / np.pi
