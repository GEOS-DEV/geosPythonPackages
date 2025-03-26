# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Any

from paraview.simple import (  # type: ignore[import-not-found]
    AssignViewToLayout,
    CreateLayout,
    CreateView,
    Delete,
    GetLayoutByName,
    GetLayouts,
    GetViews,
    GetViewsInLayout,
    RemoveLayout,
    SetActiveView,
)
from typing_extensions import Self


def buildNewLayoutWithPythonView() -> Any:  # noqa: ANN401
    """Create a new PythonView layout."""
    # create a new layout
    organization: DisplayOrganizationParaview = DisplayOrganizationParaview()
    layout_names: list[str] = organization.getLayoutsNames()
    nb_layouts: int = len(layout_names)
    layoutName: str = "Layout #" + str(nb_layouts + 1)
    # increment layout index until the layout name is a new one
    cpt: int = 1
    while layoutName in layout_names:
        layoutName = "Layout #" + str(nb_layouts + cpt)
        cpt += 1
    organization.addLayout(layoutName)

    # add a new python view to the layout
    organization.addViewToLayout("PythonView", layoutName, 0)
    return organization.getLayoutViews()[layoutName][0]


class DisplayOrganizationParaview:
    """Object to manage Paraview layouts."""

    def __init__(self: Self) -> None:
        """Keeps track of Paraview layouts and views when created or removed."""
        self._layouts_keys: list[Any] = []
        self._layout_names: list[str] = []
        self._views_cpt: int = 0
        self._layout_views: dict[str, Any] = {}
        self._views_name: dict[str, Any] = {}
        self.initLayouts()
        self.initLayoutViews()

    def initLayouts(self: Self) -> None:
        """Initialize layouts."""
        self._layouts_keys = list(GetLayouts().keys())
        self._layouts_names = []
        for layout_tuple in self._layouts_keys:
            self._layouts_names.append(layout_tuple[0])

    def getLayoutsKeys(self: Self) -> list[Any]:
        """Get layout keys.

        Returns:
            list[Any]: list of layout keys.
        """
        return self._layouts_keys

    def getLayoutsNames(self: Self) -> list[str]:
        """Get layout names.

        Returns:
            list[str]: list of layout names.
        """
        return self._layouts_names

    def getNumberLayouts(self: Self) -> int:
        """Get the number of layouts.

        Returns:
            int: number of layouts.
        """
        return len(self._layouts_keys)

    def getViewsCpt(self: Self) -> int:
        """Get the number of views.

        Returns:
            int: number of views.
        """
        return self._views_cpt

    def addOneToCpt(self: Self) -> None:
        """Increment number of views."""
        self._views_cpt += 1

    def initLayoutViews(self: Self) -> None:
        """Initialize layout views."""
        self._views_name = {}
        self._layout_views = {}
        all_views: list[Any] = GetViews()
        layouts_keys: list[Any] = self.getLayoutsKeys()
        layout_names: list[str] = self.getLayoutsNames()
        for i in range(self.getNumberLayouts()):
            self._layout_views[layout_names[i]] = []
            views_in_layout = GetViewsInLayout(GetLayouts()[layouts_keys[i]])
            for view in all_views:
                if view in views_in_layout:
                    self._layout_views[layout_names[i]].append(view)
                    name_view: str = "view" + str(self.getViewsCpt())
                    self._views_name[name_view] = view
                    self.addOneToCpt()

    def getLayoutViews(self: Self) -> dict[str, Any]:
        """Get layout views.

        Returns:
            dict[Any:Any]: dictionnary of layout views.
        """
        return self._layout_views

    def getViewsName(self: Self) -> dict[str, Any]:
        """Get view names.

        Returns:
            list[str]: list of view names.
        """
        return self._views_name

    def updateOrganization(self: Self) -> None:
        """Update layouts."""
        self._views_cpt = 0
        self.initLayouts()
        self.initLayoutViews()

    def addLayout(self: Self, new_layout_name: str) -> None:
        """Add a layout.

        Args:
            new_layout_name (str): name of the new layout.
        """
        if new_layout_name not in self.getLayoutsNames():
            CreateLayout(new_layout_name)
        else:
            print(
                f'This layout name "{new_layout_name}" is already used, please pick a new one.\n'
            )
        self.updateOrganization()

    def removeLayout(self: Self, layout_name: str) -> None:
        """Remove a layout.

        Args:
            layout_name (str): name of the layout to remove.
        """
        if layout_name not in self.getLayoutsNames():
            RemoveLayout(GetLayoutByName(layout_name))
        else:
            print(f'This layout name "{layout_name}" does not exist.')
        self.updateOrganization()

    def addViewToLayout(
        self: Self, viewType: str, layout_name: str, position: int
    ) -> None:
        """Add a view to a layout.

        Args:
            viewType (str): type of view.
            layout_name (str): name of the layout.
            position (int): position of the view.
        """
        SetActiveView(None)
        layout_to_use = GetLayoutByName(layout_name)
        new_view = CreateView(viewType)
        AssignViewToLayout(view=new_view, layout=layout_to_use, hint=position)
        self.updateOrganization()

    def RemoveViewFromLayout(
        self: Self, view_name: str, layout_name: str, position: int
    ) -> None:
        """Remove a view from a layout.

        Args:
            view_name (str): name of view.
            layout_name (str): name of the layout.
            position (int): position of the view.
        """
        views_name: dict[str, Any] = self.getViewsName()
        view_to_delete = views_name[view_name]
        SetActiveView(view_to_delete)
        Delete(view_to_delete)
        del view_to_delete
        layout_to_use = GetLayoutByName(layout_name)
        layout_to_use.Collapse(position)
        self.updateOrganization()

    def SwapCellsInLayout(
        self: Self, layout_name: str, position1: int, position2: int
    ) -> None:
        """Swap views in a layout.

        Args:
            layout_name (str): name of the layout.
            position1 (int): first position of the view.
            position2 (int): second position of the view.
        """
        layout_to_use = GetLayoutByName(layout_name)
        layout_to_use.SwapCells(position1, position2)
