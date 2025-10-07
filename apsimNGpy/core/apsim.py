"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
"""
import logging, pathlib
from builtins import str
from typing import Union, Any, Optional, Tuple, Mapping, Sequence
import os
import numpy as np
import time
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile
import apsimNGpy.manager.weathermanager as weather
import pandas as pd
from dataclasses import dataclass
import sys
# prepare for the C# import
# from apsimNGpy.core.pythonet_config import start_pythonnet
from pathlib import Path
from apsimNGpy.core.core import CoreModel, Models, ModelTools
from apsimNGpy.core.inspector import Inspector
from System.Collections.Generic import *
from Models.Core import Simulations
from System import *
from Models.Soils import Solute, Water, Chemical
from Models.Soils import Soil, Physical, SoilCrop, Organic, LayerStructure

from typing import Union
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import find_child_of_class
from apsimNGpy.settings import logger
from apsimNGpy.core.soiler import SoilManager

# constants
REPORT_PATH = {'Carbon': '[Soil].Nutrient.TotalC/1000 as dyn', 'DUL': '[Soil].SoilWater.PAW as paw', 'N03':
    '[Soil].Nutrient.NO3.ppm as N03'}


# decorator to monitor performance

@dataclass(repr=False, order=False, init=False)
class ApsimModel(CoreModel):
    """
    Main class for apsimNGpy modules.
    It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

    This implies that you can still run the model and modify parameters as needed.
    Example:
        >>> from apsimNGpy.core.apsim import ApsimModel
        >>> from pathlib import Path
        >>> model = ApsimModel('Maize', out_path=Path.home()/'apsim_model_example.apsimx')
        >>> model.run(report_name='Report') # report is the default, please replace it as needed
    """

    def __init__(self, model: Union[os.PathLike, dict, str], out_path: Union[str, Path] = None,
                 set_wd=None, **kwargs):
        super().__init__(model, out_path, set_wd, **kwargs)

    def get_soil_from_web(self,
                          simulation_name: Union[str, tuple, None] = None,
                          *,
                          # location / data source
                          lonlat: Optional[Tuple[float, float]] = None,
                          soil_series: Optional[str] = None,
                          # layer/thickness controls
                          thickness_sequence: Optional[Sequence[float]] = 'auto',
                          thickness_value: int = None,
                          max_depth: Optional[int] = 2400,
                          n_layers: int = 10,
                          thinnest_layer: int = 100,
                          thickness_growth_rate: float = 1.5,  # unit less
                          # which sections to edit
                          edit_sections: Optional[Sequence[str]] = None,
                          # attach any missing nodes before editing
                          attach_missing_sections: bool = True,
                          additional_plants: tuple = None,
                          adjust_dul: bool = True):
        """
        Download SSURGO-derived soil for a given location and populate the APSIM NG
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

        Notes
        -----
        - Assumes soil sections live under a **Soil** node; when
          ``attach_missing_sections=True`` a Soil node is created if missing.
        - Uses the optimized SoilManager routines (vectorized assignments / .NET double[] marshaling).
        - Side effects (in place on the APSIM model):
            1. Creates/attaches **Soil** when needed.
            2. Creates/updates child sections (``Physical``, ``Organic``, ``Chemical``,
               ``Water``, ``WaterBalance``, ``SoilCrop``) as listed in ``edit_sections``.
            3. Overwrites section properties (e.g., layer arrays such as ``Depth``, ``BD``,
               ``LL15``, ``DUL``, ``SAT``; solutes; crop KL/XF) with downloaded values.
            4. Add **SoilCrop** children for any names in ``additional_plants``.
            5. Performs **network I/O** to retrieve SSURGO tables when ``lonlat`` is provided.
            6. Emits log messages (warnings/info) when attaching nodes, resolving thickness controls,
               or skipping missing columns.
            7. Caches the computed soil profile in the helper during execution; the in-memory APSIM
               tree remains modified after return.
            8. Does **not** write files; call ``save()`` on the model if you want to persist changes.
            9. The existing soil-profile structure is completed override by the newly generated soil profile.
               So, variables like soil thickness, number of soil layers, etc. might be different from the old one.
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

        simulations = self.find_simulations(simulations=simulation_name)
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
                # let it compute/fill once
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
        return self

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

    def spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var="Carbon", simulations=None):
        """
        Perform a spin-up operation on the aPSim model.

        This method is used to simulate a spin-up operation in an aPSim model. During a spin-up, various soil properties or
        _variables may be adjusted based on the simulation results.

        Parameters:
        ----------
        report_name: str, optional (default: 'Report')
            The name of the aPSim report to be used for simulation results.

        start: str, optional
            The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.

        end: str, optional
            The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.

        spin_var: str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
            The variable representing the child of spin-up operation. Supported values are 'Carbon' or 'DUL'.

        Returns:
        -------
        self : ApsimModel
            The modified ``ApsimModel`` object after the spin-up operation.
            you could call ``save_edited`` file and save it to your specified location, but you can also proceed with the simulation

        """

        insert_var = REPORT_PATH.get(spin_var)
        if start and end:
            self.change_simulation_dates(start, end)
        for simu in self.find_simulations(simulations):
            pysoil = simu.FindDescendant[Physical]()
        THICKNESS = self.extract_any_soil_physical("Thickness")
        th = np.array(THICKNESS)
        self.change_report(insert_var, report_name=report_name)
        rpn = insert_var.split(" ")[-1]
        self.run(report_name=report_name)
        DF = self.results

        df_sel = DF.filter(regex=r'^{0}'.format(rpn), axis=1)
        df_sel = df_sel.mean(numeric_only=True)
        print(df_sel)
        if spin_var == 'Carbon':
            if 'TotalC' not in insert_var:
                raise ValueError("wrong report variable path: '{0}' supplied according to requested spin up " \
                                 "var".format(insert_var))

            bd = list(pysoil.DUL)

            bd = np.array(bd)
            cf = np.array(bd) * np.array(th)
            cf = np.divide(cf, 1)  # this convert to percentage
            per = np.array(df_sel) / cf
            new_carbon = [i for i in np.array(per).flatten()]

            self.replace_any_soil_organic(spin_var, new_carbon)
        if spin_var == 'DUL':
            if 'PAW' not in insert_var:
                raise ValueError("wrong report variable path: '{0}' supplied according to requested spin up var" \
                                 .format(insert_var))
            l_15 = pysoil.LL15
            ll = np.array(l_15)
            dul = ll + df_sel
            dul = list(np.array(dul).flatten())

            pysoil.DUL = dul

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

    #
    # try:
    #     lonlat = -93.7738, 42.0204
    #     al = load_default_simulations(simulations_object=False)
    #     model = al
    #
    #     from apsimNGpy import settings
    #
    #     mod = ApsimModel('Maize')
    #     model = ApsimModel(model, out_path=None,
    #                        thickness_values=settings.SOIL_THICKNESS)
    #     model.replace_met_from_web(lonlat=lonlat, start_year=2001, end_year=2020)
    #     from apsimNGpy.manager import soilmanager as sm
    #
    #     st = sm.DownloadsurgoSoiltables(lonlat)
    #     sp = sm.OrganiseSoilProfile(st, 20)
    #     sop = sp.cal_missingFromSurgo()
    #     model.replace_downloaded_soils(sop, model.simulation_names, No_till=True)
    #     bd = model.extract_any_soil_physical("BD")
    #
    # except Exception as e:
    #     print(type(e).__name__, repr(e))
    #     exc_type, exc_value, exc_traceback = sys.exc_info()
    #     # Extract the line number from the traceback object
    #     line_number = exc_traceback.tb_lineno
    #     print(f"Error: {type(e).__name__} occurred on line: {line_number} execution value: {exc_value}")

    maize_x = Path.home() / 'maize.apsimx'
    # mod = ApsimModel('Maize', out_path=maize_x)
    model = ApsimModel(maize_x, out_path=Path.home() / 'm.apsimx')
    model.get_soil_from_web(simulation_name=None, lonlat=(-89.9937, 40.4842), thinnest_layer=150, adjust_dul=True)
    # mod.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541))
    model.preview_simulation()
