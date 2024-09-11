import itertools
import os
import shutil
from os.path import realpath
from pathlib import Path

from apsimNGpy import custom_parallel
from apsimNGpy.utililies.database_utils import read_db_table
from apsimNGpy.experiment.experiment_utils import _run_experiment, experiment_runner, define_factor, define_cultivar, copy_to_many, MetaInfo
from apsimNGpy.experiment.set_ups import check_completed, DeepChainMap, define_parameters


class Experiment:
    def __init__(self, *, datastorage,
                 tag,
                 base_file,
                 wd=None,
                 simulation_id='SID',
                 use_thread=True,
                 n_core=4,
                 by_pass_completed=True,
                 **kwargs):
        self.data_generator = None
        self.total_sims = None
        self.define_cultivar = define_cultivar
        self.define_factor = define_factor
        self.factors = []
        self.meta_info = None
        self.by_pass_completed = by_pass_completed
        self.n_core = n_core
        self.simulation_id = simulation_id
        self.use_thread = use_thread
        self.datastorage = datastorage
        self.tag = tag
        self.base_file = base_file
        self.wd = wd
        self._others = kwargs.copy()

    def add_factor(self, factor_type, **kwargs):
        """
        factor_types can be: management, som, cultivar or soils
        """
        if factor_type == 'management' or factor_type == 'soils':
            self.factors.append(self.define_factor(factor_type=factor_type, **kwargs))
        else:
            self.factors.append(self.define_cultivar(**kwargs))

    def set_experiment(self, **kwargs):
        _path = Path(self.wd) if self.wd else Path(realpath(self.base_file)).parent

        self.meta_info = dict(tag=self.tag, wd=self.wd,
                              simulation_id=self.simulation_id,
                              datastorage=realpath(self.datastorage),
                              work_space=self.wd,
                              n_core=self.n_core, **self._others)

        perms = define_parameters(factors_list=self.factors)
        perms = check_completed(self.datastorage, perms, self.simulation_id) if self.by_pass_completed else perms
        self.total_sims = len(perms)
        print(self.total_sims)
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
                            self.base_file,
                            __path, self.tag,
                            use_thread=self.use_thread,
                            n_core=self.n_core,
                            **kwargs))

        def _data_generator():
            for ID, perm in perms.items():
                Meta = MetaInfo()
                [setattr(Meta, k.lower().strip(" "), v) for k, v in self.meta_info.items()]
                yield dict(SID=ID, meta_info=Meta,
                           parameters=DeepChainMap(perm))

        return _data_generator()

    def test_experiment(self, test_size: int = 10):
        """
        this function will test the experiment set up to be called by the user before running start a few things to
        check reports supplied really exist in the simulations, and the data tables are serializable into the sql
        database

        """
        t_data = []
        print('debugging started....')
        from itertools import islice
        import random
        test_data = list(self.set_experiment())
        tests_sample = random.sample(test_data, test_size)
        data_size = os.path.getsize(self.meta_info.get('datastorage'))
        for data in tests_sample:
            d_f = _run_experiment(**data)
            t_data.append(d_f)

        size_in_bytes = os.path.getsize(self.meta_info.get('datastorage'))
        size_in_mb = size_in_bytes / (1024 * 1024)
        if data_size == size_in_mb:
            print(f'data size is {size_in_mb} is the same as the initial data is not writing to the data base')
        return t_data

    def start_experiment(self):
        """
        This will run the experiment
        The method may fail miserably if you call it without a guard like if __name__ == '__main__':
        It's advisable to use this class below the line
        """
        try:
            print(f"running  '{self.total_sims}' simulations")
            list(custom_parallel(experiment_runner, self.set_experiment(), use_thread= self.use_thread, n_core=self.n_core))

            size_in_bytes = os.path.getsize(self.meta_info.get('datastorage'))
            size_in_mb = size_in_bytes / (1024 * 1024)
            self.meta_info['data size'] = size_in_mb
        finally:
            # we have to remove these tones of files every time
            self.end_experiment()

    def get_simulated_data(self):

        return [read_db_table(db=self.meta_info.get('datastorage'), report_name=report) for report in
                self.meta_info.get('reports')]

    def end_experiment(self):
        """
        cleans up stuff
        """
        shutil.rmtree(Path(self.meta_info.get('work_space') / 'apSimNGpy_experiment'), ignore_errors=True)


if __name__ == '__main__':
    path = Path(r'G:/').joinpath('scratchT')
    from apsimNGpy.core.base_data import load_default_simulations

    # import the model from APSIM.
    # if we simulations_object it,
    # returns a simulation object of apsimNGpy, but we want the path only.
    # model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
    model_path = path.joinpath('m.apsimx')

    # define the factors

    carbon = define_factor(parameter="Carbon", param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    Amount = define_factor(parameter="Amount", param_values=[200, 324, 100], factor_type='Management',
                           manager_name='MaizeNitrogenManager')
    Crops = define_factor(parameter="Crops", param_values=[200, 324, 100], factor_type='Management',
                          manager_name='Simple Rotation')
    grainFilling = define_cultivar(parameter="grain_filling", param_values=[600, 700, 500],
                                   cultivar_name='B_110',
                                   commands='[Phenology].GrainFilling.Target.FixedValue')

    exp = Experiment(database_name='sbb.db',
                     datastorage='sbx.db',
                     tag='th', base_file=model_path,
                     wd=path,
                     use_thread=True,
                     by_pass_completed=False,
                     verbose=False,
                     test=False,
                     n_core=6,
                     reports={'Report', 'MaizeR'})

    exp.add_factor(parameter='Carbon', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    exp.add_factor(parameter='Crops', param_values=['Maize', "Wheat"], factor_type='management', manager_name='Simple '
                                                                                                              'Rotation')
    # cultivar is edited via the replacement module, any simulation file supplied without Replacements for,
    # this method will fail quickly
    exp.add_factor(parameter='grain_filling', param_values=[450, 650, 700, 500], cultivar_name='B_110',
                   commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')
    exp.start_experiment()
    exp.test_experiment()
    sim_data = exp.get_simulated_data()
    print(len(exp.factors))
