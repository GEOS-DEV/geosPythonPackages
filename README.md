[![DOI](https://zenodo.org/badge/131810578.svg)](https://zenodo.org/badge/latestdoi/131810578)
[![codecov](https://codecov.io/github/GEOS-DEV/geosPythonPackages/graph/badge.svg?token=0VTEHPQG58)](https://codecov.io/github/GEOS-DEV/geosPythonPackages)
[![CI](https://github.com/GEOS-DEV/GEOS/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/GEOS-DEV/geosPythonPackages/actions?query=branch%3Adevelop)
[![docs](https://readthedocs.com/projects/geosx-geosx/badge/?version=latest)](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/)

Welcome to the GEOS Python Package Repository !
===============================================

The `geosPythonPackages` repository contains a set of python tools that are used alongside [GEOS](https://github.com/GEOS-DEV/GEOS). They include testing tools, pre- and post-processing filters and plugins, as well as diverse executables. You will find below a brief description of the different packages, please refer to the [Python Tools documentation](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/) for more details.


Packages organization
---------------------

> [!WARNING]
> This repository is currently under refactoring to improve package organization, maintainability, and dependency management. The following describes the final package organisation. Some packages may still miss or contain code that will be moved later.

* Data structures and processing packages
  * `geos-ats`: tools for managing integrated tests for GEOS.
  * `pygeos-tools`: variety of tools for working with *pygeosx* objects.
  * `geos-utils`: basic utilities
  * `geos-geomechanics`: geomechanics functions and data model
  * `geos-mesh`: generic mesh processing tools
  * `hdf5-wrapper`: wrapper to load hdf5 files
  * `geos-xml-tools`: xml reader and writer dedicated to GEOS xml file
* User-oriented API packages
  * `geos-processing`: GEOS pre- and post-processing VTK filters
  * `xml-vtk`: conversion of GEOS xml to VTK objects and conversely
* Hands-on executables that can be used through command line
  * `mesh-doctor`: GEOS pre-processing mesh validation application
  * `geos-timehistory`: load and plot hdf5 files
  * `geos-trame`: web interface to check, display objects, and edit GEOS xml file (see [Trame documentation](https://kitware.github.io/trame/guide/tutorial/))
* Paraview plugins (see [Paraview](https://docs.paraview.org/) documentation)
  * `geos-pv`: plugins that wrap GEOS Python tools


GEOS Python packages dependency tree (inter-dependency and main external dependencies) is the following:

```
├── geos-ats
├── pygeos-tools
│   ├── geos-utils
│   ├── geos-xml-tools
│   ├── geos-mesh
│   ├── vtk
│   └── h5py
|
├── geos-utils
|
├── geos-geomechanics
│   └── geos-utils
|
├── geos-mesh
│   ├── geos-utils
│   └── vtk
|
├── hdf5-wrapper
│   └── h5py
|
├── geos-xml-tools
│   ├── geos-utils
│   └── lxml
|
├── geos-processing
│   ├── geos-mesh
│   └── geos-geomechanics
|
├── xml-vtk
│   ├── geos-mesh
|   └── geos-xml-tools
│
├── geos-timehistory
│   └── hdf5-wrapper
|
├── mesh-doctor
│   ├── geos-prep
│   └── pyvista
|
├── geos-trame
│   ├── geos-xml-tools
│   ├── geos-mesh
│   ├── pyvista
│   └── trame
│
└── geos-pv
    ├── geos-processing
    ├── geos-mesh
    ├── geos-geomechanics
    ├── geos-utils
    ├── geos-xml-tools
    └── paraview
```


Installation
-------------

* *Automatic installation for GEOS developpers:*

  GEOS Python packages can be automatically installed after having build GEOS by running `make geosx_python_tools` in the GEOS build directory.

* *Manual installation:*

  GEOS Python packages can be manually installed with pip using `python` >= 3.10.

    To install any package, run the following commands from the `geosPythonPackage` directory:
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

  >[!WARNING]
   Due to local package conflicts with `pip install`, it is recommended to use the `--upgrade` option when building packages, or to use the script `install_packages.sh` located at the root of the repository.

  >[!NOTE]
  `geos-pv` package cannot be build alone, but together with Paraview ([see Paraview compilation guide](https://gitlab.kitware.com/paraview/paraview/-/blob/master/Documentation/dev/build.md)). It is recommended to use Paraview v5.13+, which is based on python 3.10+. Alternatively, plugins from `geos-pv/src/geos/pv/plugins` can be manually loaded into Paraview ([see documentation](https://docs.paraview.org/en/latest/ReferenceManual/pythonProgrammableFilter.html#python-algorithm)).


Contributions
-------------

GEOS Python packages repository gathers python scripts from any GEOS developpers and users. Feel free to share any scripts that may benefit to the GEOS community.

If you would like to report a bug, please submit an [issue](https://github.com/GEOS-DEV/geosPythonPackages/issues/new).

If you would like to contribute to GEOS Python packages, please respect the following guidelines:

1. Create a new branch named from this template: `[CONTRIBUTOR]/[TYPE]/[TITLE]` where CONTRIBUTOR is the name of the contributor, TYPE is the type of contribution among 'feature', 'refactor', 'doc', 'ci', TITLE is a short title for the branch.
2. Add your code trying to integrate into the current code architecture.
3. Run mypy, ruff and yapf in this order
  ```
  python -m pip install --upgrade mypy ruff yapf
  python -m mypy --config-file ./.mypy.ini --check-untyped-defs ./<PACKAGE_NAME>
  python -m ruff check --fix --config .ruff.toml ./<PACKAGE_NAME>
  python -m yapf -r -i --style .style.yapf ./<PACKAGE_NAME>
  ```
4. Push the branch, open a new PR respecting naming [semantics](https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716), and add reviewers

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

>[!IMPORTANT]
`geos-pv` dependencies are managed using a `requirements.txt` (together with the `setup.py`) file where all internal (and external if needed) dependencies are present. It ensures that internal dependency paths are correctly set when plugins are manually loaded into Paraview.

Release
-------

For release details and restrictions, please read the [LICENSE](https://github.com/GEOS-DEV/GEOS/blob/develop/LICENSE) file.

For copyrights, please read the [COPYRIGHT](https://github.com/GEOS-DEV/GEOS/blob/develop/COPYRIGHT ) file.

For contributors, please read the [CONTRIBUTORS](https://github.com/GEOS-DEV/GEOS/blob/develop/CONTRIBUTORS ) file.

For acknowledgements, please read the [ACKNOWLEDGEMENTS](https://github.com/GEOS-DEV/GEOS/blob/develop/ACKNOWLEDGEMENTS ) file.

For notice, please read the [NOTICE](https://github.com/GEOS-DEV/GEOS/blob/develop/NOTICE ) file.
