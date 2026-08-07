from typing import Union, Iterable

from apsimNGpy.exceptions import NodeNotFoundError

from apsimNGpy.core.model_tools import ModelTools

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR
from pydantic import BaseModel, ConfigDict
from apsimNGpy.core.sim_tools import get_root_model

Models = CLR.Models


class Specification(BaseModel):
    name: str
    specification: str

    @property
    def factor_model(self):
        fm = Models.Factorial.Factor()
        fm.Name = self.name
        fm.set_Specification(self.specification)
        return fm, self.specification


class ExperimentData(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="forbid",
        strict=True,
    )
    apsim_model: ApsimModel
    experiment: Models.Factorial.Experiment
    factors: Models.Factorial.Factors | Models.Factorial.Permutation
    experiment_name: str
    permutation: bool


def build_experiment(model, *, experiment_name, base_simulation, permutation) -> ExperimentData:
    obj = get_root_model(model, simulation_name=base_simulation)
    root, base_sim = obj["root"], obj["simulation"]
    exp = Models.Factorial.Experiment()
    exp.Name = experiment_name
    factor_holder_node = Models.Factorial.Factors()
    exp.Children.Add(factor_holder_node)
    exp.Children.Add(base_sim)
    root.Simulations.Children.Add(exp)
    parent_node = factor_holder_node if not permutation else Models.Factorial.Permutation()
    if permutation:
        factor_holder_node.Children.Add(parent_node)
    return ExperimentData(apsim_model=root, experiment=exp, factors=parent_node,
                          permutation=permutation,
                          experiment_name=experiment_name)


from collections.abc import Iterable
from typing import Union

from apsimNGpy import NodeNotFoundError
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_tools import ModelTools


