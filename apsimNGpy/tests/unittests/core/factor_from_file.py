import shutil

import numpy as np

from apsimNGpy import logger
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR
from apsimNGpy.core.experiment import create_experiment_from_file

Models = CLR.Models
from apsimNGpy.core.sim_tools import get_base_simulation

NAME = "ExperimentFromFile"


def _filter_out_simulation(model: ApsimModel):
    children = list(model.Simulations.GetChildren())
    for Child in children:
        typ = Child.GetType()
        if typ not in (CLR.Models.Storage.DataStore().GetType(), CLR.Models.Core.Folder().GetType()):
            model.Simulations.RemoveChild(Child)


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
    experiment = create_experiment_from_file('Maize', factor_file_name='data.csv', name_column='FactorFromFile')
    experiment.run()
    res = experiment.results
    final = res.merge(df, how='inner', on='FactorFromFile')
    mn = final.groupby('FactorFromFile')['Yield'].mean()
    assert len(mn) == len(X['FactorFromFile'].unique())

    assert not np.equal(*mn), f"Values {mn}  match"
    logger.info(f"Arguments: RUE; {rue} and population; {population} ok")

    with experiment:
        pass


if __name__ == '__main__':
    csv = r"C:\Users\rmagala\Downloads\ExperimentFromCSV-FactorialTrials.csv"
    vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [2, 2], '[Sow on a fixed date].Script.Population': [8, 8]}
    df = csv_generator(**vaRs, name_column="ID")
    df.to_csv('data.csv')
    m = ApsimModel('Maize')
    out = create_experiment_from_file(m, factor_file_name='data.csv', name_column='Scenario', base_simulation=0)

    test_factor_from_file(rue=(1, 2), population=(5, 5))

    test_factor_from_file(rue=(2, 2), population=(3, 6))
