import os
from copy import deepcopy
import numpy as np
from typing import List
from typing_extensions import Self
from geos.pygeos_tools.acquisition_library.Shot import Source, SourceSet, Receiver, ReceiverSet, Shot, Coordinates3D
from geos.pygeos_tools.input.Xml import XML
from geos.pygeos_tools.mesh.VtkMesh import VTKMesh
from geos.pygeos_tools.mesh.InternalMesh import InternalMesh


class Acquisition:

    def __init__( self: Self, xml: XML, dt: float = None, **kwargs ):
        """
        Parameters
        ----------
            xml : XML
                Object containing the parsed xml input file
            dt : float
                Timestep
            kwargs : keyword arguments
                sources : list of list of float
                    List of all sources coordinates
                    If None, positions are extracted from the xml
                receivers : list of list of float
                    List of all receivers coordinates
                    If None, positions are extracted from the xml
                acqId : int
                    Acquisition id \
                    Default is 1
        """
        self.type: str = "acquisition"
        self.xml: XML = xml
        self.mesh = self.xml.getMeshObject()

        self.limited_aperture: bool = False

        self.acquisition_method( **kwargs )  # defines the self.shots

        acqId = kwargs.get( "acqId", 1 )
        self.id: str = f"{acqId:05d}"

        self.dt: float = dt
        for shot in self.shots:
            if dt is not None:
                shot.dt = dt

            shot.setMesh( self.mesh )
            shot.setXml( deepcopy( self.xml ) )

    def loadMesh( self: Self ) -> None:
        """Load the mesh to set its properties (bounds, number of points, ...)"""
        if not self.mesh.isSet:
            self.mesh.updateMeshProperties()

    """
    Accessors
    """
    def getMesh( self: Self ):
        """
        Get the mesh associated to the acquisition

        Returns
        --------
            Mesh
                Mesh associated
        """
        return self.mesh

    def getSourceCenter( self: Self ) -> Coordinates3D:
        """
        Return the central position of the all the sources contained in the acquisition

        Returns
        -------
            3d list : Coordinates of the center
        """
        sourceSet = SourceSet()
        for shot in self.shots:
            sourceSet.appendSet( shot.getSourceList() )
        return sourceSet.getCenter()

    """
    Mutators
    """
    def setMesh( self: Self, mesh ) -> None:
        """Set the mesh associated to the acquisition"""
        self.mesh = mesh

    def acquisition_method( self: Self, sources=None, receivers=None, **kwargs ) -> None:
        """
        Set the shots configurations
        The same set of receivers is used for all shots

        Please provide the same type of variable for `sources` and `receivers`

        Parameters
        -----------
            sources : list of list of float or str
                Sources coordinates \
                If `sources` is str, filename containing all sources coordinates
            receivers : list of list of float
                Receivers coordinates
                If `receivers`

        Examples
        ---------
            >>>> from utilities.input import XML
            >>>> xml = XML("xmlfile.xml")

            >>>> srcList = [[1,2,3],[4,5,6]]
            >>>> rcvList = [[7,8,9],[10,11,12],[13,14,15]]
            >>>> acquisition = Acquisition(xml, sources=srcList, receivers=rcvList)

            >>>> srcArr = np.array(srcList)
            >>>> rcvArr = np.array(rcvList)
            >>>> acquisition = Acquisition(xml, sources=srcArr, receivers=rcvArr)

            >>>> srcTxt = "sources.txt"
            >>>> rcvTxt = "receivers.txt"
            >>>> acquisition = Acquisition(xml, sources=srcTxt, receivers=rcvTxt)
        """
        if sources is None or receivers is None:
            sources, receivers = self.xml.getSourcesAndReceivers()
        elif isinstance( sources, str ) and isinstance( receivers, str ):
            sources = np.loadtxt( sources )
            receivers = np.loadtxt( receivers )

        numberOfReceivers: int = len( receivers )
        numberOfSources: int = len( sources )

        receiverSet = ReceiverSet( [ Receiver( *receivers[ i ] ) for i in range( numberOfReceivers ) ] )

        shots: List[ Shot ] = list()

        for i in range( numberOfSources ):
            sourceSet = SourceSet()  #1 source per shot
            shot_id: str = f"{i+1:05d}"
            sourceSet.append( Source( *sources[ i ] ) )

            shot = Shot( sourceSet, receiverSet, shot_id )
            shots.append( deepcopy( shot ) )

        self.shots: List[ Shot ] = shots

    def limitedAperture( self: Self, dist1: float = None, dist2: float = None, dist3: float = None, comm=None,
                         export: bool = True ) -> None:
        """
        Redefine each shot mesh to correspond to a limited aperture configuration.

        Parameters
        ---------
            mesh : VTKMesh
                Original mesh
            dist1 : float
                Distance to the submesh center in the 1st direction
            dist2 : float
                Distance to the submesh center in the 2nd direction
            dist3 : float
                Distance to the submesh center in the 3rd direction
            comm : MPI.COMM_WORLD
                MPI communicator
        """
        if isinstance( self.mesh, InternalMesh ):
            print( "WARNING:\n" )
            print( "Limited Aperture configuration not handled yet for Internal Mesh.\n" )

        elif isinstance( self.mesh, VTKMesh ):
            if not self.mesh.isSet:
                self.mesh.updateMeshProperties()
            subMeshCenter: Coordinates3D = self.getSourceCenter()

            srootname = os.path.splitext( self.mesh.meshfile )[ 0 ] + f"_ACQ{self.id}"

            # Extract and generate corresponding VTK submesh
            submesh = self.mesh.extractMesh( subMeshCenter,
                                             srootname,
                                             dist=[ dist1, dist2, dist3 ],
                                             comm=comm,
                                             export=export )
            submesh.updateMeshProperties()
            self.setMesh( submesh )

            # Update xml mesh file
            self.xml.updateMesh( file=submesh.meshfile )
            xmlroot, xmlext = os.path.splitext( self.xml.filename )
            self.xml.filename = xmlroot + f"_ACQ{self.id}" + xmlext
            if export:
                self.xml.exportToXml()

            # Update mesh and receivers list for all shots of the acquisition
            for shot in self.shots:
                shot.xml.updateMesh( file=submesh.meshfile )
                shot.xml.filename = xmlroot + f"_ACQ{self.id}" + xmlext
                shot.setMesh( submesh )
                shot.receivers.keepReceiversWithinBounds( submesh.bounds )
                if len( shot.getReceiverList() ) < 1 and comm.Get_rank() == 0:
                    print( f"WARNING: Shot {shot.id}, no more receivers in the bounds" )

            self.limitedAperture = True

    def splitAcquisition( self: Self ) -> List:
        """
        Split the shots such that one Acquisition = 1 Shot

        Returns
        --------
            listOfAcquisition : list
                list of Acquisition objects such that 1 Shot = 1 Acquisition
        """
        listOfAcquisition = list()
        for shot in self.shots:
            a = Acquisition( xml=shot.xml,
                             sources=shot.getSourceCoords(),
                             receivers=shot.getReceiverCoords(),
                             dt=shot.dt )
            a.shots[ 0 ].id = shot.id
            a.shots[ 0 ].dt = shot.dt

            listOfAcquisition.append( a )

        return listOfAcquisition
