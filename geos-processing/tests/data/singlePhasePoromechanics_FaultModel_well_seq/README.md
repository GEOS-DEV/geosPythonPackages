Those meshes used for testing post-processing filters came from a GEOS simulation (commit number 1e617be86).
The XML-files used to launch the simulation came from the integrated tests of GEOS: singlePhasePoromechanics_FaultModel_well_seq_smoke.xml located [here](https://github.com/GEOS-DEV/GEOS/tree/develop/inputFiles/poromechanicsFractures)

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "CellElementRegion" from the simulation pvd result. The integrated ParaView plugin "merge block" has been used to get a vtu with the data of the second time step.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "SurfaceElementRegion" from the simulation pvd result. The integrated ParaView plugin "merge block" has been used to get a vtu with the data of the second time step.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "SurfaceElementRegion" from the simulation pvd result. The integrated ParaView plugins "merge block" and "extract surface" have been used to get a vtp with the data of the second time step.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "WellElementRegion" from the simulation pvd result. The integrated ParaView plugins "extract block" and "merge block" have been used to get a vtu with the data of the second time step of the first well.

The mesh singlePhasePoromechanicsVTKOutput.vtm has been save as vtm from the the simulation pvd result with ParaView 6.