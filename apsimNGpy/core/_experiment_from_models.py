from contextlib import suppress
from pydantic import BaseModel
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR

Models = CLR.Models
from apsimNGpy.core.sim_tools import get_root_model

EXPERIMENT_NAME = "ExperimentFromModels"
from apsimNGpy.core._test_utils import test_experiment, build_test_results


class Specification(BaseModel):
    name: str
    specification: str

    @property
    def factor_model(self):
        fm = Models.Factorial.Factor()
        fm.Name = self.name
        fm.set_Specification(self.specification)
        return fm, self.specification


def _create_experiment_from_models(model, specifications: dict, base_simulation=0, permutation: bool = True,
                                   experiment_name=EXPERIMENT_NAME):
    """
    Create an APSIM experiment entirely from a Models namespace object. user need to specify the file and specification as a dict

    This is a private helper used internally by
    `create_experiment_from_models`. Refer to the public function for
    complete documentation and usage examples.

    Parameters
    ----------
    model : str, pathlib.Path, or ApsimModel
        APSIM model path or an existing ``ApsimModel`` instance.

    specifications : dict
         The keys are name of the factor and the values is the corresponding specifications of the factor.
         Example: {Amount:"[Fertilise at sowing].Script.Amount= 0, 300"}. this avoids duplicating factors

    permutation: boolean, optional, defaults to True
             if true a permutation experiment is created, which will create all possible combinations between the specified factors

    base_simulation : int or str, default=0
        Name or index of the simulation used as the template for the
        factorial experiment.

    experiment_name : str
        Name assigned to the generated APSIM experiment.

    Returns
    -------
    ApsimModel
        The root APSIM simulations object containing the newly created
        experiment
    ==========================================================
    .. code-block:: python

     experiment = create_experiment_from_models('Maize',
                                            specifications={
                                                'ftype': "[Fertilise at sowing].Script.FertiliserType= DAP,NO3N",
                                                'Amount': "[Fertilise at sowing].Script.Amount= 0, 300",
                                            }
    experiment is an ApsimModel object, so we can do anything on it as we would do an Apsimodel isntance, freaxampel run and access reuslts as show below

    .. code-block:: python

      experiment.run()
      experiment.results

    .. code-block:: none

              CheckpointID  SimulationID  ... Maize.Total.Wt source_table
        0              1             4  ...    1521.650864       Report
        1              1             4  ...     430.402356       Report
        2              1             4  ...     309.563614       Report
        3              1             4  ...     804.300040       Report
        4              1             4  ...    1474.545216       Report
        5              1             4  ...     947.306883       Report
        6              1             4  ...    1068.293190       Report
        7              1             4  ...     835.662794       Report
        8              1             4  ...    1731.379670       Report
        9              1             4  ...     511.615966       Report
        10             1             2  ...    1095.363002       Report

    """
    obj = get_root_model(model, simulation_name=base_simulation)
    root, base_sim = obj["root"], obj["simulation"]
    exp = Models.Factorial.Experiment()
    exp.Name = experiment_name
    factor_holder_node = Models.Factorial.Factors()
    exp.Children.Add(factor_holder_node)
    exp.Children.Add(base_sim)
    root.Simulations.Children.Add(exp)
    parent_node = factor_holder_node if not permutation else Models.Factorial.Permutation()
    if permutation:
        factor_holder_node.Children.Add(parent_node)

    evaluated_specifications = set()
    for name, spec in specifications.items():
        evaluated = Specification(name=name, specification=spec)
        evaluated_specifications.add(evaluated.factor_model)
    for spec in evaluated_specifications:
        parent_node.Children.Add(spec[0])

    root.save()
    return root


def _test_specification(candidates: dict, model, output, base_sim=0):
    """
               permutation is set to True to avoid unexpected behavioral tests
               """
    vaRs = dict(candidates)

    try:
        NAME_COLUMN = 'SimulationID'

        experiment = _create_experiment_from_models(model, specifications=vaRs, base_simulation=base_sim,
                                                    permutation=True)
        changed_outputs = test_experiment(experiment=experiment, outputs=output,name_column=NAME_COLUMN)
        return build_test_results(vaRs, changed_outputs, outputs=output)
    finally:
        with suppress(PermissionError):
            pass


if __name__ == '__main__':

    vals = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": (1, 3, 2.5),
            '[Sow using a variable rule].Script.Population': (1, 12, 6)}
    spe = specifications = {
        'ftype': "[Fertilise at sowing].Script.FertiliserType= DAP,DAP",
        'Amount': "[Fertilise at sowing].Script.Amount= 0, 300",
    }
    experi = _create_experiment_from_models('Maize',
                                            specifications=spe, permutation=False)
    experi.run()

    tests = _test_specification(spe, 'Maize', output=['Yield'])
    print(tests)


    def clean(*args, **kwargs):
        from pathlib import Path
        from contextlib import suppress
        p = Path(kwargs.get('wd', '.')).resolve()
        import shutil
        for suffix in args:
            for i in p.rglob(f'*{suffix}'):
                if i.suffix == suffix:
                    with suppress(PermissionError, FileNotFoundError):
                        if i.is_dir():
                            shutil.rmtree(i)
                        else:
                            i.unlink()
                        print('removed {}'.format(i))

# clean('.db', '.apsimx', 'db-wal', '.met', '.scratch', '.csv')
