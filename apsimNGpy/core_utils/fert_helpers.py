from functools import lru_cache
from diskcache import Cache

from apsimNGpy import NodeNotFoundError, timer

cache = Cache(dir="./cache")


def fertilize_at_fixed_dates(model, missing_ok=True, **params):
    """
    Applies fertilization at predefined calendar dates using a fertilize_at_fixed_dates Manager script.

    USE ONLY WHEN:
        The model contains a manager script named 'Fertilise on fixed dates'.

    Parameters
    ----------
    model : ApsimModel
        APSIM model instance.
    missing_ok : bool, optional
      used to raise an exception if False and 'Fertilise on fixed dates' is not available. default is True

    **params : dict
        Parameters controlling fertilization schedule:

        - Amount : int or float Optional
            Amount of fertilizer applied at each specified date. Default is 180

        - FertiliserDates : str, optional
            Comma-separated list of application dates (e.g., '10-Nov, 10-Jan').
            Default is '1-May'.

        - AmountType : bool, optional
            Indicates how the amount is interpreted (default: True). Whether the amount will be applied each time (True) or spread across all
             dates (False). Default is False

        - FertiliserType : str, optional
            Type of fertilizer to apply (default: 'N03N').

    Raises
    ------
    ValueError
        If 'Amount' is not provided.

    Behavior
    --------
    - Validates required parameters.
    - Sets defaults for optional parameters.
    - Checks for existence of the target manager node.
    - Updates the manager script using `edit_model`.

    Example
    -------
    _fertilize_at_fixed_dates(
        model,
        Amount=100,
        FertiliserDates='10-Nov, 10-Jan',
        FertiliserType='Urea'
    )
    """

    params.setdefault('Amount', 180)
    params.setdefault('FertiliserType', 'N03N')
    params.setdefault('AmountType', False)
    params.setdefault('FertiliserDates', '1-May')

    if model.has_node('Fertilise on fixed dates', node_type='Models.Manager')['ok']:
        model.edit_model('Models.Manager', model_name='Fertilise on fixed dates', **params)
    else:
        if missing_ok is not True:
            raise NodeNotFoundError("'Fertilise on fixed dates' is not found in this model")


def fertilize_at_sowing(model, missing_ok=True, **params):
    """
    Applies or updates a fertilization event at sowing within the APSIM model.

    This utility checks for the existence of a manager script named
    'Fertilise at sowing' and updates its parameters accordingly. If no
    parameters are provided, default values are used.

    Parameters
    ----------
    model : ApsimModel
        An initialized APSIM model instance.
    missing_ok : bool, optional
      used to raise an exception if False and 'Fertilise on fixed dates' is not available. default is True

    **params
        Key-value pairs representing parameters to update in the
        'Fertilise at sowing' manager script.

        Common parameters include:
            - FertiliserType (str): Type of fertilizer to apply
              (default: 'NO3N').
            - Amount (float | int): Amount of fertilizer applied
              (default: 180).

    Notes
    -----
    - Default values are applied if parameters are not explicitly provided.
    - The function will only modify the model if the target manager node exists.
    - No action is taken if 'Fertilise at sowing' is not found.

    Examples
    --------
    >>> fertilize_at_sowing(model)
    Applies default fertilization (NO3N, 180 units)

    >>> fertilize_at_sowing(model, Amount=120)
    Updates fertilizer amount to 120

    >>> fertilize_at_sowing(model, FertiliserType='NH4', Amount=100)
    Applies ammonium fertilizer at 100 units
    """
    params.setdefault("FertiliserType", 'N03N')
    params.setdefault("Amount", 180)
    if model.has_node('Fertilise at sowing')['ok']:
        model.edit_model('Models.Manager', model_name='Fertilise at sowing', **params)
    else:
        if missing_ok is not True:
            raise NodeNotFoundError("'Fertilise at sowing' is not found in this model")


@cache.memoize(expire=9600)
def _fill_defaults(script_name: str, pams: dict) -> dict:
    params = dict(pams)
    AMOUNT = 180
    FertilizerType = 'NO3N'

    if 'Fertilise at sowing' == script_name:
        params.setdefault("FertiliserType", FertilizerType)
        params.setdefault("Amount", AMOUNT)
    elif 'Fertilise on fixed dates' == script_name:
        params.setdefault('Amount', AMOUNT)
        params.setdefault('FertiliserType', FertilizerType)
        params.setdefault('AmountType', False)
        params.setdefault('FertiliserDates', '1-May')
    elif 'Fertilise on Zadok stage' == script_name:
        params.setdefault('Stage', 30)
        params.setdefault('FertiliserType', FertilizerType)
        params.setdefault('Amount', AMOUNT)
    return params


@timer
def fertilize(apsim_model, script_name, missing_ok=True, **kwargs):
    params = _fill_defaults(script_name, kwargs)
    if apsim_model.has_node(script_name, node_type='Manager')['ok']:
        apsim_model.edit_model('Models.Manager', model_name=script_name, **params)
        # print(apsim_model.inspect_model_parameters(model_type="Manager", model_name=script_name))
    else:
        if not missing_ok:
            raise NodeNotFoundError(f"manager script name `{script_name}` was not found in any simulation")


if __name__ == '__main__':
    from apsimNGpy.core.config_vars import CROPS
    from apsimNGpy import ApsimModel
    import Models

    ops = Models.Operations()
    op = Models.Operation()
    op.Enabled = True
    op.Action = "[Fertiliser].Apply(10, Fertiliser.Types.UreaN, 0);"
    op.Line = "2003-11-15 [Fertiliser].Apply(10, Fertiliser.Types.UreaN, 0);"
    data = []
    # for crop in CROPS:
    #     with ApsimModel(crop) as model:
    #         mn = model.inspect_model('Models.Manager', fullpath=False)
    #         path = model.inspect_model('Models.Manager', fullpath=True)
    #         p = [model.inspect_model_parameters_by_path(p) for p in path]
    #         data.append({crop: dict(zip(mn, p))})
    for crop in CROPS:
        with ApsimModel(crop) as model:
            fertilize(model, script_name='Fertilise at sowing', Amount=230, missing_ok=True)
            if model.has_node('Fertilise at sowing', node_type=Models.Manager)['ok']:
                model.run(verbose=True)
                mn = model.results.mean(numeric_only=True)
                print(mn)
