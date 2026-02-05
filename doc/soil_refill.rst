.. _soil_param_refill:

Soil Parameter Value Replacement
=================================

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 3


Overview
==============

Soil parameters in APSIM can be updated using any of the following methods.

    - :meth:`~apsimNGpy.core.apsim.ApsimModel.get_soil_from_web`
    - :meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model`
    - :meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model_by_path`

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
---------------------------------
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

Soil profile layer thickness
---------------------------------
By default, apsimNGpy downloads soil data from the web and interpolates soil profile values to a soil profile of 10 layers, with a maximum depth of 2400 mm.
The soil profile is generated assuming a thinnest top layer of 100 mm in case no thickness_sequence is specified and thickness_growth_rate of 1.5.

Users can override this default behavior by explicitly providing a custom soil thickness sequence as a list.
For example, the following thicknesses may be supplied:

`[50, 100, 150, 200, 200, 300, 400, 400]`. The example below demonstrates how this customization works in practice.

.. code-block:: python

     with ApsimModel("Maize") as model:
       logger.info([i.Name for i in model.simulations])
       # output ['Simulation']
       th = [50, 100, 150, 200, 200, 300, 400, 400]
       model.get_soil_from_web(simulations='Simulation', lonlat=LONLAT, source="isric",  thickness_sequence=th)
       model.run(verbose=True)
       ms = model.results.Yield.mean()
       print(ms)
       # output: 7029.702721876342
       p=model.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical')
       print(p) # results are shown below

The changes were successfully propagated into the current model.
apsimNGpy applies simple interpolation techniques to adjust the parameters accordingly.
The resulting output is shown below

.. code-block:: none

         AirDry        BD       DUL       DULmm      Depth  DepthMidPoints  \
    0  0.086625  1.377500  0.365500   18.275000       0-50            25.0
    1  0.087750  1.475000  0.361000   36.100000     50-150           100.0
    2  0.088250  1.540000  0.358000   53.700000    150-300           225.0
    3  0.088667  1.546667  0.356000   71.200000    300-500           400.0
    4  0.090000  1.560000  0.352000   70.400000    500-700           600.0
    5  0.089375  1.610000  0.345125  103.537500   700-1000           850.0
    6  0.088500  1.680000  0.335500  134.200000  1000-1400          1200.0
    7  0.087500  1.760000  0.313849  125.539623  1400-1800          1600.0

           KS      LL15     LL15mm      PAWC     PAWCmm       SAT       SATmm  \
    0  1000.0  0.173250   8.662500  0.192250   9.612500  0.460189   23.009434
    1  1000.0  0.175500  17.550000  0.185500  18.550000  0.423396   42.339623
    2  1000.0  0.176500  26.475000  0.181500  27.225000  0.398868   59.830189
    3  1000.0  0.177333  35.466667  0.178667  35.733333  0.396352   79.270440
    4  1000.0  0.180000  36.000000  0.172000  34.400000  0.391321   78.264151
    5  1000.0  0.178750  53.625000  0.166375  49.912500  0.372453  111.735849
    6  1000.0  0.177000  70.800000  0.158500  63.400000  0.346038  138.415094
    7  1000.0  0.175000  70.000000  0.138849  55.539623  0.315849  126.339623

             SW        SWmm  Thickness  ThicknessCumulative
    0  0.365500   18.275000       50.0                 50.0
    1  0.361000   36.100000      100.0                150.0
    2  0.358000   53.700000      150.0                300.0
    3  0.356000   71.200000      200.0                500.0
    4  0.352000   70.400000      200.0                700.0
    5  0.345125  103.537500      300.0               1000.0
    6  0.335500  134.200000      400.0               1400.0
    7  0.313849  125.539623      400.0               1800.0

.. seealso::

   - save: :meth:`~apsimNGpy.core.apsim.ApsimModel.save`
   - results retrieval API: :attr:`~apsimNGpy.core.apsim.ApsimModel.results`

.. seealso::

   - :ref:`API Reference <api_ref>`
   - :ref:`apsimNGpy Cheat sheat <cheat>`
   - :ref:`Inspecting Model Parameters <inspect_params>`
   - :ref:`APSIM Model types <model_List>`
   - :ref:`Go back to the home page<master>`
