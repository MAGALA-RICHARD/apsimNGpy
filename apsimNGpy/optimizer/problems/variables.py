"""
Parameter Definition and Validation Utilities for APSIM Optimization
====================================================================

This module provides robust validation, normalization, and merging utilities
for APSIM optimization problems defined through Python.

It uses Pydantic models to ensure consistent parameter structures
and supports multiple variable types from the ``wrapdisc`` library,
enabling flexible mixed-variable optimization (continuous, discrete, categorical).

--------------------------------------------------------------------
Supported Variable Types
--------------------------------------------------------------------
| Class         | Type               | Example Input                 | Typical Use                  |
| --------------| ------------------ | ----------------------------- | ---------------------------- |
| `ChoiceVar`   | Categorical        | `["A", "B", "C"]`             | Select from discrete options |
| `GridVar`     | Deterministic grid | `[0, 10]`                     | Grid-based search            |
| `QrandintVar` | Quantized int      | `lower=0, upper=200, q=25`    | Integer steps                |
| `QuniformVar` | Quantized float    | `lower=0, upper=100, q=5`     | Continuous with quantization |
| `RandintVar`  | Random int         | `lower=1, upper=10`           | Random integer sampling      |
| `UniformVar`  | Random float       | `lower=0.0, upper=1.0`        | Continuous random sampling   |

--------------------------------------------------------------------
Functions Provided
--------------------------------------------------------------------
- validate_user_params: Validate and normalize parameter inputs.
- filter_apsim_params: Flatten parameters for APSIM simulation input.
- merge_params_by_path: Combine multiple parameter dictionaries with shared paths.
--------------------------------------------------------------------
"""

from datetime import datetime
from typing import Union, Optional, Tuple, Dict, List
from copy import deepcopy
from collections import defaultdict

from pydantic import BaseModel, PositiveInt, ValidationError, ConfigDict
from apsimNGpy.settings import logger

# Wrapdisc variable types
from wrapdisc.var import (
    ChoiceVar,
    GridVar,
    QrandintVar,
    QuniformVar,
    RandintVar,
    UniformVar,
)

UniformVa = UniformVar,
PLACEHOLDER = object()
ALLOWED_NAMES = {
    # Original canonical names
    "UniformVar": UniformVar,
    "QrandintVar": QrandintVar,
    "QuniformVar": QuniformVar,
    "GridVar": GridVar,
    "ChoiceVar": ChoiceVar,
    "RandintVar": RandintVar,

    # Short aliases
    "uniform": UniformVar,
    "quniform": QuniformVar,
    "qrandint": QrandintVar,
    "grid": GridVar,
    "choice": ChoiceVar,
    "randint": RandintVar,

    # Descriptive aliases (readable English)
    "continuous": UniformVar,
    "quantized_continuous": QuniformVar,
    "quantized_int": QrandintVar,
    "ordinal": GridVar,
    "categorical": ChoiceVar,
    "integer": RandintVar,

    # Alternative descriptive (for domain users)
    "step_uniform_float": QuniformVar,
    "step_random_int": QrandintVar,
    "ordered_var": GridVar,
    "choice_var": ChoiceVar
}


def string_eval(obj):
    """
    Evaluate a string expression using a restricted namespace.
    Only names defined in ALLOWED_NAMES are permitted.

    Parameters
    ----------
    obj : Any
        A string to be evaluated or any other object that will be returned unchanged.

    Returns
    -------
    Any
        The evaluated object.

    Raises
    ------
    ValueError
        If evaluation fails or expression contains unsupported names or syntax.
    """

    if not isinstance(obj, str):
        return obj

    try:
        out = eval(
            obj,
            {"__builtins__": {}},  # secure environment
            ALLOWED_NAMES  # whitelist
        )
    except (NameError, SyntaxError, TypeError, ValueError) as e:
        raise ValueError(
            f'Evaluation failed for expression "{obj}":original error: {e}'
        ) from e

    return out


