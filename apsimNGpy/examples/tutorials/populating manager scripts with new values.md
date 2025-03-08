
# Tutorial: Modifying Manager Scripts in APSIM using the default Maize Simulations

This tutorial demonstrates how to load and modify manager scripts in APSIM simulations using the apsimNGpy library, specifically for maize crop simulations. We'll dynamically manage simulation properties by updating certain parameters using Python.

## Step 1: Import Required Modules

First, import the necessary classes from the apsimNGpy package, which include the `ApsimModel` for modeling, utility functions for loading simulations, a `logger` for debugging, and an `Inspector` for script examination.

```python
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.core.inspector import Inspector
```

## Step 2: Initialize the Model

Define the crop type and load its default simulations. We specify 'Maize' as the crop of interest.

```python
CROP = 'Maize'
model = load_default_simulations(crop=CROP)
```

## Step 3: Inspect Manager Scripts

Retrieve and display the paths to the manager scripts within the simulation. Knowing the correct paths is crucial for accessing and modifying the scripts in subsequent steps.

```python
scripts = model.get_manager_ids(full_path=True, verbose=True)
```

### Output

The output is a list of manager script paths:

```plaintext
['.Simulations.Simulation.Field.Sow using a variable rule', '.Simulations.Simulation.Field.Fertilize at sowing', '.Simulations.Simulation.Field.Harvest']
```

The `verbose=True` setting automatically prints the paths, helping us verify the correct script names and their full paths.

## Step 4: Inspect Script Parameters

Next, inspect the parameters of a specific manager script. Setting `verbose=True` ensures that the parameters and their current values are printed immediately, providing a clear snapshot of the script's settings.

```python
params = model.get_manager_parameters(full_path='.Simulations.Simulation.Field.Sow using a variable rule', verbose=True)
```

### Expected Output

```plaintext
{
    'Crop': 'Maize',
    'CultivarName': 'Dekalb_XL82',
    'EndDate': '10-jan',
    'MinESW': '100.0',
    'MinRain': '25.0',
    'Population': '6.0',
    'RainDays': '7',
    'RowSpacing': '750.0',
    'SowingDepth': '30.0',
    'StartDate': '1-nov'
}
```

## Step 5: Update Script Parameters

Modify specific parameters in the manager script. Choose parameters from those listed above. Here, we update `Population` and `RainDays`.

```python
model.update_mgt_by_path(path='.Simulations.Simulation.Field.Sow using a variable rule', fmt='.',
                         Population=6.75, RainDays=10)
```

## Step 6: Verify Changes

Inspect the script parameters again to confirm that the updates were successful.

```python
model.get_manager_parameters(full_path='.Simulations.Simulation.Field.Sow using a variable rule', verbose=True)
```

### Expected Output

```plaintext
{
    'Crop': 'Maize',
    'CultivarName': 'Dekalb_XL82',
    'EndDate': '10-jan',
    'MinESW': '100.0',
    'MinRain': '25.0',
    'Population': '6.75',
    'RainDays': '10',
    'RowSpacing': '750.0',
    'SowingDepth': '30.0',
    'StartDate': '1-nov'
}
```

This revised output confirms that the parameters `Population` and `RainDays` have been updated as intended.

---

This tutorial is structured to guide users step-by-step through the process of managing APSIM simulations, ensuring clear understanding and execution of modifications in simulation parameters for any simulation.