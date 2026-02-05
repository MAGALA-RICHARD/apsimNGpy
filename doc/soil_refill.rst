.. _soil_param_refill:

Soil Parameter Value Replacement
================================

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact


Overview
==============

Soil parameters in APSIM can be updated using any of the following methods
- :meth:`~apsimNGpy.core.apsim.ApsimModel.get_soil_from_web`,
- :meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model`, and
- :meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model_by_path`.

Detailed usage of :meth:`~apsimNGpy.core.ApsimModel.edit_model` and
:meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model_by_path` is provided in the
:ref:`editor` section.

This section focuses on
:meth:`~apsimNGpy.core.apsim.ApsimModel.get_soil_from_web`, which retrieves soil
profiles from online databases. By default, soils are downloaded from
**ISRIC (SoilGrids)** for global coverage, while **SSURGO** is available
for locations within the contiguous United States.

The method also accepts optional scalar parameters (e.g., ``CONA_U``,) to further customize the soil profile. Refer to
the API documentation (:meth:`~apsimNGpy.core.apsim.ApsimModel.get_soil_from_web`) for a complete list of supported arguments.

Example workflow
====================

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.logger import logger


1. ISRIC Soil Database
========================

This example retrieves soil data from the **ISRIC** database and runs a maize simulation.

.. code-block:: python

   LONLAT = (-93.658723, 42.08567949)
   with ApsimModel("Maize") as model:
       model.get_soil_from_web(simulations=None, lonlat=LONLAT, source="isric")
       model.run(verbose=True)
       mi = model.results.Yield.mean()
       print(mi)
       # output: 5976.794446324352


2. SSURGO Soil Database
========================

This example retrieves soil data from the **SSURGO** database and runs the same maize simulation.

.. code-block:: python

   from apsimNGpy.core.apsim import ApsimModel

   LONLAT = (-93.658723, 42.08567949)

   with ApsimModel("Maize") as model:
       model.get_soil_from_web(simulations=None, lonlat=LONLAT, source="ssurgo")
       model.run(verbose=True)
       ms = model.results.Yield.mean()
       print(ms)
       # output: 6177.591814492994

.. note::

   In this example, a ``with`` block is used so that the APSIMX file and
   its associated database files are deleted automatically after the
   model run. If you prefer, you can also initialize and run the model
   directly without using a context manager.

   For example:

   .. code-block:: python

      model = ApsimModel("Maize")

   You may replace ``"Maize"`` with the path to any APSIMX file on your
   computer. When providing a custom file, ensure that the filename
   includes the ``.apsimx`` suffix.

Targeting a specific simulation
-------------------------------
By default, all available simulations are updated with the downloaded soils profiles.
However, when multiple simulations are present, you can target a specific simulation explicitly.

.. code-block:: python

   with ApsimModel("Maize") as model:
       logger.info([i.Name for i in model.simulations])
       # output ['Simulation']
       model.get_soil_from_web(simulations='Simulation', lonlat=LONLAT, source="ssurgo")
       model.run(verbose=True)
       ms = model.results.Yield.mean()
       print(ms)
       # output: 6177.591814492994

Soil thickness
-----------------
By default, apsimNGpy downloads soil data from the web and interpolates soil profile values to a soil profile of 10 layers, with a maximum depth of 2400 mm

Users can override this default behavior by explicitly providing a custom soil thickness sequence as a list. For example, the following thicknesses may be supplied:

50, 100, 150, 200, 200, 300, 400, 400

The example below demonstrates how this customization works in practice.
