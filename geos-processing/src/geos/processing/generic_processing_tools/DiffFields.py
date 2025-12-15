# SPDX-License-Identifier: Apache 2.0
# SPDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-FileContributor: Jacques Franc
import logging

import numpy as np
import numpy.typing as npt
from functools import partial

from vtk.util import numpy_support
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendFilter
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataObject
from geos.utils.Logger import ( Logger, getLogger )

__doc__ = """ 
Module to diff(operate) on fields between two meshes composing based on globalIds indirection

"""

loggerTitle : str = "DiffFieldsFilter"

class DiffFieldsFilter:

    def __init__(self):
        """ Difference of Fields"""
        self.appendFilter = vtkAppendFilter()
        self.fieldnames = set()
        self.logger = getLogger( loggerTitle )
    
    def setMeshes(self, mesh1: vtkDataObject, mesh2: vtkDataObject):
        """ Setting meshes to diff."""
        if isinstance(mesh1, vtkMultiBlockDataSet):
            #discard partial for now
            fieldnames_1 = self._displayFields_mb(mesh1)
        else:
            fieldnames_1 = self._displayFields(mesh1)
        
        if isinstance(mesh2, vtkMultiBlockDataSet):
            #discard partial for now
            fieldnames_2 = self._displayFields_mb(mesh2)
        else:
            fieldnames_2 = self._displayFields(mesh2)

        self.fieldnames = fieldnames_1.intersection(fieldnames_2)
        self.logger.info(f"Fields have been dropped as unique to one of the meshes: {fieldnames_1.difference(fieldnames_2)}")
        

#displays
    def _display_cfields(self,fields,namelist):
        print("Cell Fields available are :\n")
        cfields = fields.GetCellData()
        for i in range((off:=len(namelist)),off+cfields.GetNumberOfArrays()):
            if cfields.GetArrayName(i - len(namelist)):
                print(str(i)+": "+cfields.GetArrayName(i-off))
                namelist.append(cfields.GetArrayName(i))
            else:
                print(f"fields {i} is undefined")

        return namelist

    def _display_pfields(self,fields,namelist):
        print("Point Fields available are :\n")
        pfields = fields.GetPointData()
        for i in range(len(namelist),len(namelist) + pfields.GetNumberOfArrays()):
            print(str(i)+": *"+pfields.GetArrayName(i))
            namelist.append('*'+pfields.GetArrayName(i))

        return namelist

    def display_fields(self, fields):
        namelist = []
        self._display_pfields(fields,namelist)
        self._display_cfields(fields,namelist)

        return namelist

    def display_fields_mb(self, ugrid):
        it = ugrid.NewIterator()
        namelist = []
        namelist.extend(self.display_fields(ugrid.GetDataSet(it)))
        return namelist

