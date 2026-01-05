# SPDX-License-Identifier: Apache 2.0
# SPDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-FileContributor: Jacques Franc, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import logging

import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Any
# from functools import partial

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import ( getAttributeSet, getNumberOfComponents, getArrayInObject )
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.pieceEnum import Piece

__doc__ = """
Attributes Diff is a vtk that compute L1 and L2 differences between attributes shared by two identical meshes.

Input meshes cans be vtkDataSet or vtkMultiBlockDataSet.

To use the filter:

.. code-block:: python

    import logging
    from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet
    from geos.processing.generic_processing_tools.AttributesDiff import AttributesDiff
    from geos.utils.pieceEnum import Piece

    # Filter inputs:
    computeL2Diff: bool  # defaults to False
    speHandler: bool  # defaults to False

    # Instantiate the filter:
    attributesDiffFilter: AttributesDiff = AttributesDiff( computeL2Diff, speHandler )

    # Set the handler of yours (only if speHandler is True):
    yourHandler: logging.Handler
    attributesDiffFilter.setLoggerHandler( yourHandler )

    # Set the meshes to compare:
    listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ]
    attributesDiffFilter.setMeshes( listMeshes )

    # Log the shared attributes info (optional):
    attributesDiffFilter.logSharedAttributeInfo()

    # Get the shared attributes (optional):
    dicSharedAttributes: dict[ Piece, set[ str ] ]
    dicSharedAttributes = attributesDiffFilter.getDicSharedAttribute()

    # Set the attributes to compare:
    dicAttributesToCompare: dict[ Piece, set[ str ] ]
    attributesDiffFilter.setDicAttributesToCompare( dicAttributesToCompare )

    # Do calculations:
    attributesDiffFilter.applyFilter()

    # Get the mesh with the computed attributes differences as new attributes:
    outputMesh: vtkMultiBlockDataSet | vtkDataSet
    outputMesh = attributesDiffFilter.getOutput()
"""

loggerTitle : str = "Attributes Diff"

