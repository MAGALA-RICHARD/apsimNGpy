.. _Installation:

Installation
------------

All versions are currently in development, phase and they can be installed as follows:

- Method 1. install from PyPI

.. code:: bash

    pip install apsimNGpy

- Method 1. clone the current development repository

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

- Method 2. Use pip straight away and install from github

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git

Quick guides
----------------

Before using apsimNGpy, it is necessary to install APSIM. Please follow the instructions provided at the following link to complete the installation: https://www.apsim.info/download-apsim/downloads/
for MAcOS or Linux users see: https://apsimnextgeneration.netlify.app/install/
model documentation and tutorial are also available via; https://docs.apsim.info/
we expect that by accepting to use apsimNGpy, you have a basic understanding of APSIM process-based model, therefore, our focus is to make sure you are able to use apsimNGpy

In addition, make sure that the APSIM installation binaries folder is added to the system path.
if you run the following code and returns None you need to do something as explained below.

- 1. Use command line interface

.. code-block:: bash

     apsim_bin_path -s

- 2. Use apsimNGpy config module

.. code-block:: python

   from apsimNGpy.core import config
      print(config.get_apsim_bin_path())

You can also try to check if automatic search will be successful as follows

.. code-block:: bash

    apsim_bin_path --auto_search

The short cut

.. code-block:: bash

    apsim_bin_path -a


Locating the APSIM Binaries
---------------------------
By default the APSIM binaries are located automatically. The process for determining the APSIM binary path is as follows:

In apsimNGpy, priority is first given to the user-supplied binary path.
If no path is supplied, the module searches through the Python global environment
using the os module. If that fails, it searches through other folders.
If all approaches are exhausted and no valid path is found, a ValueError will be raised.


Changing/setting the APSIM installation binaries path
---------------------------------------------------
If the automatic search fails, please follow one of the steps below to resolve the issue:

1. Manually configure the APSIM binary path. To do this:
^^^^^^^^^^^^^^^^

In your home folder you could look for folder named apsimNGpy_meta_info './APSIMNGpy_meta_data'
     1. Locate the folder named `APSIMNGpy_meta_info` in your home directory (e.g., `./APSIMNGpy_meta_data`).
     2. Open the file `apsimNGpy_config.ini` within this folder.
     3. Modify the `apsim_location` entry to reflect your desired APSIM binary path.

2. Change based os.environ module
^^^^^^^^^^^^^^^^

Alternatively, you can use the code at the top of your script as follows

.. code-block:: python

    # Search for the APSIM binary installation path and add it to os.environ as follows:
    import os
    os.environ['APSIM'] = r'path/to/your/apsim/binary/folder/bin'

- Note:

This approach may not work consistently in all scenarios, but you can try it.
The above script line should always be placed at the beginning of your simulation script.
However, why follow this approach when you can achieve the same result more efficiently? See the approach below:

3. Use the apsimNGpy config module:
^^^^^^^^^^^^^^^^

.. code-block:: python

    from apsimNGpy.config import set_apsim_bin_path

    # Set the path to the APSIM binaries:
    set_apsim_bin_path(path=r'path/to/your/apsim/binary/folder/bin')


4. Use command line interface
^^^^^^^^^^^^^^^^

After installing apsimNGpy, navigate to your terminal and run the following

.. code-block:: bash

    apsim_bin_path -u 'path/to/your/apsim/binary/folder/bin'

Or

.. code-block:: bash

    apsim_bin_path --update 'path/to/your/apsim/binary/folder/bin'


Now that the path is set, you can import any module attached to pythonnet.
"""""""""""""""""""""

.. code-block:: python

    # For example, try importing the ApsimModel class:
    from apsimNGpy.core.apsim import ApsimModel

.. _Usage:

The above code is also applicable for running different versions of APSIM models.
The `set_apsim_bin_path` function can be called once and retained unless you uninstall `apsimNGpy`
or the APSIM application itself. This implies that you can switch between apsim versions easily if you have more than one versions installed on your computer