#

    def _computeL(self, f, callback = partial(np.linalg.norm(ord=np.inf))):
        """ compute by default inf norm """
        s = f.shape
        #loop
        sp = fp.shape
        s = f.shape
        for i in range(0,s[1]):
            n = callback( f[:,i,i1]-f[:,i,i2])
            print(self.flist[i]+": "+str(n)+" ")
        for i in range(0,sp[1]):
            n = callback( fp[:,i,i1]-fp[:,i,i2])
            print(self.flist[i]+": "+str(n)+" ")
        self.logger.info("Lmax norm for fields {name} is {value}")

    def _computeL1(self):
        # writer.SetDataModeToAscii()
        #mesh = vtk.vtkUnstructuredGrid()
        postfix = ""

        print(self.flist)
        for i,fname in enumerate(self.flist):
            try:
                arr =numpy_support.numpy_to_vtk(np.abs( f[:,i,i1]-f[:,i,i2] ))
                arr.SetName("d"+fname)
                self.fields.GetCellData().AddArray(arr)
            except:
                it = self.fields.NewIterator()
                start = 0
                while not it.IsDoneWithTraversal():
                    #scalar fill only
                    if fname[0] == '*':
                        l2g = numpy_support.numpy_to_vtk( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") )
                        arr = numpy_support.numpy_to_vtk(np.abs( fp[l2g,i,i1]-fp[l2g,i,i2] ))
                        arr.SetName("d"+fname)
                        self.fields.GetDataSet(it).GetPointData().AddArray(arr)
                    else:
                        l2g = numpy_support.numpy_to_vtk( self.fields.GetDataSet(it).GetCellData().GetArray("localToGlobalMap") )
                        arr = numpy_support.numpy_to_vtk(np.abs( f[l2g-nbp,i,i1]-f[l2g-nbp,i,i2] ))
                        arr.SetName("d"+fname)
                        self.fields.GetDataSet(it).GetCellData().AddArray(arr)
                    it.GoToNextItem()


    def _getdata(self):
        # size the output numpy array
        nv =0
        nbp = 0
        npp = 0

        try:
            nv = fields.GetCellData().GetArray("ghostRank").GetNumberOfValues()
            npp = fields.GetPointData().GetArray("ghostRank").GetNumberOfValues()
            nbp = np.max( numpy_support.vtk_to_numpy( fields.GetPointData().GetArray("localToGlobalMap") ) )
        except:
            it = self.fields.NewIterator()
            while not it.IsDoneWithTraversal():
                nv += self.fields.GetDataSet(it).GetCellData().GetArray("ghostRank").GetNumberOfValues()
                npp += self.fields.GetDataSet(it).GetPointData().GetArray("ghostRank").GetNumberOfValues()
                nbp = np.max( numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") ) )
                it.GoToNextItem()

        cnf = 0
        ncc = 0
        npcc = 0
        for ifields in self.olist:
            try:
                if ifields[0] == '*':
                    npcc = fields.GetPointData().GetArray(ifields[1:]).GetNumberOfComponents()
                else:
                    ncc = fields.GetCellData().GetArray(ifields).GetNumberOfComponents()
            except:
                it = fields.NewIterator()
                if ifields[0] == '*':
                    npcc = fields.GetDataSet(it).GetPointData().GetArray(ifields[1:]).GetNumberOfComponents()
                else:
                    ncc = fields.GetDataSet(it).GetCellData().GetArray(ifields).GetNumberOfComponents()


            ncnf = ncnf + ncc
            npcnf = npcnf + npcc

        f = np.zeros(shape=(nv,ncnf,len(filelist)),dtype='float')
        fp = np.zeros(shape=(npp,npcnf,len(filelist)),dtype='float')
        print(f"nv {nv} ncnf {ncnf} nb {nbp}")

        i = 0 # for file loop
        for fileid in filelist:
            self.reader.SetFileName(fileid)
            print(fileid)
            self.reader.Update()
            # fields = self.reader.GetOutput()
            j = 0 # for field loop
            nc = 0
            for nfields in self.olist:
                try:
                    if nfields[0] == '*':
                        field = self.fields.GetPointData().GetArray(nfields[1:])
                    else:
                        field = self.fields.GetCellData().GetArray(nfields)

                    nc = field.GetNumberOfComponents()
                    if nfields[0] == '*':
                        f[:,j:j+nc,i] = numpy_support.vtk_to_numpy(field).reshape(nv,nc)
                    else:
                        fp[:,j:j+nc,i] = numpy_support.vtk_to_numpy(field).reshape(npb,nc)
                except:
                    it = self.fields.NewIterator()
                    start = 0
                    while not it.IsDoneWithTraversal():
                        # use localToGlobalMap
                        if nfields[0] == '*':
                            field = self.fields.GetDataSet(it).GetPointData().GetArray(nfields[1:])
                            nt = field.GetNumberOfValues()
                            nc = field.GetNumberOfComponents()
                            l2g = numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetPointData().GetArray("localToGlobalMap") )
                            fp[l2g,j:j+nc,i] += numpy_support.vtk_to_numpy(field).reshape(int(nt/nc),nc)
                        else:
                            field = self.fields.GetDataSet(it).GetCellData().GetArray(nfields)
                            nt = field.GetNumberOfValues()
                            nc = field.GetNumberOfComponents()
                            l2g = numpy_support.vtk_to_numpy( self.fields.GetDataSet(it).GetCellData().GetArray("localToGlobalMap") )
                            f[l2g-nbp,j:j+nc,i] += numpy_support.vtk_to_numpy(field).reshape(int(nt/nc),nc)
                        it.GoToNextItem()

                if nc>1 & i ==0 :
                    self.flist[j:j+1] = [ self.flist[j]+"_"+str(k) for k in range(0,nc) ]
                j = j + nc
            i = i+1

        return fp,f,nbp

    def getOutput(self) -> vtkDataObject:
        return self.GetOutput()

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

    