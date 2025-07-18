"""This is on trial as a module to replace some fucntionalities provided by using pythonnet API"""
import gc
import json
import os
import sys
from apsimNGpy.core.model_loader import load_as_dict
from apsimNGpy.core.config import load_crop_from_disk
from os.path import realpath
from collections import OrderedDict
from apsimNGpy.core._modelhelpers import _eval_model, Models

path2file = load_crop_from_disk('Maize', '../t.apsim')
f_name = realpath(path2file)
import datetime
import re

with open(f_name, "r+", encoding='utf-8') as apsimx:
    data = OrderedDict()
    app_ap = data | json.load(apsimx)


def match_model_path(model_string):
    pattern = r'\b(?:[A-Za-z_][A-Za-z0-9_]*\.){1,}[A-Za-z_][A-Za-z0-9_]*\b'
    out = re.findall(pattern, model_string)
    if out:
        return out[0]


def evaluate_model_class(model_class):
    """
    make sure the provided model_class is an attributes of Models namespace.

    facilitates users in supplying only the name of the model class e.g., Clock instead of Models.Clock

    @param model_class:
    @return: full string representation of model_class
    """
    evaluated = _eval_model(model_class)
    return match_model_path(str(evaluated))


class JsonUtilities:
    def __init__(self, _mod=f_name):
        self.json_name = _mod
        self.json = self.load_json(f_name)

    @staticmethod
    def load_json(jpath):

        with open(jpath, "r+", encoding='utf-8') as json_load:
            order = OrderedDict()
            merge = order | json.load(json_load)
        return merge

    def get_children(self, scope=None, recursive=False):
        """
        Recursively extract all 'Children' nodes from the JSON tree.
        """
        scope = scope or self.json
        children = scope.get('Children', [])
        if not recursive:
            return children
        all_children = []

        for child in children:
            all_children.append(child)
            # Recursively collect from nested children
            all_children.extend(self.get_children(child))

        return all_children

    def get_simulations(self):
        """
        Recursively collect all objects of type 'Models.Core.Simulation'.
        Returns a dictionary keyed by model path.
        """
        all_nodes = self.get_children(recursive=True)
        sims = {}

        for node in all_nodes:
            model_type = node.get('$type', '')
            matches = match_model_path('Models.Core.Simulation')
            if matches and matches == 'Models.Core.Simulation':
                sims[matches] = node

        return sims

    def find_all_descendants(self, model_class, node=None):
        """
        Recursively collect all in the specified ``model_class`` objects.
        Returns a dictionary with paths as keys and node objects as values.
        """
        _model_class = evaluate_model_class(model_class)
        if not match_model_path(_model_class):
            raise ValueError('un able to proceed')
        if node is None:
            node = self.json

        def _recurse(node, path=''):
            sims = {}
            node_name = node.get('Name', '<unnamed>')
            current_path = f"{path}.{node_name}" if path else f'.{node_name}'

            model_type = node.get('$type', '')
            matches = match_model_path(model_type)

            if matches and matches == _model_class:
                sims[current_path] = node

            for child in self.get_children(scope=node, recursive=True):
                sims.update(_recurse(child, current_path))

            return sims

        return _recurse(node)

    def get_fullpath(self, model_class):
        model_class = evaluate_model_class(model_class)
        data = self.find_all_descendants(model_class)
        return tuple(data.keys())


    def edit_model_by_path(self, model_class, path, verbose=True, **kwargs):
        model = self.find_all_descendants(model_class=model_class).get(path)
        match model_class:
            case "Models.Manager":
                parameters = model.get('Parameters', {})
                kas = set(kwargs.keys())
                kav = {i['Key'] for i in parameters}
                dif = kas - kav
                if len(dif) > 0:
                    raise ValueError(f"{kas - kav} is not a valid parameter for {path}")
                # Manager scripts have extra attribute parameters

                for i in parameters:
                    param = i['Key']
                    if param in kas:
                        param_value = kwargs[param]
                        i['Value'] = param_value
                return model

            case "Models.Clock" | Models.Clock:
                validated = dict(End='End', Start='Start', end='End', start='Start', end_date='End',
                                 start_date='Start')

                for kwa, value in kwargs.items():
                    key = validated.get(kwa, 'unknown')  # APSIM uses camelcase
                    if key in ['End', 'Start']:
                        parsed_value = datetime.datetime.fromisoformat(value)
                        model[key] = parsed_value.isoformat()
                        if verbose:
                            print(f"Set {key} to {parsed_value}")

                    else:
                        raise AttributeError(
                            f"no valid Clock attributes were passed. Valid arguments are: '{", ".join(validated.keys())}'")

            case "Models.Climate.Weather" | Models.Climate.Weather:
                met_file = kwargs.get('weather_file') or kwargs.get('met_file')
                if met_file is None:
                    raise ValueError('Use key word argument "weather_file" or "met_file" to supply the weather data')
                    # To avoid carrying over a silent bug or waiting for the bug to manifest during a model run,
                    # there is a need to raise here
                if not os.path.exists(met_file):
                    raise FileNotFoundError(f"'{met_file}' rejected because it does not exist on the computer")
                if not os.path.isfile(met_file):
                    raise FileNotFoundError(f"'{met_file}' is not a valid file did you forget to add .met at the end?")
                c_file = model.get('FileName', '')
                model['FileName'] = met_file
                if verbose:
                    print(f"weather file changed from '{c_file}' to '{met_file}'")

        return model
    def read(self):
        json_string = json.dumps(self.json)

        model_frm_str = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](json_string, None,
                                                                                         True,
                                                                                         fileName='./_.apsimx')
        return model_frm_str


if __name__ == '__main__':
    sys.setrecursionlimit(9000)
    jj = JsonUtilities(app_ap)
    ch = jj.get_children()
    jj.find_all_descendants('Clock')
    jj.get_fullpath('Clock')
    jj.get_fullpath('Models.PMF.Cultivar')
    print(gc.collect())
