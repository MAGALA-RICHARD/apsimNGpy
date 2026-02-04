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
