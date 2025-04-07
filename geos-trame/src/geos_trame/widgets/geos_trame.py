# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from trame_client.widgets.core import AbstractElement

from .. import module

__all__ = [
    "Editor",
]


class HtmlElement( AbstractElement ):

    def __init__( self, _elem_name, children=None, **kwargs ):
        super().__init__( _elem_name, children, **kwargs )
        if self.server:
            self.server.enable_module( module )
