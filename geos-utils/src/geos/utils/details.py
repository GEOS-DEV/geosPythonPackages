import logging
from geos.utils.Logger import Logger, getLogger
from functools import wraps
from typing import Type, TypeVar


__doc__ = """
  Decorators

"""

def addLogSupport(loggerTitle : str):
    T = TypeVar('T')
    def decorator(cls:Type[T]) -> Type[T]:
        original_init = cls.__init__

        @wraps(cls)
        def new_init(self : T, *args, **kwargs):

            self.logger : Logger

            if kwargs.get('speHandler'):
                kwargs.pop('speHandler')
                self.logger = logging.getLogger( loggerTitle )
                self.logger.setLevel( logging.INFO )
            else:
                self.logger = getLogger( loggerTitle, True)

            original_init(self,*args,*kwargs)

        @property
        def logger(self : T)->Logger:
            return self.logger
        
        def setLoggerHandler(self, handler : logging.Handler):
            """Set a specific handler for the filter logger.

            In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

            Args:
                handler (logging.Handler): The handler to add.
            """
            if not self.logger.hasHandlers():
                self.logger.addHandler( handler )
            else:
                self.logger.warning(
                    "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
                )

        cls.__init__ = new_init
        cls.setLoggerHandler = setLoggerHandler     

        return cls

    return decorator