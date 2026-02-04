.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 1
   :class: compact

Soil Parameter Value Refilling
=============================

Soil parameters in APSIM can be updated using any of the following methods
- :meth:`apsimNGpy.core.ApsimModel.get_soil_from_web`,
- :meth:`apsimNGpy.core.ApsimModel.edit_model`, and
- :meth:`apsimNGpy.core.ApsimModel.edit_model_by_path`.

Detailed usage of :meth:`apsimNGpy.core.ApsimModel.edit_model` and
:meth:`apsimNGpy.core.ApsimModel.edit_model_by_path` is provided in the
:ref:`editor` section.

This section focuses on
:meth:`apsimNGpy.core.ApsimModel.get_soil_from_web`, which retrieves soil
profiles from online databases. By default, soils are downloaded from
**ISRIC (SoilGrids)** for global coverage, while **SSURGO** is available
for locations within the contiguous United States.

The method also accepts optional scalar parameters (e.g., ``CONA_U``,) to further customize the soil profile. Refer to
the API documentation (:meth:`apsimNGpy.core.ApsimModel.get_soil_from_web`) for a complete list of supported arguments.

Example workflow
====================

1. Source ISRIC database
---------------------------

.. code-block:: python

   from apsimNGpy.core.apsim import ApsimModel
   LONLAT = -93.658723, 42.08567949
   with ApsimModel('Maize') as maize_model:
       model.get_soil_from_web(simulations=None, lonlat=LONLAT, source='isric')
       model.run(verbose=True)
       mi =model.results.Yield.mean()
       print(mi)
       # output 5976.794446324352

2. SOURCE SSURGO
---------------------

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    LONLAT = -93.658723, 42.08567949
    with ApsimModel('Maize') as model:
       model.get_soil_from_web(simulations=None, lonlat=LONLAT, source='ssurgo')
       model.run(verbose=True)
       ms =model.results.Yield.mean()
       print(ms)
       print(ms)
       # output