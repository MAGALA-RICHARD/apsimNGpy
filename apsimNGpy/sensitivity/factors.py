import os
from pathlib import Path

import pandas as pd
from xlwings import view
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import find_child
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.tests.unittests.senstivity_study.cultivars_params import parameters
from apsimNGpy.sensitivity.sensitivity import run_sensitivity, ConfigProblem


def factor(base_model, model_name, model_type, param, bounds):
    if bounds[0] > bounds[1]:
        raise ValueError("lower bound should be less than upper bound")
    with ApsimModel(base_model) as model:
        has_node = model.has_node(model_name, model_type)
        ok = has_node.get('ok', None)
        if not ok:
            raise NodeNotFoundError(f"Node {model_name} not found")
        fp = has_node.get('fullpath', None)
        return has_node


def cultivar_factor(base_model, name, param, managers, plant, bounds):
    assert len(bounds) == 2, f"expected 2 bounds, got {len(bounds)}"
    if bounds[0] > bounds[1]:
        raise ValueError("lower bound should be less than upper bound")
    with ApsimModel(base_model) as model:
        cs = model.inspect_model('Models.PMF.Cultivar')

        for cul in cs:
            sps = cul.split('.')[-1]
            if sps == name:
                fullpath = cul
                break
        else:
            raise NodeNotFoundError(f"cultivar with name {name} not found")
        return dict(base=fullpath,
                    param=param, bounds=bounds, managers=managers, plant=plant)


if __name__ == '__main__':

    base = Path(r"D:\Elimin_rye_cover_crop_2026\APSIMX\N_2.apsimx")
    Base_N = 300
    with ApsimModel(base) as model:
        p = model.inspect_model_parameters("Models.Manager", 'AddfertlizerRotationMAize', parameters='Parameters')
        NRate = p['Parameters']['Amount']

    soil = 'N'
    para_ms = []
    for p in parameters:
        lb = p['LowerBound']
        ub = p['UpperBound']
        path = p['Path']
        pp = set(path.split('.'))
        for n in pp:
            if n in {'RUE', 'Juvenile', 'MaximumNConc'}:
                pass
        cc = cultivar_factor(base, 'A_110', bounds=(lb, ub),
                             param=path,
                             managers={'SowMaize': 'CultivarName'}, plant='Maize')
        cc['base'] = '.Simulations.Nicollet.Field1.Maize.CultivarFolder.Generic.A_110'
        para_ms.append(cc)
    assert para_ms, "params is empty can not continue"
    runner = ConfigProblem(
        base_model=base,
        params=para_ms,

        outputs=["Yield", "AGB", 'TopN2O', 'soc0_10cm', 'Top_respiration'],
    )


    def fast():
        return run_sensitivity(
            runner,
            method="fast",
            agg_func='mean',
            N=Base_N,
            total_chunks=20,
            n_cores=14,
            tables=['MaizeR'],
            grouping=['Year'],
            sample_options={
                "M": 4,

            },
            analyze_options={
                'conf_level': 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
            },
        )


    # Si_morris = run_sensitivity(
    #     runner,agg_func='sum', tables=['MaizeR'],
    #     method="morris", n_cores=10,
    #     grouping=None,
    #     N=100,
    #     sample_options={
    #         'seed': 42,
    #         "num_levels": 14,
    #         "optimal_trajectories": 24,
    #     },
    #     analyze_options={
    #         'conf_level': 0.95,
    #         "num_resamples": 1000,
    #         "print_to_console": True,
    #         'seed': 42
    #     },
    # )
    def attach_meta_data(meta_data, *arg):
        assert arg, "arg is empty"
        for da in arg:
            assert isinstance(da, pd.DataFrame), 'args must be data frames'
            for k, v in meta_data.items():
                da[k] = v
        return arg


    si_fast = fast()
    df = pd.DataFrame(si_fast)
    name = 'fast.csv'
    df.to_csv(name, index=False)
    os.startfile(name)
    ans = runner.raw_results

    from xlwings import view
    import json

    si_fast, ans = attach_meta_data(dict(BaseSample=Base_N, Soil=soil,
                                         Nrate=NRate,
                                         TotalParams=len(para_ms)), si_fast, ans)
    path = Path('D:/sensitivity_study')
    path.mkdir(exist_ok=True)
    data_path = path / 'Data'
    data_path.mkdir(exist_ok=True)
    from sqlalchemy import create_engine

    parm_len = len(para_ms)

    view(ans)
    config_file = Path(path / "database_manifest.json")

    with open(config_file, "r") as f:
        DATABASES = json.load(f)
    connections = {}

    for name, cfg in DATABASES.items():
        db_path = data_path / f"{cfg['database']}.db"
        if name.startswith('fast'):
            if True:
                engine = create_engine(f"sqlite:///{db_path}")
                table = cfg["table"]
                if 'raw' in table:
                    ans.to_sql(table, con=engine, if_exists='replace')
                elif 'statistics' in table:

                    si_fast.to_sql(table, con=engine, if_exists='replace')
