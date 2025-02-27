# <geos-posp by Alexandre BENEDICTO & Martin LEMAY>

## Description

This package provides several python tools to read, process and visualize GEOS simulation software outputs in Paraview.

GEOS outputs include a log file where many simulation statistics are dump into and a 3D mesh with properties that evolve through time.
A reader allows to parse the log to collect data and display them as tables. Other tools process the 3D mesh to clean data and compute new properties. 

The following content will present the Python plugins.

## Installation

The current code has been developed on Python 3.9.13 using the following libraries:
- matplotlib >= 3.2.1
- pandas >= 2.0.1
- numpy >= 1.24.3
- vtk >= 9.3.2 
- paraview >= 5.11.1
- pyvista >= 0.44 

The package includes:
- PVplugins: contains all Paraview plugins
- geos-posp:
  * filters: contains vtk filters
  * readers: contains vtk readers
  * writers: contains vtk writers
  * processing: contains processing modules used by vtk filters and readers
  * utils: contains utilities
  * visu: contains Paraview display and plotting functions
  * bin: contains applications

The tools included in this package can be used either through:
- python scripts that call vtk readers and filters.
- Paraview by loading plugins located in the PVplugins folder.

## Paraview plugins Usage

The procedure to load Paraview plugins is the following:
1) Open the plugins manager in Tools -> Manage Plugins
   All available plugins are listed by their name, and a property "Loaded" or "Not Loaded".

2) If the wanted plugins are already in the list and loaded, no need to go further, they are ready to be used in Paraview.

3) If the wanted plugins are already in the list but not loaded, click on each one and apply "Load selected".
   Their property should switch to "Loaded" when done.

4) If the wanted plugins are not in the list, they can be imported by:
   Click on "Load New", go to the "PVplugins" folder, then select every needed plugin, and click "OK".
   They should normally appear in the list as "Loaded" when done.

**NOTE**: Plugins can be automatically loaded when lauching ParaView by checking the option "Auto Load" in the drop down menu of the selected plugin in the plugin manager list.

PVAttributeMapping.py
----------------------

PVAttributeMapping is a Paraview Filter that transfer attributes from an input mesh to an output mesh. Both mesh must be either identical or one a subset of the other one.

PVCreateConstantAttributePerRegion.py
-------------------------------------

PVCreateConstantAttributePerRegion is a Paravie Filter that allows the user to create new attributes with constant values per regions. These regions are defined from another attribute present in the input mesh.

PVGeosExtractMergeBlocksVolume*.py
----------------------------------

They are a set of 4 Paraview filters (PVGeosExtractMergeBlocksVolume.py, PVGeosExtractMergeBlocksVolumeSurface.py, PVGeosExtractMergeBlocksVolumeWell.py, PVGeosExtractMergeBlocksVolumeSurfaceWell.py) to clean GEOS output mesh, surfaces, and wells depending on the data contained in the .pvd output file from GEOS.

PVGeomechanicsAnalysis.py
-----------------------

PVGeomechanicsAnalysis is a Paraview Filter that computes additional geomechanical properties in an output mesh from a poro-mechanical simulation with GEOS.

PVSurfaceGeomechanics.py
-----------------------

PVSurfaceGeomechanics is a Paraview Filter that computes additional geomechanical properties specific to surfacic objects in an output mesh from a contact poro-mechanical simulation with GEOS.

PVGeomechanicsWorkflowVolume*.py
---------------------------------

They are a set of 4 Paraview Filters (PVGeomechanicsWorkflowVolume.py, PVGeomechanicsWorkflowVolumeSurface.py, PVGeomechanicsWorkflowVolumeWell.py, PVGeomechanicsWorkflowVolumeSurfaceWell.py) that combines PVGeosExtractMergeBlocksVolume* and geomechanics filters (PVGeomechanicsAnalysis and PVSurfaceGeomechanics) depending on input objects.

PVMergeBocksEnhanced.py
-----------------------

PVMergeBocksEnhanced is a Paraview filter that merge blocks of various types and keep partial attributes.

PVMohrCirclePlot.py
-----------------------

PVMohrCirclePlot is a Paraview Filter that create a Mohr's circle plot from selected cells at all time steps.

PVTransferAttributesVolumeSurface.py
------------------------------------

PVTransferAttributesVolumeSurface is a Paraview filter that transfer attributes from a volume mesh to a conformal surface mesh.

PythonViewConfigurator.py
-----------------------

PythonViewConfigurator is a Paraview Filter that cross-plots selected data in a new Python View layout.


PVGeosLogReader.py
-----------------------

GeosLogReader is a Paraview Reader that load GEOS log files with the extension ".out" or ".txt" as a vtkTable.
A list of options allows to choose which information to extract from the log file.

## Credits

This work benefits from inputs from all the SIM/CS team members and GEOS developers and users.
