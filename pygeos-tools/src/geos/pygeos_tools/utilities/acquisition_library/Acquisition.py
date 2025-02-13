import os
from copy import deepcopy
import numpy as np

from geos.pygeos_tools.utilities.acquisition_library.Shot import Source, SourceSet, Receiver, ReceiverSet, Shot
from geos.pygeos_tools.utilities.mesh.VtkMesh import VTKMesh
from geos.pygeos_tools.utilities.mesh.InternalMesh import InternalMesh


class Acquisition:

    def __init__( self, xml, dt=None, **kwargs ):
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
        self.type = "acquisition"

        self.xml = xml
        self.mesh = self.xml.getMeshObject()

        self.limited_aperture = False

        self.acquisition_method( **kwargs )

        acqId = kwargs.get( "acqId", 1 )
        self.id = f"{acqId:05d}"

        self.dt = dt
        for shot in self.shots:
            if dt is not None:
                shot.dt = dt

            shot.setMesh( self.mesh )
            shot.setXml( deepcopy( self.xml ) )

    def loadMesh( self ):
        """Load the mesh to set its properties (bounds, number of points, ...)"""
        if not self.mesh.isSet:
            self.mesh.setMeshProperties()

    def getMesh( self ):
        """
        Get the mesh associated to the acquisition

        Returns
        --------
            Mesh
                Mesh associated
        """
        return self.mesh

    def acquisition_method( self, sources=None, receivers=None, **kwargs ):
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

        numberOfReceivers = len( receivers )
        numberOfSources = len( sources )

        receiverSet = ReceiverSet( [ Receiver( *receivers[ i ] ) for i in range( numberOfReceivers ) ] )

        shots = []

        for i in range( numberOfSources ):
            sourceSet = SourceSet()  #1 source per shot
            shot_id = f"{i+1:05d}"
            sourceSet.append( Source( *sources[ i ] ) )

            shot = Shot( sourceSet, receiverSet, shot_id )
            shots.append( deepcopy( shot ) )

        self.shots = shots

    def getSourceCenter( self ):
        """
        Return the central position of the all the sources contained in the acquisition

        Returns
        -------
            3d list : Coordinates of the center
        """
        sourceSet = SourceSet()
        for shot in self.shots:
            sourceSet.appendSet( shot.getSourceList() )

        center = sourceSet.getCenter()
        return center

    def limitedAperture( self, dist1=None, dist2=None, dist3=None, comm=None, export=True ):
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
                self.mesh.setMeshProperties()
            subMeshCenter = self.getSourceCenter()

            srootname = os.path.splitext( self.mesh.meshfile )[ 0 ] + f"_ACQ{self.id}"

            # Extract and generate corresponding VTK submesh
            submesh = self.mesh.extractMesh( subMeshCenter,
                                             srootname,
                                             dist=[ dist1, dist2, dist3 ],
                                             comm=comm,
                                             export=export )
            submesh.setMeshProperties()
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

    def setMesh( self, mesh ):
        """Set the mesh associated to the acquisition"""
        self.mesh = mesh

    def splitAcquisition( self ):
        """
        Split the shots such that one Acquisition = 1 Shot

        Returns
        --------
            listOfAcquisition : list
                list of Acquisition objects such that 1 Shot = 1 Acquisition
        """
        listOfAcquisition = []
        for shot in self.shots:
            a = Acquisition( xml=shot.xml,
                             sources=shot.getSourceCoords(),
                             receivers=shot.getReceiverCoords(),
                             dt=shot.dt )
            a.shots[ 0 ].id = shot.id
            a.shots[ 0 ].dt = shot.dt

            listOfAcquisition.append( a )

        return listOfAcquisition
