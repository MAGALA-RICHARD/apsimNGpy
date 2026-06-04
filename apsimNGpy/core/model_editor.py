from collections.abc import KeysView, ValuesView

from apsimNGpy.core.model_tools import validate_model_obj

from apsimNGpy.core.version_inspector import is_higher_apsim_version
from apsimNGpy.starter.starter import CLR
from model_tools import find_child, ModelTools
from apsimNGpy.core.ce import create_new_cultivar, CreatNewCultivar

Models = CLR.Models
CastHelper = CLR.CastHelper
MissingOption = object()


class ModelLocator:
    def __init__(self, apsim_model):
        self.model = apsim_model

    def find(self, scope, model_type_class, model_name):

        if is_higher_apsim_version():

            lookup_scope = (
                self.model.Simulations
                if model_type_class in {Models.Sobol, Models.Morris}
                else scope
            )

            model_instance = find_child(
                lookup_scope,
                model_type_class,
                model_name,
            )

        else:
            model_instance = (
                self.model.Simulations
                .FindDescendant[model_type_class](model_name)
            )

        if model_instance is None:
            raise ValueError(
                f"Model '{model_name}' "
                f"of type '{model_type_class}' "
                f"was not found."
            )

        model_to_cast = getattr(
            model_instance,
            "Model",
            model_instance)

        return CastHelper.CastAs[model_type_class]( model_to_cast)


class ModelTypeEditors:

    def __init__(self, apsim_model):
        self.model = apsim_model

    def generic(self, model_instance, **kwargs):

        try:
            ModelTools.edit_instance(
                model_instance,
                **kwargs
            )

        except AttributeError as err:

            attrs = self.model.inspect_settable_attributes(
                type(model_instance)
            )

            attrs = "\n".join(attrs)

            raise AttributeError(
                f"{err}\n\nAllowed attributes:\n{attrs}"
            ) from err

    def weather(
            self,
            model_instance,
            verbose=False,
            **kwargs
    ):
        self.model._set_weather_path(
            model_instance,
            param_values=kwargs,
            verbose=verbose,
        )

    def clock(
            self,
            model_instance,
            verbose=False,
            **kwargs
    ):
        self.model._set_clock_vars(
            model_instance,
            param_values=kwargs,
            verbose=verbose,
        )

    def report(
            self,
            model_instance,
            verbose=False,
            **kwargs
    ):
        self.model._set_report_vars(
            model_instance,
            param_values=kwargs,
            verbose=verbose,
        )

    def manager(
            self,
            model_instance,
            scope,
            **kwargs
    ):
        self.model.update_manager(
            scope=scope,
            manager_name=model_instance.Name,
            **kwargs
        )

    def sensitivity(
            self,
            model_instance,
            clear_old=False,
            **kwargs
    ):
        from System.Collections.Generic import List
        from Models.Sensitivity import Parameter

        required = {
            "Name",
            "Path",
            "LowerBound",
            "UpperBound",
        }

        parameters_all = List[Parameter]()

        merged = {}

        if not clear_old:

            for p in model_instance.Parameters:
                merged[p.Path] = {
                    "Name": p.Name,
                    "Path": p.Path,
                    "LowerBound": p.LowerBound,
                    "UpperBound": p.UpperBound,
                }

        for pp in kwargs.get("Parameters", []):

            if not isinstance(pp, dict):
                raise TypeError(
                    f"Expected dict got {type(pp)}"
                )

            missing = required - pp.keys()

            if missing:
                raise ValueError(
                    f"Missing required keys "
                    f"{', '.join(sorted(missing))}"
                )

            merged[pp["Path"]] = pp

        for p in merged.values():

            parameter = Parameter()

            for k, v in p.items():

                if not hasattr(parameter, k):
                    raise AttributeError(
                        f"Invalid parameter attribute '{k}'"
                    )

                setattr(parameter, k, v)

            parameters_all.Add(parameter)

        model_instance.Parameters = parameters_all

        remaining = dict(kwargs)
        remaining.pop("Parameters", None)

        for k, v in remaining.items():

            if not hasattr(model_instance, k):
                raise AttributeError(
                    f"Invalid attribute '{k}'"
                )

            setattr(model_instance, k, v)

    def cultivar(
            self,
            model_instance,
            **kwargs
    ):

        plant = kwargs.get("plant")

        if plant is None:
            raise ValueError(
                "plant is required"
            )

        commands = kwargs.get("commands")

        if commands is None:
            raise ValueError(
                "commands is required"
            )

        rename = (
                kwargs.get("rename")
                or f"e_{plant}_{model_instance.Name}"
        )

        cc = CreatNewCultivar(
            model=self.model,
            template=model_instance.Name,
            plant=plant,
        )

        match commands:

            case dict():

                cc.edit_by_cmd_pairs(
                    name=rename,
                    commands=commands,
                )

            case (
            list()
            | tuple()
            | ValuesView()
            | KeysView()
            ):

                values = kwargs.get(
                    "values",
                    [],
                )

                if not values:

                    cc.edit_by_cmd_iterable(
                        rename,
                        commands,
                    )

                else:

                    cc.edit_by_cmd_values(
                        rename,
                        commands,
                        values,
                    )

            case _:

                raise TypeError(
                    "commands must be "
                    "dict/list/tuple"
                )

        manager_map = (
                kwargs.get("manager_path")
                or kwargs.get("managers")
        )

        cultivar_manager = kwargs.get(
            "cultivar_manager"
        )

        parameter_name = kwargs.get(
            "parameter_name",
            "CultivarName",
        )

        if manager_map is None and cultivar_manager:
            manager_map = {
                cultivar_manager:
                    parameter_name
            }

        if manager_map:

            for manager, param in manager_map.items():
                cc.attach_cultivar(
                    name=rename,
                    manager=manager,
                    param_name=param,
                )


