"""This script is used to provide a simple design of experiments and to facilitate parameter replacement. The earlier
script we realized was complicated for no good reason"""
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
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
from os.path import realpath
from collections import ChainMap
from apsimNGpy.replacements.replacements import Replacements
from experiment_utils import (_run_experiment, MetaInfo, copy_to_many,
                              experiment_runner,
                              define_factor, Factor, define_cultivar)


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
        cultivar = []
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
                                if 'Cultivar' in vm:
                                    d = dict(d)
                                    d[k] = d['param_values']
                                    cultivar.append(d)
                if bool(management):
                    man = dict(management=tuple(management))

                    result.update(man)
                if soils:
                    result.update(dict(soils_params=tuple(soils)))
                if cultivar:
                    result.update(dict(cultivar_params=tuple(cultivar)))
        return result

    def control_variables(self, merged=None):
        gdata = []
        data = self.merge() if not merged else merged
        management = data.get('management')
        soils = data.get('soils_params')
        cultivar = data.get('cultivar_params')

        if management:
            for i in management:
                if i.get("Name"):
                    i.pop('Name')
            management_df = concat([DataFrame(i, [0]) for i in management], axis=1).drop(['path', 'param_values'],
                                                                                         axis=1).reset_index(drop=True)
            gdata.append(management_df)

        if soils:
            soil_df = concat([DataFrame(i, [0]) for i in soils], axis=1).drop(['path', 'param_values'],
                                                                              axis=1).reset_index(drop=True)
            gdata.append(soil_df)
        if cultivar:
            cultivar_df = concat([DataFrame(i, [0]) for i in cultivar], axis=1).drop(['path', 'param_values'],
                                                                                     axis=1).reset_index(drop=True)
            print(cultivar_df)
            gdata.append(cultivar_df)
        return concat(gdata, axis=1) if gdata else None


################################################################################
# define_parameters
################################################################################
def define_parameters(factors_list):
    permutations = create_permutations([factor.variables for factor in factors_list],
                                       [factor.variable_name for factor in factors_list])
    return permutations


@dataclass
class GlobalMetaData:
    n_cores = 5
    ...


GlobalMetaData = GlobalMetaData()


################################################################################
# check_completed
################################################################################
def track_completed(datastorage, perms, simulation_id):
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

                   **kwargs):
    _path = Path(wd) if wd else Path(os.path.realpath(base_file)).parent

    meta_ = dict(tag=tag, wd=_path,
                 simulation_id=simulation_id,
                 datastorage=realpath(datastorage),
                 work_space = _path,
                 n_core=n_core, **kwargs)

    perms = define_parameters(factors_list=factors)
    perms = track_completed(datastorage, perms, simulation_id) if by_pass_completed else perms
    Total_sims = len(perms)
    print(Total_sims)
    print(f"copying files to {_path}")
    # def _copy(i_d)
    ids = iter(perms)
    __path = _path.joinpath('apSimNGpy_experiment')
    # make sure we are creating files free from existing files
    if __path.exists():
        shutil.rmtree(__path, ignore_errors=True)
    __path.mkdir(exist_ok=True)
    list(
        custom_parallel(copy_to_many,
                        ids,
                        base_file,
                        __path, tag,
                        use_thread=use_thread,
                        n_core=n_core,
                        progress_message='processing factorial experiment please wait',
                        **kwargs))

    def _data_generator():
        for ID, perm in perms.items():
            Meta = MetaInfo()
            [setattr(Meta, k.lower().strip(" "), v) for k, v in meta_.items()]
            yield dict(SID=ID, meta_info=Meta,
                       parameters=DeepChainMap(perm))

    if kwargs.get('test'):
        print('debugging started....')
        d_f = _run_experiment(**next(_data_generator()))
        return d_f
    else:
        print(f"running  '{Total_sims}' simulations")
        list(custom_parallel(experiment_runner, _data_generator(), n_core=10))

    size_in_bytes = os.path.getsize(meta_.get('datastorage'))
    size_in_mb = size_in_bytes / (1024 * 1024)
    meta_['data size'] = size_in_mb

    return meta_

