import shutil

import numpy as np

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR

Models = CLR.Models
from apsimNGpy.core.sim_tools import get_base_simulation

NAME = "ExperimentFromFile"


def _filter_out_simulation(model: ApsimModel):
    children = list(model.Simulations.GetChildren())
    for Child in children:
        typ = Child.GetType()
        if typ not in (CLR.Models.Storage.DataStore().GetType(), CLR.Models.Core.Folder().GetType()):
            model.Simulations.RemoveChild(Child)


from pathlib import Path


def _get_root(base, simulation_name):
    match base:
        case str() | Path():
            model = ApsimModel(base)
            sim = get_base_simulation(model, simulation_name)
            _filter_out_simulation(model)
            model.save()
            return dict(root=model, simulation=sim)

        case ApsimModel():
            sim = get_base_simulation(base, simulation_name)
            _filter_out_simulation(base)
            base.save()
            return dict(root=base, simulation=sim)

        case _:
            raise TypeError(
                f"Expected a str, Path, or ApsimModel, "
                f"got {type(base).__name__}"
            )


def _create_experiment_from_file(model, factor_file_name, name_column, sheet=None, base_simulation=0, experiment_name=NAME):
    obj = _get_root(model, simulation_name=base_simulation)
    root, base_sim = obj["root"], obj["simulation"]
    exp = Models.Factorial.Experiment()
    exp.Name = experiment_name
    factor_holder_node = Models.Factorial.Factors()
    exp.Children.Add(factor_holder_node)
    exp.Children.Add(base_sim)
    root.Simulations.Children.Add(exp)
    try:
        FactorialFactorFromFile = Models.Factorial.FactorFromFile()
    except AttributeError as error:
        raise RuntimeError(
            "This APSIM Next Generation version does not support "
            "'Models.Factorial.FactorFromFile'. Upgrade to APSIM 2026.7 "
            "or a newer version."
        ) from error
    FactorialFactorFromFile.set_NameColumn(name_column)
    if Path(factor_file_name).suffix != '.csv':
        if sheet is None:
            raise ValueError(f"Expected sheet name to be specified got {sheet} instead")
        FactorialFactorFromFile.Sheet = sheet
    dst = Path('factor.csv').resolve()
    shutil.copy(factor_file_name, dst=dst)
    FactorialFactorFromFile.FileName = str(dst)
    factor_holder_node.Children.Add(FactorialFactorFromFile)

    return root


class _ExperimentFromFile(ApsimModel):
    def __init__(
            self,
            model, *,
            factor_file_name,
            name_column,
            experiment_name="ExperimentFromFile",
            base_simulation=0,
            **kwargs, ):
        super().__init__(model, **kwargs)

        self.factor_file_name = Path(factor_file_name).resolve()
        self.experiment_name = experiment_name
        self.name_column = name_column
        self.base_simulation = base_simulation

        if not self.factor_file_name.exists():
            raise FileNotFoundError(
                f"Factor file does not exist: {self.factor_file_name}"
            )
        _create_experiment_from_file(self, factor_file_name=factor_file_name, name_column=name_column,
                                     base_simulation=self.base_simulation, experiment_name=self.experiment_name)


def csv_generator(**kwargs, ):
    """parameter_path: and values"""
    from pandas import DataFrame
    df = DataFrame(kwargs)
    df['FactorFromFile'] = [str(i) for i in range(1, df.shape[0] + 1)]
    return df


def test_factor_from_file(*, rue, population):
    case1, case2 = tuple(rue), tuple(population)
    """
       Vary all population and keep radiation use efficiency
       @return:
       """
    vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [*case1],
            '[Sow using a variable rule].Script.Population': [*case2]}
    X = csv_generator(**vaRs, name_column="ID")

    X.to_csv('data.csv')
    experiment = _create_experiment_from_file('Maize', factor_file_name='data.csv', name_column='FactorFromFile')
    experiment.run()
    res = experiment.results
    final = res.merge(X, how='inner', on='FactorFromFile')
    mn = final.groupby('FactorFromFile')['Yield'].mean()
    assert len(mn) == len(X['FactorFromFile'].unique())

    assert not np.equal(*mn), f"Values {mn}  match"

    with experiment:
        pass


if __name__ == '__main__':
    # csv = r"C:\Users\rmagala\Downloads\ExperimentFromCSV-FactorialTrials.csv"
    # vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [2, 2], '[Sow on a fixed date].Script.Population': [8, 8]}
    # df = csv_generator(**vaRs, name_column="ID")
    # df.to_csv('data.csv')
    # m = ApsimModel('Maize')
    # out = create_experiment_from_file(m, factor_file_name='data.csv', name_column='Scenario', base_simulation=0)

    test_factor_from_file(rue=(1, 2), population=(5, 5))

    test_factor_from_file(rue=(2, 2), population=(3, 6))
