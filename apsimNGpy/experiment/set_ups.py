"""This script is used to provide a simple design of experiments and to facilitate parameter replacement. The earlier
script we realized was complicated for no good reason"""
import os
from dataclasses import dataclass
from pathlib import Path
from collections import namedtuple
import numpy as np
import pandas as pd
from apsimNGpy.experiment.permutations import create_permutations
from apsimNGpy.utililies.database_utils import get_db_table_names, read_db_table

NamedFactors = namedtuple('NamedFactors', [
    'managers',
    'factors',
    'parameters',
    'nodes'])


@dataclass
class Factors:
    factor: [list, tuple, np.ndarray]
    manager: str
    parameters: str
    target_node: str


def organize_factors(factors: list):
    return NamedFactors(factors=[i.factor for i in factors],
                        managers=[i.manager for i in factors],
                        nodes=[i.target_node for i in factors],
                        parameters=[i.parameters for i in factors])


class DesignExperiment:
    def __init__(self, *, factors: list, datastorage: str, evaluate_completed=False,
                 simulation_id: str = "SID"):
        self.factors = factors
        self.datastorage = datastorage
        self.evaluate_completed = evaluate_completed
        self.perms = None
        self.children = None
        self.simulation_id = simulation_id
        self.clear = None

    def evaluate_simulated(self, perms):
        if self.evaluate_completed:
            if os.path.isfile(self.datastorage) and bool(get_db_table_names(self.datastorage)):
                print(f'Total simulations: {len(self.perms)}')

                cur_data = pd.concat([read_db_table(self.datastorage, report_name=t) for t in
                                      get_db_table_names(self.datastorage)],
                                     ignore_index=True)
                already_simulated = set(cur_data[self.simulation_id])

                return {idx: perms[idx] for idx, perm in enumerate(perms) if idx not in already_simulated}
        else:
            return perms

    def design_experiment(self):

        og = organize_factors(self.factors)
        self.perms = create_permutations(factors=og.factors, factor_names=og.parameters)
        self.children = og.nodes
        scrip = og.parameters
        mgt_names = og.managers

        print(len(self.perms))
        initD = dict(zip(mgt_names, scrip))
        split = [{k: v, "Name": k} for k, v in initD.items()]
        self.perms = self.evaluate_simulated(self.perms)
        for perm in self.perms:
            ID, items = perm, self.perms[perm]

            # Create a tuple of dictionaries where each dictionary maps 'Name' to the corresponding value from initD
            # data_tuple = tuple(
            #     [{'Name': k, v: items[v]} for k, v in initD.items()]
            # )
            ap = []
            for nm, j in zip(mgt_names, scrip):
                dt = {'Name': nm, j: items[j]}
                ap.append(dt)
            # Yield the result as a tuple of index and data_tuple
            yield ID, tuple(ap)


if __name__ == '__main__':
    a = [1, 3]
    b = ('2', 4)
    a1 = Factors(parameters='amount', factor=a, target_node='manager', manager='Simple Rotation')
    b1 = Factors(parameters='b', factor=b, target_node='clock', manager='None')
    mgd = DesignExperiment(factors=[a1, b1], datastorage='sb.db', )
