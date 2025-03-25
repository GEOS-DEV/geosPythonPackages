from typing import List, Optional


class XMLTime:

    def __init__( self, name: str, event: str, target: str, value: float ):
        self.name: str = name
        self.events: List[ str ] = [ event ]
        self.targets: List[ str ] = [ target ]
        self.values: List[ float ] = [ value ]

    """
    Accessors
    """
    def getEvents( self ) -> List[ str ]:
        return self.events

    def getName( self ) -> str:
        return self.name

    def getSolverValue( self, solverName: str ) -> Optional[ float ]:
        """
        If one or multiple targets contain the '/Solvers/' filter, returns the value associated with it.

        Returns:
            Dict[ str, float ]: An example would be:
            self.targets = ['/Tasks/pressureCollection', '/Outputs/timeHistoryOutput', '/Solvers/solverName']
            self.values = [0.004, 0.1, 10.0]
            would return 10.0
        """
        identifier: str = "/Solvers/"
        for i, target in enumerate( self.targets ):
            if identifier in target and target.endswith( solverName ):
                return self.values[ i ]
        print( f"The solver '{solverName}' does not exist in the targets '{self.targets}' of XMLTime '{self.name}'." +
               " Cannot return a value." )

    def getTargets( self ) -> List[ str ]:
        return self.targets

    def getValues( self ) -> List[ float ]:
        return self.values

    """
    Mutators
    """
    def _add( self, new_event: str, new_target: str, new_value: float ) -> None:
        if new_event not in self.events:
            self.events.append( new_event )
            self.targets.append( new_target )
            self.values.append( new_value )
        else:
            print( f"Cannot add new_event '{new_event}' with new target '{new_target}' to " +
                   f" the '{self.name}' variable." )

    def _remove( self, event_or_target: str ) -> None:
        position_event: int = self.hasEvent( event_or_target )
        position_target: int = self.hasTarget( event_or_target )
        max_position: int = max( position_event, position_target )
        if max_position > -1:
            self.events.pop( max_position )
            self.targets.pop( max_position )
            self.values.pop( max_position )
        else:
            print( f"Cannot find '{event_or_target}' to remove and its associated parameters." )

    """
    Utils
    """
    def hasEvent( self, event: str ) -> int:
        """
        Checks if the given event exists in the list of events.

        Args:
            event: The event to check for.

        Returns:
            The index of the event in the list if found, otherwise -1.
        """
        if event in self.events:
            return self.events.index( event )
        return -1

    def hasTarget( self, target: str ) -> int:
        """
        Checks if the given target exists in the list of targets.

        Args:
            target: The target to check for.

        Returns:
            The index of the target in the list if found, otherwise -1.
        """
        if target in self.targets:
            return self.targets.index( target )
        return -1
