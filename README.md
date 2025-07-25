[![DOI](https://zenodo.org/badge/131810578.svg)](https://zenodo.org/badge/latestdoi/131810578)
[![codecov](https://codecov.io/github/GEOS-DEV/geosPythonPackages/graph/badge.svg?token=0VTEHPQG58)](https://codecov.io/github/GEOS-DEV/geosPythonPackages)
[![CI](https://github.com/GEOS-DEV/GEOS/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/GEOS-DEV/geosPythonPackages/actions?query=branch%3Adevelop)
[![docs](https://readthedocs.com/projects/geosx-geosx/badge/?version=latest)](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/)

Welcome to the GEOS Python Package Repository!
==============================================

This repository contains a set of python packages that are used alongside [GEOS](https://github.com/GEOS-DEV/GEOS).


Package summary
---------------

**WARNING: This repository is currently under refactoring to improve package organization, maintainability, and dependency management. The following describes the final package organisation. Some packages may still miss or contain code that will be move later.**

* `geos-ats` package includes tools for managing integrated tests for GEOS.
* `pygeos-tools` package adds a variety of tools for working with *pygeosx* objects.

The next packages are dedicated to pre- and post-process GEOS inputs/outputs. 

The following packages contain basic utilities used by the other ones:

* `geos-utils`: basic utilities
* `geos-geomecanics`: geomechanics functions and data model


The following packages define data models, vtk filters, and user-oriented API:

* `geos-xml-tools`: xml reader and writer dedicated to GEOS xml file
* `hdf5-wrapper`: wrapper to load hdf5 files
* `geos-mesh`: general mesh processing tools
* `geos-prep`: GEOS pre-processing tools
* `geos-posp`: GEOS post-processing tools


The following packages define hands-on executables that can be used through the command line:

* `mesh-doctor`: GEOS pre-processing application
* `time-history`: load and plot hdf5 files
* `geos-xml-viewer`: load GEOS xml file and display geometrical objects (mesh, boxes, wells)
* `geos-trame`: web interface to check, display objects, and edit GEOS xml file (see [Trame documentation](https://kitware.github.io/trame/guide/tutorial/))


The following package defines [Paraview](https://docs.paraview.org/) plugins that wrap GEOS Python tools

* `geos-pv`

GEOS Python packages dependency tree (inter-dependency and main external dependencies) is the following:

```
├── geos-ats
├── pygeos-tools
├── geos-utils
├── geos-geomechanics
│   ├── geos-utils
│
├── hdf5-wrapper
│   ├── h5py
│
├── geos-xml-tools
│   ├── lxml
│
├── geos-mesh
│   ├── geos-utils
│   ├── vtk
│
├── geos-prep
│   ├── geos-mesh
│   ├── geos-xml-tools
│
├── geos-posp
│   ├── geos-mesh
│   ├── geos-geomechanics
│
├── time-history
│   ├── hdf5-wrapper
│
├── mesh-doctor
│   ├── geos-prep
│   ├── pyvista
│
├── geos-trame
│   ├── geos-xml-tools
│   ├── geos-mesh
│   ├── pyvista
│   ├── trame
│
├── geos-xml-viewer
│   ├── geos-xml-tools
│   ├── geos-mesh
│   ├── pyvista
│
├── geos-pv
    ├── geos-prep
    ├── geos-posp
    ├── geos-xml-tools
    ├── paraview
```

See the [documentation](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/) for additional details about the packages and how to use them.


Installation
-------------

* *Automatic installation for GEOS developpers:*

  GEOS Python packages can be automatically installed after having build GEOS by running `make geosx_python_tools` in the GEOS build directory.

* *Manual installation:*

  GEOS Python packages can be manually installed with pip using `python` >= 3.10. 

    To install any package, run the following commands from the geosPythonPackage directory:

    ```
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install --upgrade ./<PACKAGE_NAME>
    ```

    You can test installed package by running the commands:

    ```
    python -m pip install pytest
    python -m pytest ./<PACKAGE_NAME>
    ```

  [!WARNING]
   Due to local package conflicts with `pip install`, it is recommended to use the `--upgrade` option when building packages, or to use the script `install_packages.sh` located at the root of the repository.
  [!NOTE]
  geos-pv package cannot be build alone, but together with Paraview ([see Paraview compilation guide](https://gitlab.kitware.com/paraview/paraview/-/blob/master/Documentation/dev/build.md)). It is recommended to use Paraview v5.12+, which is based on python 3.10+. Alternatively, plugins from geos-pv/PVplugins can be manually loaded into Paraview ([see documentation](https://docs.paraview.org/en/latest/ReferenceManual/pythonProgrammableFilter.html#python-algorithm)).


Contributions
-------------

GEOS Python packages repository gathers python scripts from any GEOS developpers and users. Feel free to share any scripts that may benefit to the GEOS community.

If you would like to report a bug, please submit an [issue](https://github.com/GEOS-DEV/geosPythonPackages/issues/new). 

If you would like to contribute to GEOS Python packages, please respect the following guidelines:

1. Create a new branch named from this template: `[CONTRIBUTOR]/[TYPE]/[TITLE]` where CONTRIBUTOR is the name of the contributor, TYPE is the type of contribution among 'feature', 'refactor', 'doc', 'ci', TITLE is a short title for the branch.
2. Add your code trying to integrate into the current code architecture.
3. Push the branch, open a new PR respecting naming [semantics](https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716), and add reviewers

If you do not have the rights to push the code and open new PRs, consider opening a new issue to explain what you want to do and ask for the dev rights.

Any new package must have the following architecture:

```
package-name/
├── pyproject.toml
├── src
│   ├── geos
│       ├── package_name
│           ├── file1.py
│           ├── file1.py
├── tests
    ├── test1.py
    ├── test2.py
```

If you want a package to depend on another GEOS Python package (let's say `geos-utils`), in the pyproject.toml the dependency takes the form:

```
dependencies = [
    ...
    "geos-utils",
]
```

[!IMPORTANT]
geos-pv dependencies are managed using a `requirements.txt` (together with the `setup.py`) file where all internal (and external if needed) dependencies are present. It ensures that internal dependency paths are correctly set when plugins are manually loaded into Paraview.

Release
-------

For release details and restrictions, please read the [LICENSE](https://github.com/GEOS-DEV/GEOS/blob/develop/LICENSE) file.

For copyrights, please read the [COPYRIGHT](https://github.com/GEOS-DEV/GEOS/blob/develop/COPYRIGHT ) file.

For contributors, please read the [CONTRIBUTORS](https://github.com/GEOS-DEV/GEOS/blob/develop/CONTRIBUTORS ) file.

For acknowledgements, please read the [ACKNOWLEDGEMENTS](https://github.com/GEOS-DEV/GEOS/blob/develop/ACKNOWLEDGEMENTS ) file.

For notice, please read the [NOTICE](https://github.com/GEOS-DEV/GEOS/blob/develop/NOTICE ) file.