def factor_spec(
    model,
    *,
    param_node_location: str,
    node_type: Union[str, ModelTools.CLASS_MODEL],
    param_identifier: str,
    values: Union[str, Iterable[Union[str, int, float]]] = None,
    step: Union[int, float] = None,
    bounds: tuple = None,
    rename: str = "",
):
    """
    Build and validate an APSIM factor specification.

    This function provides a convenient alternative to manually writing APSIM
    factor specification strings. It validates that the target node exists in
    the supplied model, constructs an APSIM-compatible factor expression, and
    returns it as a one-item dictionary suitable for
    :func:`create_experiment_from_models`.

    Factor levels can be supplied explicitly with ``values`` or generated from
    a numeric range using ``bounds`` and, optionally, ``step``.

    **model** : str | pathlib.Path | ApsimModel
        APSIM model used to validate the target node. This may be a path to an
        APSIM model file or an existing ``ApsimModel`` instance.

    **param_node_location** : str
        Name or full path of the APSIM node containing the target parameter.

        Examples::

            "Organic"
            "Clock"
            "Sow using a variable rule"
            ".Simulations.Simulation.Field.Organic"

        When a full path is supplied, only the terminal node name is used when
        constructing the factor specification.

    **node_type** : str | ModelTools.CLASS_MODEL
        APSIM model type associated with ``param_node_location``. This is used
        to verify that the requested node exists in the model.

        Examples include ``"Manager"``, ``"Clock"``, ``"Organic"``, or a
        corresponding APSIM Models class.

    **param_identifier** : str
        Parameter name or property path relative to the target node.

        Examples::

            "Start"
            "Carbon[1]"
            "Leaf.Photosynthesis.RUE.FixedValue"
            "Script.Population"

        For Manager nodes, ``Script.`` is automatically prefixed when it is
        not already present.

    **values** : str | Iterable[str | int | float], optional
        Explicit factor levels.

        Examples::

            [1, 5, 10]
            [0.45, 1.0, 3.0]
            ["DAP", "NO3N"]

        When ``values`` is supplied, it takes precedence over ``bounds``.
        ``step`` is ignored when explicit values are supplied.

    **step** : int | float, optional
        Increment used with ``bounds`` to construct an APSIM range
        specification.

        For example, ``bounds=(0, 200)`` with ``step=20`` produces::

            0 to 200 step 20

        This argument has no effect when explicit ``values`` are supplied.

    **bounds** : tuple[int | float, int | float], optional
        Lower and upper bounds used to construct a ranged factor
        specification.

        For example::

            bounds=(100, 4000)

        produces::

            100 to 4000

        and when combined with ``step=500`` produces::

            100 to 4000 step 500

        The tuple must contain exactly two values, and the upper bound must
        not be less than the lower bound.

    **rename** : str, optional
        Name used as the key in the returned specification dictionary.

        If omitted, the name is derived from ``param_identifier`` by removing
        periods. For example,
        ``"Leaf.Photosynthesis.RUE.FixedValue"`` becomes
        ``"LeafPhotosynthesisRUEFixedValue"``.

    Returns
    -------
    dict[str, str]
        A one-item mapping containing the factor name and its APSIM factor
        specification.

        For example::

            {
                "population":
                    "[Sow using a variable rule].Script.Population = 1, 5, 10"
            }

        The returned mapping can be passed directly to
        :func:`create_experiment_from_models` or combined with mappings
        returned by other ``factor_spec`` calls.

    Raises
    ------
    NodeNotFoundError
        If ``param_node_location`` cannot be resolved for the supplied
        ``node_type``.

    ValueError
        If neither ``values`` nor ``bounds`` is supplied, if ``bounds`` does
        not contain exactly two values, or if the upper bound is less than the
        lower bound.

    Notes
    -----
    - Manager parameters are automatically placed under ``Script`` when the
      supplied ``param_identifier`` does not already contain ``Script``.
    - For non-Manager nodes, specifications have the form
      ``[Node].Parameter = values``.
    - For layered APSIM properties, include the layer index in
      ``param_identifier``, for example ``Carbon[1]`` or ``FOM[2]``.
    - When both ``values`` and ``bounds`` are supplied, ``values`` takes
      precedence.
    - This function does not modify the supplied APSIM model. The model is
      used only to validate the target node.

    Examples
    --------
    Create a specification for a Manager parameter:

    .. code-block:: python

        population = factor_spec(
            "Maize.apsimx",
            param_node_location="Sow using a variable rule",
            node_type="Manager",
            param_identifier="Population",
            values=[1, 5, 10],
            rename="population",
        )

        print(population)

    Output::

        {
            "population":
                "[Sow using a variable rule].Script.Population = 1, 5, 10"
        }

    Create a specification using a full APSIM node path:

    .. code-block:: python

        nitrogen = factor_spec(
            "Maize.apsimx",
            param_node_location=(
                ".Simulations.Simulation.Field.Fertilise at sowing"
            ),
            node_type="Manager",
            param_identifier="Amount",
            values=[0, 100, 200],
            rename="nitrogen",
        )

    Create a factor for a layered soil property:

    .. code-block:: python

        carbon = factor_spec(
            "Maize",
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="Carbon[1]",
            values=[0.45, 1, 3],
            rename="initial_carbon",
        )

    Create a ranged factor using bounds and a step:

    .. code-block:: python

        fom = factor_spec(
            "Maize",
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="FOM[1]",
            bounds=(100, 4000),
            step=500,
            rename="fom",
        )

        print(fom)

    Output::

        {
            "fom":
                "[Organic].FOM[1] = 100 to 4000 step 500"
        }

    Combine multiple specifications:

    .. code-block:: python

        specifications = {}

        specifications.update(
            factor_spec(
                "Maize",
                param_node_location="Organic",
                node_type="Organic",
                param_identifier="Carbon[1]",
                values=[0.45, 1, 3],
                rename="initial_carbon",
            )
        )

        specifications.update(
            factor_spec(
                "Maize",
                param_node_location="Sow using a variable rule",
                node_type="Manager",
                param_identifier="Population",
                values=[6, 10, 14],
                rename="population",
            )
        )

    Pass the specifications to ``create_experiment_from_models``:

    .. code-block:: python

        experiment = create_experiment_from_models(
            model="Maize",
            specifications=specifications,
            permutation=True,
        )

        experiment.run()
        results = experiment.results

    A single factor can also be passed directly:

    .. code-block:: python

        experiment = create_experiment_from_models(
            model="Maize.apsimx",
            specifications=factor_spec(
                "Maize.apsimx",
                param_node_location="Sow using a variable rule",
                node_type="Manager",
                param_identifier="Population",
                values=[6, 10, 14],
                rename="population",
            ),
        )
    """

    with ApsimModel(model) as apsim:
        node_info = apsim.has_node(
            param_node_location,
            node_type=node_type,
        )

        if not node_info.get("ok"):
            raise NodeNotFoundError(
                f"Node identifier {param_node_location!r} "
                f"of type {node_type!r} does not exist."
            )

        fullpath = node_info.get("fullpath")

        def _is_manager(node_type_) -> bool:
            """Return True when the supplied node type represents a Manager."""
            if isinstance(node_type_, str):
                return node_type_.lower() == "manager"

            name = getattr(node_type_, "__name__", "")
            return name.lower() == "manager"

        def _knit_param_path(
            *,
            node_id,
            parameter,
            factor_values,
            factor_step,
        ):
            if factor_values is not None:
                if isinstance(factor_values, str):
                    joined_values = factor_values
                else:
                    factor_values = list(factor_values)

                    if not factor_values:
                        raise ValueError(
                            "values must contain at least one factor level."
                        )

                    joined_values = ", ".join(
                        map(str, factor_values)
                    )

            elif bounds is not None:
                if len(bounds) != 2:
                    raise ValueError(
                        "bounds must contain exactly two values: "
                        "(lower_bound, upper_bound)."
                    )

                lower_bound, upper_bound = bounds

                if upper_bound < lower_bound:
                    raise ValueError(
                        "upper bound cannot be less than the lower bound."
                    )

                joined_values = f"{lower_bound} to {upper_bound}"

                if factor_step is not None and factor_step is not False:
                    joined_values += f" step {factor_step}"

            else:
                raise ValueError(
                    "Provide either explicit factor levels using `values` "
                    "or a numeric range using `bounds`."
                )

            if _is_manager(node_type) and "script" not in parameter.lower():
                return (
                    f"[{node_id}].Script.{parameter} = "
                    f"{joined_values}"
                )

            return f"[{node_id}].{parameter} = {joined_values}"

        parameter = param_identifier

        if fullpath:
            node_name = param_node_location.split(".")[-1]
        else:
            node_name = param_node_location

        specification = _knit_param_path(
            node_id=node_name,
            parameter=parameter,
            factor_values=values,
            factor_step=step,
        )

        factor_name = rename or param_identifier.replace(".", "")

        return {factor_name: specification}