class AttributesDiff:

    def __init__(
        self: Self,
        computeL2Diff: bool = False,
        speHandler: bool = False,
    ) -> None:
        """Compute differences (L1 and L2) between two identical meshes attribute.

        Args:
            computeL2Diff (bool, optional): True to compute the L2 difference
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ] = []
        self.dicNbElements: dict[ Piece, int ] = {}

        self.dicSharedAttributes: dict[ Piece, set[ str ] ] = {}
        self.dicAttributesToCompare: dict[ Piece, set[ str ] ] = {}
        self.dicAttributesDiffNames: dict[ Piece, list[ str ] ] = {}
        self.dicAttributesArray: dict[ Piece, npt.NDArray[ np.float32 ] ] = {}

        self.computeL2Diff: bool = computeL2Diff

        self.outputMesh: vtkMultiBlockDataSet | vtkDataSet = vtkMultiBlockDataSet()

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            # This warning does not count for the number of warning created during the application of the filter.
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True"
                                 " during the filter initialization." )

    def setMeshes(
        self: Self,
        listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ],
    ) -> None:
        """Setter of the two meshes with the attributes to compare.

        Setting the two meshes will automatically compute the dictionary with the shared attribute per localization.

        Args:
            listMeshes (list[vtkMultiBlockDataSet | vtkDataSet]): The list of the meshes to compare.

        Raises:
            TypeError: The meshes do not have the same type.
            ValueError: The meshes do not have the same cells or points number or datasets indexes or the number of meshes is to small.
        """
        if len( listMeshes ) != 2:
            raise ValueError ( "The list of meshes must contain two meshes." )

        if listMeshes[ 0 ].GetClassName() != listMeshes[ 1 ].GetClassName():
            raise TypeError( "The meshes must have the same type." )

        dicMeshesMaxElementId: dict[ Piece, list[ int ] ] = { Piece.CELLS: [ 0, 0 ], Piece.POINTS: [ 0, 0 ], }
        if isinstance( listMeshes[ 0 ], vtkDataSet ):
            for meshId, mesh in enumerate( listMeshes ):
                for piece in dicMeshesMaxElementId:
                    dicMeshesMaxElementId[ piece ][ meshId ] = np.max( getArrayInObject( mesh, "localToGlobalMap", piece ) )
        elif isinstance( listMeshes[ 0 ], vtkMultiBlockDataSet ):
            setDatasetType: set[ str ] = set()
            for meshId, mesh in enumerate( listMeshes ):
                listMeshBlockId: list[ int ] = getBlockElementIndexesFlatten( mesh )
                for meshBlockId in listMeshBlockId:
                    setDatasetType.add( mesh.GetDataSet( meshBlockId ).GetClassName() )
                    dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( meshBlockId ) )
                    for piece in dicMeshesMaxElementId:
                        dicMeshesMaxElementId[ piece ][ meshId ] = max( dicMeshesMaxElementId[ piece ][ meshId ], np.max( getArrayInObject( dataset, "localToGlobalMap", piece ) ) )
                if len( setDatasetType ) != 1:
                    raise TypeError( "All datasets of the meshes must have the same type." )
        else:
            raise TypeError( "The meshes must be inherited from vtkMultiBlockDataSet or vtkDataSet.")

        for piece, listMeshMaxElementId in dicMeshesMaxElementId.items():
            if listMeshMaxElementId[ 0 ] != listMeshMaxElementId[ 1 ]:
                raise ValueError( f"The total number of { piece.value } in the meshes must be the same." )

        self.listMeshes = listMeshes
        self.dicNbElements[ Piece.CELLS ] = dicMeshesMaxElementId[ Piece.CELLS ][ 0 ] + 1
        self.dicNbElements[ Piece.POINTS ] = dicMeshesMaxElementId[ Piece.POINTS ][ 0 ] + 1
        self.outputMesh = listMeshes[ 0 ].NewInstance()
        self.outputMesh.ShallowCopy( listMeshes[ 0 ] )
        self._computeDicSharedAttributes()

        return

    def _computeDicSharedAttributes( self: Self ) -> None:
        """Compute the dictionary with the shared attributes per localization between the two meshes.

        Keys of the dictionary are the attribute localization and the value are the shared attribute per localization.
        """
        for piece in [ Piece.POINTS, Piece.CELLS ]:
            setSharedAttributes: set[ str ] = getAttributeSet( self.listMeshes[ 0 ], piece ).intersection( getAttributeSet( self.listMeshes[ 1 ], piece ))
            if setSharedAttributes != set():
                self.dicSharedAttributes[ piece ] = setSharedAttributes

        return

    def getDicSharedAttribute( self: Self ) -> dict[ Piece, set[ str ] ]:
        """Getter of the dictionary with the shared attributes per localization."""
        return self.dicSharedAttributes

    def logSharedAttributeInfo( self: Self ) -> None:
        """Log the shared attributes per localization."""
        if self.dicSharedAttributes == {}:
            self.logger.warning( "The two meshes do not share any attribute." )
        else:
            for piece, sharedAttributes in self.dicSharedAttributes.items():
                self.logger.info( f"Shared attributes on { piece.value } are { sharedAttributes }." )

        return

    def setDicAttributesToCompare( self: Self, dicAttributesToCompare: dict[ Piece, set[ str ] ] ) -> None:
        """Setter of the dictionary with the shared attribute per localization to compare.

        Args:
            dicAttributesToCompare (dict[Piece, set[str]]): The dictionary with the attributes to compare per localization.

        Raises:
            ValueError: At least one attribute to compare is not a shared attribute.
        """
        for piece, setSharedAttributesToCompare in dicAttributesToCompare.items():
            if not setSharedAttributesToCompare.issubset( self.dicSharedAttributes[ piece ] ):
                wrongAttributes: set[ str ] = setSharedAttributesToCompare.difference( self.dicSharedAttributes[ piece ] )
                raise ValueError( f"The attributes to compare { wrongAttributes } are not shared attributes.")

        dicNbComponents: dict[ Piece, int ] = {}
        dicAttributesDiffNames: dict[ Piece, list[ str ] ] = {}
        dicAttributesArray: dict[ Piece, npt.NDArray[ np.float32 ] ] = {}
        for piece, setSharedAttributesToCompare in dicAttributesToCompare.items():
            dicNbComponents[ piece ] = 0
            dicAttributesDiffNames[ piece ] = []
            for attributeName in setSharedAttributesToCompare:
                nbAttributeComponents = getNumberOfComponents( self.outputMesh, attributeName, piece )
                dicNbComponents[ piece ] += nbAttributeComponents
                diffAttributeName: str = f"diff_{ attributeName }"
                if nbAttributeComponents > 1:
                    dicAttributesDiffNames[ piece ].extend( [ diffAttributeName + "_component" + str( idAttributeComponent ) for idAttributeComponent in range( nbAttributeComponents ) ] )
                else:
                    dicAttributesDiffNames[ piece ].append( diffAttributeName )
            dicAttributesArray[ piece ] = np.zeros( shape=( self.dicNbElements[ piece ], dicNbComponents[ piece ], 2 ), dtype=np.float32 )

        self.dicAttributesArray = dicAttributesArray
        self.dicAttributesToCompare = dicAttributesToCompare
        self.dicAttributesDiffNames = dicAttributesDiffNames

        return

    def getDicAttributesToCompare( self: Self ) -> dict[ Piece, set[ str ] ]:
        """Getter of the dictionary of the attribute to compare per localization."""
        return self.dicAttributesToCompare

    def getDicAttributesDiffNames( self: Self ) -> dict[ Piece, list[ str ] ]:
        """Getter of the dictionary with the name of the attribute created with the calculated attributes diff."""
        return self.dicAttributesDiffNames

    def applyFilter( self: Self ) -> None:
        """Apply the diffFieldsFilter."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        if self.listMeshes == []:
            raise ValueError( "Set a list of meshes to compare." )

        if self.dicAttributesToCompare == {}:
            raise ValueError( "Set the attribute to compare per localization." )

        self._computeDicAttributesArray()
        self._computeL1()
        # if self.computeL2Diff:
        #     self.computeL2()

        self.logger.info( f"The filter { self.logger.name } succeed." )

        return

    def _computeDicAttributesArray( self: Self ) -> None:
        """Compute the dictionary with one array per localization with all the values of all the attributes to compare."""
        for piece, sharedAttributesToCompare in self.dicAttributesToCompare.items():
            idComponents: int = 0
            for attributeName in sharedAttributesToCompare:
                arrayAttributeData: npt.NDArray[ Any ]
                nbAttributeComponents: int
                for meshId, mesh in enumerate( self.listMeshes ):
                    if isinstance( mesh, vtkDataSet ):
                        arrayAttributeData = getArrayInObject( mesh, attributeName, piece )
                        nbAttributeComponents = getNumberOfComponents( mesh, attributeName, piece )
                        self.dicAttributesArray[ piece ][ :, idComponents : idComponents + nbAttributeComponents, meshId ] = arrayAttributeData.reshape( self.dicNbElements[ piece ], nbAttributeComponents )
                    else:
                        listMeshBlockId: list[ int ] = getBlockElementIndexesFlatten( mesh )
                        for meshBlockId in listMeshBlockId:
                            dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( meshBlockId ) )
                            arrayAttributeData = getArrayInObject( dataset, attributeName, piece )
                            nbAttributeComponents = getNumberOfComponents( dataset, attributeName, piece )
                            lToG: npt.NDArray[ Any ] = getArrayInObject( dataset, "localToGlobalMap", piece )
                            self.dicAttributesArray[ piece ][ lToG, idComponents : idComponents + nbAttributeComponents, meshId ] = arrayAttributeData.reshape( len( lToG ), nbAttributeComponents )

                idComponents += nbAttributeComponents

        return

    def _computeL1( self: Self ) -> None:
        """Compute the L1 diff for all the wanted attribute and create attribute with it on the output mesh."""
        for piece in self.dicAttributesDiffNames:
            for attributeId, attributeDiffName in enumerate( self.dicAttributesDiffNames[ piece ] ):
                attributeArray: npt.NDArray[ Any ]
                if isinstance( self.listMeshes[ 0 ], vtkDataSet ):
                    attributeArray = np.abs( self.dicAttributesArray[ piece ][ :, attributeId, 0 ] - self.dicAttributesArray[ piece ][ :, attributeId, 1 ] )
                    createAttribute( self.outputMesh, attributeArray, attributeDiffName, piece=piece, logger=self.logger )
                else:
                    listBlockId: list[ int ] = getBlockElementIndexesFlatten( self.outputMesh )
                    for BlockId in listBlockId:
                        dataset: vtkDataSet = vtkDataSet.SafeDownCast( self.outputMesh.GetDataSet( BlockId ) )
                        lToG: npt.NDArray[ Any ] = getArrayInObject( dataset, "localToGlobalMap", piece )
                        attributeArray = np.abs( self.dicAttributesArray[ piece ][ lToG, attributeId, 0 ] - self.dicAttributesArray[ piece ][ lToG, attributeId, 1 ] )
                        createAttribute( dataset, attributeArray, attributeDiffName, piece=piece, logger=self.logger )

        return

    # def computeL2(self, f, callback = partial(np.linalg.norm(ord=np.inf))):
    #     """ compute by default inf norm """
    #     s = f.shape
    #     #loop
    #     sp = fp.shape
    #     s = f.shape
    #     for i in range(0,s[1]):
    #         n = callback( f[:,i,i1]-f[:,i,i2])
    #         print(self.flist[i]+": "+str(n)+" ")
    #     for i in range(0,sp[1]):
    #         n = callback( fp[:,i,i1]-fp[:,i,i2])
    #         print(self.flist[i]+": "+str(n)+" ")
    #     self.logger.info("Lmax norm for fields {name} is {value}")

    def getOutput( self: Self ) -> vtkMultiBlockDataSet | vtkDataSet:
        """Return the mesh with the computed diff as attributes for the wanted attributes.

        Returns:
            (vtkMultiBlockDataSet | vtkDataSet): The mesh with the computed attributes diff.
        """
        return self.outputMesh

