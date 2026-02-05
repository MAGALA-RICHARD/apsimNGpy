import re
from pathlib import Path

from apsimNGpy.core.apsim import ApsimModel
from collections import OrderedDict

from apsimNGpy.core.model_tools import ModelTools, Models

from starter.cs_resources import CastHelper
from starter.pythonet_config import is_file_format_modified
from apsimNGpy.core.model_loader import get_node_by_path, AUTO_PATH

from apsimNGpy.core.runner import invoke_csharp_gc, run_model_externally

if is_file_format_modified():
    import APSIM.Core as NodeUtils
    import System

#    structure = Models.Core.ApsimFile.Structure
else:
    from apsimNGpy.core.config import apsim_version

    raise ValueError(f"The experiment module is not supported for this type of {apsim_version()} ")

from typing import Union
from apsimNGpy.core.version_inspector import is_higher_apsim_version

class ExperimentManager(ApsimModel):
    """
    This class inherits methods and attributes from: :class:`~apsimNGpy.core.apsim.ApsimModel` to manage APSIM Experiments
    with pure factors or permutations. You first need to initiate the instance of this class and then initialize the
    experiment itself with: :meth:`init_experiment`, which creates a new experiment from the suggested base simulation and ``permutation`` type

    The flow of method for :class:`ExperimentManager` class is shown in the diagram below:

    .. code-block:: none

      PlotManager ---> CoreModel ---> ApsimModel ---> ExperimentManager

    Class Roles
    ---------------
    - :class:`~apsimNGpy.core.plotmanager.PlotManager` → Produces visual outputs from model results (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.core.CoreModel`  → contains methods for running and manipulating models (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.apsim.ApsimModel` → Extends :class:`~apsimNGpy.core.core.Coremodel` capabilities with more functionalities
    - :class:`~apsimNGpy.core.experimentmanager.ExperimentManager` → Manages and creates a new experiment from the suggested base.

    """

    def __init__(self, model, out_path=AUTO_PATH):
        super().__init__(model=model, out_path=out_path)
        self.parent_factor = None
        self.experiment_node = None
        self.factorial_node = None
        self.permutation_node = None
        self.factors = OrderedDict()
        self.specs = OrderedDict()
        self.counter = 0
        self.sims = self.simulations
        self.init = False
        self.is_simulations_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        try:

            invoke_csharp_gc()

            self.clean_up(db=True)
            self.is_simulations_closed =True
        except PermissionError:
            print(self.model_info.datastore)
    # put here during debugging context db file manager, but sure will be removed after full tests
    def _run(self, report_name: Union[tuple, list, str] = None,
            simulations: Union[tuple, list] = None,
            clean_up: bool = True,
            verbose: bool = False,
            timeout: int = 800,
            **kwargs) -> 'CoreModel':
        """
        Run APSIM model simulations to write the results either to SQLite database or csv file. Does not collect the
         simulated output into memory. Please see related APIs: :attr:`results` and :meth:`get_simulated_output`.

        Parameters
        ----------
        report_name: Union[tuple, list, str], optional
            Defaults to APSIM default Report Name if not specified.
            - If iterable, all report tables are read and aggregated into one DataFrame.

        simulations: Union[tuple, list], optional
            List of simulation names to run. If None, runs all simulations.

        clean_up: bool, optional
            If True, removes the existing database before running.

        verbose: bool, optional
            If True, enables verbose output for debugging. The method continues with debugging info anyway if the run was unsuccessful

        timeout: int, defualt is 800 seconds
              Enforces a timeout and returns a CompletedProcess-like object.

        kwargs: **dict
            Additional keyword arguments, e.g., to_csv=True, use this flag to correct results from
            a csv file directly stored at the location of the running apsimx file.

        Warning:
        --------------
        In my experience with Models.exe, CSV outputs are not always overwritten; after edits, stale results can persist. Proceed with caution.


        Returns
        -------
            Instance of the respective model class e.g.,  ApsimModel, ExperimentManager.
       ``RuntimeError``
            Raised if the ``APSIM`` run is unsuccessful. Common causes include ``missing meteorological files``,
            mismatched simulation ``start`` dates with ``weather`` data, or other ``configuration issues``.

       Example:

       Instantiate an ``apsimNGpy.core.apsim.ApsimModel`` object and run::

              from apsimNGpy.core.apsim import ApsimModel
              model = ApsimModel(model= 'Maize')# replace with your path to the apsim template model
              model.run(report_name = "Report")
              # check if the run was successful
              model.ran_ok
              'True'

       .. note::

          Updates the ``ran_ok`` flag to ``True`` if no error was encountered.

       .. seealso::

           Related APIs: :attr:`results` and :meth:`get_simulated_output`.
             """
        try:
            from System import InvalidOperationException
            self.save()
            if clean_up:
                try:
                    _path = Path(self.path)
                    # delete or clear all tables
                    try:
                        self._DataStore.Dispose()
                        self.Datastore.Dispose()
                    except (AttributeError, InvalidOperationException):
                        pass
                        # delete_all_tables(str(db))
                except PermissionError:
                    pass

            # Run APSIM externally
            res = run_model_externally(
                # we run using the copied file

                self.path,
                verbose=verbose,
                to_csv=kwargs.get('to_csv', False),
                timeout=timeout
            )

            if res.returncode == 0:
                self.ran_ok = True
                self.report_names = report_name
                self.run_method = run_model_externally

            # If the model failed and verbose was off, rerun to diagnose
            if not self.ran_ok and not verbose:
                print('run time errors occurred')

            return self

        finally:
            ...

    def init_experiment(self, permutation: bool = True, base_simulation: str = None):

        """
            Initializes the factorial experiment structure inside the APSIM file.

            Parameters
            _____________
            permutation: (bool)
              If True, enables permutation mode; otherwise, uses standard factor crossing.
            base_simulation: (str)
               The base simulation name to use for the experiment. If None, the base simulation is selected
               from the available simulations

            Side Effects:
            ____________
                - Replaces any existing ExperimentManager node with a new configuration.
                - Clones the base simulation and adds it under the experiment.
                - Never mind, though all this edits are made on a cloned model.
                - In the presence of replacements, they are moved or retained directly at the simulations node


            Examples::

               from apsimNGpy.core.experimentmanager import ExperimentManager
               # initialize the model
               experiment = ExperimentManager('Maize', out_path = 'my_experiment.apsimx')
               # initialize experiment without permutation crossing of the factors
               experiment.init_experiment(permutation=False)
               # initialize experiment with permutation =True
               experiment.init_experiment(permutation=True)
               # initialize experiment with a preferred base simulation name
               experiment.init_experiment(permutation=False, base_simulation='Simulation')
               # view the simulation tree
               experiment.inspect_file()

            The method :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_file` is inherited from the
            :class:`~apsimNGpy.core.apsim.ApsimModel` class , but it is still useful here, for example, you can see
            that we added an experiment Model under Simulations as shown below.

            .. code-block:: None

               └── Simulations: .Simulations
                ├── DataStore: .Simulations.DataStore
                └── Experiment: .Simulations.Experiment
                    ├── Factors: .Simulations.Experiment.Factors
                    └── Simulation: .Simulations.Experiment.Simulation
                        ├── Clock: .Simulations.Experiment.Simulation.Clock
                        ├── Field: .Simulations.Experiment.Simulation.Field
                        │   ├── Fertilise at sowing: .Simulations.Experiment.Simulation.Field.Fertilise at sowing
                        │   ├── Fertiliser: .Simulations.Experiment.Simulation.Field.Fertiliser
                        │   ├── Harvest: .Simulations.Experiment.Simulation.Field.Harvest
                        │   ├── Maize: .Simulations.Experiment.Simulation.Field.Maize
                        │   ├── Report: .Simulations.Experiment.Simulation.Field.Report
                        │   ├── Soil: .Simulations.Experiment.Simulation.Field.Soil
                        │   │   ├── Chemical: .Simulations.Experiment.Simulation.Field.Soil.Chemical
                        │   │   ├── NH4: .Simulations.Experiment.Simulation.Field.Soil.NH4
                        │   │   ├── NO3: .Simulations.Experiment.Simulation.Field.Soil.NO3
                        │   │   ├── Organic: .Simulations.Experiment.Simulation.Field.Soil.Organic
                        │   │   ├── Physical: .Simulations.Experiment.Simulation.Field.Soil.Physical
                        │   │   │   └── MaizeSoil: .Simulations.Experiment.Simulation.Field.Soil.Physical.MaizeSoil
                        │   │   ├── Urea: .Simulations.Experiment.Simulation.Field.Soil.Urea
                        │   │   └── Water: .Simulations.Experiment.Simulation.Field.Soil.Water
                        │   ├── Sow using a variable rule: .Simulations.Experiment.Simulation.Field.Sow using a variable rule
                        │   └── SurfaceOrganicMatter: .Simulations.Experiment.Simulation.Field.SurfaceOrganicMatter
                        ├── Graph: .Simulations.Experiment.Simulation.Graph
                        │   └── Series: .Simulations.Experiment.Simulation.Graph.Series
                        ├── MicroClimate: .Simulations.Experiment.Simulation.MicroClimate
                        ├── SoilArbitrator: .Simulations.Experiment.Simulation.SoilArbitrator
                        ├── Summary: .Simulations.Experiment.Simulation.Summary
                        └── Weather: .Simulations.Experiment.Simulation.Weather

            .. seealso::

               :meth:`add_factor`


            """
        self.permutation = permutation

        def _get_base_sim():
            if base_simulation:
                for _sim in self.simulations:
                    if _sim.Name == base_simulation:
                        sim = _sim
                        break
                else:
                    raise ValueError(f"No base simulation found for this name {base_simulation}")
            else:
                sim = self.simulations[0]
            return sim

        def exp_refresher(mode):
            sim = _get_base_sim()
            print(sim.__dir__())
            print(sim.Children)
            if not sim:
                raise ValueError(f"No base simulation found")
            new_sim =Models.Core.Simulation()
            new_sim.Name = sim.Name
            new_sim.Children = sim.Children
            base = new_sim
            for simx in mode.simulations:  # it does not matter how many experiments exist; we need only one
                ModelTools.DELETE(simx)
            # replace before delete

            try:
                mode.simulations[0] = base
                base = mode.simulations[0]
            except IndexError:
                pass
            experiment = Models.Factorial.Experiment()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            self.factorial_node = factor
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            experiment.AddChild(base)
            experi = ModelTools.find_child_of_class(mode.Simulations, Models.Factorial.Experiment)

            if experi:
                ModelTools.DELETE(experi)
            mode.model_info.Node.AddChild(experiment)
            sim_final = CastHelper.CastAs[Models.Core.Simulations](mode.model_info.Node)

            if is_higher_apsim_version(self.Simulations):

                simx = ModelTools.find_all_in_scope(sim_final, Models.Core.Simulation)
                simy = [ModelTools.CLONER(i) for i in simx]

                simx = [CastHelper.CastAs[Models.Core.Simulations](i.Node) for i in simy]

                ...

            else:
                simx = list(sim_final.FindAllDescendants[Models.Core.Simulation]())

                if not mode.simulations:
                    mode.simulations.extend(simx)
            # mode.save()

        def refresher():

            replace_ments = ModelTools.find_child(self.Simulations, child_class=Models.Core.Folder,
                                                  child_name='Replacements')

            siM = self.Simulations
            # if replace_ments:
            #     siM.AddChild(replace_ments)
            #create experiment
            _experiments = list(siM.Node.FindAll[Models.Factorial.Experiment]())
            if _experiments:
                raise ValueError('Not supported at the moment, provide a base simulation and build from scratch')
            # add then new experiment Node
            experiment = Models.Factorial.Experiment()
            experiment.Children.Clear()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            factor.Children.Clear()
            self.factorial_node = factor
            # branch if it is a permutation experiment
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            # add simulation before experiment to the simulation tree
            sim = _get_base_sim()
            base_full_path = sim.FullPath
            siM.Children.Add(experiment)
            sim.SetParent(experiment)
            experiment.Children.Add(sim)
            # remove base simulation
            simulation_node = get_node_by_path(siM, node_path=base_full_path)

            siM.RemoveChild(simulation_node.Model)
            # if simulation_node:
            #     ModelTools.DELETE(simulation_node.Model)
            datastore = ModelTools.find_child_of_class(siM, Models.Storage.DataStore)
            if datastore:
                datastore = CastHelper.CastAs[Models.Storage.DataStore](datastore)
            datastore.set_FileName(self.datastore)


            # siM.Write(self.path)

            self.Simulations = siM
            self.save()

        if is_higher_apsim_version(self.Simulations):

            refresher()

        else:
            exp_refresher(self)

        self.init = True
        # compile

    def add_factor(self, specification: str, factor_name: str = None, **kwargs):
        """
        Add a new factor to the experiment from an APSIM-style script specification.

        Parameters
        ----------
        specification : str
            An APSIM script-like expression that defines the parameter variation,
            e.g. ``"[Organic].Carbon[1] = 1.2, 1.8"`` or
            ``"[Sow using a variable rule].Script.Population = 6, 10"``.
        factor_name : str, optional
            A unique name for the factor. If not provided, a name is auto-generated
            from the target variable in ``specification`` (typically the last token).
        **kwargs
            Optional metadata or configuration (currently unused).

        Raises
        ------
        ValueError
            If a script-based specification references a non-existent or unlinked
            manager script.

        Side Effects
        ------------
        - Inserts the factor into the appropriate parent node (``Permutation`` or ``Factors``).
        - If a factor at the same index already exists, it is safely deleted before inserting
          the new one.

        Notes
        -----
        All methods from :class:`~apsimNGpy.core.apsim.ApsimModel` remain available on this
        class. You can still inspect, run, and visualize results.

        Examples
        --------
        Initialize an experiment:

        .. code-block:: python

           from apsimNGpy.core.experimentmanager import ExperimentManager

           # initialize the model
           experiment = ExperimentManager('Maize', out_path='my_experiment.apsimx')

           # initialize experiment with permutation crossing of factors
           experiment.init_experiment(permutation=True)

        Inspect model components:

        .. code-block:: python

           experiment.inspect_model('Models.Manager')

        .. code-block:: none

           ['.Simulations.Experiment.Simulation.Field.Sow using a variable rule',
            '.Simulations.Experiment.Simulation.Field.Fertilise at sowing',
            '.Simulations.Experiment.Simulation.Field.Harvest']

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Experiment')

        .. code-block:: none

           ['.Simulations.Experiment']

        1) Add a factor associated with a manager script
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Sow using a variable rule].Script.Population = 6, 10',
               factor_name='Population'
           )

        2) Add a factor associated with a soil node (e.g., initial soil organic carbon)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Check how many factors have been added:

        .. code-block:: python

           experiment.n_factors
           # 2

        Inspect factors:

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Factor')

        .. code-block:: none

           ['.Simulations.Experiment.Factors.Permutation.Nitrogen',
            '.Simulations.Experiment.Factors.Permutation.initial_carbon']

        Get factor names only:

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Factor', fullpath=False)

        .. code-block:: none

           ['Nitrogen', 'initial_carbon']

        Run the model and summarize results:

        .. code-block:: python

           experiment.run()
           df = experiment.results
           df.groupby(['Population', 'initial_carbon'])['Yield'].mean()

        .. code-block:: none

                       Population  initial_carbon
           10          1.2         6287.538183
                       1.8         6225.861601
           6           1.2         5636.529504
                       1.8         5608.971306
           Name: Yield, dtype: float64

        Save the experiment (same as :class:`~apsimNGpy.core.apsim.ApsimModel`):

        .. code-block:: python

           experiment.save()

        See also :meth:`~apsimNGpy.core.apsim.ApsimModel.save`.

        Common Pitfalls
        ---------------
        1) Adding the same specification with only a different ``factor_name``
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )
           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='carbon'
           )

        By default, specifications are evaluated on their arguments, so the example above
        creates two identical factors—usually not desired.

        .. code-block:: python

           experiment.save()
           experiment.inspect_model('Models.Factorial.Factor')

        .. code-block:: none

           ['.Simulations.Experiment.Factors.Permutation.initial_carbon',
            '.Simulations.Experiment.Factors.Permutation.carbon']

        2) Invalid specification path to target parameters
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Common causes include referencing models not present in the script, adding quotes
        around numeric levels, or inserting stray spaces in paths.

        Invalid (extra quotes):

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = "1.2, 1.8"',
               factor_name='initial_carbon'
           )

        Correct:

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Invalid (extra space in path):

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic]. Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Correct:

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )
        """

        if not self.init:
            raise ValueError("Please initialize the experiment first by calling: self.init_experiment method")
        # Auto-generate factor name from specification if not provided
        if factor_name is None:
            factor_name = specification.split("=")[0].strip().split(".")[-1]

        # If it's a Script-based specification, validate linkage
        if 'Script' in specification:
            matches = re.findall(r"\[(.*?)\]", specification)
            if matches:
                manager_names = set(self.inspect_model('Models.Manager', fullpath=False))
                linked = set(matches) & manager_names
                if not linked:
                    if matches:
                        matches = ', '.join(matches)
                    raise ValueError(f'Specification{specification} has no linked script `{matches}` in the model')

        # Record factor info
        self.factors[factor_name] = (specification, kwargs)

        # Choose parent node and parent class
        parent_factor = self.permutation_node if self.permutation else self.factorial_node
        parent_class = Models.Factorial.Permutation if self.permutation else Models.Factorial.Factors
        if is_higher_apsim_version(self.Simulations):
            parent_factor = ModelTools.find_child_of_class(self.Simulations, parent_class)

        new_factor = Models.Factorial.Factor()
        new_factor.Name = factor_name
        new_factor.set_Specification(specification)

        self.specs[factor_name] = new_factor

        # Maintain counter and avoid index error
        index = len(self.specs) - 1
        try:
            # Try to remove existing child at index before inserting
            if 0 <= index < len(parent_factor.Children):
                old_child = parent_factor.Children[index]
                if old_child is not None:
                    ...
                    parent_factor.Children.Remove(old_child)
                    # NodeUtils.Node.RemoveChild(old_child)
                #  ModelTools.DELETE(old_child)

        except System.ArgumentOutOfRangeException:
            pass

        # Insert a new factor
        parent_factor.Children.Add(new_factor)
        self.parent_factor = parent_factor

    @property
    def n_factors(self):
        """
            Returns:
                int: The total number of active factor specifications currently added to the experiment.
            """
        return len(self.specs)

    def finalize(self):
        """"
        Finalizes the experiment setup by re-creating the internal APSIM factor nodes from specs.

        This method is designed as a guard against unintended modifications and ensures that all
        factor definitions are fully resolved and written before saving.

        Side Effects:
            Clears existing children from the parent factor node.
            Re-creates and attaches each factor as a new node.
            Triggers model saving.
    """
        self.parent_factor.Children.Clear()
        for name, spec in self.specs.items():
            node = NodeUtils.Node.Create(spec, parent=self.parent_factor)
            self.parent_factor.Children.Add(node.Model)
        self.save()
        invoke_csharp_gc()


import gc

gc.collect()
if __name__ == '__main__':
    with ExperimentManager("Maize", out_path='dtb.apsimx') as exp:
        exp.init_experiment(permutation=True)
        exp.add_factor("[Fertilise at sowing].Script.Amount = 0 to 200 step 20")
        exp.add_factor("[Fertilise at sowing].Script.FertiliserType= DAP,NO3N")
        exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
                       factor_name='Population')

        exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
                       factor_name='Population')
        exp.preview_simulation()
        exp.run()
        # exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
        #                factor_name='Population')
        # exp.finalize()

    print('datastore Path exists after exit:', Path(exp.datastore).exists())


