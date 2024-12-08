"""
This module attempts to provide abstract methods for paramters replacement to various nodes or childs in apsim simulations model
"""
from typing import Union
import os
import numpy as np
from apsimNGpy.core.core import APSIMNG
from abc import ABC, abstractmethod
import copy
from apsimNGpy.utililies.utils import timer
import inspect


class ReplacementHolder(APSIMNG, ABC):
    def __init__(self, model, out_path=None, **kwargs):
        super().__init__(model, out_path=None, **kwargs)
        self._model = model
        self.out_path = out_path

    @abstractmethod
    def update_mgt_by_path(self, **kwargs):
        """Abstract method to replace parameters manager scripts"""
        pass

    @abstractmethod
    def update_children_params(self, children: tuple, **kwargs):
        """Abstract method to replace parameters for more than one child node"""
        pass

    def replace_soil_properties_by_path(self, **kwargs):
        """
        Abstract method to replace soil properties
        """
        pass

    def replace_cultivar_params(self, **kwargs):
        pass


Nodes = [
    'cultivar',
    'manager',
    'weather',
    'soilphysical',
    'soilorganic',
    'soilchemical',
    'soilwater',
    'soilorganicMatter',
    'clock'
]


class Replacements(ReplacementHolder):

    def __init__(self, model: Union[os.PathLike, dict, str, 'APSIMNG'], out_path=None, **kwargs):
        super().__init__(model, out_path, **kwargs)
        # Map action types to method names
        # this will hold lower key
        self._methods = {
            'cultivar': 'edit_cultivar',
            'manager': 'update_mgt',
            'weather': 'replace_met_file',
            'soilphysical': 'replace_any_soil_physical',
            'soilorganic': 'replace_any_soil_organic',
            'soilchemical': 'replace_any_solute',
            'soilwater': 'replace_crop_soil_water',
            'soilorganicmatter': 'change_som',
            'clock': 'change_simulation_dates'
        }
        self.methods = None
        self.out_path = out_path

        # define them with human-readable formats

    def replacement_methods(self, child: str):

        if child in self._methods:
            return getattr(self, self._methods[child])
        else:
            raise TypeError(f"Unknown node: {child}, children should be any of {self._methods.keys()}")

    def replace_soil_properties_by_path(self, path: str,
                                        param_values: list,
                                        str_fmt: str = ".",
                                        **kwargs):
        # TODO I know there is a better way to implement this
        """
        This function processes a path where each component represents different nodes in a hierarchy,
        with the ability to replace parameter values at various levels.

        :param path:
            A string representing the hierarchical path of nodes in the order:
            'simulations.Soil.soil_child.crop.indices.parameter'. Soil here is a constant

            - The components 'simulations', 'crop', and 'indices' can be `None`.
            - Example of a `None`-inclusive path: 'None.Soil.physical.None.None.BD'
            - If `indices` is a list, it is expected to be wrapped in square brackets.
            - Example when `indices` are not `None`: 'None.Soil.physical.None.[1].BD'
            - if simulations please use square blocks
               Example when `indices` are not `None`: '[maize_simulation].physical.None.[1].BD'

            **Note: **
            - The `soil_child` node might be replaced in a non-systematic manner, which is why indices
              are used to handle this complexity.
            - When a component is `None`, default values are used for that part of the path. See the
              documentation for the `replace_soil_property_values` function for more information on
              default values.

        :param param_values:
            A list of parameter values that will replace the existing values in the specified path.
            For example, `[0.1, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]` could be used to replace values for `NH3`.

        :param str_fmt:
            A string specifying the formatting character used to separate each component in the path.
            Examples include ".", "_", or "/". This defines how the components are joined together to
            form the full path.

        :return:
            Returns the instance of `self` after processing the path and applying the parameter value replacements.

            Example f

            from apsimNGpy.core.base_data import load_default_simulations
            model = load_default_simulations(crop = 'maize')
            model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])
            if we want to replace carbon at the bottom of the soil profile, we use a negative index  -1
            model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.[-1].Carbon', param_values= [1.23])
        """

        function_parameters = ['simulations', 'Soil', 'soil_child', 'crop', 'indices', 'parameter']
        expected_nones = ['simulations', 'crop', 'indices']
        args = path.split(str_fmt)
        if len(args) != len(function_parameters):
            raise TypeError(f"expected order is: {function_parameters}, crop, indices and simulations can be None"
                            f"if replacement is related to soil properties, soil is a constant after the simulation name")
        # bind them to the function paramters
        fpv = dict(zip(function_parameters, args))

        # by all means, we want indices to be evaluated

        fpt = {k: (p := APSIMNG._try_literal_eval(v)) if (k in expected_nones) else (p := v)
               for k, v in fpv.items()}
        # we can now call the method below. First, we update param_values
        fpt['param_values'] = param_values
        return self.replace_soil_property_values(**fpt)

    def replace_cultivar_params(self, *, path: str, param_values: tuple, fmt: str = "/", **kwargs):
        """
        the expected path is 'Cultivar/cultivar_name/commands' Note cultivars are best edited in the replacement folder, so,
        make sure it exists in your simulation and the respective crop has been added
        """
        if fmt == '.':
            raise ValueError(f"format character '{fmt}' is not a valid here")

        args = path.split(fmt)
        # not needed all expected are strings
        # arg_ms = [(p := f"'{arg}'") if " " in arg and fmt != " " not in arg else arg for arg in args]
        data = dict(zip(('cultivar', 'CultivarName', 'commands'), args))
        data['commands'] = data['commands'],

        data['values'] = param_values if isinstance(param_values, (list, tuple, np.ndarray)) else param_values,
        return self.edit_cultivar(**data)

    def update_mgt_by_path(self, *, path: str,
                           param_values, fmt='.', **kwargs):
        """
            Updates management parameters based on a given path and corresponding parameter values.

            This method parses the provided `path` string, evaluates its components, and updates
            management configurations using the `param_values`. The path is split using the specified
            delimiter `fmt` and validated against a predefined guide of parameters. If the path is
            invalid, a `ValueError` is raised.

            Args: path (str): A formatted string that specifies the hierarchical path of parameters to update. The
            default delimiter is a period ('.'). example: path should follow this order
            'simulations_name.Manager.manager_name.out_path_name.parameter_name' Manager is constant, simulation_name
            can be None the dfault simulations will be used, and the out_path can also be None the default will be
            picked param_values: The value(s) to assign to the specified parameter in the management update.
            fmt (str, optional): The delimiter used to split the path string. Default is '.'.

            Raises:
                ValueError: If the number of elements in the `path` does not match the expected structure.

            Returns:
                The result of the `update_mgt` function after applying the updates.

            Example:
                from apsimNGpy.core.base_data import load_default_simulations
                model  = Replacements(load_default_simulations(crop ='maize').path)
                path = "['Simulation'].Manager.Sow using a variable rule.None.Population"

                path = "['Simulation'].Manager.Sow using a variable rule.None.Population"
                param_values = 9
                model.update_mgt_by_path(path=path, param_values=param_values, fmt = '.')
                print(model.extract_user_input('Sow using a variable rule'))

                 # if we want all simulations in the model to be changed, we keep that part None
                example:
                path = "None.Manager.Sow using a variable rule.None.Population"
                param_values = 9
                model.update_mgt_by_path(path=path, param_values=param_values, fmt = '.')
                print(model.extract_user_input('Sow using a variable rule'))
            """
        parameters_guide = ['simulations_name', 'Manager', 'manager_name', 'out_path_name', 'parameter_name']
        parameters = ['simulations', 'Manager', 'Name', 'out']
        args = path.split(fmt)
        if len(args) != len(parameters_guide):
            join_p = ".".join(parameters_guide)
            raise ValueError(f"Invalid path '{path}' expected path should follow {join_p}")
        args = [(p := f"'{arg}'") if " " in arg and fmt != " " and '[' not in arg else arg for arg in args]
        _eval_params = [self._try_literal_eval(arg) for arg in args]

        _eval_params[1] = {'Name': _eval_params[2], _eval_params[-1]: param_values},
        parameters[1] = 'management'
        _eval_params[0] = _eval_params[0],

        _param_values = dict(zip(parameters, _eval_params))

        return self.update_mgt(**_param_values)

    def update_children_params(self, children: tuple, **kwargs):
        """Method to perform various parameters replacements in apSim model.
        :param children: (str): name of e.g., weather space is allowed for more descriptive one such a soil organic not case-sensitive
        :keyword kwargs: these correspond to each node you are editing see the corresponding methods for each node
        the following are available for each child passed to children
        'cultivar': ('simulations','CultivarName', 'commands', 'values'),
        'manager': ('management', 'simulations', 'out'),
        'weather': ('weather_file', 'simulations'),
        'soilphysical': ('parameter', 'param_values', 'simulation'),
        'soilorganic': ('parameter', 'param_values', 'simulation'),
        'soilchemical': ('parameter', 'param_values', 'simulation'),
        'soilwater': ('parameter', 'param_values', 'simulation'),
        'soilorganicmatter': ('simulations', 'inrm', 'icnr'),
        'clock': ('start_date', 'end_date', 'simulations')
        """
        # chd = iter(children)
        # while True:
        #     child = next(chd, None)
        #     if child is None:
        #         break
        for child in children:
            child = child.lower().replace(" ", "")
            method = self.replacement_methods(child)
            sig = inspect.signature(method)
            args = {k: v for k, v in kwargs.items() if k in sig.parameters.keys()}
            method(**args)
        return self


if __name__ == "__main__":
    from apsimNGpy.core.base_data import load_default_simulations

    maize = load_default_simulations(crop='maize')
    #maize.preview_simulation()
    maizee = Replacements(maize.path, )
    mod = maizee.update_mgt_by_path(path='Simulation.Manager.Fertilise at sowing.Amount.out', param_values=100)
    print(mod.extract_user_input('Fertilise at sowing'))
