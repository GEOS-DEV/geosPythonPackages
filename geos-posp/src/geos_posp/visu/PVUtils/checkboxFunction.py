# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa
# type: ignore
def createModifiedCallback( anobject ):
    """Helper for the creation and use of vtkDataArraySelection in ParaView.

    Args:
        anobject: any object.
    """
    import weakref

    weakref_obj = weakref.ref( anobject )
    anobject = None

    def _markmodified( *args, **kwars ):
        o = weakref_obj()
        if o is not None:
            o.Modified()

    return _markmodified
