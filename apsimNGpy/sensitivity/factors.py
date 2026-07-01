import os
from pathlib import Path

import pandas as pd

from apsimNGpy import logger
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.sensitivity.sensitivity import run_sensitivity, ConfigProblem
from apsimNGpy.tests.unittests.senstivity_study.cultivars_params import parameters


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
    from apsimNGpy.core.edit import get_model_paths_to_edit
    from apsimNGpy.sensitivity.combs import add_comb_json
    base = Path(r"D:\Elimin_rye_cover_crop_2026\APSIMX\s2.apsimx")
    Base_N = 502
    NRate = 0
    fertilize_maize_script = 'AddfertlizerRotationMAize'
    model = ApsimModel(base)

    model.edit_model('Models.Manager', model_name=fertilize_maize_script, Amount=NRate)
    model.save()
    p = model.inspect_model_parameters("Models.Manager", fertilize_maize_script, parameters='Parameters')
    NRat = p['Parameters']['Amount']
    print(type(NRat))
    assert NRat == f"{NRate}"
    A_110_path = get_model_paths_to_edit(model, 'Models.PMF.Cultivar', "B_100")
    A_110 = list(set(A_110_path))[0]
    soil = 'S'
    Crop = 'Maize'
    para_ms = []
    for p in parameters:
        lb = p['LowerBound']
        ub = p['UpperBound']
        path = p['Path']
        pp = set(path.split('.'))
        for n in pp:
            if n in {'RUE', 'Juvenile', 'MaximumNConc'}:
                pass
        cc = cultivar_factor(model.path, 'B_100', bounds=(lb, ub),
                             param=path,
                             managers={'SowMaize': 'CultivarName'}, plant='Maize')
        cc['base'] = A_110
        print(A_110)
        para_ms.append(cc)
    assert para_ms, "params is empty can not continue"
    runner = ConfigProblem(
        base_model=model.path,
        params=para_ms,

        outputs=["Yield", "AGB", 'TopN2O', 'soc0_10cm', 'Top_respiration'],
    )


    def fast():
        return run_sensitivity(
            runner,
            threads=True,
            method="fast",
            agg_func='mean',
            total_chunks=38,
            N=Base_N,
            chunk_size=105,
            n_cores=12,
            tables=['MaizeR'],
            grouping=['Year'],
            sample_options={
                "M": 4,

            },
            analyze_options={
                'conf_level': 0.95,
                "num_resamples": 1000,
                "print_to_console": False,
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

    import json

    si_fast, ans = attach_meta_data(dict(BaseSample=Base_N, Soil=soil,
                                         Nrate=NRate, CropsRotation=Crop,
                                         TotalParams=len(para_ms)), si_fast, ans)
    path = Path('D:/sensitivity_study')
    path.mkdir(exist_ok=True)
    data_path = path / 'Data'
    data_path.mkdir(exist_ok=True)
    from sqlalchemy import create_engine

    parm_len = len(para_ms)

    # view(ans)
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
                    ans.to_sql(table, con=engine, if_exists='append')
                elif 'statistics' in table:

                    si_fast.to_sql(table, con=engine, if_exists='append')
    del ans
    combs = dict(NRate=NRate, Base_N=Base_N, Soil=soil, Crops=Crop, Nparams=len(para_ms))
    add_comb_json(combs)
    logger.info(f'Finished {NRate}')

