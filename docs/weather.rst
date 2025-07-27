Weather Data Replacement.
============================
apsimNGpy provides both an object oriented structure and procedural structure to replace the weather data. Here, I only demonstrate the object oriented one.

Get weather data from the web
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Replace instantly from the instantiated apsimNGpy model object. This is achieved with ``get_weather_from_web()`` with the following signature;

.. code-block:: python

     get_weather_from_web(lonlat: tuple, start: int, end: int, simulations=MissingOption, source='nasa',
                                 filename=None)

``lonlat``: ``tuple``  containing the longitude and latitude coordinates in that order.

``start``: Start date for the weather data retrieval.

``end``: End date for the weather data retrieval.

``simulations``: str, list of simulations to place the weather data, defaults to all simulation if user specification is missing.

``source``: Source of the weather data. Defaults to 'nasa' because its world wide coverage, but other sources includes the ``daymet`` (Contiguous U.S. Only)

``filename``: Name of the file to save the retrieved data. If None, a default name is generated.


To use ``get_weather_from_web()``, it requires instantiation of the model as follows;

.. code-block:: python

         from apsimNGpy.core.apsim import ApsimModel
         maize_model = ApsimModel(model='Maize') # replace maize with your apsim template file

         # replace the weather with lonlat specification as follows;
         maize_model.get_weather_from_web(lonlat = (-93.885490, 42.060650), start = 1990, end  =2001)

.. warning::

    Changing weather data with non matching start and end dates in the simulation will lead to ``RuntimeErrors``.
    To avoid this first check the start and end date before proceeding as follows.

.. code-block:: python

          dt = maize_model.inspect_model_parameters(model_type='Clock', model_name='Clock', simulations='Simulation')
          start, end = dt['Start'].year, dt['End'].year
          # out put:  1990, 2000

Using local weather data
^^^^^^^^^^^^^^^^^^^^^^^^

Got weather data stored on your computer? No problem! With `apsimNGpy`, you can easily swap in your own weather file
using the ``replace_met_file`` method. Here's how you can do it. In the same way as ``get_weather_from_web``,

.. Hint::
  If no simulation  is specified, all available simulations will get the suggested weather file

.. code-block:: python

     maize_model.replace_met_file(weather_file = './pathtotheeatherfile')
