import numpy as np
from typing import Iterable, List, Optional, Union
from typing_extensions import Self
from geos.pygeos_tools.input.Xml import XML


Coordinates3D = Iterable[ float, float, float ]


class Shot:
    """Class representing a shot configuration : a SourceSet of 1 Source and a ReceiverSet

    Attributes
    ----------
        source :
            Source object
        receivers :
            ReceiverSet object
        flag :
            A flag to say if the shot configuration has been simulated
            "Undone", "In Progress", "Done"
        id : str
            Number identification
        mesh : Mesh object
            Mesh of the problem
        xml : XML
            xml input file of the shot
    """

    def __init__( self: Self, sourceSet=None, receiverSet=None, shotId: str = None ):
        """ Constructor of Shot

        Parameters
        ----------
            sourceSet : SourceSet, optional
                Set of Sources \
            receiverSet : ReceiverSet, optional
                Set of receivers
            shotId : str
                Number identification
        """
        if sourceSet is None:
            sourceSet = SourceSet()
        else:
            assert isinstance( sourceSet, SourceSet ), "SourceSet instance expected for `sourceSet` argument"
        self.sources = sourceSet

        if receiverSet is None:
            receiverSet = ReceiverSet()
        else:
            assert isinstance( receiverSet, ReceiverSet ), "ReceiverSet instance expected for `receiverSet` argument"
        self.receivers = receiverSet

        self.flag = "Undone"
        self.dt = None
        self.id = shotId
        self.mesh = None

    def __eq__( self: Self, other ):
        if isinstance( self, other.__class__ ):
            if self.sources == other.sources and self.receivers == other.receivers:
                return True

        return False

    def __repr__( self: Self ):
        return 'Source position : \n' + str( self.sources ) + ' \n\n' + 'Receivers positions : \n' + str(
            self.receivers ) + '\n\n'

    """
    Accessors
    """
    def getMesh( self: Self ):
        """Get the mesh"""
        return self.mesh

    def getSourceList( self: Self ) -> List:
        """
        Return the list of all sources in the Shot configuration

        Returns
        --------
            list of Source
                list of all the sources
        """
        return self.sources.getList()

    def getSourceCoords( self: Self ) -> List[ Coordinates3D ]:
        """
        Return the list of all sources coordinates in the Shot configuration

        Returns
        --------
            list of list
                list of all the sources coordinates
        """
        return self.sources.getSourceCoords()

    def getReceiverCoords( self: Self ) -> List[ Coordinates3D ]:
        """
        Return the list of all receivers coordinates in the Shot configuration

        Returns
        --------
            list of list
                list of all the receivers coordinates
        """
        return self.receivers.getReceiverCoords()

    def getReceiverList( self: Self ) -> List:
        """
        Return the list of all receivers in the Shot configuration

        Returns
        --------
            list of Receiver
                list of all the sources
        """
        return self.receivers.getList()

    """
    Mutators
    """
    def setXml( self: Self, xml: XML ):
        """
        Set the Xml for the shot

        Parameters
        ----------
            xml : XML
                XML object corresponding to the GEOS xml input file
        """
        self.xml: XML = xml

    def setMesh( self: Self, mesh ):
        """
        Set the mesh

        Parameters
        -----------
            mesh : Mesh
                Mesh of the shot
        """
        self.mesh = mesh

    def loadMesh( self: Self ):
        """Load the mesh and set its properties"""
        if self.mesh and not self.mesh.isSet:
            self.mesh.updateMeshProperties()


