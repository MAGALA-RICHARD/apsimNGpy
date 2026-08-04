import shutil
from pathlib import Path
import numpy as np
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR

Models = CLR.Models
from apsimNGpy.core.sim_tools import get_root_model, create_factor_table

NAME = "ExperimentFromFile"


def _create_experiment_from_file(model, experiment_from_file, name_column, sheet=None, base_simulation=0,
                                 experiment_name=NAME):
    """
    Create an APSIM experiment from an existing factor spreadsheet.

    This is a private helper used internally by
    `create_experiment_from_file`. Refer to the public function for
    complete documentation and usage examples.

    Parameters
    ----------
    model : str, pathlib.Path, or ApsimModel
        APSIM model path or an existing ``ApsimModel`` instance.

    experiment_from_file : str or pathlib.Path
        Path to the CSV or Excel file containing the factorial treatments.

    name_column : str
        Name of the column used to identify each generated simulation.

    sheet : str, optional
        Name of the Excel worksheet. Ignored when the factor file is a CSV.

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
    """
    obj = get_root_model(model, simulation_name=base_simulation)
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
    if Path(experiment_from_file).suffix != '.csv':
        if sheet is None:
            raise ValueError(f"Expected sheet name to be specified got {sheet} instead")
        FactorialFactorFromFile.Sheet = sheet
    FactorialFactorFromFile.FileName = str(Path(experiment_from_file).resolve())
    factor_holder_node.Children.Add(FactorialFactorFromFile)

    return root


def test_factor_from_file(*, rue, population):
    case1, case2 = tuple(rue), tuple(population)
    """
       Vary any factor and keep other constant to test
       @return:
       """
    vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [*case1],
            '[Sow using a variable rule].Script.Population': [*case2]}
    X = create_factor_table(**vaRs, name_column="FactorFromFile")

    X.to_csv('data.csv')
    experiment = _create_experiment_from_file('Maize', experiment_from_file='data.csv', name_column='FactorFromFile')
    experiment.run()
    res = experiment.results
    final = res.merge(X, how='inner', on='FactorFromFile')
    mn = final.groupby('FactorFromFile')['Yield'].mean()
    assert len(mn) == len(X['FactorFromFile'].unique())

    assert not np.equal(*mn), f"Values {mn}  match"

    with experiment:
        pass


if __name__ == '__main__':

    test_factor_from_file(rue=(1, 2), population=(5, 5))

    test_factor_from_file(rue=(2, 2), population=(3, 6))


    def clean(*args):
        import shutil
        for suffix in args:
            from pathlib import Path
            from contextlib import suppress
            p = Path(r'D:\package\apsimNGpy2\apsimNGpy')
            for i in p.rglob(f'*{suffix}'):
                if i.suffix == suffix:
                    with suppress(PermissionError, FileNotFoundError):
                        if i.is_dir():
                            shutil.rmtree(i)
                        else:
                            i.unlink()
                        print('removed {}'.format(i))
    clean('.db', '.apsimx', 'db-wal', '.met', '.scratch', '.csv')