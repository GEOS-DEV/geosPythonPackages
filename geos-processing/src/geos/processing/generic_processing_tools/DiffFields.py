# SPDX-License-Identifier: Apache 2.0
# SPDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-FileContributor: Jacques Franc
import logging

import numpy as np
import numpy.typing as npt
from functools import partial

from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendFilter
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataObject
from geos.utils.Logger import ( Logger, getLogger )

__doc__ = """ 
Module to diff(operate) on fields between two meshes composing on AppendFilter

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
        
        #rename fields
        cfields = mesh1.GetCellData()
        ptable1 = self.getPtable(mesh1)
        for i in range(cfields.GetNumberOfArrays()):
            cfields.GetArray(i).SetName(f"{cfields.GetArrayName(i)}_0")
        self.appendFilter.AddInputData(mesh1)
        #
        cfields = mesh2.GetCellData()
        for i in range(cfields.GetNumberOfArrays()):
            cfields.GetArray(i).SetName(f"{cfields.GetArrayName(i)}_1")
        #eventually append
        self.appendFilter.AddInputData(self._repartition(mesh2, ptable1))


    def _display_fields(self,mesh):
        cfields = mesh.GetCellData()
        namelist = set()
        for i in range(0,cfields.GetNumberOfArrays()):
            namelist.add(cfields.GetArrayName(i))

        return namelist

    def display_fields_mb(self, ugrid):
        it = ugrid.NewIterator()
        namelist = set()
        namelist.update(self.display_fields(ugrid.GetDataSet(it)))
        return namelist

    def _computeL2(self, f, callback = partial(np.linalg.norm(ord=np.inf))):
        s = f.shape
        #loop

        self.logger.info("L2 norm for fields {name} is {value}")
        pass

    def _computeLmax(self):
        #loop
        self.logger.info("L2 norm for fields {name} is {value}")
        pass

    def _computeL1(self):
        
        pass

    def _repartition(mesh, ptable):

        pass

    def Update(self):
        self.appendFilter.Update()
        # size the output numpy array
        try:
            nv = fields.GetCellData().GetArray("ghostRank").GetNumberOfValues()
        except:
            nv = 0
            it = self.fields.NewIterator()
            while not it.IsDoneWithTraversal():
                nv += self.fields.GetDataSet(it).GetCellData().GetArray("ghostRank").GetNumberOfValues()
                it.GoToNextItem()

        for fielname in self.fieldnames:
            self.appendFilter.Get

        pass

    def getOutput(self) -> vtkDataObject:
        return self.appendFilter.GetOutput()

    