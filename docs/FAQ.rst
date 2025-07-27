.. _faq:

Frequently Asked Questions (FAQ) – apsimNGpy
=============================================

1. What is ``apsimNGpy``?
--------------------------
``apsimNGpy`` is a Python package that provides a programmatic interface to the APSIM Next Generation (APSIM-X) platform. It allows users to automate simulations, manipulate model components, edit parameters, and analyze outputs within a Python workflow.

2. What can I do with ``apsimNGpy``?
-------------------------------------
With ``apsimNGpy``, you can:

- Programmatically load, edit, and run ``.apsimx`` simulations.
- Batch process simulations with varying inputs.
- Extract and analyze simulation outputs.
- Calibrate and validate APSIM models using Python tools.
- Build scalable and reproducible agroecosystem modeling workflows.

3. Is ``apsimNGpy`` compatible with all APSIM Next Generation versions?
------------------------------------------------------------------------
Yes. ``apsimNGpy`` is designed to be compatible with APSIM Next Generation (APSIM-X), and it interacts with the APSIM binaries through the .NET Common Language Runtime (CLR) using ``pythonnet``. Make sure your installed version of APSIM-X matches your simulation needs.

4. What are the prerequisites for using ``apsimNGpy``?
-------------------------------------------------------
To use ``apsimNGpy``, you'll need:

- Python 3.10+
- .NET Core/Framework compatible with your APSIM-X installation
- APSIM Next Generation installed
- ``pythonnet`` package (automatically installed)
- Other dependencies include ``pandas``, ``numpy``, ``tenacity``, ``scipy``, etc.

5. How do I install ``apsimNGpy``?
-----------------------------------
Install directly from PyPI:

.. code-block:: bash

    pip install apsimNGpy

Alternatively, clone from the GitHub repository:

.. code-block:: bash

    git clone https://github.com/your-org/apsimNGpy.git
    cd apsimNGpy
    pip install -e .

6. Can I run APSIM simulations in parallel?
-------------------------------------------
Yes. ``apsimNGpy`` supports parallel execution of simulations using Python’s ``multiprocessing`` or other parallel task managers. Ensure that simultaneous access to APSIM executables does not lead to file conflicts.

7. How do I edit parameters in an APSIM model using ``apsimNGpy``?
-------------------------------------------------------------------
You can use the ``edit_model()`` method to modify components in the model tree:

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    sim = ApsimModel("path/to/model.apsimx")
    sim.edit_model(model_type='Clock', model_name='Clock', Start="1990-04-15")

8. Does ``apsimNGpy`` support calibration and optimization?
------------------------------------------------------------
Yes. You can integrate ``apsimNGpy`` with Python packages like ``scipy``, ``DEAP``, or ``optuna`` to perform model calibration and optimization.

9. How do I extract simulation outputs?
---------------------------------------
Simulation outputs can be read using:

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    sim = ApsimModel("path/to/model.apsimx")
    sim.run()
    outputs = sim.get_simulatated_output(report_name="Report")

This returns a ``pandas.DataFrame`` containing the simulation results.

10. Can I contribute to ``apsimNGpy``?
---------------------------------------
Yes! We welcome contributions. You can fork the repository, submit issues or feature requests, and open pull requests on GitHub. Please ensure your changes are tested and documented.

11. Who maintains ``apsimNGpy``?
---------------------------------
``apsimNGpy`` is developed and maintained by researchers and developers working on crop modeling, with contributions from the APSIM user community. Check the GitHub repository for maintainers and collaborators.

12. Where can I get help?
--------------------------
- Official documentation: https://magala-richard.github.io/apsimNGpy-documentations/index.html
- GitHub issues page: https://github.com/MAGALA-RICHARD/apsimNGpy/issues
- Community forums and APSIM support groups
- Microsoft Teams community: https://teams.live.com/l/community/FAAbNOQj7y9dPcoaAM
- Email: rmagala640@gmail.com
