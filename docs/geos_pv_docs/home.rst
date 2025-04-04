Home
====

**geos-pv** is a Python package that gathers `Paraview <https://www.paraview.org/>`_ plugins of GEOS python tools. 

It includes:

* a reader able to parse the GEOS output log (before commit version #9365098) to collect data and display them as tables;
* tools to clean and check GEOS input mesh;
* tools to clean GEOS output mesh;
* tools to compute additional geomechanical properties from GEOS outputs;
* tools to display Mohr's circles at a given time step and the evolution through time from GEOS outputs.

The packages can be loaded into Paraview using the Plugin Manager from `Tools > Plugin Manager`. On success, you will 
see the selected plugin in the `Filters`` menu (see `Paraview documentation <https://docs.paraview.org/en/latest/ReferenceManual/pythonProgrammableFilter.html>`.

Alternatively, geos-pv package can be build together with Paraview ([see Paraview compilation guide](https://gitlab.kitware.com/paraview/paraview/-/blob/master/Documentation/dev/build.md)). 
It is recommended to use Paraview v5.12+, which is based on python 3.10+. If you need to build geos-pv package with the paraview dependency, use the command:
`pip install Path/To/geosPythonPackages/geos-pv[paraview]`
