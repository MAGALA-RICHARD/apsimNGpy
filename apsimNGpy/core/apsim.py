"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
"""
import logging, pathlib
from builtins import str
from typing import Union, Any
import os
import numpy as np
import time
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile
import apsimNGpy.manager.weathermanager as weather
import pandas as pd
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

# constants
REPORT_PATH = {'Carbon': '[Soil].Nutrient.TotalC/1000 as dyn', 'DUL': '[Soil].SoilWater.PAW as paw', 'N03':
    '[Soil].Nutrient.NO3.ppm as N03'}


# decorator to monitor performance


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
        self.soil_type = None
        self.SWICON = None
        self.lonlat = lonlat
        self.n_layers = bottomdepth / thickness
        bm = bottomdepth * 10
        if thickness_values is None:
            thickness_values = self.auto_gen_thickness_layers(max_depth=bm, n_layers=int(self.n_layers))
        self.soil_series = soil_series
        self.thickness = thickness
        self.out_path = out_path or out
        self._thickness_values = thickness_values
        self.copy = True
        self.run_all_soils = run_all_soils
        if not isinstance(thickness_values, np.ndarray):
            self.thickness_values = np.array(self._thickness_values,
                                             dtype=np.float64)  # apsim uses floating digit number
        else:
            self.thickness_values = self._thickness_values
        if kwargs.get('experiment', False):
            self.create_experiment()
        self.base_simulations = None

    @property
    def thickness_values(self):
        return self._thickness_values

    @thickness_values.setter
    def thickness_values(self, values):
        self._thickness_values = values

    def show_cropsoil_names(self, simulations):
        for simu in self.find_simulations(simulations):
            pysoil = simu.FindDescendant[Physical]()
            soil_crop = pysoil.FindAllDescendants[SoilCrop]()
            # can be use to target specific crop
            for cropLL in soil_crop:
                print(cropLL.Name)

    def _replace_cropsoil_names(self, simulations, existing_crop_names, new_cropname):
        for simu in self.find_simulations(simulations):
            pysoil = simu.FindDescendant[Physical]()
            soil_crop = pysoil.FindAllDescendants[SoilCrop]()

            for crops in soil_crop:
                if crops.Name == existing_crop_names:
                    crops.Name = new_cropname

    def adjust_dul(self, simulations: Union[tuple, list] = None):
        """
        - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly
        - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

        ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

        ``returns``:
            model object
        """
        duL = self.extract_any_soil_physical('DUL', simulations)
        print(duL)
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
                    print(d)
                else:
                    duls[enum] = d
            if not simulations:
                soil_object = self.Simulations.FindDescendant[Soil]()

                soilsy = soil_object.FindDescendant[Physical]()
                soilsy.DUL = duls
        self.save()
        # self.replace_any_soil_physical('DUL', simulations, duL)
        return self

    def _get_SSURGO_soil_profile(self, lonlat: tuple, run_all_soils: bool = False):
        self.lonlat = None
        self.lonlat = lonlat
        self.dict_of_soils_tables = {}
        if not self.run_all_soils:
            self.soil_tables = DownloadsurgoSoiltables(self.lonlat, select_componentname=self.soil_series)
            for ss in self.soil_tables.componentname.unique():
                self.dict_of_soils_tables[ss] = self.soil_tables[self.soil_tables['componentname'] == ss]

        if self.run_all_soils:
            self.dict_of_soils_tables = {}
            self.soil_tables = DownloadsurgoSoiltables(self.lonlat)

            self.percent = self.soil_tables.prcent.unique()
            # create a dictionary of soil series
            self.unique_soil_series = self.soil_tables.componentname.unique()

            new_col = []
            for i in range(len(self.soil_tables['chkey'])):
                xi = str(list(self.soil_tables['chkey'])[i]) + "-" + list(self.soil_tables['componentname'])[i]
                new_col.append(xi)
            self.soil_tables["ch_comp"] = list(new_col)
            self.grouped = self.soil_tables.groupby('ch_comp')['prcent'].unique().apply(lambda x: x[0])
            self.component_percent_dict = self.grouped.to_dict()
            for ss in self.soil_tables.componentname.unique():
                self.dict_of_soils_tables[ss] = self.soil_tables[self.soil_tables['componentname'] == ss]
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

    def replace_soils(self, lonlat: tuple, simulation_names: Union[tuple, list], verbose=False):
        self.thickness_replace = None
        if isinstance(self.thickness_values, np.ndarray):  # since it is alreaduy converted to an array
            self.thickness_replace = self.thickness_values

        else:
            tv = np.tile(float(self.thickness), int(self.n_layers))
            self.thickness_replace = tv
        pss = self._get_SSURGO_soil_profile(lonlat)
        for keys in pss.dict_of_soils_tables.keys():
            self.soil_type = keys
            if verbose:
                print("Padding variabales for:", keys)
            self.soil_profile = OrganiseSoilProfile(self.dict_of_soils_tables[keys],
                                                    thickness_values=self.thickness_values,
                                                    thickness=self.thickness)
            missing_properties = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame
            physical_calculated = missing_properties[0]
            self.organic_calcualted = missing_properties[1]
            self.cropdf = missing_properties[2]
            # ps = self._get_SSURGO_soil_profile()

            # self.thickness_replace = list(np.full(shape=int(self.n_layers,), fill_value=self.thickness*10,  dtype=np.float64))
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
                # replace the organic soils
            for simu in self.find_simulations(simulation_names):
                organic = simu.FindDescendant[Organic]()
                organic.Thickness = self.thickness_replace
                organic.SoilCNRatio = self.organic_calcualted.SoilCNRatio
                organic.FBiom = self.organic_calcualted.FBiom
                organic.FOM = self.organic_calcualted.FOM
                organic.FInert = self.organic_calcualted.FInert
                organic.Carbon = self.organic_calcualted.Carbon
                chemical = simu.FindDescendant[Chemical]()
                chemical.Thickness = self.thickness_replace
                # to do fix the crop management may use FindAllDescendants. it worked
                # XF = np.full(shape=self.n_layers, fill_value=1,  dtype=np.float64)
                XF = np.tile(float(1), int(self.n_layers))

            for simu in self.find_simulations(simulation_names):
                soil_crop = pysoil.FindAllDescendants[SoilCrop]()
                # can be use to target specific crop
                for cropLL in soil_crop:
                    cropLL.LL = pysoil.AirDry
                    cropLL.KL = self.organic_calcualted.cropKL
                    cropLL.XF = XF
                    cropLL.Thickness = self.thickness_replace
            if verbose:
                print("soil replacement complete")
            # self.run()
        return self
        # print(self.results)

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
        physical_calculated = soil_tables[0]
        self.organic_calcualted = soil_tables[1]
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

    # print(self.results)

    def _change_met_file(self, lonlatmet: tuple = None,
                         simulation_names: Union[tuple, list] = None):  # to be accessed only in this class
        """_similar to class weather management but just in case we want to change the weather within the subclass
        # uses existing start and end years to download the weather data

        """
        if lonlatmet == None:
            self.lonlat = self.lonlat
        else:
            self.lonlat = lonlatmet

        start, end = self.extract_start_end_years()
        wp = weather.get_met_from_day_met(self.lonlat, start, end)
        wpath = os.path.join(os.getcwd(), wp)
        wpath = os.path.join(os.getcwd(), wp)
        if self.simulation_names:
            sim_name = list(self.simulation_names)
        else:
            sim_name = self.simulation_names  # because it is a property decorator
        self.replace_met_file(wpath, sim_name)
        return self

    def run_edited_file(self, table_name=None):
        # to be deprecated
        """

            :param table_name (str): repot table name in the database

        """
        return self.run(report_name=table_name).results

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

    def auto_gen_thickness_layers(self,
                                  max_depth, n_layers=10, thin_layers=3, thin_thickness=100,
                                  growth_type="linear", thick_growth_rate=1.5
                                  ):
        """
        Generate layer thicknesses from surface to depth, starting with thin layers and increasing thickness.

        Args:
            ``max_depth`` (float): Total depth in mm.

            ``n_layers`` (int): Total number of layers.

            ``thin_layers`` (int): Number of initial thin layers.

            ``thin_thickness`` (float): Thickness of each thin layer.

            ``growth_type`` (str): 'linear' or 'exponential'.

            ``thick_growth_rate`` (float): Growth factor for thick layers (e.g., +50% each layer if exponential).

        ``Returns:``
            List[float]: List of layer thicknesses summing to max_depth.
        """
        from math import pow

        assert 0 < thin_layers < n_layers, "thin_layers must be less than total layers"
        assert thin_thickness > 0, "thin_thickness must be positive"
        assert growth_type in ['linear', 'exponential'], "Invalid growth_type"

        thick_layers = n_layers - thin_layers
        thin_total = thin_layers * thin_thickness
        remaining_depth = max_depth - thin_total

        if remaining_depth <= 0:
            raise ValueError("Thin layers consume more than total depth.")

        # --- Step 1: Thin layers ---
        thin_parts = [thin_thickness] * thin_layers

        # --- Step 2: Thick layers ---
        if growth_type == "linear":
            # We'll solve an arithmetic series: a + (a + d) + ... = remaining_depth
            # Assume a = base_thick, d = constant increment
            # So: total = thick_layers * a + d * (0 + 1 + ... + thick_layers-1)
            increments = list(range(thick_layers))
            sum_increments = sum(increments)
            base_thick = (remaining_depth - sum_increments * thick_growth_rate) / thick_layers
            thick_parts = [base_thick + i * thick_growth_rate for i in increments]

        elif growth_type == "exponential":
            # Geometric series: a*r^0 + a*r^1 + ... = remaining_depth
            r = thick_growth_rate
            denom = sum([pow(r, i) for i in range(thick_layers)])
            a = remaining_depth / denom
            thick_parts = [a * pow(r, i) for i in range(thick_layers)]

        # Final result
        layers = thin_parts + thick_parts

        # Precision check
        total = sum(layers)
        if abs(total - max_depth) > 1e-6:
            # Final adjustment to fix floating point error
            layers[-1] += max_depth - total
        layers.sort()
        layers = [int(i) for i in layers]

        return layers

    def replace_soil_profile_from_web(self, **kwargs):
        from apsimNGpy.manager.weathermanager import _is_within_USA_mainland
        lon_lat = kwargs.get('lonlat', self.lonlat)
        if not _is_within_USA_mainland(lon_lat):
            raise ValueError(f"{lon_lat} is not within USA. coordnates outside USA are not supported yet")
        thickness = kwargs.get('thickness', 20)
        sim_name = kwargs.get('sim_name', self.simulation_names)
        assert lon_lat, 'Please supply the lonlat'
        sp = DownloadsurgoSoiltables(lon_lat)
        sop = OrganiseSoilProfile(sp, thickness, thickness_values=self.thickness_values).cal_missingFromSurgo()

        if self.thickness_values is None:
            self.thickness_values = self.auto_gen_thickness_layers(max_depth=2200, n_layers=int(self.n_layers),
                                                                   thin_layers=3, thin_thickness=100,
                                                                   growth_type='linear', thick_growth_rate=50)
        self.thickness_replace = self.thickness_values.copy()
        self.replace_downloaded_soils(sop, simulation_names=sim_name)
        self.save()
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
    from apsimNGpy.core.base_data import load_default_simulations

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

    mod = ApsimModel('Maize')
    maize_x = Path.home() / 'maize.apsimx'
