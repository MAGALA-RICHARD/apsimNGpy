from pathlib import Path

import numpy as np

from apsimNGpy import logger
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.experiment import create_experiment_from_file, create_factor_table
from apsimNGpy.starter.starter import CLR

Models = CLR.Models

NAME = "ExperimentFromFile"


def all_equal(arr):
    arr = np.asarray(arr)

    if arr.size == 0:
        return True

    return np.all(arr == arr.flat[0])


def test_factor_from_file(*, rue, population):
    case1, case2 = tuple(rue), tuple(population)
    """
       Vary all population and keep radiation use efficiency
       @return:
       """
    vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [*case1],

            '[Sow using a variable rule].Script.Population': [*case2]}
    X = create_factor_table(**vaRs, )
    cpath = Path('data.csv').resolve()
    X.to_csv(cpath, index=False)
    experiment = create_experiment_from_file('Maize', experiment_from_file=cpath, name_column='FactorFromFile')
    experiment.run()
    res = experiment.results
    final = res.merge(X, how='inner', on='FactorFromFile')
    mn = final.groupby('FactorFromFile')['Yield'].mean()
    assert len(mn) == len(X['FactorFromFile'].unique())
    if not all_equal(case1) or not all_equal(case2):
        if not all_equal(mn):
            logger.info("All tests passed ok")
            logger.info(f"Arguments: RUE; {rue} and population; {population} ok")
    else:
        logger.warning(f"Not all tests might have passed as inputs  {rue, population} are the same in each entry")

    with experiment:
        pass


if __name__ == '__main__':
    # csv = r"C:\Users\rmagala\Downloads\ExperimentFromCSV-FactorialTrials.csv"
    # vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [2, 2], '[Sow on a fixed date].Script.Population': [8, 8]}
    # df = csv_generator(**vaRs, name_column="ID")
    # df.to_csv('data.csv')
    # m = ApsimModel('Maize')
    # out = create_experiment_from_file(m, factor_file_name='data.csv', name_column='Scenario', base_simulation=0)

    test_factor_from_file(rue=(1, 2), population=(5, 5), )

    test_factor_from_file(rue=(2, 2), population=(3, 6), )

    test_factor_from_file(rue=(2, 2), population=(6, 6), )
