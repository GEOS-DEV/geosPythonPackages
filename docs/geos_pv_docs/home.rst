Home
====

**geos-pv** is a Python package that gathers `Paraview <https://www.paraview.org/>`_ plugins of GEOS python tools. 

It includes:

* Paraview readers allowing to load data;
* generic tools to processes meshes;
* GEOS pre-processing tools to clean and check GEOS input mesh;
* GEOS post-processing tools to clean GEOS output mesh, compute additional properties, or create specific plots such as Mohr's circle plot.

The packages can be loaded into Paraview using the Plugin Manager from `Tools > Plugin Manager`. On success, you will 
see the selected plugin in the `Filters`` menu (see `Paraview documentation <https://docs.paraview.org/en/latest/ReferenceManual/pythonProgrammableFilter.html>`.

Alternatively, geos-pv package can be build together with Paraview ([see Paraview compilation guide](https://gitlab.kitware.com/paraview/paraview/-/blob/master/Documentation/dev/build.md)). 
It is recommended to use Paraview v5.12+, which is based on python 3.10+. If you need to build geos-pv package with the paraview dependency, use the command:
`pip install Path/To/geosPythonPackages/geos-pv[paraview]`