# #####
# class diff_visu:

#     def __init__(self, fname):
#         self.t = fname[-1]
#         self.filelist = fname
#         print(self.filelist)

#         self.extension = fname[0].split('.')[-1]
#         #TODO check extension for all files
#         if self.extension == "vtk":
#             self.reader = vtk.vtkUnstructuredGridReader()
#             self.writer = vtk.vtkUnstructuredGridWriter()
#             self.reader.SetFileName(fname[0])
#             self.reader.Update()
#             self.fields = self.reader.GetOutput()
#             namelist = self.display_fields(self.fields)# as indexes change between time 0 and others
#         elif self.extension == "vtr" :
#             self.reader = vtk.vtkRectilinearGridReader()
#             self.writer = vtk.vtkRectilinearGridWriter()
#             self.reader.SetFileName(fname[0])
#             self.reader.Update()
#             self.fields = self.reader.GetOutput()
#             namelist = self.display_fields(self.fields)# as indexes change between time 0 and others
#         elif self.extension == "vtu":
#             self.reader = vtk.vtkXMLUnstructuredGridReader()
#             self.writer = vtk.vtkXMLUnstructuredGridWriter()
#             self.reader.SetFileName(fname[0])
#             self.reader.Update()
#             self.fields = self.reader.GetOutput()
#             namelist = self.display_fields(self.fields)# as indexes change between time 0 and others
#         elif self.extension == "vtm":
#             self.reader = vtk.vtkXMLMultiBlockDataReader()
#             self.writer = vtk.vtkXMLMultiBlockDataWriter()
#             self.reader.SetFileName(fname[0])
#             self.reader.Update()
#             self.fields = self.reader.GetOutput()
#             namelist = self.display_fields_mb(self.fields)# as indexes change between time 0 and others

