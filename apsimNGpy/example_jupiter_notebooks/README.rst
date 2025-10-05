===============================
Example Jupyter Notebooks (apsimNGpy)
===============================

This folder contains small, self-contained notebooks and helper files for
working with **APSIM Next Gen** via **apsimNGpy**. Use these examples to
instantiate models, run simulations, visualize outputs, and demonstrate
method chaining.

.. contents::
   :local:
   :depth: 2

Quick start
-----------

1. Create/activate an environment and install dependencies::

     python -m venv .venv
     .venv\Scripts\activate
     pip install apsimNGpy jupyter pandas matplotlib seaborn

2. Launch Jupyter::

     jupyter lab
     # or
     jupyter notebook

3. Open one of the notebooks listed below (e.g., ``instantiate_model.ipynb``).

Directory contents
------------------

- **scratch/**
  Working directory used by examples. Temporary files may be created here
  when you do not specify an absolute ``out_path`` for APSIM models.

- **configs.ini**
  Optional configuration used by notebooks/scripts (e.g., paths, defaults).

- **data_plotting_and_visualization.ipynb**
  Walkthrough for plotting simulation outputs (time series, comparisons,
  derived indicators).

- **instantiate_model.ipynb**
  Minimal example showing how to load a built-in APSIM template
  (e.g., ``Maize``), set weather/report nodes, and run a simulation.

- **method_chain.ipynb**
  Fluent API example: instantiate → configure → run → collect results in a
  single chain.

- **maize.apsimx**
  will be produced if you run the `instantiate_model.ipynb` note book.

- **maize.apsimx.bak**
  will be produced if you run the `instantiate_model.ipynb` note book.

- **maize.db**, **maize.db-shm**, **maize.db-wal**
  APSIM ``DataStore`` (SQLite) and its journaling files. The ``*.db-shm`` and
  ``*.db-wal`` files are transient; they disappear when the database is closed
  cleanly. Do not delete them while APSIM/Jupyter is writing. Will be produced if you run the `instantiate_model.ipynb` note book.

- **repair.py**
  Utility for fixing general notebook or file issues.

- **repair_notebooks.py**
  Repairs invalid notebooks (e.g., adds missing ``execution_count`` / ``outputs``) imports repair.py. repair.py takes in sys.args, therefore, can be executed on the command line

Hints & conventions
-------------------

- **Template vs. local file**:
  ``ApsimModel("Maize")`` loads a built-in template (no ``.apsimx`` suffix).
  ``ApsimModel("path/to/file.apsimx")`` loads your local file (suffix present).

- **Paths**:
  If ``out_path`` is **omitted or relative**, a scratch/working location is used.
  If ``out_path`` is an **absolute path**, the model is saved exactly there.

- **Method chaining** (concise and readable)::

     from apsimNGpy.core.apsim import ApsimModel
     df = (
         ApsimModel("Maize", out_path="maize.apsimx")
           .get_weather_from_file("data/ames_2020.met")
           .ensure_report(variables=["[Clock].Today as Date", "[Maize].LAI"], events=["Daily"])
           .run()
     )

  Drawbacks: order sensitivity, less transparent intermediate state, and
  sometimes harder debugging. Break the chain at checkpoints if needed.

Troubleshooting
---------------

**Invalid Notebook: 'execution_count' is a required property**

Some tools strip required fields from code cells. Fix with the provided helper::

  python repair.py path/to/notebook.ipynb out_new_path.ipynb

(Internally this ensures each code cell has ``execution_count: null`` and
``outputs: []`` at minimum.)

Reproducibility
---------------

- Record versions of APSIM NG, apsimNGpy, and Python in your notebooks.
- Consider pinning versions in ``requirements.txt`` or your environment file.
- Keep ``*.apsimx`` and key scripts under version control; ignore transient
  ``*.db-shm``/``*.db-wal`` and large outputs.

See also
--------

- `apsimNGpy documentation <https://magala-richard.github.io/apsimNGpy-documentations/index.html>`_
- `apsimNGpy API reference <https://magala-richard.github.io/apsimNGpy-documentations/api.html>`_
