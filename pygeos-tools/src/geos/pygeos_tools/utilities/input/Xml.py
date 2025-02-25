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
from xml.etree import cElementTree as ET
import xmltodict
from re import findall
from geos.pygeos_tools.utilities.mesh.InternalMesh import InternalMesh
from geos.pygeos_tools.utilities.mesh.VtkMesh import VTKMesh


class XML():

    def __init__( self, xmlFile ):
        self.filename = xmlFile

        self.tree = ET.parse( xmlFile )
        root = self.tree.getroot()

        root = self.processIncludes(root)

        to_string = ET.tostring( root, method='xml' )
        self.outputs = None

        root = xmltodict.parse( to_string, attr_prefix="", dict_constructor=dict )
        for k, v in root[ 'Problem' ].items():
            words = findall( '[A-Z][^A-Z]*', k )
            words[ 0 ] = words[ 0 ].lower()
            attr = "".join(words)
            setattr( self, attr, v )

    def processIncludes(self, root):
        """Process any <Included> elements by merging the referenced XML files into the main XML tree."""
        includes = root.find("Included")
        if includes is not None:
            for file_element in includes.findall("File"):
                file_name = file_element.get("name")
                full_path = file_name if os.path.isabs(file_name) else os.path.join(os.path.dirname(self.filename), file_name)
                try:
                    included_tree = ET.parse(full_path)
                    included_root = included_tree.getroot()
                    for child in list(included_root):
                        root.append(child)
                except Exception as e:
                    print(f"Error including file {full_path}: {e}")

            root.remove(includes)
        return root

    def updateSolvers( self, solverName, **kwargs ):
        root = self.tree.getroot()
        solver = root.find( "./Solvers/" + solverName )
        for k, v in kwargs.items():
            if k in solver.attrib:
                solver.set( k, v )
                self.solvers[ solverName ].update( { k: str( v ) } )

    def updateMesh( self, **kwargs ):
        root = self.tree.getroot()
        mesh = root.find( "./Mesh//" )
        for k, v in kwargs.items():
            if k in mesh.attrib:
                mesh.set( k, v )
                self.mesh[ mesh.tag ].update( { k: str( v ) } )

    def updateGeometry( self, boxname, **kwargs ):
        root = self.tree.getroot()
        geometry = root.find( "./Geometry//*[@name=" + boxname + "]" )

        for i in len( self.geometry[ geometry.tag ] ):
            box = self.geometry[ geometry.tag ][ i ]
            if boxname == box[ "name" ]:
                break

        for k, v in kwargs.items():
            if k in geometry.attrib:
                geometry.set( k, v )
                self.geometry[ geometry.tag ][ i ].update( { k: str( v ) } )

    def getMeshObject( self ):
        if "InternalMesh" in self.mesh.keys():
            #Not working properly for now
            return InternalMesh( self )

        elif "VTKMesh" in self.mesh.keys():
            vtkFile = self.mesh[ "VTKMesh" ][ "file" ]
            if not os.path.isabs( vtkFile ):
                vtkFile = os.path.join( os.path.split( self.filename )[ 0 ], vtkFile )
            return VTKMesh( vtkFile )

    def getAttribute( self, parentElement, attributeTag ):
        if parentElement == "root":
            pElement = self.tree.find( f"./[@{attributeTag}]" )
        else:
            pElement = self.tree.find( f"./*/{parentElement}/[@{attributeTag}]" )

        return pElement.get( attributeTag )

    def getSolverType( self ):
        return [ k for k in self.solvers.keys() if k[ 0 ].isupper() ]

    def getSourcesAndReceivers( self ):
        solverType = self.getSolverType()
        if len( solverType ) > 1:
            pass
        else:
            src = self.getAttribute( f"{solverType[0]}", "sourceCoordinates" )
            src = eval( src.replace( "{", "[" ).replace( "}", "]" ) )

            rcv = self.getAttribute( f"{solverType[0]}", "receiverCoordinates" )
            rcv = eval( rcv.replace( "{", "[" ).replace( "}", "]" ) )
        return src, rcv

    def exportToXml( self, filename=None ):
        if filename is None:
            self.tree.write( self.filename )
        else:
            self.tree.write( filename )
