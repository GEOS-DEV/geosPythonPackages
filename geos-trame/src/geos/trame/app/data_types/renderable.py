# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from enum import Enum


class Renderable( Enum ):
    """Enum class for renderable types and their ids."""
    BOX = "Box"
    VTKMESH = "VTKMesh"
    INTERNALMESH = "InternalMesh"
    INTERNALWELL = "InternalWell"
    PERFORATION = "Perforation"
    VTKWELL = "VTKWell"
