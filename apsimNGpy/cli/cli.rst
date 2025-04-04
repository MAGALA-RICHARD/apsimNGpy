.. _cli_usage:

=========================
Command-Line Usage Guide
=========================
APSIMNGpy provides a CLI interface that allows you to modify configurations and run simulations using a single-line command.

Usage
-----

Setting the APSIM binary path is implemented via the `apsim_bin_path` CLI module as follows:

After installing apsimNGpy, navigate to your terminal and run the following command to update the APSIM binary path:

.. code-block:: bash

    apsim_bin_path -u 'path/to/your/apsim/binary/folder/bin'

 Or

.. code-block:: bash

    apsim_bin_path --update 'path/to/your/apsim/binary/folder/bin'

To run APSIM via APSIMNGpy from the command line, use:

.. code-block:: bash

   apsim [OPTIONS]

Additionally, ensure that the APSIM installation binaries folder is added to the system path.
If you run the following command and it returns `None`, you need to set the correct bin path as explained below.

The following command displays the bin path currently used by APSIMNGpy:

.. code-block:: bash

   apsim_bin_path -s

You can also attempt an automatic search for the APSIM bin path:

.. code-block:: bash

    apsim_bin_path --auto_search

Shortcut for auto search:

.. code-block:: bash

    apsim_bin_path -a


Running Simulations
-------------------

On the command-line interface, simulations are executed using the keyword `apsim`.

This module provides a command-line interface (CLI) for running APSIM simulations with various options. Below is a guide on how to use it.

Options
-------

The following options are available:

- ``-m, --model`` (str, optional): Path to the APSIM model file. Defaults to `"Maize"`. If providing a path, ensure it ends with `.apsimx` and is absolute if not in the current directory.
- ``-o, --out`` (str, optional): Output directory.
- ``-t, --table`` (str, optional): Report table name. Defaults to `"Report"`.
- ``-w, --met_file`` (str, optional): Path to the weather data file.
- ``-sim, --simulation`` (str, optional): Name of the APSIM simulation to run.
- ``-ws, --wd`` (str, optional): Working directory for the simulation.
- ``-l, --lonlat`` (str, optional): Latitude and longitude (comma-separated) for fetching weather data.
- ``-sf, --save`` (str, optional): File name for saving output data.
- ``-s, --aggfunc`` (str, optional): Statistical summary function (e.g., `mean`, `median`). Defaults to `"mean"`.

Example Usage
-------------

Run a simulation with a specific APSIM model:

.. code-block:: bash

  apsim -m maize --aggfunc median

Fetch weather data for a specific location and run the simulation:

.. code-block:: bash

   apsim -m maize --aggfunc median --lonlat '-92.5123, 41.045'

Specify an alternative aggregation function:

.. code-block:: bash

   apsim -m "Maize" -s "max"

Logging
-------

The script logs key actions and summaries to assist with debugging. Logged messages include:

- Command summary with parsed arguments.
- Weather file updates.
- Model execution status.
- Data aggregation results.

Troubleshooting
---------------

- Ensure APSIM is installed and accessible.
- Verify that input file paths are correct.
- If weather data is not downloading, check the API source and internet connectivity.
- Use ``--help`` to see available options:

  .. code-block:: bash

     apsim --help
