from trame_client.widgets.core import AbstractElement
from .. import module

__all__ = [
    "Gantt",
]


#will eventually be a dependency, so we'll skip some type checks
class HtmlElement( AbstractElement ):

    def __init__( self, _elem_name, children=None, **kwargs ) -> None:  # noqa
        super().__init__( _elem_name, children, **kwargs )  # noqa
        if self.server:
            self.server.enable_module( module )


class Gantt( HtmlElement ):
    """Gantt Editor component.

    Properties:
        tasks
        availableCategoriesList

    Emit:
        taskUpdated.
    """

    def __init__( self, **kwargs ) -> None:  #noqa
        super().__init__(
            "GanttChart",
            **kwargs,
        )
        self._attr_names += [ "tasks", "availableCategoriesList" ]
        self._event_names += [ "taskUpdated" ]