#         else:
#             raise NotImplementedError

#         #self.data_d = self.len_*[vtk.vtkFloatArray()]
#         prs = input("number to diff ?\n")
#         # debug
#         # prs = '22 23'
#         olist = [ namelist[int(item)] for item in prs.split() ]
#         print(olist)
#         self.flist = olist.copy()

#         fp, f ,nbp = self.extract_data(self.filelist,olist)
#         self.write_report(fp,f,0,1)#diff first and second
#         self.write_vizdiff(fp,f,0,1,nbp)


# #displays
#     def _display_cfields(self,fields,namelist):
#         print("Cell Fields available are :\n")
#         cfields = fields.GetCellData()
#         for i in range((off:=len(namelist)),off+cfields.GetNumberOfArrays()):
#             if cfields.GetArrayName(i - len(namelist)):
#                 print(str(i)+": "+cfields.GetArrayName(i-off))
#                 namelist.append(cfields.GetArrayName(i))
#             else:
#                 print(f"fields {i} is undefined")

#         return namelist

#     def _display_pfields(self,fields,namelist):
#         print("Point Fields available are :\n")
#         pfields = fields.GetPointData()
#         for i in range(len(namelist),len(namelist) + pfields.GetNumberOfArrays()):
#             print(str(i)+": *"+pfields.GetArrayName(i))
#             namelist.append('*'+pfields.GetArrayName(i))

