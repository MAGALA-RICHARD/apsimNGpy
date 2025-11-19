import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.validation.evaluator import Validate
from apsimNGpy.exceptions import ApsimRuntimeError

obs_suffix = '_obs'
pred_suffix = '_pred'

metric_direction = {
    "rmse": -1,
    "mae": -1,
    "mse": -1,
    "rrmse": -1,
    "bias": -1,
    "me": 1,
    "wia": 1,
    "r2": 1,
    "ccc": 1,
    "slope": 1,
}


def eval_observed(obs, pred, index, pred_col, obs_col, method='rmse', exp=None):
    """"
    Evaluate the observed and predicted values based on a given loss function method
    examples of supported loss functions:
     ['RMSE', 'MAE', 'MSE', 'RRMSE', 'bias', 'ME', 'WIA', 'R2', 'CCC', 'slope']
        | Metric    | Meaning                             | Better when | Sign                           |
        | :-------- | :---------------------------------- | :---------- | :----------------------------- |
        | **RMSE**  | Root Mean Square Error              | smaller     | `-1`                           |
        | **MAE**   | Mean Absolute Error                 | smaller     | `-1`                           |
        | **MSE**   | Mean Square Error                   | smaller     | `-1`                           |
        | **RRMSE** | Relative RMSE                       | smaller     | `-1`                           |
        | **bias**  | Mean Bias                           | closer to 0 | `-1` (minimize magnitude)      |
        | **ME**    | Modeling Efficiency (NSE)           | larger      | `+1`                           |
        | **WIA**   | Willmott’s Index of Agreement       | larger      | `+1`                           |
        | **R2**    | Coefficient of Determination        | larger      | `+1`                           |
        | **CCC**   | Concordance Correlation Coefficient | larger      | `+1`                           |
        | **slope** | Regression slope                    | closer to 1 | `+1` (maximize closeness to 1) |

    """
    observed = obs.copy()
    predicted = pred.copy()
    # 3 make the same dtype
    predicted[index] = predicted[index].astype(float)
    observed[index] = observed[index].astype(float)
    observed.set_index(index, inplace=True)
    predicted.set_index(index, inplace=True)
    data = observed.join(predicted, rsuffix=obs_suffix, lsuffix=pred_suffix)
    data.reset_index(inplace=True)
    if obs_col == pred_col:
        out = Validate(data[f"{obs_col}{obs_suffix}"], data[f"{pred_col}{pred_suffix}"]).evaluate(
            method.upper())
    else:
        out = Validate(data[f"{obs_col}"], data[f"{pred_col}"]).evaluate(method.upper())

    return metric_direction[method.lower()] * out


from apsimNGpy.core.model_tools import find_child
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.model_loader import get_node_by_path

import Models
from System import Array, String


def find_all_model_type(parent, model_type):
    node = getattr(parent, "Node", parent)
    return node.FindAll[model_type]()


def trace_cultivar(location, cultivar_name):
    plants = find_all_model_type(location, Models.PMF.Plant)
    for plant in plants:
        node = getattr(plant, "Node", plant)
        if node.FindChild[Models.PMF.Cultivar](cultivar_name, recurse=True):
            return {cultivar_name: plant.Name}


def search_cultivar_loc(model: str, cultivar_name='Dekalb_XL82'):
    get_manager_name = None
    get_manager_param = None
    with ApsimModel(model) as model:
        man_names = model.inspect_model('Models.Manager', fullpath=False)
        managers = model.inspect_model('Models.Manager', fullpath=True)
        for manager, name in zip(managers, man_names):
            mn = model.inspect_model_parameters_by_path(manager)
            for k, v in mn.items():
                if v == cultivar_name:
                    get_manager_name = name
                    get_manager_param = k
                    break

        model.edit_model(Models.PMF.Cultivar, 'Dekalb_XL82',
                         parameter_name=get_manager_param, cultivar_manager=get_manager_name,
                         commands='x',
                         values='2',
                         new_cultivar_name='x')
        model.inspect_file(cultivar=True)

        tr= trace_cultivar(model.Simulations, 'B_110')
        print(tr)
        model.edit_model_by_path('.Simulations.Simulation.Field.Maize.x',
                                 commands='34', values=20,
                                 parameter_name=get_manager_param,)


def cultivar_plugin(model):
    with ApsimModel(model) as model:
        model.add_base_replacements()
        node = model.get_replacements_node()
        b_110 = node.Node.FindChild[Models.PMF.Cultivar]('B_110', recurse=True)
        b_110
        b_110 = CastHelper.CastAs[Models.PMF.Cultivar](b_110)
        lc = list(b_110.Command)
        lc.extend((['[Phenology].Photosensitive.Target.XYPairs.m = 0, 12.5, 29']))
        from pathlib import Path
        par = str(Path(b_110.FullPath).stem)
        np = get_node_by_path(node, node_path=par)
        print('/', np)

        print()
        string_array = Array[String](lc)
        print(b_110)
        b_110.Command = string_array
        for cmd in b_110.Command:
            print(cmd)
        print()
        # node.Children.Add(b_110)
        for i in node.Children:
            print(i.Name)

        setattr(b_110, "Command", string_array)

        np.Model.AddChild(b_110)
        for i in dir(np.Model):
            print('=', i)

        model.inspect_file(cultivar=True)

        print()
        node_p = node.Node.FindChild[Models.PMF.Cultivar]('B_110', recurse=True)
        print(node_p, '===')
        cc = Models.PMF.Cultivar()
        lc.append('[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue2=55')
        cc.Name = 'B_110'
        cc.Command = lc
        cc.set_Command(lc)
        b_110.set_Command([])
        np.ReplaceChild(node_p, cc)
        """this is failing may be employ trick to search the cultvar name in the sowing scripts"""
        print()
        print(b_110.FullPath)
        model.save()
        cv = model.inspect_model_parameters_by_path(cc.FullPath)
        for i, v in cv.items():
            print(i, v)
        from apsimNGpy.core.model_tools import get_or_check_model

        # model.edit_model_by_path(path='.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_100',
        #                                        commands='[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue',
        #                                        values =40)


def runner(model, params, table=None):
    with ApsimModel(model) as model:
        for param in params:
            model.set_params(param)
        df = model.run(report_name=table).results
        df["date"] = pd.to_datetime(df["Clock.Today"])

        # Extract components
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day

        return df


if __name__ == '__main__':
    from apsimNGpy.tests.unittests.test_factory import obs, pred

    rt = eval_observed(obs, pred, index='year', obs_col='observed', pred_col='predicted', method='ccc', exp=None)

    search_cultivar_loc('Maize')
