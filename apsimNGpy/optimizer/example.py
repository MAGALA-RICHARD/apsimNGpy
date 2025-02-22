import os
import shutil
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.optimizer.optimizer import Problem, Solvers, SingleProblem
from apsimNGpy.optimizer.mixed import MixedOptimizer


def func_wheat(model):
    model.run(['MaizeR', 'WheatR'])
    wheat = model.results['WheatR'].w_AGB.mean()
    maizeY = model.results['MaizeR'].Maize_Yield.mean()
    return -wheat * 0.5 + maizeY * 0.5


if __name__ == '__main__':
    # DO  not try this wholeheartedly just follow along
    mode = Path.home() / 'Maize.apsimx'
    from variables import manager, cultivar

    maize = load_default_simulations(crop='maize', simulations_object=False)
    aps = 'D:/WATERSHED MODELING/PEWI_Prairie/python scripts/apsim_source_files/sw.apsimx'
    ws = Path(r'G:/').joinpath('chapter_3_sim_out_put')
    ows = ws.joinpath('optimization')
    ows.mkdir(parents=True, exist_ok=True)
    os.chdir(ws)
    w_file = ows.joinpath('optimization.apsimx')


    # shutil.copy(aps, w_file)

    # the first step is to define the loss function
    # here we use a simple function which will take in apsimNG object class.
    # in most cases, we compare predicted to the observed for lack of data this
    # example is simple just maximizing the yield based on N input
    def func_soybean(model):
        # model.update_mgt_by_path(path='Simulation.Manager.Simple Rotation.None.Crops', param_values='Soybean')

        model.run('SoybeanR')
        mn = model.results.SoyYield.mean()
        ans = mn
        return -ans


    def func_maize(model):
        model.run('MaizeR')
        mn = model.results.Maize_Yield.mean()
        return -mn


    WS = Path(r'G:/')


    def planting_va_opt(crop, file_name, func):
        pm = {'Soybean': 'SowSoy', 'Maize': 'SowMaize', 'Wheat': 'SowWheat'}[crop]
        # initialize the problem and supply the func and path to the apsim Model
        prob = MixedOptimizer.set_up_data(model=aps, ws=WS, func=func)
        man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
        StartDate = manager(params={'path': f"Simulation.Manager.{pm}.None.StartDate"}, label='StartDate',
                            var_desc=ChoiceVar(('27-sep', '22-sep', '29-sep', '2-oct', '24-sep')))
        EndDate = manager(params={'path': f"Simulation.Manager.{pm}.None.StartDate"}, label='EndDate',
                          var_desc=ChoiceVar(categories=['5-oct', '12-oct', '18-oct', '20-oct']))
        ew = manager(params={'path': f"Simulation.Manager.{pm}.None.MinESW"},
                     var_desc=GridVar([50, 70, 100, 150, 160]),
                     label='MEW')
        cul = {'soybean': [f"Generic_MG{i + 1}" for i in range(8)],
               'Wheat': ['Bennett', 'Stephens', 'Yecora'],
               "Maize": ["B_110", 'B_108', 'B_100', 'Laila', 'B_120', 'A_110']}[crop]
        cultivarS = manager(params={'path': f"Simulation.Manager.{pm}.None.CultivarName"}, label='cultivar',
                            var_desc=ChoiceVar(categories=cul))

        options = {'disp': True}

        prob.add_control_variable(control=cultivarS)
        prob.add_control_variable(control=StartDate)
        prob.add_control_variable(control=EndDate)
        prob.add_control_variable(control=ew)
        init_guess = ('Yecora', '27-sep', '5-oct', 150,)
        mn = prob.minimize_wrap_vars(ig=None, maxiter=150, popsize=30,
                                     workers=1, strategy='best1exp', )
        from joblib import Parallel, delayed, dump
        del mn.cache_info
        save_path = r'D:\WATERSHED MODELING\PEWI_Prairie\python scripts\optimized apsim inputs'
        dump(mn, os.path.join(save_path, file_name))

        return mn


    mxp = planting_va_opt(crop='Maize', file_name='wheat_plant_varOpt', func=func_wheat)
