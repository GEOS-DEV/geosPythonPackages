
Python Tools
==========================


.. _PythonToolsSetup:

Python Tools Setup
---------------------------------

The preferred method to setup the GEOS python tools is to run the following command in the build directory:

.. code-block:: bash

    make geosx_python_tools


The ats setup command also sets up the python tools:

.. code-block:: bash

    make ats_environment


These will attempt to install the required packages into the python distribution indicated via the `Python3_EXECUTABLE` cmake variable (also used by pygeosx).
If any package dependencies are missing, then the install script will attempt to fetch them from the internet using pip.
After installation, these packages will be available for import within the associated python distribution, and a set of console scripts will be available within the GEOS build bin directory.


.. note::
    To re-install or update an installed version of geosPythonTools, you can run the `make geosx_python_tools_clean` and `make geosx_python_tools` commands.


Manual Installation
---------------------------------

In some cases, you may need to manually install or update geosPythonPackages.
To do this, you can clone a copy of the geosPythonPackages repository and install them using pip:


.. code-block:: bash

    cd /path/to/store/python/tools
    git clone https://github.com/GEOS-DEV/geosPythonPackages.git

    # Install/upgrade geos-ats
    cd geosPythonPackages/
    python -m pip install --upgrade geos-ats


.. note::
    To upgrade an existing installation, the python executable in the above command should correspond to the version you indicated in your host config.  If you have previously built the tools, this version will be linked in the build directory: `build_dir/bin/python`.

.. Important::
    Due to local package dependencies, it is advised to always use the `--upgrade` option when building with the `pip install` option.

Development & Debugging
---------------------------

Be default, the python environment setup commands target the "main" branch of geosPythonTools.
To target another version of the tools, you can set the `GEOS_PYTHON_PACKAGES_BRANCH` cmake variable to the name of another valid branch (or git tag) in the host config file.
In this case, the code will pull the most recent commit of the desired branch when building geosPythonTools.


.. note::
    If you are working on significant updates to geosPythonTools, you should open a testing branch in the main GEOS repository that defines the `GEOS_PYTHON_PACKAGES_BRANCH` variable.  This will ensure that your changes are tested as part of the GEOS CI.


If you need to debug one of the packages in geosPythonTools, we recommend using VSCode with the Python extension installed.
Some of the packages contain specific entry point scripts that can be used to assist in this process.



Packages
-----------------------


.. toctree::
    :maxdepth: 5

    hdf5-wrapper

    geos-ats

    geos-geomechanics

    geos-mesh

    geos-processing

    geos-pv

    geos-timehistory

    geos-utils

    geos-xml-tools

    geos-xml-viewer

    pygeos-tools