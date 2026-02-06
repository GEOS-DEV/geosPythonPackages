Those meshes used for testing post-processing filters came from a GEOS simulation (commit number 1e617be86).
The XML-files used to launch the simulation came from the integrated tests of GEOS: singlePhasePoromechanics_FaultModel_well_seq_smoke.xml located [here](https://github.com/GEOS-DEV/GEOS/tree/develop/inputFiles/poromechanicsFractures)

The mesh geosOutput2Ranks.vtm has been saved as vtm from the the GEOS simulation on 2 ranks pvd result with ParaView 6 with the data of the second time step.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "CellElementRegion" from the GEOS simulation on 2 ranks pvd result. The integrated ParaView plugin "merge block" has been used to get a vtu with the data of the second time step and save as extractAndMergeVolume.vtu on ParaView 6.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "SurfaceElementRegion" from the GEOS simulation on 2 ranks pvd result. The integrated ParaView plugin "merge block" has been used to get a vtu with the data of the second time step and save as extractAndMergeSurface.vtu on ParaView 6.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "SurfaceElementRegion" from the GEOS simulation on 2 ranks pvd result. The integrated ParaView plugins "merge block" and "extract surface" have been used to get a vtp with the data of the second time step and save as extractAndMergeSurface.vtp on ParaView 6.

The ParaView plugin "PVGeosBlockExtractAndMerge" has been used to get the vtm with the block "WellElementRegion" from the GEOS simulation on 2 ranks pvd result. The integrated ParaView plugins "extract block" and "merge block" have been used to get a vtu with the data of the second time step of the first well  and save as extractAndMergeWell1.vtu on ParaView 6.

The mesh extractAndMergeFaultWell1.vtm is a hand made vtm referring to the meshes extractAndMergeSurface.vtp and extractAndMergeWell1.vtu.

The mesh extractAndMergeVolumeWell1.vtm is a hand made vtm referring to the meshes extractAndMergeVolume.vtu and extractAndMergeWell1.vtu.

The mesh CellElementRegion2Ranks.vtm is a hand made vtm referring to the CellElementRegion block meshes of the geosOutput2Ranks.vtm.

The mesh CellElementRegion4Ranks.vtm contains the CellElementRegion block meshes extracted with the integrated ParaView plugin 'extract block' from a GEOS simulations on 4 ranks pvd result. The extraction and save have been made with the data of the second time step step.
