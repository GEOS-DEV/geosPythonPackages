
Time History Tools
--------------------------

The `geos-timehistory` package contains tools to treat and plot time-history data from GEOS output.

Usage
^^^^^^^^

.. code-block:: bash

    $ python plot_time_history.py --help

    usage: plot_time_history.py [-h] [--sets name [name ...]]
                            [--indices index [index ...]]
                            [--components int [int ...]]
                            history_file variable_name

    A script that parses geosx HDF5 time-history files and produces time-history
    plots using matplotlib

    positional arguments:
    history_file          The time history file to parse
    variable_name         Which time-history variable collected by GEOSX to
                            generate a plot file for.

    options:
    -h, --help            show this help message and exit
    --sets name [name ...]
                            Which index set of time-history data collected by GEOS
                            to generate a plot file for, may be specified multiple
                            times with different indices/components for each set.
    --indices index [index ...]
                            An optional list of specific indices in the most-
                            recently specified set.
    --components int [int ...]
                            An optional list of specific variable components


API
^^^^

.. automodule:: geos.timehistory.plot_time_history
    :members:

