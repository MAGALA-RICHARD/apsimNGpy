from apsimNGpy.core.apsim import ApsimModel
from os.path import realpath, dirname, join, abspath, basename
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile
from ast import literal_eval
from pathlib import Path
from apsimNGpy.parallel.process import custom_parallel
import pandas as pd
from typing import Union
class Assembly:
    def __init__(self, data, sim_id, model, tag ='onion', wd =None, location_column='lon_lat',
                 water_model = "swat", end = 2022, start =1986):

        self.data = data
        self.sim_id = sim_id
        self.model= model
        self.start = start
        self.end =end
        self.tag = tag
        self.water_model = water_model
        if wd:
            self.w_d = wd
        else:
            self.w_d = dirname(abspath(self.file_path))
        if data.get(location_column)  or data.get('lon_lat'):
           self.cod_name = data['location_column']    
        else:
            raise ValueError("You must supply the name of the lonlat column or set it to lon_lat")
        
    def create_simulation_ids(self):
        l_ength = self.data.shape[0]
        self.data['sim_id'] = [f"{i}-{j}" for j in range(l_ength) for i in data[self.sim_id]]
        self.data['model_id'] = ApsimModel(self.model).replicate_file(l_ength, tag = self.tag, path=self.w_d)
        return self

    def down_soils_and_weather(self, sim_id, **kwargs):
        sth_values = self.kwargs.get("soil_thickness_values")
        if sth_values:
            thickness_array = sth_values
            if thickness_array[0] >30 and self.water_model == 'swim':
                raise ValueError(f"SWIM model requires a very narrow top soil thickness, adjust {thickness_array[0]}: accordingly")
        else:
            thickness_swim = [30, 150, 200, 200, 200, 250, 300, 300, 400, 500]
            thickness_SWAT = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
            thickness_array = thickness_swim if self.water_model =='swim' else thickness_SWAT
        lon_lat = data.loc[data[self.sim_id] == sim_id, self.cod_name].iloc[0]
        if isinstance(lon_lat, np.ndarray):
            lon_lat = literal_eval(lon_lat.values)
        model_name =  self.data.loc[data[self.sim_id] == sim_id, 'model_id'].iloc[0]
        model = ApsimModel(model_name, thickness_values=thickness_array)
        met_name = basename(model_name).srip('apsimx') + '.met'
        model.replace_met_from_web(lon_lat, self.start, self.end, file_name=met_name)
        sp  = DownloadsurgoSoiltables(lon_lat, model, self)
        sop = OrganizeAPSIMsoil_profile(sp, 20).cal_missingFromSurgo()
        save_dir = Path(self.w_d).joinpath("apsim_files")
        save_dir.mkdir(exist_ok=True)
        self.data['dest'] = save_dir
        save_to_out_path = realpath(save_dir) + sim_id + ".apsimx"
        csr =None
        if adjust_rue:
            if isinstance(sop[3], pd.Series):
                csr = int(sop[3].sample(1).iloc[0]) / 100

                # print(csr)
                rue = csr ** np.log(1 / csr) * kwargs.get('RUE',2)
                com = '[Leaf].Photosynthesis.RUE.FixedValue',
                model.edit_cultivar(CultivarName="B_110", commands=com,
                                    values=rue)
                data.loc[data['SIMID'] == SIMID, 'CSR'] = csr
        data['CSR'] = csr
        model.save(out_path =  save_to_out_path)
    def download_csr(self, sim_id):
        def _wo_rk():
            csr =None
            lon_lat = self.data.loc[data[self.sim_id] == sim_id, self.cod_name].iloc[0]
            sp = DownloadsurgoSoiltables(lon_lat, model, self)
            sop = OrganizeAPSIMsoil_profile(sp, 20).cal_missingFromSurgo()
            if isinstance(sop[3], pd.Series):
               csr=  int(sop[3].sample(1).iloc[0]) / 100
            self.data.loc[data[self.sim_id] == sim_id, 'CSR']  =csr
            return self.data[data[self.sim_id] == sim_id]
        csr = custom_parallel(_wo_rk, self.data[self.sim_id])
        csr_list = [i for i in csr if i is not None]
        self.data = pd.concat(csr_list)
        return self


    def create(self):
        custom_parallel(self.down_soils_and_weather, self.data[self.sim_id])

        
        