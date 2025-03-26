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

import os
from xml.etree import cElementTree as ET, ElementTree
from xml.etree.ElementTree import Element
from xmltodict import parse as xmltodictparse
from re import findall
from typing import Dict, List, Set
from geos.pygeos_tools.utilities.mesh.InternalMesh import InternalMesh
from geos.pygeos_tools.utilities.mesh.VtkMesh import VTKMesh
from geos.utils.errors_handling.classes import required_attributes
from geos.utils.xml.XMLTime import XMLTime


class XML:

    def __init__( self, xmlFile: str ):
        """
        Parameters
        -----------
            xmlFile (str) : Filepath to an existing .xml file.
        """
        self.filename: str = xmlFile

        self.tree: ElementTree = ET.parse( xmlFile )
        root: Element = self.tree.getroot()
        root = self.processIncludes( root )

        to_string: bytes = ET.tostring( root, method='xml' )
        self.outputs = None
        # root_dict = { "Problem": { "Mesh": { ... }, "Solvers": { ... } } }
        root_dict = xmltodictparse( to_string, attr_prefix="", dict_constructor=dict )
        for xml_block_path, xml_block in root_dict[ 'Problem' ].items():
            words: List[ any ] = findall( '[A-Z][^A-Z]*', xml_block_path )  # Example with xml_block_path = "Mesh"
            words[ 0 ] = words[ 0 ].lower()  # words = [ "mesh" ]
            attr: str = "".join( words )
            setattr( self, attr, xml_block )  # creates a new attribute self.mesh = xml_block

        self.xmlTimes: Dict[ str, XMLTime ] = None
        if hasattr( self, "events" ):
            self.updateXMLTimes()

    def processIncludes( self, root: Element ) -> Element:
        """
        Process any <Included> elements by merging the referenced XML files into the main XML tree.

        Parameters
        -----------
            root (Element): XML ElementTree Element.

        Returns
        --------
            Element: root
        """
        includes: Element = root.find( "Included" )
        if includes is not None:
            for file_element in includes.findall( "File" ):
                file_name: str = file_element.get( "name" )
                if os.path.isabs( file_name ):
                    full_path: str = file_name
                else:
                    full_path = os.path.join( os.path.dirname( self.filename ), file_name )
                try:
                    included_tree: ElementTree = ET.parse( full_path )
                    included_root: Element = included_tree.getroot()
                    for child in list( included_root ):
                        root.append( child )
                except Exception as e:
                    print( f"Error including file {full_path}: {e}" )

            root.remove( includes )
        return root

    """
    Accessors
    """
    def getAttribute( self, parentElement, attributeTag ):
        if parentElement == "root":
            pElement = self.tree.find( f"./[@{attributeTag}]" )
        else:
            pElement = self.tree.find( f"./*/{parentElement}/[@{attributeTag}]" )

        return pElement.get( attributeTag )

    @required_attributes( "elementRegions" )
    def getCellBlocks( self ) -> List[ str ]:
        """
        Get the cell blocks names from the XML

        Returns
        --------
            parameter_names : List(str)
        """
        try:
            cellElementRegion: Dict[ str, str ] = self.elementRegions[ "CellElementRegion" ]
            cellBlocks: List[ str ] = cellElementRegion[ "cellBlocks" ].strip( "{ }" ).split( "," )
            return cellBlocks
        except KeyError:
            raise KeyError( "The CellElementRegion does not exist or the cellBlocks are not defined." )

    @required_attributes( "mesh" )
    def getMeshObject( self ):
        if "InternalMesh" in self.mesh.keys():
            return InternalMesh( self )  #  Not working properly for now

        elif "VTKMesh" in self.mesh.keys():
            vtkFile: str = self.mesh[ "VTKMesh" ][ "file" ]
            if not os.path.isabs( vtkFile ):
                vtkFile = os.path.join( os.path.split( self.filename )[ 0 ], vtkFile )
            return VTKMesh( vtkFile )

    @required_attributes( "mesh" )
    def getMeshName( self ) -> str:
        """
        Get the mesh 'name' attribute from the xml
        
        Returns
        -------
            str
                Mesh name from the xml
        """
        if len( self.mesh ) == 0:
            raise ValueError( "No mesh defined in the 'mesh' XML block." )
        elif len( self.mesh ) > 1:
            raise ValueError( "More than 1 mesh defined in the 'mesh' XML block. Cannot decide." )
        else:
            if "InternalMesh" in self.mesh.keys():
                mesh: dict[ str, str ] = self.mesh[ "InternalMesh" ]
            elif "VTKMesh" in self.mesh.keys():
                mesh = self.mesh[ "VTKMesh" ]
            else:
                raise ValueError( f"Unknown mesh type and not retrievable in : {self.mesh.keys()}" )

            try:
                return mesh[ "name" ]
            except KeyError:
                raise KeyError( f"The mesh '{mesh}' does not have a name attribute." )

    @required_attributes( "outputs" )
    def getOutputTargets( self ) -> Dict[ str, List[ str ] ]:
        outputs: Dict[ str, Dict[ str, str ] ] = self.outputs
        # Set the targets
        collectionTargets = list()
        hdf5Targets = list()
        vtkTargets = list()
        if isinstance( list( outputs.values() )[ 0 ], list ):
            if "TimeHistory" in outputs.keys():
                for hdf5 in outputs[ "TimeHistory" ]:
                    collectionTargets.append( hdf5[ 'sources' ].strip( "{} " ) )
                    hdf5Targets.append( "Outputs/" + hdf5[ 'name' ] )

            if "VTK" in outputs.keys():
                for vtk in outputs[ "VTK" ]:
                    vtkTargets.append( "Outputs/" + vtk[ 'name' ] )

        else:
            if "TimeHistory" in list( outputs.keys() ):
                hdf5 = outputs[ "TimeHistory" ]
                collectionTargets.append( hdf5[ 'sources' ].strip( "{} " ) )
                hdf5Targets.append( "Outputs/" + hdf5[ 'name' ] )

            if "VTK" in list( outputs.keys() ):
                vtk = outputs[ "VTK" ]
                vtkTargets.append( "Outputs/" + vtk[ 'name' ] )

        return { "collection": collectionTargets, "hdf5": hdf5Targets, "vtk": vtkTargets }

    @required_attributes( "solvers" )
    def getSolverTypes( self ) -> List[ str ]:
        """
        Get the solver types from the XML

        Returns
        --------
            solverTypes : List(str)
        """
        solverTypes: List[ str ] = [ k for k in self.solvers.keys() if k[ 0 ].isupper() ]
        if len( solverTypes ) == 0:
            raise ValueError( f"You must provide a Solver in the XML '{self.filename}'." )
        return solverTypes

    def getSolverTypeDependantParameters( self, param_name: str, stype: str = None ) -> List[ str ]:
        """
        Get the solver parameter from the XML

        Parameters
        -----------
            stype: str that are solver types that can be present in the XML.

        Returns
        --------
            parameter_names : List(str) and if stype is not None, the number of parameters is equal to 1.
            Cannot be an empty list.
        """
        # Implies that at least one solver exists so len( solverTypes ) >= 1
        solverTypes: List[ str ] = self.getSolverTypes()
        if stype is not None:
            if stype not in solverTypes:
                raise ValueError( f"Solver type '{stype}' does not exist in the XML '{self.filename}'." )
            solverTypesToUse: List[ str ] = [ stype ]
        else:
            solverTypesToUse = solverTypes
        # once solver types have been identified, we can retrieve their names
        try:
            return [ self.solvers[ solvertype ][ param_name ] for solvertype in solverTypesToUse ]
        except KeyError:
            raise KeyError( f"One solver does not have a '{param_name}' parameter defined." )

    def getSolverNames( self, stype: str = None ) -> List[ str ]:
        """
        Get the solver names from the XML

        Parameters
        -----------
            stype: str that are solver types that can be present in the XML.

        Returns
        --------
            names : List(str) and if stype is not None, the number of names is equal to 1.
        """
        return self.getSolverTypeDependantParameters( "name", stype )

    def getSolverDiscretizations( self, stype: str = None ) -> List[ str ]:
        """
        Get the solver discretizations from the XML

        Parameters
        -----------
            stype: str that are solver types that can be present in the XML.

        Returns
        --------
            discretization : List(str) and if stype is not None, the number of discretization is equal to 1.
        """
        return self.getSolverTypeDependantParameters( "discretization", stype )

    def getSolverTargetRegions( self, stype: str = None ) -> List[ str ]:
        """
        Get the solver target regions from the XML

        Parameters
        -----------
            stype: str that are solver types that can be present in the XML.

        Returns
        --------
            targetRegions : List(str)
        """
        # targetRegionsRaw example : [ '{ region0, region2, ..., regionN }', '{ region1, region3, ..., regionM }' ]
        targetRegionsRaw: List[ str ] = self.getSolverTypeDependantParameters( "targetRegions", stype )
        targetRegions: List[ str ] = [ t.strip( "{ }" ).split( "," ) for t in targetRegionsRaw ]
        return targetRegions

    def getSourcesAndReceivers( self ):
        solverType: List[ str ] = self.getSolverTypes()
        if len( solverType ) > 1:
            pass
        else:
            src = self.getAttribute( f"{solverType[ 0 ]}", "sourceCoordinates" )
            src = eval( src.replace( "{", "[" ).replace( "}", "]" ) )

            rcv = self.getAttribute( f"{solverType[ 0 ]}", "receiverCoordinates" )
            rcv = eval( rcv.replace( "{", "[" ).replace( "}", "]" ) )
        return src, rcv

    @required_attributes( "xmlTimes" )
    def getXMLTimes( self ) -> Dict[ str, XMLTime ]:
        return self.xmlTimes

    """
    Updates xml attributes
    """
    @required_attributes( "geometry" )
    def updateGeometry( self, boxname, **kwargs ):
        root: Element = self.tree.getroot()
        geometry: Element = root.find( "./Geometry//*[@name=" + boxname + "]" )

        for i in len( self.geometry[ geometry.tag ] ):
            box = self.geometry[ geometry.tag ][ i ]
            if boxname == box[ "name" ]:
                break

        for k, v in kwargs.items():
            if k in geometry.attrib:
                geometry.set( k, v )
                self.geometry[ geometry.tag ][ i ].update( { k: str( v ) } )

    @required_attributes( "mesh" )
    def updateMesh( self, **kwargs ):
        root = self.tree.getroot()
        mesh = root.find( "./Mesh//" )
        for k, v in kwargs.items():
            if k in mesh.attrib:
                mesh.set( k, v )
                self.mesh[ mesh.tag ].update( { k: str( v ) } )

    @required_attributes( "solvers" )
    def updateSolvers( self, solverName: str, **kwargs ):
        root: Element = self.tree.getroot()
        solver: Element = root.find( "./Solvers/" + solverName )
        for k, v in kwargs.items():
            if k in solver.attrib:
                solver.set( k, v )
                self.solvers[ solverName ].update( { k: str( v ) } )

    @required_attributes( "events" )
    def updateXMLTimes( self ) -> None:
        """
        Parses the self.events dict where all the events are stored and for each time related variables,
        creates a dict with the time variable as key and a XMLTime object as value.

        An example of self.xmlTimes:
        { 'maxTime': { 'Events': 0.801 },
          'forceDt': { 'Events/solverApplications': 0.001 },
          'timeFrequency': { 'Events/timeHistoryCollection': 0.004, 'Events/timeHistoryOutput': 0.004 } }
        """
        xmlTimes: Dict[ str, XMLTime ] = dict()
        min_max: Set[ str ] = { "minTime", "maxTime" }
        event_types: Set[ str ] = { "PeriodicEvent", "HaltEvent", "SoloEvent" }
        time_params: Set[ str ] = { "beginTime", "endTime", "finalDtStretch", "forceDt", "maxEventDt", "maxRuntime",
                                    "timeFrequency" }
        for event_type, event in self.events.items():
            if event_type in min_max:
                xmlTimes[ event_type ] = XMLTime( event_type, "Events", "Events", float( event ) )
            elif event_type in event_types:
                if not isinstance( event, list ):
                    event = [ event ]
                for sub_event in event:
                    params: Set[ str ] = set( sub_event.keys() )
                    try:
                        sub_event_name: str = sub_event[ "name" ]
                        sub_event_target: str = sub_event[ "target" ]
                        params.remove( "name" )
                        params.remove( "target" )
                    except KeyError:
                        print( f"The Event block {event_type} does not contain the 'target' keyword." )
                        continue

                    for param in params:
                        if param in time_params:
                            if param not in xmlTimes:
                                xmlTimes[ param ] = XMLTime( param, sub_event_name, sub_event_target,
                                                             float( sub_event[ param ] ) )
                            else:
                                xmlTimes[ param ]._add( sub_event_name, sub_event_target, float( sub_event[ param ] ) )

        self.xmlTimes = xmlTimes

    def exportToXml( self, filename: str = None ):
        if filename is None:
            self.tree.write( self.filename )
        else:
            self.tree.write( filename )