#         return namelist

#     def display_fields(self, fields):
#         namelist = []
#         self._display_pfields(fields,namelist)
#         self._display_cfields(fields,namelist)

#         return namelist

#     def display_fields_mb(self, ugrid):
#         it = ugrid.NewIterator()
#         namelist = []
#         namelist.extend(self.display_fields(ugrid.GetDataSet(it)))
#         return namelist


# #extract

#     def extract_data(self,filelist,olist):
#         self.reader.SetFileName(filelist[0])
#         self.reader.Update()
#         fields = self.reader.GetOutput()
#         nv =0
#         nbp = 0
#         npp = 0

#         #number of cells
#         try:
#             nv = fields.GetCellData().GetArray("ghostRank").GetNumberOfValues()
#             npp = fields.GetPointData().GetArray("ghostRank").GetNumberOfValues()
#             nbp = np.max( numpy_support.vtk_to_numpy( fields.GetPointData().GetArray("localToGlobalMap") ) )
#         except:
#             it = self.fields.NewIterator()
#             while not it.IsDoneWithTraversal():
#                 nv += self.fields.GetDataSet(it).GetCellData().GetArray("ghostRank").GetNumberOfValues()
#                 npp += self.fields.GetDataSet(it).GetPointData().GetArray("ghostRank").GetNumberOfValues()
#                 nbp = np.max( numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") ) )
#                 it.GoToNextItem()



#         ncnf = 0
#         npcnf = 0
#         ncc = 0
#         npcc = 0
#         for ifields in olist:
#             try:
#                 if ifields[0] == '*':
#                     npcc = fields.GetPointData().GetArray(ifields[1:]).GetNumberOfComponents()
#                 else:
#                     ncc = fields.GetCellData().GetArray(ifields).GetNumberOfComponents()
#             except:
#                 it = fields.NewIterator()
#                 if ifields[0] == '*':
#                     npcc = fields.GetDataSet(it).GetPointData().GetArray(ifields[1:]).GetNumberOfComponents()
#                 else:
#                     ncc = fields.GetDataSet(it).GetCellData().GetArray(ifields).GetNumberOfComponents()


#             ncnf = ncnf + ncc
#             npcnf = npcnf + npcc

#         f = np.zeros(shape=(nv,ncnf,len(filelist)),dtype='float')
#         fp = np.zeros(shape=(npp,npcnf,len(filelist)),dtype='float')
#         print(f"nv {nv} ncnf {ncnf} nb {nbp}")

