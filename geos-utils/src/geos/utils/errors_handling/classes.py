from typing import Any, Callable, Tuple


def required_attributes( *attributes: str ) -> Callable:
    """A decorator to ensure that specified attributes are defined and not None.

    Args:
        *attributes (str): The names of the attributes to check.

    Returns:
        Callable: The decorator function.
    """
    def decorator( method: Callable ) -> Callable:
        def wrapper( self, *args: Tuple[ Any, ...], **kwargs: Any ) -> Callable:
            for attribute in attributes:
                if not isinstance( attribute, str ):
                    raise TypeError( f"Attribute '{attribute}' needs to be a str." )
                if getattr( self, attribute, None ) is None:
                    raise AttributeError( f"The '{attribute}' attribute is not defined or is None." )
            return method( self, *args, **kwargs )
        return wrapper
    return decorator
