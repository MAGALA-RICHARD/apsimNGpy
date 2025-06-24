from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

from apsimNGpy.core.apsim import ApsimModel


class Calibrator(ApsimModel):

    def __init__(self, model: Union[Path, dict, str], out_path: Union[str, Path] = None, out: Union[str, Path] = None,
                 lonlat: tuple = None, soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,
                 thickness_values: list = None, run_all_soils: bool = False, set_wd=None, **kwargs):

        super().__init__(model, out_path, set_wd, **kwargs)
        self.soiltype = None
        self.SWICON = None
        self.lonlat = lonlat
        self.Nlayers = bottomdepth / thickness
        bm = bottomdepth * 10
        if thickness_values is None:
            thickness_values = self.auto_gen_thickness_layers(max_depth=bm, n_layers=int(self.Nlayers))
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


    def auto_calibrate(self, obs, *, data_table, output_column, time_column='year'):
        DATE = 'date'

        def _proc_df(obs, data_table, column, time_step):
            time = time_step.capitalize()
            a_reports = self.inspect_model('Models.Report', fullpath=False)
            assert isinstance(data_table, str), 'Data table must be a scalar'
            if data_table not in a_reports:
                raise ValueError(f"Data table {data_table} not found in {a_reports} ")

            self.add_report_variable([f'[Clock].Today.{time} as {time}', f'[Clock].Today as {DATE}'], data_table)

            dtf = self.run(data_table).results
            columns = dtf.columns.tolist()
            if column not in columns:
                raise ValueError(f'Column {column} not found in the data table')
            obs_time = obs[time_step]
            sdf = dtf[dtf[time].isin(obs_time)]
            if sdf.shape[0] != obs.shape[0]:
                raise ValueError(
                    f"observed data does not match expected simulation results, apsim simulated data has ({sdf.shape[0]} rows)\n observed has ({obs.shape[0]} rows)")
            obs.sort_values(inplace=True, by=time_step)
            ans = pd.DataFrame()
            ans[DATE] = sdf[DATE]
            ans[time_step] = sdf[time]
            ans['apsim'] = sdf[output_column]
            ans['observed'] = obs[output_column]

            return ans

        match obs:
            case pd.DataFrame():
                obs = obs.copy()
            case str():
                obs = pd.read_csv(obs)
            case Path():
                obs = pd.read_csv(obs)
            case _:
                raise TypeError(f"Unsupported type for 'obs': {type(obs)}")

        # validate if the data provided is present

        return _proc_df(obs, data_table=data_table, column=output_column, time_step=time_column)


if __name__ == "__main__":
    obs = r'D:\package\synthetic_observed.csv'
    df = pd.read_csv(obs)
    mod = Calibrator('Maize')
    ar = df.to_numpy(copy=True)
    df= mod.auto_calibrate(obs=df, data_table='Report', output_column='Yield')
