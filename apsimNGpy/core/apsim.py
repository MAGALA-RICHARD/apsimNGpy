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
        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> path_model = load_default_simulations(crop='Maize', simulations_object=False)
        >>> model = ApsimModel(path_model, set_wd=Path.home())# replace with your path
        >>> model.run(report_name='Report') # report is the default replace as needed
    """

    def __init__(self, model: Union[os.PathLike, dict, str], out_path: Union[str, Path] = None,
                 out: Union[str, Path] = None,
                 lonlat: tuple = None, soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,

                 thickness_values: list = None, run_all_soils: bool = False, set_wd=None, **kwargs):
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
                          adjust_dul: bool = False):
        """
        Pull SSURGO-derived soil for a given location
        populate the APSIM simulation’s soil sections

        Parameters
        ----------
        ``simulation``: simulation names (str, tuple, optional): Target a simulation or simulations. if None all simulations will be updated with the downloaded soil profile

        ``lonlat`` (lon, lat) tuple
            Location for SSURGO download. Ignored if `soil_tables` is given.

        ``soil_series`` : str
            Optional component/series filter for SSURGO selection. Be careful if not found an error is raised, safest is to leve it to None, and adormiant one is returned

        ``thickness_sequence`` : sequence[float]
            Explicit thickness layout per layer. If auto, it will be auto-generated from n_layers, m=thickness_growth_rate, thinnest layer and max_depth
            thickness_value if thickness_sequence is None this value must be provided to generate the thickness sequence and together with max_depth m ust be provided

       ``thickness_value`` (int, optional): The thickness for all the soil layers. if both thickness_sequence and thickness_value are provided, priority is given to thickness_sequence

        ``max_depth`` (int, optional): Maximum depth of the soil bottom layers. If not provided, it defaults 2400 mm:

        ``edit_sections`` : sequence[str]
            Which sections to edit. Defaults to all:
            ("physical", "organic", "chemical", "water", "water_balance", "solutes", "soil_crop", 'meta_info')
            note that if a few sections are edited with different number of soil layers, APSIm will throw an error during run time

        ``attach_missing_sections`` : bool
            If True, create/attach missing section nodes before editing.

        ``additional_plants``: sequence[str]. if there were recently added crops, that need crop soil conditions such as KL

        ``adjust_dul``: sometimes the SAT value(s) is/are above the DUL threshold, so adjustment is needed, else,
         APSIM with throw an errors, which will also cause apsimNGpy to respond with APsimRuntimeError during runtime

        Returns
        ----------
        self for method chaining

        Notes
        -----
        - Assumes soil sections live under a Soil node; missing sections are attached there when
          `attach_missing_sections=True`.
        - Uses your optimized SoilManager methods (vectorized + .NET double[] marshaling).

        Raises

        - ValueError
        -------------------------
         - when a thickness sequence is not auto and has zero  or less than zero values
         - when a thickness sequence is none and thickness value is none
         - if thickness value and max depth do not match in-terms of units

        Side Effects
        ------------
        - Mutates the target APSIM simulation tree in place:
          - Creates and attaches a **Soil** node if missing when ``attach_missing_sections=True``.
          - Creates and/or updates child sections (``Physical``, ``Organic``, ``Chemical``,
            ``Water``, ``WaterBalance``, ``SoilCrop``) as requested in ``edit_sections``.
          - Overwrites section properties (e.g., layer arrays such as ``Depth``, ``CLL``, ``SAT``,
            ``BD``, solute columns, crop KL/XF, etc.) with values derived from the downloaded profile.
        - May add **SoilCrop** children for any names in ``additional_plants`` (and populate their
          properties), potentially replacing previously set values.
        - Performs **network I/O** to retrieve SSURGO tables when ``lonlat`` is provided (runtime and
          results depend on internet availability and the external service).
        - Emits **log messages** (warnings/info) via the package logger (e.g., when attaching nodes,
          when both thickness controls are provided, or when sections/columns are absent).
        - Caches the computed soil profile **within the helper manager instance** during execution,
          but does not persist it globally; the APSIM model in memory remains modified after return.
        - Does **not** write any files or save the APSIM document; call the model’s save method separately
          if persistence to disk is desired.
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
            model object
        """
        duL = self.extract_any_soil_physical('DUL', simulations)

        saT = self.extract_any_soil_physical('SAT', simulations)
        for sim in duL:
            duls = duL[sim]

            sats = saT[sim]
            for enum, (s, d) in enumerate(zip(sats, duls)):
                # first check if they are equal
                if d >= s:
                    # if d is greater than s, then by what value, we need this value to add it to 0.02
                    #  to be certain all the time that dul is less than s we subtract the summed value
                    diff = d - s
                    duls[enum] = d - (diff + 0.02)

                else:
                    duls[enum] = d
            if not simulations:
                soil_object = self.Simulations.FindDescendant[Soil]()

                soilsy = soil_object.FindDescendant[Physical]()
                soilsy.DUL = duls
        self.save()
        # self.replace_any_soil_physical('DUL', simulations, duL)
        return self

    @staticmethod
    def get_weather_online(lonlat: tuple, start: int, end: int):
        wp = weather.get_met_from_day_met(lonlat, start=start, end=end)
        wpath = os.path.join(os.getcwd(), wp)
        return wpath

    @property
    def get_unique_soil_series(self):
        """this function collects the unique soil types

        Args:
            lonlat (_tuple_): longitude and latitude of the target location

        """
        try:
            soil_tables = DownloadsurgoSoiltables(self.lonlat)
            pr = soil_tables.prcent.unique()

            grouped = soil_tables.groupby('componentname')[
                'prcent'].unique()  # .agg(list) #.unique().apply(lambda x: x[0])
            component_percent_dict = grouped.to_dict()
            return component_percent_dict
        except Exception as e:
            raise

    def replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs):
        """
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
        ``report_name`` : str, optional (default: 'Report')
            The name of the aPSim report to be used for simulation results.

        ``start`` : str, optional
            The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.

        ``end`` : str, optional
            The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.

        ``spin_var`` : str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
            The variable representing the child of spin-up operation. Supported values are 'Carbon' or 'DUL'.

        ``Returns:``
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

    def replace_met_from_web(self, lonlat, start_year, end_year, file_name=None):
        if not file_name:
            file_name = self.path.strip(".apsimx") + "_w_.met"
        w_f = weather.get_met_from_day_met(lonlat, start=start_year, end=end_year, filename=file_name)
        wf = os.path.abspath(w_f)
        self.replace_met_file(weather_file=wf)
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

        """Read APSIM NG datastore for the current model. Raises FileNotFoundError if the model was initialized from 
        default models because those need to be executed first to generate a database.

        The rationale for this method is that you can just access the results from the previous session without running it,
        if the database is in the same location as the apsimx file.

        Since apsimNGpy clones the apsimx file, the original file is kept with attribute name `_model`, that is what is
        being used to access the dataset

        table (str): name of the database table to read if none of all tables are returned

         Returns: pandas.DataFrame"""
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

        raise ValueError(f"{table} is not a valid table name associated with apsimx {self._model}")


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
    model.get_soil_from_web(simulation_name=None, lonlat=(-89.9937, 40.4842), thinnest_layer=150)
    # mod.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541))
    model.preview_simulation()