#         i = 0 # for file loop
#         for fileid in filelist:
#             self.reader.SetFileName(fileid)
#             print(fileid)
#             self.reader.Update()
#             # fields = self.reader.GetOutput()
#             j = 0 # for field loop
#             nc = 0
#             for nfields in olist:
#                 try:
#                     if nfields[0] == '*':
#                         field = self.fields.GetPointData().GetArray(nfields[1:])
#                     else:
#                         field = self.fields.GetCellData().GetArray(nfields)

#                     nc = field.GetNumberOfComponents()
#                     if nfields[0] == '*':
#                         f[:,j:j+nc,i] = numpy_support.vtk_to_numpy(field).reshape(nv,nc)
#                     else:
#                         fp[:,j:j+nc,i] = numpy_support.vtk_to_numpy(field).reshape(npb,nc)
#                 except:
#                     it = self.fields.NewIterator()
#                     start = 0
#                     while not it.IsDoneWithTraversal():
#                         # use localToGlobalMap
#                         if nfields[0] == '*':
#                             field = self.fields.GetDataSet(it).GetPointData().GetArray(nfields[1:])
#                             nt = field.GetNumberOfValues()
#                             nc = field.GetNumberOfComponents()
#                             l2g = numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") )
#                             fp[l2g,j:j+nc,i] += numpy_support.vtk_to_numpy(field).reshape(int(nt/nc),nc)
#                         else:
#                             field = self.fields.GetDataSet(it).GetCellData().GetArray(nfields)
#                             nt = field.GetNumberOfValues()
#                             nc = field.GetNumberOfComponents()
#                             l2g = numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetCellData().GetArray("localToGlobalMap") )
#                             f[l2g-nbp,j:j+nc,i] += numpy_support.vtk_to_numpy(field).reshape(int(nt/nc),nc)
#                         it.GoToNextItem()

#                 if nc>1 & i ==0 :
#                     self.flist[j:j+1] = [ self.flist[j]+"_"+str(k) for k in range(0,nc) ]
#                 j = j + nc
#             i = i+1

#         return fp,f,nbp

#     def write_report(self,fp,f,i1,i2):
#         sp = fp.shape
#         s = f.shape
#         print(s)
#         for i in range(0,s[1]):
#             n = np.linalg.norm( f[:,i,i1]-f[:,i,i2], np.inf )
#             print(self.flist[i]+": "+str(n)+" ")
#         for i in range(0,sp[1]):
#             n = np.linalg.norm( fp[:,i,i1]-fp[:,i,i2], np.inf )
#             print(self.flist[i]+": "+str(n)+" ")


#     def write_vizdiff(self,fp,f,i1,i2, nbp):
#         # writer.SetDataModeToAscii()
#         #mesh = vtk.vtkUnstructuredGrid()
#         postfix = ""

#         print(self.flist)
#         for i,fname in enumerate(self.flist):
#             try:
#                 arr =numpy_support.numpy_to_vtk(np.abs( f[:,i,i1]-f[:,i,i2] ))
#                 arr.SetName("d"+fname)
#                 self.fields.GetCellData().AddArray(arr)
#             except:
#                 it = self.fields.NewIterator()
#                 start = 0
#                 while not it.IsDoneWithTraversal():
#                     #scalar fill only
#                     if fname[0] == '*':
#                         l2g = numpy_support.numpy_to_vtk( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") )
#                         arr = numpy_support.numpy_to_vtk(np.abs( fp[l2g,i,i1]-fp[l2g,i,i2] ))
#                         arr.SetName("d"+fname)
#                         self.fields.GetDataSet(it).GetPointData().AddArray(arr)
#                     else:
#                         l2g = numpy_support.numpy_to_vtk( self.fields.GetDataSet(it).GetCellData().GetArray("localToGlobalMap") )
#                         arr = numpy_support.numpy_to_vtk(np.abs( f[l2g-nbp,i,i1]-f[l2g-nbp,i,i2] ))
#                         arr.SetName("d"+fname)
#                         self.fields.GetDataSet(it).GetCellData().AddArray(arr)
#                     it.GoToNextItem()


#         self.writer.SetFileName( "diff_field_"+postfix+"."+self.extension )
#         self.writer.SetInputData(self.fields)
#         self.writer.Write()

