import logging
from geos.utils.Logger import Logger, getLogger
from functools import wraps
from typing import Type, TypeVar, Callable, Protocol, Any

__doc__ = """
  Group of decorators and Protocols that will be used in filters to wrap behaviors without code replication

"""


class HasLogger( Protocol ):
    """Protocol for classes that have logging support."""

    logger: Logger

    def setLoggerHandler( self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        pass


T = TypeVar( 'T', bound='HasLogger' )


def addLogSupport( loggerTitle: str ) -> Callable[ [ Type[ T ] ], Type[ T ] ]:
    """Decorator to add logger support in the class following existing architecture.

    Args:
        loggerTitle (str): Title to display in the logger
    """

    def decorator( cls: Type[ T ] ) -> Type[ T ]:
        original_init = cls.__init__

        @wraps( original_init )
        def new_init( self: T, *args: Any, **kwargs: Any ) -> None:
            spe_handler = kwargs.pop( 'speHandler', False )
            if spe_handler:
                self.logger = logging.getLogger( loggerTitle )
                self.logger.setLevel( logging.INFO )
            else:
                self.logger = getLogger( loggerTitle, True )

            original_init( self, *args, **kwargs )

        def setLoggerHandler( self: T, handler: logging.Handler ) -> None:
            # No docstring needed - Protocol defines the contract
            if not self.logger.handlers:
                self.logger.addHandler( handler )
            else:
                self.logger.warning(
                    "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
                )

        cls.__init__ = new_init  # type: ignore[assignment]
        cls.setLoggerHandler = setLoggerHandler  # type: ignore[assignment]

        return cls

    return decorator
