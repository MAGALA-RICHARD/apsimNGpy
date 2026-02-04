
.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact

More examples about `edit_model_by_path`
=======================================

.. code-block:: python

    from pathlib import Path
    from os.path import realpath
    from apsimNGpy.core.apsim import ApsimModel



The variable constants listed below are required for the subsequent demonstration example

.. code-block:: python

    from apsimNGpy.core.config import load_crop_from_disk
    Fertilise_at_sowing = '.Simulations.Simulation.Field.Fertilise at sowing'
    SurfaceOrganicMatter = '.Simulations.Simulation.Field.SurfaceOrganicMatter'
    Clock = ".Simulations.Simulation.Clock"
    Weather = '.Simulations.Simulation.Weather'
    Organic = '.Simulations.Simulation.Field.Soil.Organic'
    cultivar_path = '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_100'
    cultivar_path_soybean ='.Simulations.Simulation.Field.Soybean.Cultivars.Generic.Generic_MG2'
    cultivar_path_for_sowed_soybean = '.Simulations.Simulation.Field.Soybean.Cultivars.Australia.Davis'
    cultivar_path_for_sowed_maize = '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82'
    # Create weather file on disk
    met_file = realpath(Path('wf.met'))
    met_file = load_crop_from_disk('AU_Goondiwindi', out=met_file, suffix='.met')

.. code-block:: python

Edit cultivar and provide a custom new name

.. code-block:: python

        with ApsimModel('Maize') as model:

            model.edit_model_by_path(
                path=cultivar_path_for_sowed_maize,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=20,
                sowed=True,
                rename='edm'
            )

            # Verify rename
            edited = model.inspect_model_parameters_by_path(cultivar_path)



Mixed code examples for editing weather, organic, clock and manger nodes

.. code-block:: python

        with ApsimModel('Maize') as apsim:
            #_________________________
            # Apply edits
            #_________________________
            apsim.edit_model_by_path(Fertilise_at_sowing, Amount=12)
            apsim.edit_model_by_path(Clock, start_date='01/01/2020')
            apsim.edit_model_by_path(SurfaceOrganicMatter, InitialCNR=100)
            apsim.edit_model_by_path(Weather, weather_file=realpath(met_file))
            apsim.edit_model_by_path(Organic, Carbon=1.23)
            #_________________________
            # Inspect updated values
            #_________________________
            organic_params = apsim.inspect_model_parameters_by_path(Organic)
            #_________________________
            # use dict unpacking
            #_________________________
            apsim.edit_model_by_path(**dict(path=Organic, Carbon=1.20))
            cc = apsim.inspect_model_parameters_by_path(Organic)
            #_________________________
            # use set_param method
            #_________________________
            apsim.set_params(dict(path=Organic, Carbon=1.58))
            updated = apsim.inspect_model_parameters_by_path(Organic)




edit cultivar when not yet sowed. this is accomplished by providing the fullpath to the manager script sowing the cultivar

.. code-block:: python

        with ApsimModel('Maize') as model:
            model.inspect_file(cultivar=True)
            model.edit_model_by_path(
                path='.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowed=True,
                rename='edit-added')



.. code-block:: python

        with ApsimModel('Maize') as model:
            model.edit_model_by_path(
                path=cultivar_path,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=505,
                update_manager=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')


Edit cultivar parameters, when it is not sowed

.. code-block:: Python

        with ApsimModel('Soybean') as model:
            model.edit_model_by_path(
                path=cultivar_path_soybean,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowed=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')




