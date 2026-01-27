Those meshes used for testing post-processing filters came from a GEOS simulation with the version of the 27th November 2025.
The XML-files used to launch the simulation came from the integrated tests of GEOS: singlePhasePoromechanics_FaultModel_well_seq_smoke.xml located [here](https://github.com/GEOS-DEV/GEOS/tree/develop/inputFiles/poromechanicsFractures)

The ParaView plugin "PVGeosBlockExtractAndMerge" has been use to get the vtm with the block "CellElementRegion"from the simulation pvd result. The integrated ParaView plugin "merge block" has been use to get a vtu with the data of the second time step.

The mesh singlePhasePoromechanicsVTKOutput.vtm has been save as vtm from the the simulation pvd result with ParaView 6.