class ShotPoint:
    """
    Class defining the methods common to shot points (Source or Receiver)

    Attributes
    -----------
        coords : list of float
            Coordinates of the shot point
    """

    def __init__( self: Self, x, y, z ):
        """
        Parameters
        -----------
            x : str, int or float
                x coordinate
            y : str, int or float
                y coordinate
            z : str, int or float
                z coordinate
        """
        self.setPosition( x, y, z )  # defines the self.coords attribute

    def __str__( self: Self ):
        return f'Position of Shot point : {self.coords}'

    def __repr__( self: Self ):
        return f'ShotPoint({self.coords[ 0 ]}, {self.coords[ 1 ]}, {self.coords[ 2 ]})'

    def __eq__( self: Self, other ):
        if isinstance( self, other.__class__ ):
            if self.coords == other.coords:
                return True

        return False

    """
    Accessors
    """
    def getPosition( self: Self ) -> List:
        """
        Return the position coordinates

        Returns
        -----------
            list
                Coordinates
        """
        return self.coords

    @property
    def x( self: Self ) -> float:
        """
        Get the x position

        Returns
        --------
            float
                X coordinate
        """
        return self.coords[ 0 ]

    @property
    def y( self: Self ) -> float:
        """
        Get the y position

        Returns
        --------
            float
                Y coordinate
        """
        return self.coords[ 1 ]

    @property
    def z( self: Self ) -> float:
        """
        Get the z position

        Returns
        --------
            float
                Z coordinate
        """
        return self.coords[ 2 ]

    """
    Mutators
    """
    def setCoordinate( self: Self, coord: int, value: Union[ int, float ] ) -> None:
        """
        Set one of the coordinates

        Parameters
        -----------
            coord : int
                Which coordinate to update \
                Choices are 0, 1, 2
            value : float or int
                New value
        """
        assert coord in ( 0, 1, 2 ), "coord can only be 0, 1 or 2"
        assert isinstance( value, float ) or isinstance( value, int )

        self.coords[ coord ] = value

    def setPosition( self: Self, x, y, z ) -> None:
        """
        Set all the coordinates

        Parameters
        -----------
            coords : list or array of len 3
                New coordinates
        """
        assert all(
            str( c ).replace( ".", "", 1 ).isdigit() or isinstance( c, float ) or isinstance( c, int )
            for c in ( x, y, z ) ), "Only numeric values are accepted"

        self.coords: Coordinates3D = [ float( c ) for c in ( x, y, z ) ]

    def isinBounds( self: Self, b ) -> bool:
        """
        Check if the receiver is in the bounds

        Parameters
        -----------
            b : list or array of len 6
                Bounds of format \
                (xmin, xmax, ymin, ymax, zmin, zmax)

        Returns
        --------
            bool
                True if receiver is in bounds, False otherwise
        """
        return ( b[ 0 ] <= self.x() <= b[ 1 ] and b[ 2 ] <= self.y() <= b[ 3 ] and b[ 4 ] <= self.z() <= b[ 5 ] )


class Receiver( ShotPoint ):
    """A class representing a receiver

    Attributes
    ----------
        coords :
            Coordinates of the receiver
    """

    def __init__( self: Self, x, y, z ):
        """Constructor for the receiver

        Parameters
        ----------
            pos : len 3 array-like
                Coordinates for the receiver
        """
        super().__init__( x, y, z )

    def __str__( self: Self ):
        return f'Position of Receiver : {self.coords}'

    def __repr__( self: Self ):
        return f'Receiver({self.coords[ 0 ]}, {self.coords[ 1 ]}, {self.coords[ 2 ]})'


class Source( ShotPoint ):
    """A class representing a point source

    Attributes
    ----------
        coords : list of float
            Coordinates of the source
    """

    def __init__( self: Self, x, y, z ):
        """Constructor for the point source

        Parameters
        ----------
            coords : list of float
                Coordinates for the point source
        """
        super().__init__( x, y, z )

    def __str__( self: Self ):
        return f'Position of Source : {self.coords}'

    def __repr__( self: Self ):
        return f'Source({self.coords[ 0 ]}, {self.coords[ 1 ]}, {self.coords[ 2 ]})'


class ShotPointSet:
    """
    Class defining methods for sets of shot points

    Attributes
    -----------
        list : list
            List of ShotPoint
        number : int
            Number of ShotPoint in the set
    """

    def __init__( self: Self, shotPointList: List[ ShotPoint ] = None ):
        """
        Parameters
        -----------
            shotPointList : list
                List of ShotPoint \
                Default is None
        """
        self.updateList( shotPointList )  # defines the self.list and self.number attributes

    def __eq__( self: Self, other ):
        if isinstance( self, other.__class__ ):
            if self.number == other.number:
                for sp1 in self.list:
                    if self.list.count( sp1 ) != other.list.count( sp1 ):
                        return False
                return True

        return False

    def getList( self: Self ) -> List[ ShotPoint ]:
        """
        Return the list of Shot points in the set

        Returns
        --------
            list
                List of Shot Points
        """
        return self.list

    def updateList( self: Self, newList: List[ ShotPoint ] = None ) -> None:
        """
        Update the full list with a new one

        Parameters
        -----------
            newList : list
                New shot points set \
                Default is empty list (reset)
        """
        if newList is None:
            self.list = list()
        else:
            assert ( isinstance( newList, list ) or isinstance( newList, tuple ) )
            assert all( isinstance( sp, ShotPoint )
                        for sp in newList ), "`shotPointList` should only contain `ShotPoint` instances"

            self.list = list( newList )

        self.number: int = len( self.list )

    def append( self: Self, shotPoint: ShotPoint = None ) -> None:
        """
        Append a new shot point to the set

        Parameters
        -----------
            shotPoint : ShotPoint
                Element to be added
        """
        if shotPoint is not None:
            assert isinstance( shotPoint, ShotPoint ), "Can only add a `ShotPoint` object to the set"

            self.list.append( shotPoint )
            self.number += 1

    def appendSet( self: Self, shotPointSet ) -> None:
        """
        Append a list or a set of Shot Points to the existing one

        Parameters
        -----------
            shotPointSet : list or ShotPointSet
                Set of shot points to be added
        """
        if isinstance( shotPointSet, list ):
            shotPointList = shotPointSet
        elif isinstance( shotPointSet, ShotPointSet ):
            shotPointList = shotPointSet.getList()
        else:
            raise TypeError( "Only Sets and list objects are acceptable" )

        for shotPoint in shotPointList:
            self.append( shotPoint )


