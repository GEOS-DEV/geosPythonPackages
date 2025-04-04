def required_attributes( *attributes ):
    def decorator( method ):
        def wrapper( self, *args, **kwargs ):
            for attribute in attributes:
                if not isinstance( attribute, str ):
                    raise TypeError( f"Attribute '{attribute}' needs to be a str." )
                if getattr( self, attribute, None ) is None:
                    raise AttributeError( f"The '{attribute}' attribute is not defined or is None." )
            return method( self, *args, **kwargs )
        return wrapper
    return decorator
