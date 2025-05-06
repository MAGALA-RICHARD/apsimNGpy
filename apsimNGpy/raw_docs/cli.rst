.. _cli_usage:

=========================
Command-Line Usage Guide
=========================

This module provides a command-line interface (CLI) for running APSIM simulations with various options. Below is a guide on how to use it.

Usage
-----

setting apsim bin path is implemented via apsim_bin_path cli module as follows

After installing apsimNGpy, navigate to your terminal and run the following to update the bin path apsim version

.. code-block:: bash

    apsim_bin_path -u 'path/to/your/apsim/binary/folder/bin'

Or
.. code-block::

    apsim_bin_path --update 'path/to/your/apsim/binary/folder/bin'

To run the apsim via apsimNGpy from the command line, use:

.. code-block:: bash

   apsim [OPTIONS]

In addition, make sure that the APSIM installation binaries folder is added to the system path. if you run the following code and returns None you need to do something as explained below.

The code below displays the bin path that is currently being used by apsimNGpy

.. code-block::

   apsim_bin_path -s

You can also try to check if automatic search will be successful as follows
.. code-block::
    apsim_bin_path --auto_search

The short cut

.. code-block::

    apsim_bin_path -a

Options
-------

The following options are available:

- ``-m, --model`` (str, optional): Path to the APSIM model file. Defaults to "Maize". If path, it should end with .apsimx and should be absolute is not in the current directory
- ``-o, --out`` (str, optional): Output directory.
- ``-i, --inspect`` (str, optional): inspect file or specific model type within the file.
- ``-t, --table`` (str, optional): Report table name. Defaults to "Report".
- ``-w, --met_file`` (str, optional): Path to the weather data file.
- ``-sim, --simulation`` (str, optional): Name of the APSIM simulation to run.
- ``-ws, --wd`` (str, optional): Working directory for the simulation.
- ``-l, --lonlat`` (str, optional): Latitude and longitude (comma-separated) for fetching weather data.
- ``-sf, --save`` (str, optional): File name for saving output data.
- ``-s, --aggfunc`` (str, optional): Statistical summary function (e.g., mean, median). Defaults to "mean".

Example Usage
-------------

Run a simulation with a specific APSIM model:

.. code-block:: bash

  apsim -m maize  --aggfunc median


Fetch weather data for a specific location and run the simulation:

.. code-block:: bash

   apsim -m  maize  --aggfunc median --lonlat '-92.5123, 41.045'


Specify an alternative aggregation function:

.. code-block:: bash

   apsim -m "Maize" -s "max"

inspect a model:

.. code-block:: bash

   apsim -m "Maize" --inspect Models.Manager

inspect the whole file in the APSIM simulation:

.. code-block:: bash

   apsim -m "Maize" --inspect file

other arguments can not be passed successfuly when inspecting, because the execution ends on model inspection.

Logging
-------

The script logs key actions and summaries to help with debugging. Logged messages include:

- Command summary with parsed arguments.
- Weather file updates.
- Model execution status.
- Data aggregation results.

Troubleshooting
---------------

- Ensure APSIM is installed and accessible.
- Verify input file paths are correct.
- If weather data is not downloading, check the API source and internet connectivity, the start and end dates in the model.
- Use ``--help`` to see available options:

  .. code-block:: bash

     apsim --help