class ReceiverSet( ShotPointSet ):
    """
    Class representing a set receiver

    Attributes
    ----------
        list : list
            List of Receivers
        number : int
            Number of Receivers
    """

    def __init__( self: Self, receiverList: List[ Receiver ] = None ):
        """Constructor for the receiver set

        Parameters
        ----------
            receiverList : list of Receiver
                List of Receiver
        """
        super().__init__( receiverList )

    def __repr__( self: Self ):
        if self.number >= 10:
            return str( self.list[ 0:4 ] )[ :-1 ] + '...' + '\n' + str( self.list[ -4: ] )[ 1: ]
        else:
            return str( self.list )

    """
    Accessors
    """
    def getReceiver( self: Self, i ) -> int:
        """
        Get a specific receiver from the set with its index

        Parameters
        -----------
            i : int
                Index of the receiver requested
        """
        if len( self.list ) - 1 >= i:
            return self.list[ i ]
        else:
            raise IndexError( "The receiver set is smaller than the index requested" )

    def getReceiverCoords( self: Self ) -> List[ Coordinates3D ]:
        """
        Get the coordinates of all the receivers

        Returns
        --------
            receiverCoords : list of Coordinates3D
                List of all the receivers positions
        """
        return [ receiver.coords for receiver in self.getList() ]

    def keepReceiversWithinBounds( self: Self, bounds ) -> None:
        """
        Filter the list to keep only the ones in the given bounds

        Parameters
        -----------
            bounds : list or array of len 6
                Bounds of format \
                (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        newList: List = list()

        for receiver in self.list:
            if receiver.isinBounds( bounds ):
                newList.append( receiver )

        self.updateList( newList )

    def append( self: Self, receiver ) -> None:
        """
        Append a new receiver to the receiver set

        Parameters
        ----------
            receiver : Receiver
                Receiver to be added
        """
        assert isinstance( receiver, Receiver )
        super().append( receiver )


class SourceSet( ShotPointSet ):
    """
    Class representing a source set

    Attributes
    ----------
        list :
            List of sources
        number :
            Number of sources
    """

    def __init__( self: Self, sourceList=None ):
        """Constructor for the source set

        Parameters
        ----------
            sourceList : list of Source
                List of sources
        """
        super().__init__( sourceList )

    def __repr__( self: Self ):
        if self.number >= 10:
            return str( self.list[ 0:4 ] )[ :-1 ] + '...' + '\n' + str( self.list[ -4: ] )[ 1: ]
        else:
            return str( self.list )

    """
    Accessors
    """
    def getCenter( self: Self ) -> Optional[ Coordinates3D ]:
        """
        Get the position of the center of the SourceSet

        Returns
        --------
            center : tuple or None
                Central position of the source set
        """
        if self.number > 0:
            return tuple( np.mean( np.array( self.getSourceCoords() ), axis=0 ) )

    def getSource( self: Self, i ) -> int:
        """
        Get a specific source from the set with its index

        Parameters
        -----------
            i : int
                Index of the source requested
        """
        if len( self.list ) - 1 >= i:
            return self.list[ i ]
        else:
            raise IndexError( "The source set is smaller than the index requested" )

    def getSourceCoords( self: Self ) -> List[ Coordinates3D ]:
        """
        Get the coordinates of all the sources

        Returns
        --------
            sourceCoords : list of Coordinates3D
                List of all the source positions
        """
        return [ source.coords for source in self.getList() ]

    def append( self: Self, source ) -> None:
        """
        Append a new source to the source set

        Parameters
        ----------
            source : Source
                Source to be added
        """
        assert isinstance( source, Source )
        super().append( source )