# -------------------------------------------------------------------------
# Parameter Schema Definition
# -------------------------------------------------------------------------
class BaseParams(BaseModel):
    """
    Base model for defining APSIM optimization parameters.

    Attributes
    ----------
    path : str
        APSIM node path where the parameter resides (e.g., '.Simulations.Simulation.Field.Soil.Organic').
    vtype : tuple
        A tuple of variable type instances (from wrapdisc.var), one per candidate parameter.

        Supported Variable Types
        --------------------------------------------------------------------
        | Class         | Type               | Example Input                 | Typical Use                  |
        | --------------| ------------------ | ----------------------------- | ---------------------------- |
        | `ChoiceVar`   | Categorical        | `["A", "B", "C"]`             | Select from discrete options |
        | `GridVar`     | Deterministic grid | `[0, 10]`                     | Grid-based search            |
        | `QrandintVar` | Quantized int      | `lower=0, upper=200, q=25`    | Integer steps                |
        | `QuniformVar` | Quantized float    | `lower=0, upper=100, q=5`     | Continuous with quantization |
        | `RandintVar`  | Random int         | `lower=1, upper=10`           | Random integer sampling      |
        | `UniformVar`  | Random float       | `lower=0.0, upper=1.0`        | Continuous random sampling   |

    start_value : tuple[str | int | float]
        Initial starting values for each parameter in candidate_param.
    candidate_param : str | tuple[str]
        APSIM variable names corresponding to the optimization factors.
    bounds : tuple[float, float], optional
        Lower and upper bounds for continuous parameters.
    other_params : dict, optional
        Static parameters that should remain fixed during optimization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bounds: Optional[Tuple[float, float]] = None
    path: str
    vtype: Tuple[
        Union[
            ChoiceVar,
            GridVar,
            QrandintVar,
            QuniformVar,
            RandintVar,
            UniformVar,
        ],
        ...,
    ]
    start_value: Union[Tuple[str, ...], Tuple[int, ...], Tuple[float, ...]]
    candidate_param: Union[Tuple[str, ...]]
    other_params: Optional[Dict[str, Union[int, float, str, bool]]] = None
    cultivar: Optional[bool] = False

    def __hash__(self):
        """Allow instances to be hashable for OrderedDict or caching."""
        return hash(
            (
                self.path,
                self.candidate_param,
                self.start_value,
                tuple(v.__dict__.values() for v in self.vtype),
                tuple((self.other_params or {}).values()),
                self.bounds,
            )
        )


# -------------------------------------------------------------------------
# Validation Utilities
# -------------------------------------------------------------------------
def validate_user_params(params: Dict) -> BaseParams:
    """
    Validate user-supplied parameters using the BaseParams schema.

    This function checks structure, length consistency, and conflicts between
    candidate and other parameters. It does not validate the *existence* of APSIM nodes.

    Parameters
    ----------
    params : dict
        Dictionary with user-defined parameters, e.g.:
        {
            "path": ".Simulations.Simulation.Field.Soil.Organic",
            "vtype": (UniformVar(1, 2),),
            "start_value": ("1",),
            "candidate_param": ("Carbon",),
            "other_params": {"FBiom": 2.3}
        }

    Returns
    -------
    BaseParams
        A validated BaseParams instance.

    Raises
    ------
    ValidationError
        If schema or data type validation fails.
    ValueError
        If start_value, candidate_param, and vtype lengths are inconsistent.
    """
    # try factor or variable string evaluation before proceeding to the evaluation section
    vtype = string_eval(params['vtype'])# if params['vtype'] tuple is a string
    # deep evaluation
    vtype = tuple(string_eval(i) for i in vtype)
    params['vtype'] = vtype
    try:
        validated = BaseParams(**params)
        others = validated.other_params or {}
        candidates = validated.candidate_param
        start_value = validated.start_value
        vtypes = validated.vtype

        # Ensure matching tuple lengths
        lengths = [len(i) if isinstance(i, (list, tuple)) else 1 for i in [candidates, start_value, vtypes]]
        if len(set(lengths)) > 1:
            raise ValueError("Length of 'start_value', 'candidate_param', and 'vtype' must match.")

        # Remove overlapping keys from other_params
        for key in (candidates if isinstance(candidates, (list, tuple)) else [candidates]):
            others.pop(key, None)

        logger.info(f"Data type validation succeeded")
        return validated

    except ValidationError as e:
        logger.error(f"Validation failed for params: {params}")
        raise


# -------------------------------------------------------------------------
# APSIM Parameter Filtering
# -------------------------------------------------------------------------
def filter_apsim_params(params: BaseParams, place_holder=PLACEHOLDER) -> Dict:
    """
    Flatten a validated BaseParams object into a dictionary suitable for APSIM execution.

    - Merges 'other_params' into the main structure
    - Replaces candidate parameters with placeholders
    - Preserves the APSIM node 'path'

    Parameters
    ----------
    params : BaseParams
        Validated parameter model.
    place_holder : object, optional
        A sentinel object to represent unassigned optimization variables.

    Returns
    -------
    dict
        Flattened dictionary containing APSIM parameter mappings.
    """
    _params = {}
    cultivar = params.cultivar
    for key, value in params.__dict__.items():
        if key == "other_params" and isinstance(value, dict):
            _params.update(value)
        elif key == "candidate_param":
            for v in (value if isinstance(value, (list, tuple)) else [value]):
                _params[v] = place_holder

        elif key == "path":
            _params[key] = value
    if cultivar:
        _params['cultivar'] = cultivar

    return _params


# -------------------------------------------------------------------------
# Parameter Merging
# -------------------------------------------------------------------------
def merge_params_by_path(param_list: List[Dict]) -> List[Dict]:
    """
    Merge parameter dictionaries that share the same APSIM node path.

    Useful for grouping multiple variable definitions targeting the same node.

    Parameters
    ----------
    param_list : list of dict
        List of parameter dictionaries to merge.

    Returns
    -------
    list of dict
        A list of merged parameter dictionaries, one per unique path.
    """
    merged = {}
    for param in param_list:
        path = param["path"]
        if path not in merged:
            merged[path] = deepcopy(param)
        else:
            merged[path]["other_params"].update(param.get("other_params", {}))

            # Merge candidate parameters safely
            existing = merged[path].setdefault("candidate_param", [])
            if isinstance(existing, list):
                if isinstance(param["candidate_param"], list):
                    existing.extend(param["candidate_param"])
                else:
                    existing.append(param["candidate_param"])
            else:
                merged[path]["candidate_param"] = [existing, param["candidate_param"]]

    return list(merged.values())


# -------------------------------------------------------------------------
# Example Usage
# -------------------------------------------------------------------------
example_param = {
    "path": ".Simulations.Simulation.Field.Soil.Organic2",
    "vtype": (UniformVar(1, 2),),
    "start_value": ("1",),
    "candidate_param": ("Carbon",),
    "other_params": {"FBiom": 2.3},
}

example_param2 = {
    "path": ".Simulations.Simulation.Field.Soil.Organic",
    "vtype": (UniformVar(1, 2),),
    "start_value": ("1",),
    "candidate_param": ("Carbon",),
    "other_params": {"FBiom": 2.3, "FOM": 3},
}
ev_param = {
    "path": ".Simulations.Simulation.Field.Soil.Organic",
    "vtype": ('UniformVar(1, 2)',),
    "start_value": ("1",),
    "candidate_param": ("Carbon",),
    "other_params": {"FBiom": 2.3, "FOM": 3},
}


def search(s):
    import re
    name = re.match(r"^[^(]+", s).group()
    return name


if __name__ == "__main__":
    pp = validate_user_params(example_param2)
    print(filter_apsim_params(pp))
    mg = merge_params_by_path([example_param2, example_param])
    print(mg)
    # test evaluation
    string_eval('continuous(1, 2)')
    #test string evaluation
    pv =validate_user_params(ev_param)
