# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# Copyright (c) 2019-     INRIA project-team Makutu
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
from mpi4py import MPI
import numpy as np
import numpy.typing as npt
import os
import pygeosx
import sys
from typing import Dict, List, Optional, Union
from typing_extensions import Self
from geos.pygeos_tools.wrapper import ( find_first_difference_between_wrapper_paths, get_all_matching_wrapper_paths,
                                        get_wrapper )
from geos.pygeos_tools.input.Xml import XML
from geos.pygeos_tools.input.GeosxArgs import GeosxArgs
from geos.utils.errors_handling.classes import required_attributes
from geos.utils.pygeos.solvers import GEOS_STATE
from geos.utils.xml.XMLTime import XMLTime

__doc__ = """
Solver class which is the base class for every other **Solver classes.
The driving methods for pygeosx such as initialize and execute, and get/set methods for pygeosx wrappers are defined.

.. WARNING::
    This does not handle coupled solvers simulations.

    Methods ending with the name "For1RegionWith1CellBlock" are designed to only work when dealing with mesh containing
    only hexahedral elements and only 1 CellElementRegion. In every other cases, do not use these methods.

.. todo::
    If possible, add the capabilities to handle coupled solvers.
"""


class Solver:
    """
    Solver class containing the main methods of a GEOS solver

    Attributes
    -----------
        alreadyInitialized: bool
            Tells if the Solver has been initialized
        collections : List[ pygeosx.Group ]
            geosx group
        collectionsTargets : List[ str ]
            Name of TimeHistory
        dt : float
            Time step for simulation
        geosx : pygeosx.Group
            Problem group
        geosxArgs : GeosxArgs
            Object containing GEOSX launching options
        hdf5Outputs : List[ pygeosx.Group ]
            geosx group
        hdf5Targets : List[ str ]
            Outputs of TimeHistory
        maxTime : float
            End time of the simulation
        meshName : str
            Name of the mesh in the GEOS XML deck
        minTime : float
            Begin time of the simulation
        name : str
            Name of the solver defined in the GEOS XML deck
        timeVariables : Dict[ str, float ]
            Possible time variables found in the GEOS XML deck that are link to the solver
        type : str
            The solverType targeted in GEOS XML deck
        vtkOutputs : List[ pygeosx.Group ]
            geosx group
        vtkTargets : List[ str ]
            Outputs of vtk
        xml : XML
            XML object
    """

    def __init__( self: Self, solverType: str, **kwargs ):
        self.alreadyInitialized: bool = False
        argv = kwargs.get( "geosx_argv", sys.argv )
        self.geosxArgs = GeosxArgs( argv )

        try:
            self.xml = XML( self.geosxArgs.options[ "xml" ] )
        except KeyError:
            raise ValueError( "You need to provide a xml input file" )

        solverTypesInXML: List[ str ] = self.xml.getSolverTypes()
        if solverType not in solverTypesInXML:
            raise ValueError( f"The solver type '{solverType}' does not exist in your XML '{self.xml.filename}'." )
        self.type: str = solverType

        # Other attributes that will be defined after initialization
        self.collections: List[ pygeosx.Group ] = None
        self.collectionsTargets: List[ str ] = None
        self.discretization: str = None
        self.dt: float = None
        self.geosx: pygeosx.Group = None
        self.hdf5Outputs: List[ pygeosx.Group ] = None
        self.hdf5Targets: List[ str ] = None
        self.maxTime: float = None
        self.meshName: str = None
        self.minTime: float = None
        self.name: str = None
        self.targetRegions: List[ str ] = None
        self.timeVariables: Dict[ str, float ] = None
        self.vtkOutputs: List[ pygeosx.Group ] = None
        self.vtkTargets: List[ str ] = None

    def initialize( self: Self, rank: int = 0, xml: XML = None ) -> None:
        """
        Initialization or reinitialization of GEOS that will update these parameters:
        - the solver name stored in self.name
        - the solver pygeosx.Group stored in self.solver
        - the discretization used by the solver
        - the name of the mesh
        - the regions targeted by the solver
        - the different possible outputs which are self.collections, self.hdf5Outputs, self.vtkOutputs
        - the available time variables defined in the XML and that are relevant to the current solver

        Parameters
        ----------
            rank : int
                Process rank
            xml : XML
                XML object containing parameters for GEOS initialization.
                Only required if not set in the __init__ OR if different from it
        """
        if xml:
            self.setXml( xml )
            if self.geosxArgs.updateArg( "xml", xml.filename ):
                self.alreadyInitialized = False

        if not self.alreadyInitialized:
            geosState: int = self._getGEOSState()
            if geosState == GEOS_STATE.UNINITIALIZED.value:
                self.geosx = pygeosx.initialize( rank, self.geosxArgs.getCommandLine() )
                self.alreadyInitialized = True

            elif geosState in ( GEOS_STATE.INITIALIZED.value, GEOS_STATE.READY_TO_RUN.value ):
                self.geosx = pygeosx.reinit( self.geosxArgs.getCommandLine() )
                self.alreadyInitialized = True

            elif geosState == GEOS_STATE.COMPLETED.value:
                raise ValueError( "Cannot initialize GEOS because GEOS simulation is completed." )

            else:
                raise ValueError( f"Unknown GEOS state with value '{geosState}'. Only acceptable values are:" +
                                  f" { {state.value: state.name for state in GEOS_STATE} }" )

            self.updateSolverName()
            self.updateSolverGroup()
            self.updateDiscretization()
            self.updateMeshName()
            self.updateTargetRegions()
            self.updateOutputs()
            self.updateTimeVariables()

    """
    Accessors from pygeosx and xml
    """

    @required_attributes( "xml" )
    def _getCellBlocks( self: Self ) -> List[ str ]:
        """
        Get the cell blocks names from the xml

        Returns
        -------
            List[ str ]
                cell blocks from the xml
        """
        return self.xml.getCellBlocks()

    def _getGEOSState( self: Self ) -> int:
        f"""
        Return the current GEOS state

        Returns
        ---------
            int
                GEOS state
                { {state.value: state.name for state in GEOS_STATE} }
        """
        return pygeosx.getState()

    """
    Accessors for solver attributes
    """

    @required_attributes( "collections" )
    def getCollections( self: Self ) -> List[ pygeosx.Group ]:
        return self.collections

    @required_attributes( "discretization" )
    def getDiscretization( self: Self ) -> str:
        return self.discretization

    @required_attributes( "dt" )
    def getDt( self: Self ) -> float:
        return self.dt

    @required_attributes( "geosx" )
    def getGeosx( self: Self ) -> pygeosx.Group:
        return self.geosx

    @required_attributes( "hdf5Outputs" )
    def getHdf5Outputs( self: Self ) -> List[ pygeosx.Group ]:
        return self.hdf5Outputs

    @required_attributes( "maxTime" )
    def getMaxTime( self: Self ) -> float:
        return self.maxTime

    @required_attributes( "meshName" )
    def getMeshName( self: Self ) -> str:
        return self.meshName

    @required_attributes( "minTime" )
    def getMinTime( self: Self ) -> float:
        return self.minTime

    @required_attributes( "name" )
    def getName( self: Self ) -> str:
        return self.name

    @required_attributes( "targetRegions" )
    def getTargetRegions( self: Self ) -> List[ str ]:
        return self.targetRegions

    @required_attributes( "timeVariables" )
    def getTimeVariables( self: Self ) -> Dict[ str, float ]:
        return self.timeVariables

    @required_attributes( "type" )
    def getType( self: Self ) -> str:
        return self.type

    @required_attributes( "vtkOutputs" )
    def getVtkOutputs( self: Self ) -> List[ pygeosx.Group ]:
        return self.vtkOutputs

    """
    Accessors focusing on Geos wrappers
    """

    @required_attributes( "geosx" )
    def getAllGeosWrapperByName( self: Self,
                                 name: str,
                                 filters: List[ str ] = list(),
                                 write_flag: bool = False ) -> Dict[ str, npt.NDArray ]:
        if isinstance( filters, str ):
            filters = [ filters ]
        wrapper_paths: List[ str ] = get_all_matching_wrapper_paths( self.geosx, [ name ] + filters )
        return { path: get_wrapper( self.geosx, path, write_flag ) for path in wrapper_paths }

    @required_attributes( "geosx" )
    def getGeosWrapperByName( self: Self,
                              name: str,
                              filters: List[ str ] = list(),
                              write_flag=False ) -> Optional[ npt.NDArray ]:
        """
        Get the requested wrapper as numpy array and restrict the research with filters.
        For example, if multiple "PeriodicEvent" blocks are defined with a "forceDt", getGeosWrapperByName("forceDt")
        will find multiple values and will not be able to decide which one to return, so it will return None.
        Specifying in the filters the name of the desired "PeriodicEvent" with [ "nameX" ], you will find the exact
        value required.

        Parameters
        -----------
            name : str
                Name of the wrapper in GEOS.
            filters : List(str)
                Keywords that can be used to restrict more the research of field in GEOS.
            write_flag : bool
                Sets write mode (default=False)

        Returns
        -------
            field : npt.NDArray
                Field requested
        """
        if isinstance( filters, str ):
            filters = [ filters ]
        wrapper_paths: List[ str ] = get_all_matching_wrapper_paths( self.geosx, [ name ] + filters )
        if len( wrapper_paths ) == 1:
            return get_wrapper( self.geosx, wrapper_paths[ 0 ], write_flag )
        elif len( wrapper_paths ) == 0:
            print( f"No wrapper '{name}' have been found with the help of filters '{filters}'. This wrapper either" +
                   " does not exist or the filters are invalid." )
        else:
            differences: List[ str ] = find_first_difference_between_wrapper_paths( wrapper_paths )
            print( f"Multiple wrappers with the same name '{name}' have been found. Cannot decide between all" +
                   f" choices: {wrapper_paths}. Specify more filters to choose which one to use. Given examples are:" +
                   f" {differences}." )

    @required_attributes( "geosx" )
    def getGeosWrapperByTargetKey( self: Self, target_key: str, write_flag: bool = False ) -> Optional[ npt.NDArray ]:
        """
        Get the requested wrapper as numpy array using a target_key which is the complete path to the wrapper.

        Parameters
        ----------
            target_key : str
                Key for the target wrapper
            write_flag : bool
                Sets write mode (default=False)
        """
        try:
            return get_wrapper( self.geosx, target_key, write_flag )
        except KeyError:
            print( f"The target_key used '{target_key}' does not represent the path to a wrapper." )

    def _getPrefixPathFor1RegionWith1CellBlock( self: Self,
                                                targetRegion: str = None,
                                                meshName: str = None,
                                                cellBlock: str = None ) -> str:
        """
        Return the prefix path to get wrappers or fields in GEOS.
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            targetRegion : str, optional
                Name of the target Region \
                Default value is taken from the xml
            meshName : str, optional
                Name of the mesh \
                Default value is taken from the xml
            cellBlock : str, optional
                Name of the cell blocks \
                Default value is taken from the xml

        Returns
        -------
            prefix : str
                Prefix path

        Raises
        -------
            AssertionError : if the variables 'targetRegion', 'meshName' \
                or `cellBlock` have multiple or no values
        """
        targetRegion = self.targetRegions[ 0 ]
        meshName = self.meshName
        cellBlock = self._getCellBlocks()[ 0 ]
        discretization = self.discretization if self.discretization is not None else "Level0"
        assert None not in (
            targetRegion, meshName, cellBlock, discretization
        ), "No values or multiple values found for `targetRegion`, `meshName` and `cellBlock` arguments"

        prefix = os.path.join( "/domain/MeshBodies", meshName, "meshLevels", discretization,
                               "ElementRegions/elementRegionsGroup", targetRegion, "elementSubRegions", cellBlock, "" )
        return prefix

    def _getWrapperNamesReachableWithPrefix( self: Self,
                                             targetRegion: str = None,
                                             meshName: str = None,
                                             cellBlock: str = None ) -> List[ str ]:
        """
        Return the prefix path to get wrappers or fields in GEOS.
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            targetRegion : str, optional
                Name of the target Region \
                Default value is taken from the xml
            meshName : str, optional
                Name of the mesh \
                Default value is taken from the xml
            cellBlock : str, optional
                Name of the cell blocks \
                Default value is taken from the xml

        Returns
        -------
            prefix : str
                Prefix path

        Raises
        -------
            AssertionError : if the variables 'targetRegion', 'meshName' \
                or `cellBlock` have multiple or no values
        """
        if hasattr( self, "_wrapperNamesReachableWithPrefix" ):
            return self._wrapperNamesReachableWithPrefix
        else:
            prefix: str = self._getPrefixPathFor1RegionWith1CellBlock( targetRegion, meshName, cellBlock )
            wraps: List = self.geosx.get_group( prefix ).wrappers()
            wrap_paths: List[ str ] = [ w.__str__().split()[ 0 ] for w in wraps ]
            wrap_names: List[ str ] = [ wp.split( "/" )[ -1 ] for wp in wrap_paths ]
            self._wrapperNamesReachableWithPrefix = wrap_names
            return wrap_names

    def getSolverFieldWithPrefix( self: Self, fieldName: str, **kwargs ) -> npt.NDArray:
        """
        Get the requested field as numpy array.
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            fieldName : str
                Name of the field in GEOSX

        Returns
        -------
            field : npt.NDArray
                Field requested
        """
        prefix: str = self._getPrefixPathFor1RegionWith1CellBlock( **kwargs )
        try:
            return get_wrapper( self.solver, prefix + fieldName )
        except KeyError:
            wrap_names: List[ str ] = self._getWrapperNamesReachableWithPrefix( **kwargs )
            print( f"No wrapper named '{fieldName}'found at the the target '{prefix}'. The available ones are"
                   f" '{wrap_names}'." )

    def getElementCenterFor1RegionWith1CellBlock( self: Self, filterGhost: bool = False, **kwargs ) -> npt.NDArray:
        """
        Get element center position as numpy array
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            filterGhost : bool

        Returns
        -------
            elementCenter : array-like
                Element center coordinates
        """
        elementCenter = self.getSolverFieldWithPrefix( "elementCenter", **kwargs )

        if elementCenter is not None:
            if filterGhost:
                elementCenter_filtered = self.filterGhostRankFor1RegionWith1CellBlock( elementCenter, **kwargs )
                if elementCenter_filtered is not None:
                    return elementCenter_filtered
                else:
                    print( "getElementCenterFor1RegionWith1CellBlock->filterGhostRank: No ghostRank was found." )
            else:
                return elementCenter
        else:
            print( "getElementCenterFor1RegionWith1CellBlock: No elementCenter was found." )

    def getElementCenterZFor1RegionWith1CellBlock( self: Self, filterGhost=False, **kwargs ) -> npt.NDArray:
        """
        Get the z coordinate of the element center
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            filterGhost : str

        Returns
        -------
            elementCenterZ : array-like
                Element center z coordinates
        """
        elementCenter = self.getElementCenterFor1RegionWith1CellBlock( filterGhost, **kwargs )
        if elementCenter is not None:
            elementCenterZ = np.ascontiguousarray( elementCenter[ :, 2 ] )
            return elementCenterZ
        else:
            print( "getElementCenterZFor1RegionWith1CellBlock: No elementCenter was found." )

    def getGhostRankFor1RegionWith1CellBlock( self: Self, **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Get the local ghost ranks
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            filters : list(str)
                Keywords that can be used to restrict more the research of 'ghostRank' field in GEOS.

        Returns
        -------
            ghostRank : npt.NDArray
                Local ghost ranks
        """
        ghostRank = self.getSolverFieldWithPrefix( "ghostRank", **kwargs )
        if ghostRank is not None:
            return ghostRank
        else:
            print( "getGhostRankFor1RegionWith1CellBlock: No ghostRank was found." )

    def getLocalToGlobalMapFor1RegionWith1CellBlock( self: Self,
                                                     filterGhost=False,
                                                     **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Get the local rank element id list
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            filterGhost : str

        Returns
        -------
            Numpy Array : Array containing the element id list for the local rank
        """
        localToGlobalMap = self.getSolverFieldWithPrefix( "localToGlobalMap", **kwargs )

        if localToGlobalMap is not None:
            if filterGhost:
                localToGlobalMap_filtered = self.filterGhostRankFor1RegionWith1CellBlock( localToGlobalMap, **kwargs )
                if localToGlobalMap_filtered is not None:
                    return localToGlobalMap_filtered
                else:
                    print( "getLocalToGlobalMapFor1RegionWith1CellBlock->filterGhostRank: Filtering of ghostRank" +
                           "could not be performed. No map returned." )
            else:
                return localToGlobalMap
        else:
            print( "getLocalToGlobalMapFor1RegionWith1CellBlock: No localToGlobalMap was found." )

    """
    Mutators
    """

    def setDt( self: Self, value: float ) -> None:
        self.dt = value

    @required_attributes( "timeVariables" )
    def setDtFromTimeVariable( self: Self, timeVariable: str ) -> None:
        try:
            self.dt = self.timeVariables[ timeVariable ]
        except KeyError:
            raise ValueError( f"The time variable '{timeVariable}' does not exist amongst the current timeVariables" +
                              f" '{list( self.timeVariables.keys() )}'. Cannot change dt." )

    @required_attributes( "geosx" )
    def setGeosWrapperValueByName( self: Self,
                                   name: str,
                                   value: Union[ float, npt.NDArray ],
                                   filters: List[ str ] = list() ) -> None:
        """
        Set the value of a self.geosx wrapper using the name of the wrapper.

        Parameters
        ----------
            name : str
                Name of the wrapper to find.
            value (Union[ float, npt.NDArray ])
                Value to set the wrapper.
            filters : list(str)
                Keywords that can be used to restrict more the research of field in GEOS.
        """
        if isinstance( filters, str ):
            filters = [ filters ]
        wrapper_paths: List[ str ] = get_all_matching_wrapper_paths( self.geosx, [ name ] + filters )
        if len( wrapper_paths ) == 1:
            geos_model = get_wrapper( self.geosx, wrapper_paths[ 0 ], write_flag=True )
            geos_model[ : ] = value
        elif len( wrapper_paths ) == 0:
            raise KeyError( f"No wrapper '{name}' have been found with the help of filters '{filters}'. This" +
                            " wrapper either does not exist or the filters are invalid." )
        else:
            differences: List[ str ] = find_first_difference_between_wrapper_paths( wrapper_paths )
            raise KeyError( f"Multiple wrappers with the same name '{name}' have been found. Cannot decide between" +
                            f" all choices: {wrapper_paths}. Specify more filters to choose which one to use. Given" +
                            f" examples are: {differences}." )

    @required_attributes( "geosx" )
    def setGeosWrapperValueByTargetKey( self: Self, target_key: str, value: Union[ float, npt.NDArray ] ) -> None:
        """
        Set the value of a self.geosx wrapper using the complete path or target_key.

        Parameters
        ----------
            target_key : str
                Key for the target wrapper
            value : Union[ float, npt.NDArray ]
                Value to set the wrapper.
        """
        try:
            geos_model = get_wrapper( self.geosx, target_key, write_flag=True )
            geos_model[ : ] = value
        except KeyError:
            raise KeyError( f"The target_key used '{target_key}' does not represent the path to a wrapper. Did not" +
                            f" change the value specified '{value}'." )

    @required_attributes( "hdf5Outputs" )
    def setHdf5OutputsName( self: Self, directory: str, filenames: List[ str ], reinit: bool = False ) -> None:
        """
        Overwrite GEOSX hdf5 Outputs paths that have been read in the XML.

        Parameters
        ----------
            list_of_output : list of str
                List of requested output paths
            reinit : bool
                Perform reinitialization or not. Must be set to True if called after applyInitialConditions()
        """

        if len( self.hdf5Outputs ) > 0:
            for i in range( len( filenames ) ):
                os.makedirs( directory, exist_ok=True )

                self.hdf5Outputs[ i ].setOutputName( os.path.join( directory, filenames[ i ] ) )
                if reinit:
                    self.hdf5Outputs[ i ].reinit()
        else:
            raise ValueError( "No HDF5 Outputs specified in XML." )

    def setMinTime( self: Self, new_minTime: float ) -> None:
        self.minTime = new_minTime

    def setMaxTime( self: Self, new_maxTime: float ) -> None:
        self.maxTime = new_maxTime

    @required_attributes( "vtkOutputs" )
    def setVtkOutputsName( self: Self, directory: str ) -> None:
        """
        Overwrite GEOSX vtk Outputs paths that have been read in the XML.

        Parameters
        ----------
            list_of_output : list of str
                List of vtk output paths
            reinit : bool
                Perform reinitialization or not. Must be set to True if called after applyInitialConditions()
        """
        if len( self.vtkOutputs ) > 0:
            self.vtkOutputs[ 0 ].setOutputDir( directory )
        else:
            raise ValueError( "No VTK Output specified in XML." )

    @required_attributes( "timeVariables" )
    def setTimeVariable( self: Self, timeVariable: str, value: float ) -> None:
        """
        Overwrite a XML time variable or set a new one.

        Parameters
        ----------
            timeVariable : str
                Variable name
            value : float
        """
        self.timeVariables[ timeVariable ] = value

    def setXml( self: Self, xml: XML ) -> None:
        """
        Sets the new XML object.

        Parameters
        -----------
            xml : XML
                XML object corresponding to GEOSX input
        """
        self.xml = xml

    """
    PYGEOSX methods
    """

    def applyInitialConditions( self: Self ) -> None:
        """Apply the initial conditions after GEOS (re)initialization"""
        if self._getGEOSState() == GEOS_STATE.INITIALIZED.value:
            pygeosx.apply_initial_conditions()

    def finalize( self: Self ) -> None:
        """Terminate GEOSX"""
        pygeosx._finalize()

    """
    PYGEOSX solver methods
    """

    @required_attributes( "solver" )
    def cleanup( self: Self, time: float ) -> None:
        """
        Finalize simulation. Also triggers write of leftover seismogram data

        Parameters
        ----------
        time : float
            Current time of simulation
        """
        self.solver.cleanup( time )

    @required_attributes( "solver" )
    def execute( self: Self, time: float ) -> None:
        """
        Do one solver iteration

        Parameters
        ----------
            time : float
                Current time of simulation
        """
        self.solver.execute( time, self.dt )

    @required_attributes( "solver" )
    def reinitSolver( self: Self ) -> None:
        """Reinitialize Solver"""
        self.solver.reinit()

    @required_attributes( "vtkOutputs" )
    def outputVtk( self: Self, time: float ) -> None:
        """
        Trigger the VTK output

        Parameters
        ----------
            time : float
                Current time of simulation
        """
        for vtkOutput in self.vtkOutputs:
            vtkOutput.output( time, self.dt )

    """
    Update methods when initializing or reinitializing the solver
    """

    @required_attributes( "xml" )
    def updateDiscretization( self: Self ) -> None:
        """
        Change the self.discretization when the XML has been updated.
        """
        self.discretization = self.xml.getSolverDiscretizations( self.type )[ 0 ]

    @required_attributes( "xml" )
    def updateOutputs( self: Self ) -> None:
        """
        Change the outputs when the XML has been updated.
        """
        outputTargets: Dict[ str, List[ str ] ] = self.xml.getOutputTargets()
        if all( out_tar in outputTargets for out_tar in { "collection", "hdf5", "vtk" } ):
            # Set the collections
            self.collections = list()
            self.collectionsTargets = outputTargets[ "collection" ]
            self.hdf5Outputs = list()
            self.hdf5Targets = outputTargets[ "hdf5" ]
            self.vtkOutputs = list()
            self.vtkTargets = outputTargets[ "vtk" ]

            for target in outputTargets[ "collection" ]:
                self.collections.append( self.geosx.get_group( target ) )

            for target in outputTargets[ "hdf5" ]:
                self.hdf5Outputs.append( self.geosx.get_group( target ) )

            for target in outputTargets[ "vtk" ]:
                self.vtkOutputs.append( self.geosx.get_group( target ) )
        else:
            raise ValueError( "xml.getOutputTargets() is out of date." )

    @required_attributes( "xml" )
    def updateMeshName( self: Self ) -> None:
        """
        Change the self.meshName when the XML has been updated.
        """
        self.meshName = self.xml.getMeshName()

    @required_attributes( "geosx" )
    def updateSolverGroup( self: Self ) -> None:
        """
        Change the solver pygeosx.Group for self.solver when the XML has been updated.
        """
        self.solver = self.geosx.get_group( "/Solvers/" + self.name )

    @required_attributes( "xml" )
    def updateSolverName( self: Self ) -> str:
        """
        Change the solver name when the XML has been updated.
        """
        # For a specific solver type, you can have only 1 name
        # So getSolverNames will return a list of 1 element
        self.name = self.xml.getSolverNames( self.type )[ 0 ]

    @required_attributes( "xml" )
    def updateTargetRegions( self: Self ) -> None:
        """
        Change the self.targetRegions when the XML has been updated.
        """
        self.targetRegions = self.xml.getSolverTargetRegions( self.type )[ 0 ]

    @required_attributes( "xml" )
    def updateTimeVariables( self: Self ) -> None:
        """
        Change the self.timeVariables when the XML has been updated.
        This is more complex than just calling the function getXMLTimes from the XML class.
        This first method will return a dict with the time parameter name like "minTime", "forceDt" ect ...
        and then, for each parameter, this function will decide which value stored for each parameters targets the
        current solver. This like linking the self.name and the target of an Event in GEOS.
        """
        xmlTimes: Dict[ str, XMLTime ] = self.xml.getXMLTimes()
        timeVariables: Dict[ str, float ] = dict()
        if "minTime" in xmlTimes:
            timeVariables[ "minTime" ] = xmlTimes[ "minTime" ].getValues()[ 0 ]
        if "maxTime" in xmlTimes:
            timeVariables[ "maxTime" ] = xmlTimes[ "maxTime" ].getValues()[ 0 ]
        for param, xmlTime in xmlTimes.items():
            value: float = xmlTime.getSolverValue( self.name )
            if value is not None:
                timeVariables[ param ] = value
        self.timeVariables = timeVariables

    """
    Utils
    """

    def bcastFieldFor1RegionWith1CellBlock( self: Self,
                                            fullField: npt.NDArray,
                                            comm,
                                            root=0,
                                            **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Broadcast a field to local ranks with GEOS local to global map
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            fullField : numpy array
                Full field
            comm : MPI.COMM_WORLD
                MPI communicator
            root : int
                MPI rank used for the gather \
                Default is rank 0

        Returns
        --------
            field : numpy array
                Local field
        """
        rank = comm.Get_rank()
        size = comm.Get_size()

        ghostRank = self.getGhostRankFor1RegionWith1CellBlock( **kwargs )
        localToGlobalMap = self.getLocalToGlobalMapFor1RegionWith1CellBlock( **kwargs )
        if ghostRank is not None and localToGlobalMap is not None:
            nlocalElements = ghostRank.shape[ 0 ]

            field = np.zeros( nlocalElements )

            if rank == root:
                jj = np.where( ghostRank < 0 )[ 0 ]
                field[ jj ] = fullField[ localToGlobalMap[ jj ] ]

                for r in range( size ):
                    if r != root:
                        nrcv = comm.recv( source=r, tag=1 )
                        fieldRcv = np.zeros( nrcv, dtype=np.float64 )
                        ghostRankRcv = np.zeros( nrcv, dtype=np.int32 )
                        localToGlobalMapRcv = np.zeros( nrcv, dtype=np.int64 )

                        comm.Recv( ghostRankRcv, r, 3 )
                        comm.Recv( localToGlobalMapRcv, r, 4 )

                        jj = np.where( ghostRankRcv < 0 )[ 0 ]
                        fieldRcv[ jj ] = fullField[ localToGlobalMapRcv[ jj ] ]

                        comm.Send( fieldRcv, dest=r, tag=100 + r )

            else:
                nrcv = nlocalElements
                comm.send( nrcv, root, 1 )
                comm.Send( ghostRank, root, 3 )
                comm.Send( localToGlobalMap, root, 4 )

                comm.Recv( field, source=root, tag=100 + rank )

            return field
        else:
            if ghostRank is None:
                print( "bcastFieldFor1RegionWith1CellBlock: No ghostRank was found to cast the fields." )
            if localToGlobalMap is None:
                print( "bcastFieldFor1RegionWith1CellBlock: No localToGlobalMap was found to cast the fields." )

    def filterGhostRankFor1RegionWith1CellBlock( self: Self, field: npt.NDArray, **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Filter the ghost rank from a GEOS field
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            field : numpy array
                Field to filter

        Returns
        -------
            field : numpy array
                Filtered field
        """
        ghostRank = self.getGhostRankFor1RegionWith1CellBlock( **kwargs )
        if ghostRank is not None:
            ind = np.where( ghostRank < 0 )[ 0 ]
            return field[ ind ]
        else:
            print( "filterGhostRankFor1RegionWith1CellBlock: No ghostRank was found to be filtered." )

    def gatherFieldFor1RegionWith1CellBlock( self: Self,
                                             field: npt.NDArray,
                                             comm,
                                             root=0,
                                             **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Gather a full GEOS field from all local ranks
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            field : numpy array
                Local field
            comm : MPI.COMM_WORLD
                MPI communicator
            root : int
                MPI rank used for the gather \
                Default is rank 0
        """
        assert isinstance( root, int )
        assert root < comm.Get_size()

        rank = comm.Get_rank()

        ghostRank = self.getGhostRankFor1RegionWith1CellBlock( **kwargs )
        localToGlobalMap = self.getLocalToGlobalMapFor1RegionWith1CellBlock( **kwargs )
        if ghostRank is not None and localToGlobalMap is not None:
            # Prepare buffer
            nlocalElements = ghostRank.shape[ 0 ]
            nmax = np.zeros( 1 )
            nmax[ 0 ] = np.max( localToGlobalMap )  # max global number of elements

            comm.Barrier()
            comm.Allreduce( MPI.IN_PLACE, nmax, op=MPI.MAX )
            ntot = round( nmax[ 0 ] + 1 )

            if rank != root:
                fullField = None
                nrcv = nlocalElements
                comm.send( nrcv, dest=root, tag=1 )
                comm.Send( field, dest=root, tag=2 )
                comm.Send( ghostRank, dest=root, tag=3 )
                comm.Send( localToGlobalMap, dest=root, tag=4 )

            else:
                fullField = np.full( ( ntot ), fill_value=np.nan )
                jj = np.where( ghostRank < 0 )[ 0 ]
                fullField[ localToGlobalMap[ jj ] ] = field[ jj ]

                for r in range( comm.Get_size() ):
                    if r != root:
                        nrcv = comm.recv( source=r, tag=1 )

                        fieldRcv = np.zeros( nrcv, dtype=np.float64 )
                        ghostRankRcv = np.zeros( nrcv, dtype=np.int32 )
                        localToGlobalMapRcv = np.zeros( nrcv, dtype=np.int64 )

                        comm.Recv( fieldRcv, source=r, tag=2 )
                        comm.Recv( ghostRankRcv, source=r, tag=3 )
                        comm.Recv( localToGlobalMapRcv, source=r, tag=4 )

                        jj = np.where( ghostRankRcv < 0 )[ 0 ]

                        fullField[ localToGlobalMapRcv[ jj ] ] = fieldRcv[ jj ]
            comm.Barrier()
            return fullField, ntot
        else:
            if ghostRank is None:
                print( "gatherFieldFor1RegionWith1CellBlock: No ghostRank was found to gather the fields." )
            if localToGlobalMap is None:
                print( "gatherFieldFor1RegionWith1CellBlock: No localToGlobalMap was found to gather the fields." )