class ModelEditor:

    def __init__(self, apsim_model):

        self.model = apsim_model

        self.locator = ModelLocator(
            apsim_model
        )

        self.editors = ModelTypeEditors(
            apsim_model
        )

    def _resolve_scopes(
            self,
            simulations,
            exclude,
    ):

        if exclude is None:
            exclude = set()

        elif isinstance(exclude, str):
            exclude = {exclude}

        else:
            exclude = set(exclude)

        if (
                simulations == "all"
                or simulations is None
                or simulations == MissingOption
        ):
            simulations = (
                self.model.inspect_model(
                    Models.Core.Simulation,
                    fullpath=False,
                )
            )

            simulations = [
                s
                for s in simulations
                if s not in exclude
            ]

        replacements = (
            self.model.get_replacements_node()
        )

        if isinstance(
                simulations,
                (
                        Models.Core.Simulation,
                        Models.Core.Folder,
                )
        ):

            scopes = [simulations]

        else:

            scopes = self.model.find_simulations(
                simulations
            )

        if replacements is not None:
            scopes.append(replacements)

        unique = []
        seen = set()

        for s in scopes:

            sid = id(s)

            if sid not in seen:
                unique.append(s)
                seen.add(sid)

        return unique

    def edit(
            self,
            model_type,
            model_name,
            simulations="all",
            exclude=None,
            verbose=False,
            clear_old=False,
            **kwargs,
    ):

        model_type_class = (
            validate_model_obj(model_type)
        )

        scopes = self._resolve_scopes(
            simulations,
            exclude,
        )

        for scope in scopes:

            model_instance = (
                self.locator.find(
                    scope,
                    model_type_class,
                    model_name,
                )
            )

            match type(model_instance):

                case Models.Climate.Weather:

                    self.editors.weather(
                        model_instance,
                        verbose=verbose,
                        **kwargs,
                    )

                case Models.Clock:

                    self.editors.clock(
                        model_instance,
                        verbose=verbose,
                        **kwargs,
                    )

                case Models.Manager:

                    self.editors.manager(
                        model_instance,
                        scope,
                        **kwargs,
                    )

                case Models.Report:

                    self.editors.report(
                        model_instance,
                        verbose=verbose,
                        **kwargs,
                    )

                case Models.Sobol | Models.Morris:

                    self.editors.sensitivity(
                        model_instance,
                        clear_old=clear_old,
                        **kwargs,
                    )

                case Models.PMF.Cultivar:

                    self.editors.cultivar(
                        model_instance,
                        **kwargs,
                    )

                case _:

                    self.editors.generic(
                        model_instance,
                        **kwargs,
                    )

        self.model.ran_ok = False

        return self.model
