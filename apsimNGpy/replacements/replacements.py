"""
This module attempts to provide abstract methods for paramters replacement to various nodes or childs in apsim simulations model
"""
from apsimNGpy.core.core import APSIMNG
from abc import ABC, abstractmethod
import copy


class ReplacementHolder(APSIMNG, ABC):
    def __init__(self, model, **kwargs):
        super().__init__(model, **kwargs)
        self._model = model

    @abstractmethod
    def update_child_params(self, child: str, **kwargs):
        """Abstract method to replace parameters for a single child node"""
        pass

    @abstractmethod
    def update_children_params(self, children: tuple, **kwargs):
        """Abstract method to replace parameters for more than one child node"""
        pass


class Replacements(ReplacementHolder):

    def __init__(self, model, **kwargs):
        super().__init__(model, **kwargs)
        # Map action types to method names
        # this will hold lower key
        self.methods = None
        # define them with human-readable formats

    @property
    def __methods(self):
        ___methods = {
            'cultivar': self.edit_cultivar,
            'manager': self.update_mgt,
            'weather': self.replace_met_file,
            'soilphysical': self.replace_any_soil_physical,
            'soilorganic': self.replace_any_soil_organic,
            'soilchemical': self.replace_any_solute,
            'soilwater': self.replace_crop_soil_water,
            'soilorganicMatter': self.change_som,
            'clock': self.change_simulation_dates
        }
        return ___methods

    def Method(self, child):
        if child in self.__methods:
            return self.__methods[child]
        else:
            raise TypeError(f"Unknown node: {child}, children should be any of {self.__methods.keys()}")

    def update_child_params(self, child: str, **kwargs):
        """Abstract method to perform various parameters replacements in apSim model. :param child: (str): name of
        e.g., weather space is allowed for more descriptive one such a soil organic not case-sensitive :keyword
        kwargs: these correspond to each node you are editing. Please see the corresponding methods for each node
        """
        # Convert keys to lowercase
        _child = child.lower().replace(" ", "")
        methods = self.Method(_child)
        return methods(**kwargs)

    # to be deprecated
    def update_children_params(self, children: tuple, **kwargs):
        """Abstract method to perform various parameters replacements in apSim model.
        :param children: (str): name of e.g., weather space is allowed for more descriptive one such a soil organic not case-sensitive
        :keyword kwargs: these correspond to each node you are editing see the corresponding methods for each node
        """
        # Convert keys to lowercase
        self.methods = {key.lower(): value for key, value in self.__methods(chilredren).items()}
        """Perform various actions based on the node_type."""
        # convert to lower and also remove spaces if any
        nodes = (child.replace(" ", "") for child in children)

        for node in nodes:
            if node.lower() not in self.methods:
                raise TypeError(f"Unknown child node: {node}, children should be any of {self.__methods.keys()}")

            else:
                self.methods[node.lower()](**kwargs)
        return self


if __name__ == '__main__':
    from pathlib import Path

    import os

    os.chdir(Path.home())
    from apsimNGpy.core.base_data import load_default_simulations, weather_path

    mn = load_default_simulations(crop='Maize')
    ce = Replacements(mn.path)
    mets = Path(weather_path).glob('*.met')
    met = os.path.realpath(list(mets)[0])
    # the method make_replacements can be chained with several other action types
    model = ce.update_child_params(child='weather', weather_file=met)
    mgt = {'Name': 'Simple Rotation', 'Crops': "Maize, Soybean"},
    chilredren = 'Manager', 'weather', 'SoilOrganicMatter'
    # ce.update_children_params(children=chilredren, icnr=120, weather_file=met, management=mgt)
