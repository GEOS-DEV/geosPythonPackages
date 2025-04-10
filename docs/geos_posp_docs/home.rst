Home
-----

**Geos-posp** is a Python library to read, process and visualize GEOS simulation software outputs.

**GEOS** is an open-source THM (Thermo-Hydro-Mechanical) simulation framework designed for modeling coupled flow, transport, 
and geomechanics in the subsurface on high performance computing platforms. It provides advanced solvers for various applications, 
including carbon sequestration and geothermal energy systems. 

Developed as part of the FC-MAELSTROM research project by Lawrence Livermore National Laboratory (LLNL), Stanford University, TotalEnergies, and Chevron,
GEOS draws on their expertise in simulation and high-performance computing research. If you are interested, 
you can explore more about GEOS in the `official documentation <https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/QuickStart.html/>`_.

GEOS outputs include:

* a log file where many simulation statistics are dump into;
* csv and hdf5 files containing simulation properties through time
* a 3D mesh with properties that evolve through time.

This library is based on `vtk <https://vtk.org/>`_ framework and `Paraview <https://www.paraview.org/>`_ visualization software. 
It includes:

* a reader able to parse the GEOS output log to collect data and display them as tables;
* tools to clean imported 3D mesh;
* tools to compute additional geomechanical properties;
* tools to display Mohr's circles at a given time step and the evolution through time.

The tools included in this library can be used either through:

* Python scripts that call vtk readers and filters.
* Paraview software by loading plugins located in the PVplugins folder.


The current code has been developed on Python 3.9.13 (i.e., Python version used by Paraview 5.12.0) using the following libraries:

* matplotlib 3.2.1
* pandas 2.0.1
* numpy 1.24.3
* vtk 9.3.2 
* typing_extensions 4.12

Additional dependencies:

* paraview - if plugins are used through Paraview
