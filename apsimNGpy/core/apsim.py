"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Optional, Tuple, Sequence
from typing import Union
from apsimNGpy.core.pythonet_config import CLR
import numpy as np
import pandas as pd
from Models.Soils import Physical, SoilCrop, Organic, LayerStructure
from Models.Soils import Water, Chemical
from System import *
from System.Collections.Generic import *

from apsimNGpy.core.core import CoreModel, ModelTools


Models = CLR.Models
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.model_loader import AUTO_PATH
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import find_child_of_class
from apsimNGpy.core.soiler import SoilManager
from apsimNGpy.logger import logger
from apsimNGpy.soils.helpers import soil_water_param_fill


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

    def evaluate_simulated_output(
            self,
            ref_data: pd.DataFrame,
            table,
            ref_data_col,
            target_col,
            index_col,
            expr=None
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
                          obs_col=ref_data_col, exp=expr)

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

    def __exit__(self, exc_type, exc, tb):
        db_flag = getattr(self, "db", True)
        csv_flag = getattr(self, "csv", True)

        try:
            path = Path(self.path)

            # Common sidecars we may want to clean
            _db = path.with_suffix('.db')
            bak = path.with_suffix('.bak')
            db_wal = path.with_suffix('.db-wal')
            db_shm = path.with_suffix('.db-shm')

            clean_candidates = {bak, db_wal, db_shm, path}
            if csv_flag:
                try:
                    reps = self.inspect_model(Models.Report, fullpath=False) or {}

                    clean_candidates.update({path.with_suffix(f'.{rep}.csv') for rep in reps})
                except Exception:
                    # If inspect_model/Models is unavailable, skip CSV cleanup
                    pass

            # Optionally include the SQLite .db sidecar (force GC on pythonnet/.NET first)
            if db_flag:
                try:

                    CLR.System.GC.Collect()
                    import gc
                    gc.collect()
                    CLR.System.GC.WaitForPendingFinalizers()
                except Exception:
                    pass
                clean_candidates.add(_db)

            # Remove files if present
            for candidate in clean_candidates:
                try:
                    candidate.unlink(missing_ok=True)
                except PermissionError:
                    # File locked; leave it
                    pass

        except PermissionError:
            # Path itself locked; nothing we can do here
            pass

        # Do not suppress exceptions from the with-block
        return False

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

    def create_new_simulation(self, sim_name, lonlat=None):
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
    maize_x = Path.home() / 'maize.apsimx'
    # mod = ApsimModel('Maize', out_path=maize_x)
    mode = ApsimModel(maize_x, out_path=Path.home() / 'm.apsimx')
    # mode.get_soil_from_web(simulations=None, lonlat=(-93.9937, 40.4842), thinnest_layer=150, adjust_dul=True,
    #                         source='isric')
    # mod.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541))
    from apsimNGpy.tests.unittests.test_factory import obs

    outside_usa__lonlat = 47.1553, 59.0809


    def source_test(soil_source='isric'):
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
            model.evaluate_simulated_output(ref_data=obs, table=df, index_col=['year'],
                                            target_col='Yield', ref_data_col='observed')
            df = model.results
            print(df.Yield.mean())

        print(os.path.exists(model.datastore))
        return df


    with ApsimModel('Maize') as model:
        model.set_params(
            {'path': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82', 'sowed': True, 'values': [550.0],
             'commands': ['[Grain].MaximumGrainsPerCob.FixedValue']})
        isric = source_test(soil_source='isric')
        ssurgo = source_test(soil_source='ssurgo')
        ssurgo['ssurgo_yield'] = ssurgo['Yield']
        model.evaluate_simulated_output(ref_data=isric, table=ssurgo, index_col=['year'], target_col='ssurgo_yield',
                                        ref_data_col='Yield')
