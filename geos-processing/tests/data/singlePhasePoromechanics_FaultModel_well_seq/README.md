Those meshes used for testing post-processing filters came from a GEOS simulation (commit number 1e617be86).
The XML-files used to launch the simulation came from the integrated tests of GEOS: singlePhasePoromechanics_FaultModel_well_seq_smoke.xml located [here](https://github.com/GEOS-DEV/GEOS/tree/develop/inputFiles/poromechanicsFractures)

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "CellElementRegion" from the simulation pvd result. The integrated ParaView plugin "merge block" has been used to get a vtu with the data of the second time step.

The mesh singlePhasePoromechanicsVTKOutput.vtm has been saved as vtm from the the simulation pvd result with ParaView 6.

The meshes CellElementRegion2Ranks.vtm and CellElementRegion4Ranks.vtm have been extracted with the integrated ParaView plugin 'extract block' from two identical GEOS simulations except for the partitioning, respectively on 2 and 4 ranks. The extraction and save of the meshes have been made for the last time step.