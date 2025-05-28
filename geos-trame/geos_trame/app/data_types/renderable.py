# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from enum import Enum


class Renderable( Enum ):
    VTKMESH = "VTKMesh"
    INTERNALMESH = "InternalMesh"
    INTERNALWELL = "InternalWell"
    PERFORATION = "Perforation"
    VTKWELL = "VTKWell"
