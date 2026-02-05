Application of Multiprocessing
==============================

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact


In this tutorial, we demonstrate how multiprocessing can be used to run custom
experimental simulations that are difficult to implement using the
``ExperimentManager`` API alone.

Problem Description
-------------------

We consider two crop rotation systems:

- Maize → Wheat → Soybean
- Maize → Wheat

Our objective is to evaluate **specific planting date combinations**, where
**wheat is planted before soybean**. For example, wheat may be terminated on
**26th April**, followed by soybean planting on **1st May**.

Simulation Design
-----------------

The experiment evaluates multiple planting-date scenarios:

- Soybean planting dates are spaced **every 5 days**
- A total of **11 soybean planting dates** are considered
- For each soybean planting date, the corresponding wheat termination date is
  adjusted accordingly
- Each planting-date combination is simulated for **both rotation systems**

This results in a total of:

.. math::

   2 \times 11 = 22

independent simulation runs.

Why Multiprocessing?
--------------------

Although these simulations could be executed sequentially using a simple loop,
they are **independent tasks** and therefore well suited to a multiprocessing
approach. Using multiprocessing:

- Reduces overall execution time
- Demonstrates how custom simulation workflows can be scaled
- Provides flexibility beyond what is easily achievable with the
  ``ExperimentManager`` API

In this tutorial, multiprocessing is used primarily **for demonstration
purposes**, showing how multiple simulation jobs can be dispatched and executed
concurrently.

Import the necessary libraries

.. code-block:: python

    import os
    from pathlib import Path
    from loguru import logger
    from apsimNGpy.core.config import set_apsim_bin_path
    from dotenv import load_dotenv

Set up the workspace

.. code-block:: python

    Base_DIR = Path(__file__).parent
    plots = Base_DIR / 'Plots'
    plots.mkdir(exist_ok=True)
    out_apsimx = Base_DIR / 'output'
    out_apsimx.mkdir(exist_ok=True)

Create arrays for planting and termination dates

.. code-block:: python

   soybean_PD = [
    "01-may",
    "06-may",
    "11-may",
    "16-may",
    "21-may",
    "26-may",
    "31-may",
    "05-jun",
    "10-jun",
    "15-jun",
    "29-jun",]

    wheat_termination_date = [
        "26-apr",
        "01-may",
        "06-may",
        "11-may",
        "16-may",
        "21-may",
        "26-may",
        "31-may",
        "05-jun",
        "10-jun",
        "24-jun",
    ]

Zip them up for iteration since are correlated

.. code-block:: python

   td_plt = dict(zip(soybean_PD, wheat_termination_date))

.. code-block:: python

  def create_jobs(base_file):
    index =0
    for crop in ['Maize, Wheat', 'Maize, Wheat, Soybean']:

        for idx, (soy_planting, rye_termination) in enumerate(td_plt.items()):
            index += 1
            jj = {
                "model": base_file,
                "ID": index,
                "inputs": [
                    {
                        "path": ".Simulations.P3051.Field1.SowSoy",
                        "StartDate": soy_planting,
                    },
                    {
                        "path": ".Simulations.P3051.Field1.HarvestWheat",
                        "Date": rye_termination,
                    },
                    {
                        'path': '.Simulations.P3051.Field1.Simple Rotation',
                        'Crops': crop
                    }
                ],
            }
            yield jj

.. tip::

    The function above returns an iterator that yields jobs one at a time, with each job consumed immediately during execution.
    This design ensures that jobs are not stored in memory, keeping the memory footprint of simulations low and preventing system overload.
    These principles are central to apsimNGpy’s architecture, which is explicitly designed to manage large simulation campaigns efficiently on local machines.
    As a result, even the MultiCoreAPI runs smoothly in the background under high simulation counts; in practice, users can execute on the order of one million simulations on a local device, provided sufficient time is allowed for completion.

.. code-block:: python

    base_file = Base_DIR / 'APSIMX' / 'cc_cover.apsimx'

The base file has been configured with a rotation manager.
If you require this simple rotation manager, please raise an issue on GitHub and we will be happy to share it.

.. code-block:: python

    if __name__ == '__main__':
        # Assumes that the APSIM binary path has been set
        from apsimNGpy.core.mult_cores import MultiCoreManager
        edited_model_path= Base_DIR / 'APSIMX'/'cc_cover_edited.apsimx'
        jobs = create_jobs(edited_model_path)
        manager = MultiCoreManager()
        subset_columns = ['AGB', 'SoyYield']
        manager.run_all_jobs(jobs, ncore=-10, subset_columns=subset_columns)
        df = manager.results
        base_path = Base_DIR / 'Results'
        for tables in df.source_table.unique():
            tb_df = df[df.source_table == tables]
            tb_df.to_csv(base_path/f'{tables}.csv', index=False)
        df.to_csv(Base_DIR / 'Results/simulated.csv', index=False)
        wheat_r= df[df['source_table']=='WheatR']
