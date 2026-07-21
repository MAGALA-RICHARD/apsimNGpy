"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
"""

import os
from contextlib import suppress
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Iterable
from typing import Optional, Tuple, Sequence
from typing import Union
from apsimNGpy.starter.starter import CLR
import numpy as np
import pandas as pd
from apsimNGpy.core.core import CoreModel, ModelTools
from apsimNGpy.core_utils.utils import get_array_like

Models = CLR.Models
CastHelper = CLR.CastHelper
from apsimNGpy.core.model_loader import AUTO_PATH
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import find_child_of_class
from apsimNGpy.core.soiler import SoilManager
from apsimNGpy.core_utils.utils import get_array_like
from apsimNGpy import logger, timer, NodeNotFoundError, is_scalar
from apsimNGpy.soils.helpers import soil_water_param_fill
from System.Collections.Generic import List
from System.Collections.Generic import KeyValuePair
from apsimNGpy.core.edit import edit_model_by_name
from apsimNGpy.core.water import (swim_data, layer_struct,
                                  set_swim_lower_bc,
                                  ci, sub_surface_tile_drainage,
                                  geometric_layers, )
from apsimNGpy.core.runner import run_apsim_by_path


# expose some models
# ===================================
Physical = CLR.Models.Soils.Physical
SoilCrop = CLR.Models.Soils.SoilCrop
Organic = CLR.Models.Soils.Organic
LayerStructure = CLR.Models.Soils.LayerStructure
Water = CLR.Models.Soils.Water
Chemical = CLR.Models.Soils.Chemical


# ===================================================================================================

@dataclass(repr=False, order=False, init=False)
class ApsimModel(CoreModel):
    """
    This class inherits from :class:`~apsimNGpy.core.core.CoreModel` and extends its capabilities.

    High-level methods/attributes flow between the :class:`~apsimNGpy.core.apsim.ApsimModel` class and its parents, and child class is illustrated below:

    .. code-block:: python

      'PlotManager' ---> 'CoreModel' ---> 'ApsimModel' ---> 'ExperimentManager'

    Class Roles
    -----------
    - :class:`~apsimNGpy.core.plotmanager.PlotManager`. Produces visual outputs from model results.
      (Not exposed in the public API reference.)
    - :class:`~apsimNGpy.core.core.CoreModel`. Provides core methods for running and manipulating APSIM models.
      (Not exposed in the public API reference.)
    - :class:`~apsimNGpy.core.apsim.ApsimModel`. Extends :class:`~apsimNGpy.core.core.CoreModel` with higher-level functionality.
    - :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`. Creates and manages multi-factor experiments from a base scenario.


    Examples
    --------

    .. code-block:: python

        from pathlib import Path
        from apsimNGpy.core.apsim import ApsimModel

        # Initialize a model
        model = ApsimModel(
            'Maize',
            out_path=Path.home() / 'apsim_model_example.apsimx'
        )

        # Run the model
        model.run(report_name='Report')  # 'Report' is the default table name; adjust if needed

        # Get all results
        res = model.results

        # Or fetch a specific report table from the APSIM database
        report_df = model.get_simulated_output('Report')
    """

    def __init__(self, model: Union[os.PathLike, dict, str],
                 out_path: Union[str, Path] = AUTO_PATH,
                 set_wd=None, **kwargs):
        super().__init__(model=model, out_path=out_path, set_wd=set_wd, **kwargs)
        self._model = model
        self.out_path = Path(out_path) if out_path is not AUTO_PATH else AUTO_PATH
        self._extra_kwargs = kwargs or {}

    def __hash__(self):
        """
        Make instances hashable for use in sets, OrderedDicts, or caches.

        Notes
        -----
        - Converts unhashable types (like dicts or Paths) into strings.
        - Includes only stable identifying attributes to avoid collisions.
        """
        model_hash = hash(str(self._model))
        path_hash = hash(str(self.out_path)) if self.out_path else 0
        extras_hash = hash(tuple(sorted(self._extra_kwargs.items())))

        return hash((model_hash, path_hash, extras_hash))

    @timer
    def runner(self, cpu_counts=-1, verbose=True, files=None, to_csv=False, timeout=None):
        file_to_run = get_array_like(files or self.path, container=list)
        ret = run_apsim_by_path(file_to_run, verbose=verbose, n_cores=cpu_counts, to_csv=to_csv, timeout=timeout)
        if ret.returncode == 0:
            self.ran_ok = True

    def append_simulation(self, simulation: Union[Models.Core.Simulation], rename: str = None,
                          payload: Union[dict, tuple, list] = None, fp=False) -> None:
        """
        Add a simulation to the simulation collection.

        Parameters
        ----------
        simulation : Union[str, int]
            Simulation object or identifier to append.

        rename : str
            Unique name assigned to the appended simulation.
            Renaming is expensive as appended simulations grow, since the method first checks if the suggested name exists in the simulation, use external simulation and rename them before insertion

        payload: list[dict] or dict
            list of edits following the edit_model methods that should be applied to the appended simulations. exception is that no ned to specify the simulation

        fp : bool, default=False
            Selects the parameter update method. If `False`, updates are performed via
            `edit_model()`, where parameters are identified by their simulation name,
            model type, and model name. If `True`, updates are performed via
            `set_params()`, where each parameter must be specified using its full path relative to the root of the simulation
            path. All these must be defined properly in the payload argument

        Raises
        ------
        ValueError
            If a simulation with the same name already exists.

        Unlike ``clone_simulation``, the ``append_simulation` method supports appending
        external simulations originating from other ``ApsimModel`` objects,
        making it more flexible for workflows involving cross-model simulation
        transfer and aggregation. In addition to external simulations,
        ``append`` can also duplicate or append existing simulations already
        present within the current ``ApsimModel`` instance.

        .. note::

           This method should not be used with ``ExperimentManager`` objects,
           even though ``ExperimentManager`` inherits from ``ApsimModel``.
           Experiment-related simulation structures are managed differently and
           may produce unintended behavior when appended directly.

           If you want to test 2–10 different model input combinations, this
            method is typically fast because APSIM executes simulations using
            threads internally. However, it may not be efficient for large-scale
            parameter permutations or factorial experiment designs. For such
            workflows, please use ``ExperimentManager`` instead.
        """

        if rename:
            existing_names = {s.Name for s in self}
            rename = rename.strip()
            if rename in existing_names:
                raise ValueError(
                    f"Simulation '{rename}' already exists. "
                    "Choose a unique simulation name."
                )

        # Add simulation
        self.Simulations.Children.Add(simulation)
        if rename:
            simulation.Name = rename
        # Persist changes
        self.save(reload=True)
        if payload:
            payload = get_array_like(payload, container=tuple)

            def edit_with_no_fp(pa):
                pa_copy = dict(pa)
                pa_copy['simulations'] = simulation.Name
                if pa_copy.get('commands') or pa_copy.get('command'):
                    rename_cultivar = f"CultivarFor{simulation.Name}"
                    pa_copy['rename'] = pa_copy.get('rename') or rename_cultivar
                    self.edit_model(**pa_copy)

            if not fp:
                _ = [edit_with_no_fp(p) for p in payload]
            else:
                def re_organize(pyload):
                    pl = dict(pyload)
                    if pyload.get('commands') or pyload.get('command'):
                        _rename_cultivar = f"CultivarFor{simulation.Name}"
                        pl['rename'] = pyload.get('rename') or _rename_cultivar
                    node_p = pyload['path'].split(".")
                    node_p[2] = simulation.Name
                    nfp = '.'.join(node_p).strip()
                    if 'Replacements' not in node_p:
                        # node_in = get_node_by_path(self.Simulations, nfp, cast_as='auto')
                        pl['path'] = nfp
                        return pl
                    return pl

                def edit_with_fp(pa):
                    pa['simulations'] = simulation.Name
                    pld = re_organize(pa)
                    self.set_params(**pld)

                _ = [edit_with_fp(p) for p in payload]

    def evaluate_simulated_output(
            self,
            ref_data: pd.DataFrame,
            table,
            ref_data_col,
            target_col,
            index_col,
            expr=None,
    ):
        """
        Deprecated wrapper for :meth:`evaluate`.

        This method is maintained for backward compatibility and will be
        removed in a future release. Please use :meth:`evaluate` instead.
        """
        import warnings
        warnings.warn(
            "`evaluate_simulated_output` is deprecated and will be removed "
            "in a future version. Please use `evaluate` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.evaluate(
            ref_data=ref_data,
            table=table,
            ref_data_col=ref_data_col,
            target_col=target_col,
            index_col=index_col,
            expr=expr,
        )

    def edit_model_by_name(self, model_type, model_name, simulations=None, clear_old=False, **kwargs):
        edit_model_by_name(self, model_type, model_name, simulations=simulations, clear_old=clear_old, **kwargs)

    def evaluate(
            self,
            ref_data: pd.DataFrame,
            table,
            ref_data_col,
            target_col,
            index_col,
            expr=None,
            verbose=True
    ):
        """
        Evaluate APSIM-simulated output against a reference (observed) dataset.

        This method compares observed data (``ref_data``) with simulated predictions
        obtained either from a provided :class:`pandas.DataFrame` or from an APSIM
        output table name. When a table name is supplied, simulated output is retrieved
        via :meth:`~apsimNGpy.core.apsim.ApsimModel.get_simulated_output`.


        .. versionadded:: 0.39.12.21

        Parameters
        ----------
        ref_data : pandas.DataFrame
            Reference (observed) dataset against which APSIM simulations are evaluated.
            Must contain the column specified by ``ref_data_col`` and the join/index
            column.

        table : str or pandas.DataFrame
            Simulated data source. One of the following:

            - **str**: Name of an APSIM output table. Simulated output is retrieved
              internally using
              :meth:`~apsimNGpy.core.apsim.ApsimModel.get_simulated_output`.
            - **pandas.DataFrame**: A DataFrame containing simulated predictions
              directly.

            Any other type will raise a :class:`TypeError`.

        ref_data_col : str
            Column name in ``ref_data`` containing observed values.

        target_col : str
            Column name in the simulated dataset containing predicted values to be
            compared against observations.

        index_col : str or list[str]
            Column(s) used to align observed and simulated data (e.g., year, date,
            sample ID). Both datasets must contain these column(s).

        expr : callable or str, optional
            Optional transformation or expression applied prior to evaluation.
            May be a callable, a string expression, or ``None``.
            Default is ``None``.
        verbose: bool
           If ``True``, prints all results on for each metric on the console

        Returns
        -------
        dict or pandas.DataFrame
            Output returned by ``final_eval``, typically containing evaluation metrics
            such as RMSE, RRMSE, WIA, CCC, ME, and bias.

        Raises
        ------
        TypeError
            If ``table`` is neither a string nor a pandas DataFrame.

        Notes
        -----
        This method streamlines comparison between observed and simulated APSIM outputs
        during model calibration and performance assessment. It supports both direct
        DataFrame input and automatic retrieval of APSIM report tables, enabling a
        consistent and reproducible evaluation workflow.

        Examples
        ----------
        Evaluate simulated yield against observed data using a report database table generated by APSIM

        .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.tests.unittests.test_factory import obs

            model = ApsimModel("Maize")

            # Add a common index column for joining simulated and observed data
            model.add_report_variable(
                variable_spec='[Clock].Today.Year as year',
                report_name='Report'
            )

            metrics = model.evaluate_simulated_output(
                ref_data=obs,
                table="Report",
                index_col="year",
                target_col="Yield",
                ref_data_col="observed"
            )

        Example output:

        .. code-block:: none

            Model Evaluation Metrics
            -----------------------
            RMSE    : 0.0003
            MAE     : 0.0003
            MSE     : 0.0000
            RRMSE   : 0.0000
            bias    : -0.0001
            ME      : 1.0000
            WIA     : 1.0000
            R2      : 1.0000
            CCC     : 1.0000
            SLOPE   : 1.0000

        .. versionadded:: 0.39.12.21+
        """

        from apsimNGpy.optimizer.problems.back_end import final_eval
        if not isinstance(table, pd.DataFrame) and isinstance(table, str):
            if not self.ran_ok:
                raise RuntimeError('ApsimModel object has not been run')
            predicted = self.get_simulated_output(table)
        elif isinstance(table, pd.DataFrame):
            predicted = table
        else:
            raise TypeError(f"un supported type {type(table)}")
        if not isinstance(ref_data, pd.DataFrame):
            raise TypeError(f"Expected {pd.DataFrame}, got {type(ref_data)}")
        return final_eval(ref_data, predicted, pred_col=target_col, index=index_col,
                          obs_col=ref_data_col, exp=expr, verbose=verbose)

    def set_params(self, params: dict[str, Any] | None = None, **kwargs) -> "ApsimModel":
        """
        Set parameters for the given model by passing a dictionary or keyword arguments.

        Parameters
        ----------
        params : dict, optional
            A dictionary mapping APSIM parameter names to their corresponding values.
            If ``params`` is ``None``, then ``kwargs`` is expected, following the same
            signature as :meth:`~apsimNGpy.core.ApsimModel.edit_model_by_path`.
        **kwargs :
            Additional keyword arguments equivalent to entries in ``params``. These are
            interpreted according to the same signature as
            :meth:`~apsimNGpy.core.ApsimModel.edit_model_by_path`.

        Returns
        -------
        self : ApsimModel
            Returns the same instance for method chaining.
        Raises
        -------
        TypeError if any of the above arguments does not resolve to a dictionary. Other errors maybe raised gracefully
          by :meth:`~apsimNGpy.core.ApsimModel.edit_model_by_path`.

        Notes
        -----
        This flexible design allows users to supply parameters either as standard
        keyword arguments or as dictionary objects.
        The dictionary-based approach is particularly useful when working with
        **JSON-compatible data structures**, as commonly required during large-scale
        model optimization, calibration, or parameter sensitivity analysis workflows.
        In such cases, parameter sets can be programmatically generated, serialized,
        and reused without manual modification of code.
        """
        pa = params or kwargs

        # Final type safety check
        if not isinstance(pa, dict):
            raise TypeError("Resolved parameters must be a dictionary.")

        # the rest of errors are handled by edit_model_path gracefully

        # Apply to model
        if 'values' in pa and 'commands' in pa:
            cmds, vals = pa['commands'], pa['values']
            if len(cmds) != len(vals):
                raise ValueError(" values and commands must be equal")
            pa['commands'] = dict(zip(cmds, vals))

        self.edit_model_by_path(**pa)
        self.save()
        return self

    def get_soil_from_web(self,
                          simulations: Union[str, tuple, None] = None,
                          *,
                          # location / data source
                          lonlat: Optional[Tuple[float, float]] = None,
                          soil_series: Optional[str] = None,
                          # layer/thickness controls
                          thickness_sequence: Optional[Sequence[float]] = 'auto',
                          thickness_value: int = None,
                          max_depth: Optional[int] = 2400,
                          n_layers: int = 10,
                          thinnest_layer: int = 50,
                          thickness_growth_rate: float = 1.5,  # unit less
                          # which sections to edit
                          edit_sections: Optional[Sequence[str]] = None,
                          # attach any missing nodes before editing
                          attach_missing_sections: bool = True,
                          additional_plants: tuple = None,
                          source='isric',
                          top_finert=0.65,
                          top_fom=1000,
                          top_fbiom=0.04,
                          fom_cnr=40,
                          soil_cnr=12,
                          swcon=0.3,
                          top_urea=0,
                          top_nh3=0.5,
                          top_nh4=0.05,
                          adjust_dul: bool = True, **soil_kwargs):
        """
        Download soil profiles for a given location and populate the APSIM NG
        soil sections in the current model.

        This method updates the target Simulation(s) in-place by attaching a Soil node
        (if missing) and writing section properties from the downloaded profile.

        Parameters
        ----------
        simulation : str | sequence[str] | None, default None
            Target simulation name(s). If ``None``, all simulations are updated.

        lonlat : tuple[float, float] | None
            Location for SSURGO download, as ``(lon, lat)`` in decimal degrees
            (e.g., ``(-93.045, 42.012)``).

        soil_series : str | None, optional
            Optional component/series filter. If ``None``, the dominant series
            by area is used. If a non-existent series is supplied, an error is raised.

        thickness_sequence : sequence[float] | str | None, default "auto"
            Explicit layer thicknesses (mm). If ``"auto"``, thicknesses are generated
            from the layer controls (e.g., number of layers, growth rate, thinnest layer,
            and ``max_depth``). If ``None``, you must provide ``thickness_value`` and
            ``max_depth`` to construct a uniform sequence.

        thickness_value : int | None, optional
            Uniform thickness (mm) for all layers. Ignored if ``thickness_sequence`` is
            provided; used only when ``thickness_sequence`` is ``None``.

        max_depth : int, default 2400
            Maximum soil depth (mm) to cover with the thickness sequence.

        edit_sections : sequence[str], optional
            Sections to edit. Default:
            ``("physical", "organic", "chemical", "water", "water_balance", "solutes", "soil_crop", "meta_info")``.
            Note: if sections are edited with differing layer counts, APSIM may error at run time.

        attach_missing_sections : bool, default True
            If ``True``, create and attach missing section nodes before editing.

        additional_plants : sequence[str] | None, optional
             Plant names for which to create/populate ``SoilCrop`` entries (e.g., to set KL/XF).

        adjust_dul : bool, optional
            If ``True``, adjust layer values where ``SAT`` exceeds ``DUL`` to prevent APSIM runtime errors.
        n_layers: int
           number of soil layers to generate a soil profile.
        source : str, optional default='isric'
           the database source to use. Currently only 'isric' and 'ssurgo' are supported
        top_finert : float, optional
            Fraction of inert organic matter (FInert) in the surface soil layer.
            Default is 0.88.
        top_fom : float, optional
            Fresh organic matter (FOM) content of the surface soil layer
            in kg C ha⁻¹. Default is 180.
        top_fbiom : float, optional
            Fraction of microbial biomass carbon (FBiom) in the surface layer.
            Default is 0.04.
        fom_cnr : float, optional
            Carbon-to-nitrogen ratio (C:N) of fresh organic matter.
            Default is 40.
        soil_cnr : float, optional
            Carbon-to-nitrogen ratio (C:N) of soil organic matter (humic pool).
            Default is 12.
        swcon : float, optional
            Soil water conductivity parameter controlling water extraction
            rate by roots (APSIM `SWCON`). Typical values range from 0.1–1.
            Default is 0.3.
        top_urea : float, optional
            Initial urea nitrogen in the surface soil layer (kg N ha⁻¹).
            Default is 0.
        top_nh3 : float, optional
            Initial nitrate nitrogen (NO₃⁻–N) in the surface soil layer
            in kg N ha⁻¹. Default is 0.5.
        top_nh4 : float, optional
            Initial ammonium nitrogen (NH₄⁺–N) in the surface soil layer
            in kg N ha⁻¹. Default is 0.05.

        soil_kwargs:
        Additional keyword arguments to pass to the function related to soil water module such as the WinterCona.
        See the following list:

         winter_cona : float, optional
            Drying coefficient for stage 2 soil water evaporation in winter
            (APSIM: ``WinterCona``).
            Scalar parameter.
        psi_dul : float, optional
            Matric potential at drained upper limit (DUL), in cm
            (APSIM: ``PSIDul``).
            Scalar parameter.
        depth : list of str, optional
            Soil layer depth intervals expressed as strings
            (e.g., ``"0-150"``, ``"150-300"``).
            Layered parameter.
        diffus_slope : float, optional
            Effect of soil water storage above the lower limit on soil water
            diffusivity (mm) (APSIM: ``DiffusSlope``).
            Scalar parameter.
        diffus_const : float, optional
            Constant in soil water diffusivity calculations
            (APSIM: ``DiffusConst``).
            Scalar parameter.
        k_lat : float, optional
            Lateral hydraulic conductivity parameter for catchment flow
            (APSIM: ``KLAT``).
            Scalar parameter.
        pore_interaction_index : float, optional
            Pore interaction index controlling soil water movement
            (APSIM: ``PoreInteractionIndex``).
            Scalar parameter.
        discharge_width : float, optional
            Basal width of the downslope boundary of the catchment used in
            lateral flow calculations (m) (APSIM: ``DischargeWidth``).
            Scalar parameter.
        swcon : list of float, optional
            Soil water conductivity parameter controlling root water uptake
            (APSIM: ``SWCON``).
            Layered parameter (one value per soil layer).
        cn_cov : float, optional
            Fractional cover at which maximum runoff curve number reduction
            occurs (APSIM: ``CNCov``).
            Scalar parameter.
        catchment_area : float, optional
            Catchment area used for runoff and lateral flow calculations (m²)
            (APSIM: ``CatchmentArea``).
            Scalar parameter.
        water : dict, optional
            Nested water balance configuration block
            (APSIM: ``Water``).
            Dictionary parameter.
        salb : float, optional
            Fraction of incoming solar radiation reflected by the soil surface
            (albedo) (APSIM: ``Salb``).
            Scalar parameter.
        winter_u : float, optional
            Cumulative soil water evaporation required to complete stage 1
            evaporation during winter (APSIM: ``WinterU``).
            Scalar parameter.
        runoff : float, optional
            Runoff fraction or runoff scaling factor
            (APSIM: ``Runoff``).
            Scalar parameter.
        cn2_bare : int or float, optional
            Runoff curve number for bare soil under average moisture conditions
            (APSIM: ``CN2Bare``).
            Scalar parameter.
        winter_date : str, optional
            Calendar date marking the switch to winter parameterization
            (APSIM: ``WinterDate``), e.g. ``"1-Apr"``.
            Scalar string parameter.
        potential_infiltration : float, optional
            Potential infiltration limit used in runoff calculations
            (APSIM: ``PotentialInfiltration``).
            Scalar parameter.
        summer_date : str, optional
            Calendar date marking the switch to summer parameterization
            (APSIM: ``SummerDate``), e.g. ``"1-Nov"``.
            Scalar string parameter.
        sw_mm : float, optional
            Total soil water storage (mm) if explicitly specified
            (APSIM: ``SWmm``).
            Scalar parameter.
        summer_cona : float, optional
            Drying coefficient for stage 2 soil water evaporation in summer
            (APSIM: ``SummerCona``).
            Scalar parameter.
        summer_u : float, optional
            Cumulative soil water evaporation required to complete stage 1
            evaporation during summer (APSIM: ``SummerU``).
            Scalar parameter.
        precipitation_interception : float, optional
            Fraction or amount of precipitation intercepted before reaching
            the soil surface (APSIM: ``PrecipitationInterception``).
            Scalar parameter.

        Returns
        -------
        self
            The same instance, to allow method chaining.

        Raises
        ------
        ValueError
            - ``thickness_sequence`` provided with any non-positive value(s).
            - ``thickness_sequence`` is ``None`` **and** ``thickness_value`` is ``None``.
            - Units mismatch or inconsistency between ``thickness_value`` and ``max_depth``.
            - lonlat do not match the source database specified. For example, if coordinates are outside the USA, but a source is source.
             for worldwide soil request use source = isric
     Examples:
     ------------------

     .. code-block python

            with ApsimModel("Maize") as model:
            datastore = Path(model.datastore)
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report',
                                      simulations='Simulation')
            model.get_soil_from_web(simulations=None, lonlat=(-93.9937, 40.4842), thinnest_layer=100,
                                    adjust_dul=True,

                                    summer_date='1-May', precipitation_interception=13.5, winter_date='1-nov',
                                    source='isric')

        """

        # Default: edit all known sections
        if not edit_sections:
            edit_sections = (
                "physical", "organic", "chemical", "water", "water_balance", "solutes", "soil_crop", 'meta_info')

        # Helper to ensure a section exists and is attached under the Soil node
        def _ensure_section(sim, cls):
            node = find_child_of_class(sim, child_class=cls)
            if node:
                return node
            if not attach_missing_sections:
                return None
            # find Soil parent, then attach
            soil_parent = find_child_of_class(sim, child_class=Models.Soils.Soil)
            if not soil_parent:
                # If there is no Soil node at all, create and attach one
                soil_parent = Models.Soils.Soil()
                # Attach Soil to the Simulation (APSIM NG usually allows Children.Add)
                if hasattr(sim, "Children"):
                    sim.Children.Add(soil_parent)
                else:
                    logger.warning("Simulation has no Children collection; cannot attach Soil node.")
                    return None
            section = cls()
            soil_parent.Children.Add(section)
            return section

        simulation_name = simulations  # for backward compatibility
        simulations = self.find_simulations(simulations=simulations)
        for simulation in simulations:
            # Pre-attach requested sections (avoids "created but unreachable" inside editor)
            if attach_missing_sections:
                # Core soil sections
                want = {
                    "physical": Models.Soils.Physical,
                    "organic": Models.Soils.Organic,
                    "chemical": Models.Soils.Chemical,
                    "water": Models.Soils.Water,
                    "water_balance": Models.WaterModel.WaterBalance,
                    # soil_crop is handled below because it's usually a child under Physical
                }
                for key, typ in want.items():
                    if key in edit_sections:
                        _ensure_section(simulation, typ)

                # Ensure SoilCrop path: Soil -> Physical -> SoilCrop
                if "soil_crop" in edit_sections:
                    phys = find_child_of_class(simulation, child_class=Models.Soils.Physical) or _ensure_section(
                        simulation, Models.Soils.Physical
                    )
                    if phys is not None:
                        sc = find_child_of_class(phys, child_class=Models.Soils.SoilCrop)
                        if not sc:
                            phys.Children.Add(Models.Soils.SoilCrop())

            # Build the manager (cached profile happens inside)

            mgr = SoilManager(
                simulation_model=simulation,
                lonlat=lonlat,
                soil_tables=None,
                soil_series=soil_series,
                thickness_sequence=thickness_sequence,
                thickness_value=thickness_value,
                max_depth=max_depth,
                n_layers=n_layers,
                thinnest_layer=thinnest_layer,
                thickness_growth_rate=thickness_growth_rate,
                soil_profile=None,
                source=source,
                top_finert=top_finert,
                top_fom=top_fom,
                top_fbiom=top_fbiom,
                fom_cnr=fom_cnr,
                soil_cnr=soil_cnr,
                top_urea=top_urea,
                top_nh3=top_nh3,
                top_nh4=top_nh4,
                swcon=swcon

            )
            add_crop = additional_plants if additional_plants is not None else ()
            # Do edits
            mgr.edit_meta_info()
            if "physical" in edit_sections:
                mgr.edit_soil_physical()
            if "organic" in edit_sections:
                mgr.edit_soil_organic()
            if "chemical" in edit_sections:
                mgr.edit_soil_chemical()
            if "water" in edit_sections:
                mgr.edit_soil_initial_water()
            if "water_balance" in edit_sections:
                mgr.edit_soil_water_balance()
            if "solutes" in edit_sections:
                mgr.edit_solute_sections()
            if "soil_crop" in edit_sections:
                mgr.edit_soil_crop(crops_in=add_crop)
        if adjust_dul:
            self.adjust_dul(simulation_name)
        if soil_kwargs:
            soil_water_param_fill(self, **soil_kwargs)
        return self

    @timer
    def remove_node(self, node):
        """
        Removes a node from the Simulating tree
        @param node: str or Models object
        @return: True if cleared successfully
        """
        name = None
        if isinstance(node, str):
            fpath = node
            name = fpath.split('.')[-1]
        elif hasattr(node, 'FullPath'):
            fpath = node.FullPath
        else:
            raise TypeError(f'type {type(node)} is not supported. Please try a valid str path or Models object')
        fpath = fpath.split('.')[:-1]  # removes the current node
        parent_parent = '.'.join(fpath)  # what is left is the parent path
        parent_node = get_node_by_path(self.Simulations, node_path=parent_parent, cast_as='auto')
        if isinstance(node, str):
            for i_node in parent_node.Children:
                if i_node.Name == name:
                    parent_node.Children.Remove(i_node)
                    break
            else:

                raise RuntimeError(f'Something really went wrong with the deleting {node}')
        else:
            parent_node.Children.Remove(node)
        return True

    def clear_water_model(self, wat_model, sim_obj):
        """
        If switching to swim3, we clear the water balance model and other wise
        @param sim_obj: simulations
        @param wat_model: str
        @return: None
        """
        wat_model = wat_model.lower()

        match wat_model:
            case 'swim3':
                model_type = Models.Soils.Swim3
                sw = self.inspect_model(model_type=model_type, scope=sim_obj)
            case 'soil water' | 'water balance' | 'water_balance':
                model_type = Models.WaterModel.WaterBalance
                sw = self.inspect_model(model_type=model_type, scope=sim_obj)
            case _:
                raise NotImplementedError(f'{wat_model} is not supported try any of swim3, or soil water')

        _ = [self.remove_node(i) for i in sw]

    def _get_simulations(self, simulations: Union[str, None, Iterable] = None):
        if simulations is None:
            return [i for i in self]
        if is_scalar(simulations):
            simulations = {simulations}
        return [s for s in self if s.Name in simulations]

    def _create_swim3(self, simulations=None, layer_structure_thickness=None, swim3_params=None,
                      water_clearance: callable = None):
        if isinstance(layer_structure_thickness, set):
            raise TypeError("layer thickness must be an indexed object not a set")
        from apsimNGpy.core.water import nh4, no3, urea
        sims = self._get_simulations(simulations)
        if layer_structure_thickness is not None:
            layer_struct['Thickness'] = list(layer_structure_thickness)
        for sim in sims:
            if callable(water_clearance):
                water_clearance(wat_model='water balance', sim_obj=sim)
            else:
                raise ValueError('Water clearance must be callable got {}'.format(type(water_clearance)))
            zone = self.inspect_model(model_type=Models.Core.Zone, scope=sim)
            soil_path = self.inspect_model(model_type=Models.Soils.Soil, scope=sim)[0]
            # expect one zone per simulation
            zone_path = zone[0]

            self.add_new_model(parent_type=Models.Core.Zone,
                               replace=True,
                               parent_identifier=zone_path, source=set_swim_lower_bc)
            soil_node = get_node_by_path(sim, node_path=soil_path, cast_as='auto')
            phys = self.inspect_model_parameters_by_path(path=f"{soil_node.FullPath}.Physical",
                                                         parameters=['Thickness', 'Depth'])
            NO3 = self.inspect_model_parameters_by_path(path=f"{soil_node.FullPath}.NO3",
                                                        parameters=['Thickness', 'InitialValues'])
            NH4 = self.inspect_model_parameters_by_path(path=f"{soil_node.FullPath}.NH4",
                                                        parameters=['Thickness', 'InitialValues'])
            TH = list(phys['Thickness'])
            if layer_structure_thickness is None:
                layer_struct['Thickness'] = geometric_layers(max_depth=int(sum(TH)), max_thickness=10, growth=1.1)
            len_g = len(phys['Thickness'])
            fip = [1.0] * len_g
            CI, urea, nh4, no3 = dict(ci), dict(urea), dict(nh4), dict(no3)
            CI['FIP'] = fip
            CI['Exco'] = [0.0] * len_g
            CI['Thickness'] = TH
            no3['Thickness'] = TH
            no3['InitialValues'] = list(NO3['InitialValues'])
            no3['Exco'] = [0.0] * len_g
            no3['FIP'] = fip
            nh4['FIP'] = fip
            nh4['Exco'] = [1.0] * len_g
            nh4['Thickness'] = TH
            nh4['InitialValues'] = list(NH4['InitialValues'])
            urea['Thickness'] = TH
            urea['InitialValues'] = [0.0] * len_g
            urea['FIP'] = fip
            urea['Exco'] = [0.0] * len_g

            CI['InitialValues'] = [0.0] * len_g

            if swim3_params is not None and isinstance(swim3_params, dict):
                swim_user_params, swim_defaults = dict(swim3_params), dict(swim_data)
                if len(swim_user_params) == 0:
                    logger.warning(
                        f'swim_model_parameters dict provided is empty, switching to all defaults')
                invalid = []
                for k, v in swim_user_params.items():
                    if k not in swim_defaults.keys():
                        invalid.append(k)
                if invalid:
                    swi = dict(swim_defaults)
                    # $type carries no meaning to the user, because if changed, the model may not be configured as required
                    swi.pop('$type', None)
                    valid_keys = ", ".join(swi.keys())
                    val = 'are not valid SWIM3 parameters.' if len(invalid) > 1 else 'is not a valid SWIM3 parameter.'
                    raise ValueError(f'swim_model_parameters: {invalid} {val}'
                                     f' valid parameters are: {valid_keys}')
                swim_model_params = swim_defaults | swim_user_params

            elif swim3_params is None:
                swim_model_params = dict(swim_data)

            else:
                raise TypeError(
                    "swim3_params must be either a dictionary containing "
                    "SWIM3 parameter overrides or None to use the default "
                    "SWIM3 configuration."
                )
            for obj in (layer_struct, swim_model_params, CI, no3, nh4, urea):
                self.add_new_model(parent_type=Models.Soils.Soil,
                                   replace=True,
                                   parent_identifier=soil_node.FullPath, source=obj)

    def switch_wm_to_swim3(
            self,
            layer_structure_th=None,
            simulations=None,
            ss_tile_drainage=None,
            swim_model_params=None
    ):
        """
        Replace the existing soil water balance model with the SWIM3 module.

        This method removes or clears the current water balance model and
        inserts a SWIM3 (`Models.Soils.Swim3`) node into the selected
        APSIM simulation(s). Optionally, subsurface tile drainage parameters
        can also be added to the SWIM3 configuration.

        SWIM3 is a physically based soil water model that solves Richards'
        equation and supports advanced hydrological processes including:

        - Saturated and unsaturated flow
        - Water table dynamics
        - Subsurface tile drainage
        - Capillary rise
        - Lateral flow

        Parameters
        ----------
        layer_structure_th : list[int] or list[float], optional
            Soil layer thickness structure (mm) used when constructing
            the SWIM3 profile. If `None`, the existing soil profile
            thicknesses are used a geometric mathematical structure that is based on the deepest layer of the soil profile.

        simulations : str or list[str], optional
            Name or list of APSIM simulation nodes where the water model
            should be replaced with SWIM3. If `None`, the operation is
            applied to all simulations in the current APSIM model. Use ``self.inspect_model('Simulation')`` to see a list of available simulations

        ss_tile_drainage : None, str (auto) or dict, default=False
            Configure subsurface tile drainage for SWIM3.

            If `None`, no subsurface drainage node is added and SWIM3
            is configured using its internal/default drainage behavior.

            If `auto`, a default subsurface tile drainage configuration
            is added using the following parameters::

                {
                    "DrainDepth": 1200.0,
                    "DrainSpacing": 40000.0,
                    "DrainRadius": 40000.0,
                    "Klat": 50.0,
                    "ImpermDepth": 2850.0,
                    "Open": True,
                    "Name": "SwimSubsurfaceDrain"
                }

            If a dictionary is supplied, the user-defined parameters are
            merged with the default drainage configuration above. Any keys
            provided by the user override the corresponding default values,
            while unspecified parameters retain their defaults.

            Example::

                ss_tile_drainage = {
                    "DrainDepth": 1000,
                    "DrainSpacing": 30000
                }

            results in::

                {
                    "DrainDepth": 1000,
                    "DrainSpacing": 30000,
                    "DrainRadius": 40000.0,
                    "Klat": 50.0,
                    "ImpermDepth": 2850.0,
                    "Open": True,
                    "Name": "SwimSubsurfaceDrain"
                }
        swim_model_params: dict or None. Default is None.
            If auto, the following parameters are used.
            {"Salb": 0.13,                  "CN2Bare": 50.0,                "CNRed": 20.0,
            "CNCov": 0.8,                  "KDul": 1.0,                    "PSIDul": -100.0,
            "VC": True,                    "DTMin": 0.0,                   "DTMax": 60.0,
            "MaxWaterIncrement": 5.0,      "SpaceWeightingFactor": 0.0,    "SoluteSpaceWeightingFactor": 1.0,
            "Dis": 0.0,                    "Disp": 1.0,                    "A": 2.0,
            "DTHC": 0.1,                   "DTHP": 2.0,                    "vcon1": 7.28E-09,
            "vcon2": 7.26E-07,             "eo_time": "06:00",             "eo_durn": 720.0,
            "default_rain_time": "00:00",  "default_rain_duration": 720.0, "Diagnostics": True,}
            If a dictionary is supplied, the user-defined parameters are
            merged with the default SWIM3 configuration above. Any keys
            provided by the user override the corresponding default values,
            while unspecified parameters retain their defaults.

        Returns
        -------
        None
            The APSIM model is modified in-place and saved to disk.

        Notes
        -----
        This method internally calls :meth:`_create_swim3` to generate
        the SWIM3 node before optionally adding a subsurface tile drainage
        configuration.

        The parameters of the SWIM3 supplied via ss_tile_drainage are case-sensitive and follows APSIM internal naming convention

        The SWIM3 node must exist before tile drainage components are added.

        When tile drainage is enabled, users should ensure that:

        - ``ImpermDepth > DrainDepth``
        - Soil profile depth exceeds the drain depth
        - Saturated hydraulic conductivity (`KS`) values are realistic

        Improper configuration may result in SWIM numerical instability
        or APSIM runtime errors.

        A layer structure is also added automatically using geometric mathematical operations, based on the lower soil depth

        Examples
        --------
        Replace the default water model with SWIM3::

            model.switch_wm_to_swim3()

        Add SWIM3 with default tile drainage settings::

            model.switch_wm_to_swim3(ss_tile_drainage=True)

        Add SWIM3 with custom tile drainage parameters::

            model.switch_wm_to_swim3(
                ss_tile_drainage={
                    "DrainDepth": 1200,
                    "DrainSpacing": 30000,
                    "ImpermDepth": 3000
                },
                swim_model_params = {"eo_time": "05:00", "eo_durn": 600.0,
                     "default_rain_time": "00:00",
                      "default_rain_duration": 500.0,
                       "Diagnostics": False
            }
            )
        Add SWIM3 with with custom swim model configuration parameters::

             model.switch_wm_to_swim3(
                    ss_tile_drainage={
                        "DrainDepth": 1200,
                        "DrainSpacing": 30000,
                        "ImpermDepth": 3000
                    }
                )

        See Also
        --------
        _create_swim3 : Create and configure a SWIM3 node.
        add_new_model : Insert new APSIM model components dynamically.

        References
        ----------
        Verburg, K., Ross, P. J., & Bristow, K. L. (1996).
        SWIM v2.1 User Manual.

        APSIM Initiative.
        SWIM3 soil water model documentation.

        """
        self._create_swim3(simulations=simulations, layer_structure_thickness=layer_structure_th,
                           water_clearance=self.clear_water_model, swim3_params=swim_model_params)
        # it has to be after creating the swim3 node above
        if ss_tile_drainage is not None:
            ss_default = dict(sub_surface_tile_drainage)
            if ss_tile_drainage == 'auto':
                in_data = ss_default
            elif isinstance(ss_tile_drainage, dict):
                ss_user = dict(ss_tile_drainage)
                if len(ss_user) == 0:
                    logger.warning(
                        f'ss_tile_drainage {ss_user} dict provided is empty, switching to all defaults')
                invalid = []

                for k, v in ss_user.items():
                    if k not in ss_default:
                        invalid.append(k)
                if invalid:
                    ss = dict(ss_default)
                    ss.pop('$type', None)
                    # $type carries no meaning to the user, because if changed, the model may not be configured as required
                    valid_keys = ", ".join(ss.keys())
                    raise ValueError(
                        f"Unknown key '{','.join(invalid)}' in 'ss_tile_drainage'. "
                        f"Valid keys are: {valid_keys}."
                    )
                in_data = ss_default | ss_user
            else:
                raise TypeError(f"Value `TypeError` Error for ss_tile_drainage: expected None,"
                                f" auto or a dict got a {type(ss_tile_drainage).__name__} instead")

            self.add_new_model(parent_type='Models.Soils.Swim3', parent_identifier=swim_data['Name'],
                               source=in_data,
                               replace=True)
        self.save()

    def __exit__(self, exc_type, exc, tb):
        db_flag = getattr(self, "db", True)
        csv_flag = getattr(self, "csv", True)
        path = Path(self.path)
        # Common sidecars we may want to clean
        _db = path.with_suffix('.db')
        bak = path.with_suffix('.bak')
        db_wal = path.with_suffix('.db-wal')
        db_shm = path.with_suffix('.db-shm')

        clean_candidates = {bak, db_wal, db_shm, path}
        if csv_flag:
            reps = self.inspect_model(Models.Report, fullpath=False) or {}
            with suppress(TypeError):
                clean_candidates.update({path.with_suffix(f'.{rep}.csv') for rep in reps})
        # Optionally include the SQLite .db sidecar (force GC on pythonnet/.NET first)
        if db_flag:
            # with suppress(Exception, CLR.System.Exception):
            #    # CLR.System.GC.Collect()
            #    pass
            #     #CLR.System.GC.WaitForPendingFinalizers()
            clean_candidates.add(_db)

        # Remove files if present
        for candidate in clean_candidates:
            with suppress(PermissionError):
                candidate.unlink(missing_ok=True)

    def clone_simulation(self, rename: str, base_simulation: Union[int, str] = 0) -> bool:
        """
        Clone an existing simulation and assign it a new name.

        The cloned simulation is appended to the simulations collection and can
        subsequently be modified using methods such as ``edit_model``.

        Parameters
        ----------
        rename : str
            Name to assign to the cloned simulation.
        base_simulation : int or str, default is the first simulation at index 0
            Identifier of the simulation to clone. This can be either:
            - Index (int) of the simulation
            - Name (str) of the simulation

        Returns
        -------
        bool
            True if the simulation was successfully cloned and saved.

        Raises
        ------
        ValueError
            If the base simulation cannot be found or `rename` is invalid.

        Notes
        -----
        The cloned simulation is added to the end of the simulations list.
        Ensure that `rename` is unique to avoid ambiguity in subsequent operations.


        Examples
        --------
        .. code-block:: python

            from apsimNGpy import Apsim

            apsim = Apsim()
            model = apsim.ApsimModel("Maize")

            # Inspect existing simulations
            model.inspect_model("Simulation", fullpath=False)
            # Output: ['Simulation']

            # Clone simulation
            model.clone_simulation(rename="new_sim", base_simulation=0)

            model.inspect_model("Simulation", fullpath=False)
            # Output: ['Simulation', 'new_sim']

            # Modify fertilization amounts
            model.edit_model(
                model_type="Models.Manager",
                model_name="Fertilise at sowing",
                simulations="new_sim",
                Amount=300,
            )

            model.edit_model(
                model_type="Models.Manager",
                model_name="Fertilise at sowing",
                simulations="Simulation",
                Amount=0,
            )

            # Add report variables
            model.edit_model(
                model_type="Models.Report",
                model_name="Report",
                variable_spec=[
                    "[Fertilise at sowing].Script.Amount as amount",
                    "[Simulation].Name as simulations",
                ],
            )

            # Run simulation
            model.run()
            data = model.results

            # Group by simulation
            data.groupby("simulations")["Yield"].mean()
            # Expected:
            # Simulation    1747.866065
            # new_sim       5547.565724

            # Group by fertilizer amount (should match above)
            data.groupby("amount")["Yield"].mean()
            # Expected:
            # 0.0      1747.866065
            # 300.0    5547.565724
       """
        if not rename or not isinstance(rename, str):
            raise ValueError("`rename` must be a non-empty string.")

        sim = self[base_simulation]
        if sim is None:
            raise ValueError(f"Simulation '{base_simulation}' not found.")

        # Add clone
        ModelTools.ADD(sim, self.Simulations)

        # Retrieve last added simulation (the clone)
        if rename:
            sim.Name = rename

        self.save()
        return True

    @staticmethod
    def _get_node(self, node_id, node_type):
        if (node_type == "Simulations"
                or node_type == CLR.Models.Core.Simulations
                or node_type == "Models.Core.Simulations"):
            return self.Simulations

        # name identifies the node
        if node_id in self.inspect_model(node_type, fullpath=False):
            node_loc = ModelTools.find_child(self.Simulations, child_class=node_type, child_name=node_id)
            # full path identifies the node
        elif node_id in self.inspect_model(node_type, fullpath=True):
            node_loc = get_node_by_path(self.Simulations, node_path=node_id, cast_as='auto')
        else:
            # node is identified by either name or full path but does not exist
            raise NodeNotFoundError(f"suggested node type '{node_type}'  named '{node_id}' not found.")
        return node_loc

    def independent_clone(self, simulation):
        """
        Independent clone, clone the existing model and return
        @return:
        """
        self.save(reload=True)
        with CoreModel(self.path) as base_model:
            # just extract the simulation by name or index
            return base_model.get_sim_by_name_or_index(simulation)

    @staticmethod
    @cache
    def _check_candidate_node(node, *, replace, rename, node_from_node):
        """
        Internal utility to handle node replacement and renaming prior to insertion.

        This function:
        - Optionally removes an existing child node from the target location (`node`)
          if it matches both name and type.
        - Optionally renames the incoming node (`node_from_node`) before insertion.

        Parameters
        ----------
        node : Any
            Target APSIM node whose children will be inspected.

        replace : bool
            If True, remove the first child node matching:
            - Name == `node_from_id`
            - Type == `node_from_node.GetType()`

        rename : str | None
            If provided, assigns this name to `node_from_node`.

        node_from_node : Any
            Node to be inserted; used for type comparison and renaming.

        Notes
        -----
        - Matching is strict: both name and CLR type must match.
        - Only the first matching node is removed.
        - Type comparison relies on `.GetType()` (CLR), not Python `type()`.

        Returns
        -------
        None
        """
        node_from_id = node_from_node.Name
        if replace:
            # delete the node with the same name and type
            chd_s = node.Children
            for chd in list(chd_s):
                # strictly delete if name and type matches
                if chd.Name == node_from_id and type(chd.GetType()) == type(node_from_node.GetType()):
                    chd_s.Remove(chd)
                    break
            else:
                pass
                # logger.warning(
                #     f"node id {node_from_id} and {type(node_to_loc.GetType())} does not exist in the specified node location {node_to_id}")
                # pass
        if rename:
            node_from_node.Name = rename

    def add_node_from_models(self, source, target: dict, replace=True, rename=None):
        """
        Add a new node constructed from the APSIM ``Models`` namespace.

        This method instantiates a node (e.g., ``Models.Clock``) or uses an existing
        instance, and inserts it into a specified target location. Newly created
        nodes are typically not parametrized, meaning they have a blank parameter field. e.g,
        Clock will have no start and end date users must use other methods to populate the paramters.

        Parameters
        ----------
        source : str | type | object | dict
            Source specification. Supported inputs:

            - str:
                Name of a model in the ``Models`` namespace (e.g., "Clock").
            - type:
                CLR type (e.g., Models.Clock).
            - object:
                Existing APSIM node instance.
            - dict:
                Must contain key ``"model"`` with any of the above values.

        target : dict
            Target location specification. Required keys:

            - ``identifier`` : str
                Node name or full APSIM path where the node will be inserted.
            - ``model_type`` : str | type
                Expected type of the target node (e.g., "Simulation", Models.Core.Zone).

        replace : bool, optional
            If True, removes the first existing child node in the target location
            matching both name and type before insertion. Default is True.

        rename : str, optional
            If provided, assigns this name to the inserted node before adding.

        Raises
        ------
        TypeError
            If the source cannot be resolved to a valid Models namespace node.
        AttributeError
            If a string source cannot be found in the Models namespace.

        Notes
        -----
        - Nodes created from the Models namespace are typically empty and require
          further configuration via ``edit_model`` or similar methods.
        - Type resolution uses CLR reflection via ``GetType()``.
        - ``source`` accepts multiple forms for flexibility but is normalized internally.
        - Target node resolution is handled via ``_get_node``.

        Examples
        --------
        .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel

            model = ApsimModel("Maize")

            # Add a new Clock node in the simulation; 'Simulation' from Models namespace
            model.add_node_from_models(
                source="Clock",
                target={
                    "identifier": ".Simulations.Simulation",
                    "model_type": "Simulation",
                },
                rename="clock_memory",
            )

            # Using CLR type
            from Models.Clock import Clock

            model.add_node_from_models(
                source=Clock,
                target={
                    "identifier": ".Simulations.Simulation",
                    "model_type": "Simulation",
                },
                replace=True,
            )

            # Using existing instance
            clock = Clock()
            model.add_node_from_models(
                source=clock,
                target={
                    "identifier": ".Simulations.Simulation",
                    "model_type": "Simulation",
                },
            )
        """
        node_to_id = target['identifier']
        node_to_type = target['model_type']
        node_from = source if not isinstance(source, dict) else source.get('model')  # to be consistent with similar API
        # node is from models namespace
        if isinstance(node_from, ModelTools.CLASS_MODEL):
            node_from_node = node_from()  # it is in the form Models.Clock
        # most likely initialized
        # example: Models.Clock()
        elif (
                hasattr(node_from, "Name") and not callable(node_from)
                and hasattr(node_from, "GetType") and node_from.GetType().FullName.startswith("Models.")
        ):
            node_from_node = node_from
        elif isinstance(node_from, str):
            # string attribute we have to search from the Models namespace
            _node_from_node = self.find_model(node_from)
            if _node_from_node is None:
                raise AttributeError('un able to find attribute:{} from the Models names space'.format(node_from))
            # call the retrieved class attribute
            node_from_node = _node_from_node()
        else:
            raise TypeError(
                f'un able to find {node_from} from Models Namespace')
        node_to_loc = self._get_node(self, node_to_id, node_to_type)
        self._check_candidate_node(node_to_loc, replace=replace, rename=rename,
                                   node_from_node=node_from_node)
        ModelTools.ADD(node_from_node, node_to_loc)
        self.save()

    def add_new_model(self, *, parent_identifier, parent_type, source: dict, replace=True, rename=None):
        """
            Add a new APSIM model node to a specified parent node using a dictionary specification.

            This method constructs a CLR APSIM model object from a Python dictionary (`source`),
            assigns attributes, validates insertion rules, and attaches it to the target parent node.

            Parameters
            ----------
            parent_identifier : str
                Identifier used to locate the parent node. Interpretation depends on `parent_type`.
                Examples:
                    - "Simulation"
                    - "Clock"
                    - ".Simulations.Simulation.Field"

            parent_type : str
                Type of the parent node used for resolution (e.g., "Simulation", "Zone", "Manager").
                This ensures correct disambiguation when multiple nodes share names.

            source : dict
                Dictionary defining the APSIM model to create.

                Requirements:
                - MUST include either:
                    * "$type" (APSIM standard), or
                    * "type" (Python-friendly alias)
                - The type must be resolvable to a valid APSIM CLR model.

                Example:
                --------
                {
                    "$type": "Models.Manager, Models",
                    "Name": "FertiliserManager",
                    "Parameters": [
                        {"Key": "Amount", "Value": 50},
                        {"Key": "FertiliserType", "Value": "Urea"}
                    ]
                }

                Notes:
                ------
                - Keys must match APSIM property names exactly.
                - Special handling is applied for:
                    * Clock date fields (parsed to System.DateTime)
                    * Manager.Parameters (converted to .NET List[KeyValuePair])
                - "Children" key is ignored during assignment.

            replace : bool, default=True
                Controls behavior when a node with the same name and type already exists.

                - True:
                    Existing matching node is removed and replaced.
                - False:
                    Raises an error if a conflicting node exists.

            rename : str or None, default=None
                Optional new name for the incoming node.

                - If provided, the node will be renamed before insertion.
                - Useful when `replace=False` and avoiding naming conflicts.

            Returns
            -------
            None
                The model is modified in-place and automatically saved.

            Raises
            ------
            ValueError
                If `source` does not define a valid APSIM model type.

            AttributeError
                If the APSIM model type cannot be resolved.

            RuntimeError
                If insertion fails due to conflicts and `replace=False`.

            Notes
            -----
            - The method performs the following steps:
                1. Resolve parent node from `parent_identifier` and `parent_type`.
                2. Instantiate APSIM CLR model from `$type` or `type`.
                3. Assign attributes with type-aware handling.
                4. Validate insertion using `replace` / `rename` logic.
                5. Attach node to parent.
                6. Persist changes via `self.save()`.

            - Attribute assignment is best-effort:
                Unsupported or incompatible attributes are silently ignored.

            - This method assumes familiarity with APSIM's internal model structure.

            Warnings
            --------
            - Incorrect `$type` values will fail at runtime.
            - Passing improperly structured `Parameters` for Manager nodes will result in invalid configurations.
            - Silent attribute failures may hide misconfigured keys—validate inputs carefully.

            Examples
            --------
            >>> model = ApsimModel("Maize")
            >>> model.add_new_model(
            ...     parent_identifier="Simulation",
            ...     parent_type="Simulation",
            ...     source={
            ...         "$type": "Models.Clock, Models",
            ...         "Start": "2000-01-01",
            ...         "End": "2020-12-31"
            ...     }
            ... )

            >>> model.add_new_model(
            ...     parent_identifier=".Simulations.Simulation.Field",
            ...     parent_type="Zone",
            ...     source={
            ...         "type": "Models.Manager, Models",
            ...         "Name": "IrrigationManager",
            ...         "Parameters": [
            ...             {"Key": "Amount", "Value": 30}
            ...         ],
                     'CodeArray':[] # code array must be defined to use this method with manager script
            ...     },
            ...     replace=False,
            ...     rename="IrrigationManager_v2"
            ... )
            """
        # strict the source dict should have the parameter names as those in APSIM, and most importantly should define the type of the models
        node_to_loc = self._get_node(self, parent_identifier, parent_type)
        # Copy source to avoid mutation
        pl = dict(source)
        node_from_type = pl.get("$type") or source.get(
            "type")  # the latter is more pythonic, although not a standard in APSIM key attributes names
        if not node_from_type:
            raise ValueError("source must define '$type' or 'type'")
        # pop it
        pl.pop('$type', None), pl.pop('type', None)
        # if node is in this form "Models.PMF.Plant, Models"
        # Extract CLR type (strip assembly if present)
        head = node_from_type.split(",", 1)[0].strip()
        _node_from_node = self.find_model(head)
        #
        if _node_from_node is None:
            raise AttributeError(
                f"Unable to resolve APSIM model type: '{node_from_type}'"
            )
        node_from_node = _node_from_node()

        for k, v in pl.items():
            match type(node_from_node):
                case CLR.Models.Clock:
                    if k in {'End', 'Start', 'StartDate', 'EndDate'}:
                        v = CLR.System.DateTime.Parse(v)
                case CLR.Models.Climate.Weather:
                    pass
                case CLR.Models.Manager:

                    if k == 'Parameters':
                        net_list = List[KeyValuePair[str, str]](len(v))
                        node_from_node.Parameters = net_list
                        for i, dicto in enumerate(v):
                            param = dicto['Key']
                            value = dicto['Value']

                            app = KeyValuePair[CLR.System.String, CLR.System.String](param, f"{value}")
                            net_list.Add(app)
                        continue  # skip this key for sett attr below
            if k == 'Children':
                # this expected to be empty at this time, above all `[]` will be rejected by pythonnet
                continue
            try:
                setattr(node_from_node, k, v)
            except TypeError:
                pass

        # Validate replacement / rename logic
        self._check_candidate_node(node_to_loc,
                                   replace=replace,
                                   rename=rename,
                                   node_from_node=node_from_node)
        # Attach node to parent
        ModelTools.ADD(node_from_node, node_to_loc)
        # save the model
        self.save()

    def add_model_from_apsimx(self, *, source: dict, target: dict, replace=True, rename=None):
        """
        Add a node from a source into a target location within the APSIM model.

        This method transfers (or constructs) a node and inserts it into a specified
        location in the current model. The source can be:
        - A model on disk (e.g., "Soybean")
        - A built-in APSIM example
        - A class or instance from the ``Models`` namespace

        Parameters
        ----------
        source : dict
            Dictionary describing the node to extract. Expected keys:

            - ``model`` : str | object
                Source of the node. Can be:
                - APSIM model name (e.g., "Soybean")
                - File path to APSIM model

            - ``model_type`` : str | type
                Type of the node to retrieve (e.g., "Models.Clock" or Models.Clock)

            - ``identifier`` : str
                Node identifier. Can be:
                - Node name (e.g., "Clock")
                - Full node path (e.g., ".Simulations.Simulation.Clock")

        target : dict
            Dictionary describing where the node will be inserted. Expected keys:

            - ``identifier`` : str
                Target location. Can be:
                - Node name (e.g., "Simulation")
                - Full node path (e.g., ".Simulations.Simulation.Field")

            - ``model_type`` : str | type
                Expected type of the target node (e.g., "Models.Core.Zone")

        replace : bool, optional
            If True, removes an existing node with the same name and type before adding.
            If False, the new node is added alongside existing ones. Default is True.

        rename : str, optional
            If provided, renames the inserted node.

        Notes
        -----
        - All parameters are keyword-only to prevent mis-ordered arguments.
        - ``identifier`` supports both node names and full APSIM paths.
        - When ``replace=False``, multiple nodes of the same type may coexist.
        - When ``replace=True``, only nodes matching both name and type are removed.

        Examples
        --------
        .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            from Models.Core import Simulation

            model = ApsimModel("Maize")

            # Example 1: Add node from another APSIM model
            model.add_node_from_apsimx(
                source={
                    "model": "Soybean",
                    "model_type": "Models.Clock",
                    "identifier": "Clock",
                },
                target={
                    "identifier": ".Simulations.Simulation",
                    "model_type": "Simulation",
                },
                replace=True,
                rename="our_clock",
            )

            # Example 2: Allow duplicates
            model.add_node_from_apsimx(
                source={
                    "model": "Soybean",
                    "model_type": "Models.Clock",
                    "identifier": "Clock",
                },
                target={
                    "identifier": ".Simulations.Simulation",
                    "model_type": 'Simulation',
                },
                replace=False,
                rename="our_clock",
            )


            # Example 3: Add soil node into Field
            model.add_node_from_apsimx(
                source={
                    "model": "Soybean",
                    "model_type": "Models.Soils.Soil",
                    "identifier": "Soil",
                },
                target={
                    "identifier": ".Simulations.Simulation.Field",
                    "model_type": "Zone",
                },
                replace=True,
                rename="soil_added",
            )

            model.open_in_gui(watch=False)

        Tip
        ---
        To detect a node type:

        .. code-block:: python

            node_type = model.detect_model_type(".Simulations.Simulation.Field", full_name=True)
        """
        source, target = dict(source), dict(target)
        node_from = source['model']
        node_from_type = source['model_type']
        node_from_id = source['identifier']
        node_to_id = target['identifier']
        node_to_type = target['model_type']
        node_to_loc = self._get_node(self, node_to_id, node_to_type)

        # model from disk or raw name, specifying one of the examples
        mod = CoreModel(node_from)
        with mod:
            node_from_node = self._get_node(mod, node_from_id, node_from_type)
            self._check_candidate_node(node_to_loc, node_from_node=node_from_node, replace=replace, rename=rename)

            # add the node to the specified location
            ModelTools.ADD(node_from_node, node_to_loc)
            self.save()

    def adjust_dul(self, simulations: Union[tuple, list] = None):
        """
        - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly

        - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

        ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

        ``returns``:

            model the object for method chaining
        """
        if simulations is None:
            simulations = self.simulations
        else:
            simulations = self.find_simulations(simulations)
        for sim_ in simulations:
            physical = find_child_of_class(sim_, Models.Soils.Physical)

            physical = CastHelper.CastAs[Models.Soils.Physical](physical)
            if not isinstance(physical, Models.Soils.Physical):
                raise RuntimeError(f"failed to cast IModel physical to {Models.Soils.Physical}")
            duL = list(physical.DUL)

            saT = list(physical.SAT)

            for enum, (s, d) in enumerate(zip(saT, duL)):
                # first check if they are equal
                if d >= s:
                    # if d is greater than s, then by what value, we need this value to add it to 0.02
                    #  to be certain all the time that dul is less than s we subtract the summed value
                    diff = d - s
                    duL[enum] = d - (diff + 0.02)

                else:
                    duL[enum] = d
            physical.DUL = duL
            physical.SAT = saT
        self.save()
        # self.replace_any_soil_physical('DUL', simulations, duL)
        return self

    def replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs):
        """ @deprecated and will be removed in the future versions
            Updates soil parameters and configurations for downloaded soil data in simulation models.

            This method adjusts soil physical and organic parameters based on provided soil tables and applies these
            adjustments to specified simulation models.

            Parameters:
            ``soil_tables`` (list): A list containing soil data tables. Expected to contain: see the naming
            convention in the for APSIM - [0]: DataFrame with physical soil parameters. - [1]: DataFrame with organic
            soil parameters. - [2]: DataFrame with crop-specific soil parameters. - simulation_names (list of str): Names or identifiers for the simulations to
            be updated.s


            Returns:
            - self: Returns an instance of the class for ``chaining`` methods.

            This method directly modifies the simulation instances found by ``find_simulations`` method calls,
            updating physical and organic soil properties, as well as crop-specific parameters like lower limit (``LL``),
            drain upper limit (``DUL``), saturation (``SAT``), bulk density (``BD``), hydraulic conductivity at saturation (``KS``),
            and more based on the provided soil tables.

    ->> key-word argument

            ``set_sw_con``: Boolean, set the drainage coefficient for each layer
            ``adJust_kl``:: Bollean, adjust, kl based on productivity index
            ``CultvarName``: cultivar name which is in the sowing module for adjusting the rue
            ``tillage``: specify whether you will be carried to adjust some physical parameters

        """

        self.thickness_replace = self.thickness_values
        physical_calculated = soil_tables['physical']
        self.organic_calcualted = soil_tables['organic']
        self.cropdf = soil_tables[2]
        self.SWICON = soil_tables[6]  # TODO To put these tables in the dictionary isn't soilmanager module
        for simu in self.find_simulations(simulation_names):
            pysoil = simu.FindDescendant[Physical]()  # meaning physical soil child

            soil_crop = pysoil.FindChild[SoilCrop]()
            water = simu.FindDescendant[Water]()  # for the crop water parameters
            soil_crop.LL = physical_calculated.AirDry
            pysoil.DUL = physical_calculated.DUL
            pysoil.SAT = physical_calculated.SAT
            pysoil.BD = physical_calculated.BD
            pysoil.KS = physical_calculated.KS
            pysoil.LL15 = physical_calculated.LL15
            pysoil.ParticleSizeClay = physical_calculated.ParticleSizeClay
            pysoil.ParticleSizeSand = physical_calculated.ParticleSizeSand
            pysoil.ParticleSizeSilt = physical_calculated.ParticleSizeSilt
            water.InitialValues = physical_calculated.DUL

            water.Thickness = self.thickness_replace
            pysoil.AirDry = soil_crop.LL
            pysoil.Thickness = self.thickness_replace
            # print(len(pysoil.Thickness))
            # replace the organic soils
        for simu in self.find_simulations(simulation_names):
            organic = simu.FindDescendant[Organic]()
            organic.Thickness = self.thickness_replace
            organic.SoilCNRatio = self.organic_calcualted.SoilCNRatio
            organic.FBiom = self.organic_calcualted.FBiom
            # you could adjust practices here, but still looking for a cool way to do it
            if kwargs.get('No_till', False):
                self.organic_calcualted.loc[:1, 'FBiom'] = self.organic_calcualted.loc[:1,
                                                           'FBiom'] + 0.2 * self.organic_calcualted.loc[:1, 'FBiom']
                organic.FBiom = self.organic_calcualted.FBiom[:2]
            organic.FOM = self.organic_calcualted.FOM
            organic.FInert = self.organic_calcualted.FInert
            organic.Carbon = self.organic_calcualted.Carbon
            chemical = simu.FindDescendant[Chemical]()
            chemical.Thickness = self.thickness_values
            XF = np.tile(float(1), int(self.n_layers))

        for simu in self.find_simulations(simulation_names):
            soil_crop = pysoil.FindAllDescendants[SoilCrop]()
            # can be used to target specific crop
            for cropLL in soil_crop:
                cropLL.LL = pysoil.LL15
                kl = self.organic_calcualted.cropKL
                cropLL.KL = kl
                # if kwargs.get('No_till', False):
                #     cropLL.KL = cropLL.KL + np.array([0.2]) * cropLL.KL
                cropLL.XF = XF
                cropLL.Thickness = self.thickness_replace
        for simu in self.find_simulations(simulation_names):
            zone = simu.FindChild[Models.Core.Zone]()
            try:
                swim = pysoil.FindAllDescendants[LayerStructure]()
                swim.LayerStructure = self.thickness_values
            except Exception as e:
                pass
        # replace drainage coefficient for each layer based on DUL and BD
        for sim in self.find_simulations(simulation_names):
            try:
                wb = sim.FindDescendant[Models.WaterModel.WaterBalance]()
                wb.SWCON = self.SWICON
                wb.Thickness = self.thickness_values
                if kwargs.get('CN2Bare', None):
                    wb.CN2Bare = kwargs.get('CN2Bare')
                if kwargs.get('CNRed', None):
                    wb.CNRed = kwargs.get('CNRed')
            except:
                # in the case of sim model, pass

                pass

        return self

    def check_kwargs(self, path, **kwargs):
        if hasattr(self.Simulations, "FindByPath"):
            mod_obj = self.Simulations.FindByPath(path)
        else:
            mod_obj = get_node_by_path(self.Simulations, path)
            model = getattr(mod_obj, "Model", mod_obj)
            model_ty = model.GetType()
            mod_obj = CastHelper.CastAs[model_ty](model)
        if mod_obj is None:
            raise ValueError(f"Could not find model associated with path {path}")
        v_mod = getattr(mod_obj, 'Value', mod_obj)
        kas = set(kwargs.keys())

        def _raise_value_error(_path, acceptable, user_info, msg='not a valid attribute'):
            _dif = user_info - acceptable
            if len(_dif) > 0:
                raise ValueError(f"{_dif} is not a valid parameter for {_path}")

        match type(v_mod):
            case Models.Manager:
                kav = {v_mod.Parameters[i].Key for i in range(len(v_mod.Parameters))}
                _raise_value_error(path, kav, kas)

            case Models.Clock:
                acceptable = {'End', "Start"}
                _raise_value_error(path, acceptable, kas)
            case Models.Climate.Weather:
                met_file = kwargs.get('weather_file') or kwargs.get('met_file')
                if met_file is not None:
                    if not os.path.isfile(met_file):
                        raise ValueError(f"{met_file} is not a valid file")
                else:
                    raise ValueError(f"{met_file} file name is needed use key word 'met_file' or 'weather_file'")
            case Models.Surface.SurfaceOrganicMatter:
                accept = {'SurfOM', 'InitialCPR', 'InitialResidueMass',
                          'InitialCNR', 'IncorporatedP', }
                if kwargs == {}:
                    raise ValueError(f"Please supply at least one parameter: value \n '{', '.join(accept)}' for {path}")
                _raise_value_error(path, accept, kas)
            case Models.PMF.Cultivar:
                # Define required parameters
                required_keys = ["commands", "values", "cultivar_manager", "parameter_name", "new_cultivar_name"]
                # Extract input parameters
                param_values = kwargs
                missing = [key for key in required_keys if not param_values.get(key)]

                if missing:
                    raise ValueError(f"Missing required parameter(s): {', '.join(missing)}")

    def _get_base_simulations(self):
        if self.base_simulations is None:
            base_sim = self.Simulations.FindInScope[Models.Core.Simulation]()
            base_sim = ModelTools.CLONER(base_sim)
            self.base_simulations = base_sim
        return ModelTools.CLONER(self.base_simulations)

    def _create_new_simulation(self, sim_name, lonlat=None):
        _sim = self._get_base_simulations()
        _sim.Name = sim_name
        ModelTools.ADD(sim_name, self.Simulations)

    def read_apsimx_data(self, table=None):

        """
        Read APSIM NG datastore for the current model. Raises FileNotFoundError if the model was initialized from
        default models because those need to be executed first to generate a database.

        The rationale for this method is that you can just access the results from the previous session without
        running it if the database is in the same location as the apsimx file.

        Since apsimNGpy clones the apsimx file, the original file is kept with attribute name `_model`, that is what is
        being used to access the dataset

        table: (str) name of the database table to read if none of all tables are returned

         Returns: pandas.DataFrame

         Raises
         ------------
          KeyError: if table is not found in the database

         """
        from pathlib import Path
        from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
        cls_name = type(self).__name__

        model_path = Path(self._model)
        if model_path.suffix.lower() != ".apsimx" or not model_path.exists():
            raise FileNotFoundError(
                "Data cannot be retrieved from a template/default APSIMX file.\n"
                f"Please run the model first, then use `{cls_name}.results` or "
                f"`{cls_name}.get_simulated_output(...)`."
            )
        base = Path(self._model)
        db = base.resolve().with_suffix('.db')
        try:
            all_tables = get_db_table_names(db)
        except FileNotFoundError:
            all_tables = []
            pass

        if not all_tables:
            raise FileNotFoundError("Perhaps loaded model was not yet executed")
        if table is None and all_tables:
            res = (read_db_table(db, i) for i in all_tables)
            res = (df.assign(source_table=t) for df, t in zip(res, all_tables))
            return pd.concat(res)

        if table in all_tables:
            return read_db_table(db, table).assign(source_table=table)

        raise KeyError(f"{table} is not a valid table name associated with apsimx {self._model}")


if __name__ == '__main__':
    # test

    os.chdir(Path.home())
    maize_x = "maize"
    # mod = ApsimModel('Maize', out_path=maize_x)
    mode = ApsimModel(maize_x, out_path=Path.home() / 'm.apsimx')
    # mode.get_soil_from_web(simulations=None, lonlat=(-93.9937, 40.4842), thinnest_layer=150, adjust_dul=True,
    #                         source='isric')
    # mod.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541))
    from apsimNGpy.tests.unittests.test_factory import obs

    outside_usa__lonlat = 47.1553, 59.0809


    def source_test(soil_source='ssurgo'):
        with ApsimModel("Maize") as model:
            datastore = Path(model.datastore)
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report',
                                      simulations='Simulation')
            model.get_soil_from_web(simulations=None, lonlat=(-93.9937, 40.4842), thinnest_layer=100,
                                    adjust_dul=True,
                                    summer_date='1-May', precipitation_interception=13.5, winter_date='1-nov',
                                    source=soil_source)
            model.get_weather_from_web(lonlat=(-93.9937, 40.4842), start=1989, end=2020, source='nasa')
            model.run()
            print(model.results.columns)
            df = model.results
            print(df.columns)
            df["date"] = pd.to_datetime(df["Clock.Today"])
            # Extract components
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df["day"] = df["date"].dt.day
            model.evaluate(ref_data=obs, table=df, index_col=['year'],
                           target_col='Yield', ref_data_col='observed')
            df = model.results
            print(df.Yield.mean())

        print(os.path.exists(model.datastore))
        return df


    model = ApsimModel('Maize', out_path='fxm.apsimx')
    model.set_params(
        {'path': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82', 'sowed': True, 'values': [550.0],
         'commands': ['[Grain].MaximumGrainsPerCob.FixedValue'], 'plant': 'Maize',
         'managers': {'Sow using a variable rule': 'CultivarName'}}, )
    # isric = source_test(soil_source='isric')
    ssurgo = source_test(soil_source='ssurgo')
    ssurgo['ssurgo_yield'] = ssurgo['Yield']
    # model.evaluate(ref_data=isric, table=ssurgo, index_col=['year'], target_col='ssurgo_yield',
    #                ref_data_col='Yield')
    model.clone_simulation(rename='new_sim', base_simulation=0)
    print(model[0])

    model.add_model_from_apsimx(source=dict(model="Soybean", model_type='Models.Clock', identifier="Clock"),
                                target=dict(identifier=".Simulations.new_sim", model_type=Models.Core.Simulation),
                                replace=True,
                                rename='our_clock')
    clocks1 = model.inspect_model('Models.Clock', fullpath=False)
    # because simulations are two, if we delete and replace, they will remain two
    assert len(clocks1) == 2, "clocks expected to be two because of two simulations"
    assert 'our_clock' in clocks1, "our_clock not found"
    # create new instance and text
    model = ApsimModel('Maize', out_path='fxm2.apsimx')
    with model:
        model.add_model_from_apsimx(source=dict(model="Soybean", model_type='Models.Clock', identifier="Clock"),
                                    target=dict(identifier=".Simulations.Simulation", model_type='Simulation'),
                                    replace=True,
                                    rename='our_clock')

        clocks2 = model.inspect_model('Models.Clock', fullpath=False)
    assert len(clocks1) == 2, "clocks expected to be two because of two simulations"
    assert 'our_clock' in clocks1, "our_clock not found"
    # test adding soils
    model = ApsimModel('Maize', out_path='fmx3.apsimx')
    with model:
        model.add_model_from_apsimx(source=dict(model="Soybean", model_type='Soil', identifier="Soil"),
                                    target=dict(identifier=".Simulations.Simulation.Field", model_type='Zone'),
                                    replace=True,
                                    rename='soil_added')
        soil_nodes = model.inspect_model('Soil', fullpath=False)

    assert 'soil_added' in soil_nodes, " Soil nodes: `soil_added` not found"
    assert len(soil_nodes) == 1, 'soil nodes was not added as expected'
    # test adding manager
    model = ApsimModel('Maize')
    with model:
        model.add_model_from_apsimx(
            source=dict(model="Soybean", model_type='Manager', identifier="Fertilise at sowing"),
            target=dict(identifier="Simulation", model_type='Simulation'), replace=True,
            rename="fertilizer_at_sowing")

    # testing adding from memory

    model = ApsimModel('Maize', )

    # model.add_node_from_apsimx(source=dict(model='Models.Clock', model_type=Models.Clock, identifier="Clock", source_kind='Models'),
    #                            target=dict(identifier=".Simulations.Simulation", model_type='Simulation'), replace=True,
    #                            rename='clock_mem')
    # model.add_node_from_apsimx(
    #     source=dict(model='Models.Operations', model_type='Simulation', identifier="Simulation", source_kind='Models'),
    #     target=dict(identifier=".Simulations", model_type='Simulations'), replace=False,
    #     rename='sim2')
    model.add_node_from_models(Models.Soils.Soil(), target=dict(identifier="Field", model_type='Zone'))
    model.add_node_from_models(source=Models.Soils.Physical, target=dict(identifier="Soil", model_type='Soil'))
    clock_memory = model.inspect_model('Clock', fullpath=False)
    print(clock_memory)
    model.add_node_from_models(source=Models.Core.Folder,
                               target=dict(identifier=".Simulations", model_type='Simulations'),
                               rename='Replacements')
    model.add_node_from_models(source=Models.PMF.Plant,
                               target=dict(identifier=".Simulations.Replacements", model_type='Folder'),
                               rename='Maize')

    model.has_node('.Simulations.Simulation.Field', node_type='Zone')

    with model:
        # model.open_in_gui()
        import time

        # time.sleep(10)
        pass
    mp = ApsimModel(model='Maize', out_path='m.apsimx')
    clock_node = {
        "$type": "Models.Clock, Models",
        "Start": "1992-01-01",
        "End": "1995-12-31",
        "Name": "Clock",
        "Enabled": True,
        "ReadOnly": False,
    }
    weather_node = {
        "$type": "Models.Climate.Weather, Models",
        "ConstantsFile": None,
        "FileName": r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.2.7990.0\Examples\WeatherFiles\AU_Ingham.met"
        #  "ExcelWorkSheetName": "",
        #  "Name": "Weather",
        #  "ResourceName": None,
        #  "Children": [],
        #  "Enabled": True,
        #  "ReadOnly": False,
    }
    plant_node = {
        "$type": "Models.PMF.Plant, Models",
        "Name": "Maize",
        "ResourceName": "Canola",

        "Enabled": True,
        "ReadOnly": False,
    }
    cultivar = {
        "$type": "Models.PMF.Cultivar, Models",
        "Command": [
            "[Phenology].Juvenile.Target.FixedValue = 190",
            "[Phenology].Photosensitive.Target.XYPairs.X = 0, 12.5, 24",
            "[Phenology].Photosensitive.Target.XYPairs.Y = 0, 0, 124",
            "[Phenology].FlagLeafToFlowering.Target.FixedValue = 10",
            "[Phenology].FloweringToGrainFilling.Target.FixedValue = 170",
            "[Phenology].GrainFilling.Target.FixedValue = 520",
            "[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue = 25",
            "[Grain].MaximumGrainsPerCob.FixedValue =  55"
        ],
        "Name": "B_10000000000000000000000",
        "ResourceName": None,

        "Enabled": True,
        "ReadOnly": False,
    }
    from nodes import manager_node, soil_arbitrator

    # mp.add_node_from_dict(parent_type='Simulation', parent_identifier='Simulation', source=clock_node)
    # mp.add_node_from_dict(parent_type='Simulation', parent_identifier='Simulation', source=clock_node)
    mp.add_crop_replacements()
    mp.add_new_model(parent_type='Models.PMF.Plant',
                     parent_identifier='Maize',
                     source=cultivar)
    mp.add_new_model(parent_type='Simulation', parent_identifier='Simulation',
                     source={'type': 'Models.Summary', 'Verbosity': '0'})
    mp.save()


    def edit_cultivar(self, commands, template, parent_plant, rename=None):
        match commands:
            case dict():
                commands = {f"{k}={v}" for k, v in commands.items()}
            case list() | tuple() | set():
                commands = set(commands)
            case str():
                commands = {commands}
            case _:
                raise ValueError(f"Unknown command type: {type(commands)} expected list, str, tuple, dicts or set")
        existing_params = self.inspect_model_parameters(model_type='Models.PMF.Cultivar', model_name='B_100')
        all_commands = {f"{k}={v}" for k, v in existing_params.items()} | commands
        rename = rename or f"ed{template}"

        cult_load = {
            "$type": "Models.PMF.Cultivar, Models",
            "Command": [
                *all_commands
            ],
            "Name": f"{rename}",
            # "Enabled": True,
            "ReadOnly": False,

        }

        if 'Replacements' not in {i.Name for i in self.Simulations.Children}:
            folder = CLR.Models.Core.Folder()
            folder.Name = 'Replacements'
            self.Simulations.Children.Add(folder)
            plant = Models.PMF.Plant()
            plant.Name = parent_plant
            folder.Children.Add(plant)
        else:
            rep = [i for i in self.Simulations.Children if i.Name == 'Replacements']
            if rep:
                replacements = rep[0]
                if parent_plant not in {i.Name for i in replacements.Children}:
                    plant = CLR.Models.PMF.Plant()
                    plant.Name = parent_plant
                    replacements.Children.Add(plant)

        self.add_new_model(parent_type='Models.PMF.Plant',
                           parent_identifier=f'{parent_plant}',
                           replace=True,
                           source=cult_load)


    edit_cultivar(mp, commands={'[leaf].Photosynthesis.RUE.FixedValue = 2.3', }, parent_plant='Maize',
                  template='B_100', rename='B_100x')

    # mp.open_in_gui()

    # set_up_crop_rotation()

    # with mp:
    #     pass

    # te

    from model_tools import NodeInfo

    with ApsimModel('Maize') as mo:
        # mo.clear_water_model('soil water')
        th = geometric_layers(max_depth=1800, max_thickness=10, growth=1.1, top_thickness=10)
        # mo.switch_wm_to_swim3(layer_structure_th=th, ss_tile_drainage={}, swim_model_params={}
        #                       )
        mo.run(verbose=True)
        mo.save()
        sp = mo.inspect_model(Models.WaterModel.WaterBalance)
        print(mo.results.Yield.mean())
        # mo.open_in_gui(watch=True)
        print(sp)
    node = NodeInfo('Simulations')
