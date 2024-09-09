"""This script is used to provide a simple design of experiments and to facilitate parameter replacement. The earlier
script we realized was complicated for no good reason"""
import os
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from collections import namedtuple
import numpy as np
import msvcrt
import pandas as pd
from apsimNGpy.experiment.permutations import create_permutations
from apsimNGpy.utililies.database_utils import get_db_table_names, read_db_table
from pandas import DataFrame, concat
from sqlalchemy import create_engine
from apsimNGpy.parallel.process import custom_parallel
import warnings
from collections import ChainMap
from apsimNGpy.replacements.replacements import Replacements
from experiment_utils import (_run_experiment, MetaInfo, copy_to_many, define_factor, Factor)


################################################################################
# Deep chain mapper
################################################################################
class DeepChainMap(ChainMap):
    'Variant of ChainMap that allows direct updates to inner scopes from collection module'

    def __setitem__(self, key, value):

        for mapping in self.maps:

            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)

    def merge(self):
        result = {}
        management = []
        soils = []
        for counter in range(len(self.maps)):
            if isinstance(self.maps[counter], dict):
                for k, d, in self.maps[counter].items():
                    if isinstance(d, dict):
                        for km, vm in d.items():
                            if isinstance(vm, str):
                                if 'Manager' in vm:
                                    d = dict(d)
                                    d[k] = d['param_values']
                                    management.append(d)
                                if 'Soil' in vm:
                                    d = dict(d)
                                    d[k] = d['param_values']
                                    soils.append(d)
                if bool(management):
                    man = dict(management=tuple(management))

                    result.update(man)
                if soils:
                    result.update(dict(soils_params=tuple(soils)))
        return result

    def control_variables(self, merged=None):
        gdata = []
        data = self.merge() if not merged else merged
        management = data.get('management')
        soils = data.get('soils_params')
        cultivar = data.get('cultivar')

        if management:
            for i in management:
                if i.get("Name"):
                    i.pop('Name')
            management_df = concat([DataFrame(i, [0]) for i in management], axis=1).drop(['path', 'param_values'],
                                                                                         axis=1).reset_index(drop=True)
            gdata.append(management_df)

        if soils:
            dt = {}
            soil_df = concat([DataFrame(i, [0]) for i in soils], axis=1).drop(['path', 'param_values'],
                                                                              axis=1).reset_index(drop=True)
            gdata.append(soil_df)
        return concat(gdata, axis=1) if gdata else None


################################################################################
# define_parameters
################################################################################
def define_parameters(factors_list):
    permutations = create_permutations([factor.variables for factor in factors_list],
                               [factor.variable_name for factor in factors_list])
    return permutations


@dataclass
class MetaData:
    ...


################################################################################
# check_completed
################################################################################
def check_completed(datastorage, perms, simulation_id):
    if os.path.isfile(datastorage) and bool(get_db_table_names(datastorage)):
        print(f'Total simulations: {len(perms)}')
        try:
            cur_data = pd.concat([read_db_table(datastorage, report_name=t) for t in
                                  get_db_table_names(datastorage)],
                                 ignore_index=True)
            already_simulated = set(cur_data[simulation_id])

        except (KeyError, ValueError, TypeError):
            warnings.warn('errors reading the simulated data\n'
                          'proceeding with all total simulations without filter', UserWarning)
            return perms

        perms = {idx: perms[idx] for idx, perm in enumerate(perms) if
                 idx not in already_simulated}
        return perms

    else:
        return perms


################################################################################
# set_experiment
################################################################################
def set_experiment(*, datastorage,
                   tag,
                   base_file,
                   factors,
                   wd=None,
                   simulation_id='SID',
                   use_thread=True,
                   n_core=4,
                   by_pass_completed=True,
                   data_schema=None,
                   **kwargs):
    _path = Path(wd) if wd else Path(os.path.realpath(base_file)).parent

    meta_ = dict(tag=tag, wd=_path,
                 simulation_id=simulation_id,
                 datastorage=datastorage,
                 path=_path,
                 data_schema=kwargs.get('data_schema', data_schema),
                 n_core=n_core, **kwargs)

    perms = define_parameters(factors_list=factors)
    perms = check_completed(datastorage, perms, simulation_id) if by_pass_completed else perms

    print(len(perms))
    print(f"copying files to {_path}")
    # def _copy(i_d)
    ids = iter(perms)
    __path = _path.joinpath('apSimNGpy_experiment')
    # make sure we are creating files free from existing files
    if __path.exists():
        shutil.rmtree(__path)
    __path.mkdir(exist_ok=True)
    list(
        custom_parallel(copy_to_many,
                        ids,
                        base_file,
                        __path, tag,
                        use_thread=use_thread,
                        n_core=n_core,
                        **kwargs))
    for ID, perm in perms.items():
        Meta = MetaInfo()
        [setattr(Meta, k.lower().strip(" "), v) for k, v in meta_.items()]
        yield dict(SID=ID, meta_info=Meta,
                   parameters=DeepChainMap(perm))
    ...


parameters = ['datastorage', 'perms', 'simulation_id', 'factors', 'base_file', 'tag', 'perms']

if __name__ == '__main__':
    path = Path(r'G:/').joinpath('scratchT')
    a = ['Maize', "Wheat"]
    reports = dict(zip(a, ['Annual', 'Annual']))

    Amount = [{'management': dict(Name='MaizeNitrogenManager', Amount=i)} for i in
              [20, 40, 60, 80]]
    Crops = [{'management': {'Name': "Simple Rotation", "Crops": i}} for i in
             ['Maize', 'Wheat, Maize']]
    a1 = Factor(name='Crops', variables=Crops)
    b1 = Factor(name='Amount', variables=Amount)

    facs = [Crops, Amount]
    ap = set_experiment(factors=[a1, b1],
                        database_name='sbb.db',
                        datastorage='sbx.db',
                        tag='th', base_file='ed.apsimx',
                        wd=path,
                        use_thread=True,
                        children=['manager'],
                        by_pass_completed=False,
                        reports={'Maize': 'Annual', 'Wheat, Maize': 'Annual'})

    df = _run_experiment(**next(ap))

    xp = create_permutations(facs, ['a', 'b'])
    xm = DeepChainMap(xp[0])
    from apsimNGpy.utililies.database_utils import read_db_table
