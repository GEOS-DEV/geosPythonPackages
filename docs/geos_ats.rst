
GEOS ATS
==========

The `geos_ats` python package includes tools for managing integrated tests for GEOS.
It is built using the `Automated Test System <https://ats.readthedocs.io/en/latest/>`_ (ATS) package.
The available console scripts for this package and its API are described below.


run_geos_ats
----------------

Primary entry point for running integrated tests.

.. argparse::
   :module: geos_ats.command_line_parsers
   :func: build_command_line_parser
   :prog: run_geos_ats


.. note::
    Arguments can be passed to the underlying ATS system with the `--ats` argument.


.. note::
    Other machine-specific options for ATS can be viewed by running `run_geos_ats --ats help`


API
------


Restart Check
^^^^^^^^^^^^^^^

.. automodule:: geos_ats.helpers.restart_check
    :members:


Curve Check
^^^^^^^^^^^^^^^

.. automodule:: geos_ats.helpers.curve_check
    :members:


