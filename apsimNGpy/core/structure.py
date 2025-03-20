from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.apsim import ApsimModel
import Models
from apsimNGpy.settings import logger

# manipulation methods
ADD = Models.Core.ApsimFile.Structure.Add
DELETE = Models.Core.ApsimFile.Structure.Delete
MOVE = Models.Core.ApsimFile.Structure.Move
RENAME = Models.Core.ApsimFile.Structure.Rename
REPLACE = Models.Core.ApsimFile.Structure.Replace

FOLDER = Models.Core.Folder()
model = load_default_simulations(crop='maize')
from apsimNGpy.core_utils.utils import timer


@timer
def add_crop_replacements(_model, _crop):
    _FOLDER = Models.Core.Folder()
    "everything is edited in place"
    CROP = _crop
    _FOLDER.Name = "Replacements"
    PARENT = _model.Simulations
    ADD(_FOLDER, PARENT)
    _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
    if _crop is not None:
        ADD(_crop, _FOLDER)
    else:
        logger.error(f"No plants of crop{CROP} found")


def add_replacement_folder(_model):
    PARENT = _model.Simulations
    ADD(FOLDER, PARENT)


def find_model(model_name: str, model_namespace=None):
    """
    Find a model from the Models namespace and return its path.

    Args:
        model_name (str): The name of the model to find.
        model_namespace (object, optional): The root namespace (defaults to Models).
        path (str, optional): The accumulated path to the model.

    Returns:
        str: The full path to the model if found, otherwise None.

    Example:
        >>> find_model("Weather")  # doctest: +SKIP
        'Models.Climate.Weather'
        >>> find_model("Clock")  # doctest: +SKIP
        'Models.Clock'
    """
    if model_namespace is None:
        model_namespace = Models  # Default to Models namespace

    if not hasattr(model_namespace, "__dict__"):
        return None  # Base case: Not a valid namespace

    for attr, value in model_namespace.__dict__.items():
        if attr == model_name and isinstance(value, type(getattr(Models, "Clock", object))):
            return value

        if hasattr(value, "__dict__"):  # Recursively search nested namespaces
            result = find_model(model_name, value)
            if result:
                return result

    return None  # Model not found


def check_if_str_path(model_name):
    if isinstance(model_name, type(Models.Clock)):  # need this kind of objects from Models namespace
        return True


def add_model(_model, model_type, adoptive_parent, rename=None,
              adoptive_parent_name=None, verbose=True, **kwargs):
    """
    Add a model to the Models Simulations NameSpace. some models are tied to specific models, so they can only be added
    to that models an example, we cant add Clock model to Soil Model
    @param _model: apsimNGpy.core.apsim.ApsimModel object
    @param model_name: string name of the model
    @param where: loction along the Models Simulations nodes or children to add the model e.g at Models.Core.Simulation,
    @param adoptive_parent_name: importatn to specified the actual final destination, if there are more than one simulations
    @return: none, model are modified in place, so the modified object has the same reference pointer as the _model
        Example:
     >>> from apsimNGpy import core
     >>> model =core.base_data.load_default_simulations(crop = "Maize")
     >>> remove_model(model,Models.Clock) # first delete model
     >>> add_model(model, Models.Clock, adoptive_parent = Models.Core.Simulation, rename = 'Clock_replaced', verbose=False)

    """

    replacer = {'Clock': 'change_simulation_dates', 'Weather': 'replace_met_file'}
    sims = _model.Simulations
    # find where to add the model
    if adoptive_parent == Models.Core.Simulations:
        parent = _model.Simulations
    else:
        if isinstance(adoptive_parent, type(Models.Clock)):

            if not adoptive_parent_name:
                adoptive_parent_name = adoptive_parent().Name
        parent = _model.Simulations.FindInScope[adoptive_parent](adoptive_parent_name)

    # parent = _model.Simulations.FindChild(where)

    if isinstance(model_type, type(Models.Clock)):
        which = model_type
    elif isinstance(model_type, str):
        which = find_model(model_type)
    if which and parent:
        loc = which()
        if rename:
            loc.Name = rename

        ADD(loc, parent)
        if verbose:
            logger.info(f"Added {loc.Name} to {parent.Name}")
        # we need to put the changes into effect
        _model.save()
        logger.info(f'successfuly saved to {_model.path}')

    else:
        logger.debug(f"Adding {model_type} to {parent.Name} failed, perhaps models was not found")


def remove_model(_model, model_type, model_name=None):
    """
    Remove a model from the Models Simulations NameSpace
    @param _model: apsimNgpy.core.model model object
    @param model_name: name of the model e.g Clock
    @return: None
    """
    # imodel = _model.Simulations.Parent.FullPath + model_name
    if not model_name:
        model_name = model_type().Name
    DELETE(_model.Simulations.FindInScope[model_type](model_name))


def move_model(_model, model_type, new_parent_type, model_name=None, new_parent_name=None):
    sims = _model.Simulations
    if not model_name:
        model_name = model_type().Name
    child_to_move = sims.FindInScope[model_type](model_name)
    if not new_parent_name:
        new_parent_name = new_parent_type().Name
        print(new_parent_name)
    new_parent = sims.FindInScope[new_parent_type](new_parent_name)
    print(new_parent.Name)
    print(child_to_move.Name)
    MOVE(child_to_move, new_parent)
    logger.info(f"Moved {child_to_move.Name} to {new_parent.Name}")
    _model.save()


if __name__ == '__main__':
    import doctest

    doctest.testmod()
    # test
    add_crop_replacements(model, _crop='Maize')
    # sims.FindByPath(modelToCheck.Parent.FullPath + "." + newName)
    import ApsimNG

    nexp = load_default_simulations(crop='Maize')
    # add experiment
    add_model(nexp, model_type=Models.Factorial.Experiment, adoptive_parent=Models.Core.Simulations)
    # add factor holder
    add_model(nexp, model_type=Models.Factorial.Factors, adoptive_parent=Models.Factorial.Experiment)
    # now add individual factorst
    add_model(nexp, model_type=Models.Factorial.Factor, adoptive_parent=Models.Factorial.Factors)
    add_model(model, model_type=Models.Clock, adoptive_parent=Models.Core.Simulation, rename='sim5',
              adoptive_parent_name='Simulation')
    # final step is to move the base simulation
    move_model(nexp, Models.Core.Simulation, Models.Factorial.Experiment, None, None)
    pp = nexp.Simulations.FindInScope[Models.Factorial.Factor]()
    pp.set_Specification("[Fertilise at sowing].Script.Amount = 0 to 100 step 20")
    nexp.save()
    nexp.run()
    crop = model.Simulations.FindInScope[Models.PMF.Plant]('Soybean')
