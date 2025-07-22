.. _editor:

.. caption:: Model Parameter Editing

Editing Model Parameters
===========================================

Editing a model involves changing model parameter values. This task can be accomplished via a unified method called ``edit_model`` or ``edit_model_by_path`` from ``CoreModel`` or ``ApsimModel`` Class
by specifying the model type, name and simulation name, or path, respectively.

edit_method function signature

.. code-block:: python

     edit_model(model_type: str, simulations: Union[str, list], model_name: str, **kwargs)


``model_type`` : str, required
    Type of the model component to modify (e.g., 'Clock', 'Manager', 'Soils.Physical', etc.).

``simulations`` : Union[str, list], optional
    A simulation name or list of simulation names in which to search. Defaults to all simulations in the model.

``model_name`` : str, required
    Name of the model instance to modify.

The following additional kwargs are specific to each each model type.

``**kwargs`` : dict, required

    - ``Weather``: requires a ``weather_file`` (str) argument, describing path to the ``.met`` weather file.

    - ``Clock``: Date properties such as ``Start`` and ``End`` in ISO format (e.g., '2021-01-01').

    - ``Manager``: Variables to update in the Manager script using ``update_mgt_by_path``. The parameters in a manager script are specific to each script. See :ref:`inspect_model_parameters:Inspect Model Parameters` for more details. for more details. for more details. on how to inspect and retrieve these paramters without opening the file in a GUI

    - ``Physical | Chemical | Organic | Water:``
      The supported key word arguments for each model type are given in the table below. Please note the values are layered and thus a ``str`` or ``list`` is accepted.
      when a value is supplied as ``str``, then it goes to the top soil layer. In case of a ``list``, value are replaced based on their respective index in the list.
      As a caution if the length of the list supplied exceeds the available number of layers in the profile, a ``RuntimeError`` during model ``runs`` will be raised.
      It is possible to target a specific layer(s) by supplying the location of that layer(s) using ``indices`` key word argument, if there is a need to target the bottom layer, use ``indices  = [-1]``

        +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
        | Soil Model Type  | **Supported key word arguments**                                                                                                     |
        +==================+======================================================================================================================================+
        | Physical         | AirDry, BD, DUL, DULmm, Depth, DepthMidPoints, KS, LL15, LL15mm, PAWC, PAWCmm, SAT, SATmm, SW, SWmm, Thickness, ThicknessCumulative  |
        +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
        | Organic          | CNR, Carbon, Depth, FBiom, FInert, FOM, Nitrogen, SoilCNRatio, Thickness                                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
        | Chemical         | Depth, PH, Thickness                                                                                                                 |
        +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            - ``SurfaceOrganicMatter``
       - InitialCNR: (int)
       - InitialResidueMass (int)

    - ``Report``:
        - ``report_name`` (str): Name of the report model (optional depending on structure).
        - ``variable_spec`` (list[str] or str): Variables to include in the report.
        - ``set_event_names`` (list[str], optional): Events that trigger the report.

    - ``Cultivar``:
        - ``commands`` (str, required): APSIM path to the cultivar model to update.
        - ``values`` (Any. required): Value to assign.
        - ``new_cultivar_name`` (str, required): the new name for the edited cultivar.
        - ``cultivar_manager`` (str, required): Name of the Manager script managing the cultivar, which must contain the `CultivarName` parameter. Required to propagate updated cultivar values, as APSIM treats cultivars as read-only.

.. warning::
    Raises the following errors:

    ``ValueError``
        If the model instance is not found, required kwargs are missing, or `kwargs` is empty.

    ``NotImplementedError``
        If the logic for the specified `model_type` is not implemented.

Quick Examples:

.. code-block:: python
        print('start')
        from apsimNGpy.core.apsim import ApsimModel
        model = ApsimModel(model='Maize')
        print(model)

Edit a cultivar model:

.. code-block:: python

    model.edit_model(
        model_type='Cultivar',
        simulations='Simulation',
        commands='[Phenology].Juvenile.Target.FixedValue',
        values=256,
        new_cultivar_name = 'B_110-e',
        model_name='B_110',
        cultivar_manager='Sow using a variable rule')

.. Hint::

    ``model_name: 'B_110'`` is an existing cultivar in the Maize Model, which we want to edit. Please note that editing a cultivar without specifying the  ``new_cultivar_name`` will throw a ``ValueError``.
    The name should be different to the the one being edited.

Edit a soil organic matter module:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Organic',
        simulations='Simulation',
        model_name='Organic',
        Carbon=1.23)

Edit multiple soil layers:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Organic',
        simulations='Simulation',
        model_name='Organic',
        Carbon=[1.23, 1.0])

Edit solute models:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Solute',
        simulations='Simulation',
        model_name='NH4',
        InitialValues=0.2)

    model.edit_model(
        model_type='Solute',
        simulations='Simulation',
        model_name='Urea',
        InitialValues=0.002)

Edit a manager script:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Manager',
        simulations='Simulation',
        model_name='Sow using a variable rule',
        population=8.4)

Edit surface organic matter parameters:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='SurfaceOrganicMatter',
        simulations='Simulation',
        model_name='SurfaceOrganicMatter',
        InitialResidueMass=2500)

    model.edit_model(
        model_type='SurfaceOrganicMatter',
        simulations='Simulation',
        model_name='SurfaceOrganicMatter',
        InitialCNR=85)

Edit Clock start and end dates:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Clock',
        simulations='Simulation',
        model_name='Clock',
        Start='2021-01-01',
        End='2021-01-12')

Edit report variables:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Report',
        simulations='Simulation',
        model_name='Report',
        variable_spec='[Maize].AboveGround.Wt as abw')

Multiple report variables:

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model(
        model_type='Report',
        simulations='Simulation',
        model_name='Report',
        variable_spec=[
            '[Maize].AboveGround.Wt as abw',
            '[Maize].Grain.Total.Wt as grain_weight'
        ])


If you prefer little boiler plate code, we got you covered with ``edit_model_by_path`` the function signature of this method is shown below.

.. code-block:: python

   model = ApsimModel(model='Maize')
   model.edit_model_by_path(path, **kwargs)

.. hint::

   The method ``edit_model_by_path`` from ``ApsimModel`` class operates on the same principle as ``edit_model``, where each model type requires specific keyword arguments.
   For example, let’s edit a manager script: ``"Sow using a variable rule"`` that performs sowing operations such as plant population, sowing date etc.

.. code-block:: python

    model = ApsimModel(model='Maize')
    model.edit_model_by_path(path = '.Simulations.Simulation.Field.Sow using a variable rule', Population =12)

.. warning::

    When using the full path, keep in mind that it inherently references a specific model type. The edit_model_by_path method internally detects this type and applies the appropriate logic.
    Therefore, if you supply an argument that is not valid for that model type, a ``ValueError`` will be raised.

.. tip::
   if in doubt, use ``detect_model_type`` followed by the corresponding full model path.

.. code-block:: python

   model = ApsimModel(model='Maize')
   model_type = model.detect_model_type('.Simulations.Simulation.Field.Sow using a variable rule')
   # outputs: Models.Manager

.. tip::

    After editing the file or model, you can save the file using the ``save()`` method. This method takes a single argument: the desired file path or name.
    Without specifying the full path to the desired storage location, the file will be saved in the current working directory.

.. code-block:: python

    model.save('./edited_maize_model.apsimx')

.. seealso::

   - :ref:`API Reference <api>`
   - :ref:`apsimNGpy Cheat sheat <cheat>`
