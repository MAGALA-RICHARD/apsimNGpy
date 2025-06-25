import os.path
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.pythonet_config import Models


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
        self.parameters = []
        self.run_all_soils = run_all_soils
        if not isinstance(thickness_values, np.ndarray):
            self.thickness_values = np.array(self._thickness_values,
                                             dtype=np.float64)  # apsim uses floating digit number
        else:
            self.thickness_values = self._thickness_values
        if kwargs.get('experiment', False):
            self.create_experiment()

    def evaluate_kwargs(self, path, **kwargs):
        mod_obj = self.Simulations.FindByPath(path)
        if mod_obj is None:
            raise ValueError(f"Could not find model associated with path {path}")
        v_mod = mod_obj.Value
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
                    raise ValueError(f"{met_file} file name is need use key word 'met_file' or 'weather_file'")
            case Models.Surface.SurfaceOrganicMatter:
                accept = {'SurfOM', 'InitialCPR', 'InitialResidueMass',
                          'InitialCNR', 'IncorporatedP', }
                if kwargs == {}:
                    raise ValueError(f"Please supply at least one parameter: value \n '{', '.join(accept)}' for {path}")
                _raise_value_error(path, accept, kas)
            case Models.PMF.Cultivar:
                accept = {}

    def add_parameters(self, path: str, **kwargs):
        """
        Add a parameter set associated with a given APSIM model path.

        Parameters
        ----------
        path : str
            The full APSIM component path where the parameters should be edited.
        **kwargs :
            Key-value pairs of parameters to be updated. One and only one value should be
            designated ("?", 'fill') to indicate the parameter to be optimized.

        Notes
        -----
        - Only one parameter per call should be marked with either "?" or 'fill' (to be filled or edited during calibration).
        - Duplicate entries are ignored.
        """
        # Pre-check parameter keys/values for validity in APSIM context
        self.evaluate_kwargs(path, **kwargs)

        # Allow only one parameter to be unspecified as "?" or 'fill'
        missing = [k for k, v in kwargs.items() if v in ("?", 'fill')]
        if len(missing) == 0:
            raise ValueError("At least one parameter value must be left unspecified (e.g., '') for optimization.")
        if len(missing) > 1:
            raise ValueError("Only one parameter value should be unspecified per call.")

        # Check for invalid types (optional)
        for k, v in kwargs.items():
            if not isinstance(k, str):
                raise TypeError(f"Parameter name {k!r} must be a string.")

        # Avoid duplicates
        entry = (path, kwargs)
        if entry not in self.parameters:
            self.parameters.append(entry)

    @timer
    def _do_model_edit(self, x):
        """Objective function: apply `x` values to APSIM model during parameter optimization or calibration."""
        if not self.parameters:
            raise ValueError("No parameters defined for calibration.")

        if len(x) != len(self.parameters):
            raise ValueError(f"Expected {len(self.parameters)} parameters, but got {len(x)}.")

        for i, value in enumerate(x):
            path, param_dict = self.parameters[i]
            updated_params = {k: value for k in param_dict.keys() if param_dict[k] == '?'}
            self.edit_model_by_path(path=path, **updated_params)

    @staticmethod
    def is_incomplete_date(series: pd.Series) -> bool:
        """
        Determine if a pandas datetime series was likely created from year, month or days onlyvalues.
        Assumes the default day and month values are 1 (i.e., January 1st).
        """
        if not pd.api.types.is_datetime64_any_dtype(series):
            raise ValueError("Input series must be datetime type")

        # Check if all dates are January 1st
        return (series.dt.month == 1).all() and (series.dt.day == 1).all()

    @staticmethod
    def _match(text):
        import re
        pattern = r'\[[^\]]+\]\.\w+'
        return re.findall(pattern, text)

    def _process_data(self, obs, *, data_table, output_column, time_step='Year', obs_time_column='year'):
        """

        @param obs:
        @param data_table:
        @param output_column:
        @param time_step: Must be 'Year', 'Month', 'Day''
        @param obs_time_column:
        @return:
        """
        DATE = 'date'
        obs_ser = obs[obs_time_column]
        obs_date = pd.to_datetime(obs_ser)

        def _proc_df(_obs, _data_table, column, _time_step, _obs_time_column):

            time = _time_step.capitalize()
            if time not in {'Year', 'Month', 'Day'}:
                raise ValueError('Invalid time step')

            if self.is_incomplete_date(obs_date):
                time_stem_spec = f'[Clock].Today.{time} as {_obs_time_column}'
            else:
                time_stem_spec = f'[Clock].Today as {_obs_time_column}'

            a_reports = self.inspect_model('Models.Report', fullpath=False)
            assert isinstance(_data_table, str), 'Data table must be a scalar'
            if not a_reports:
                raise ValueError('No report table was found')
            if _data_table not in a_reports:
                scalar = 'Did you mean'
                many = 'Did you mean any of the following'
                msg = scalar if len(a_reports) == 1 else many
                raise ValueError(f"Data table {_data_table} not found. {msg} '{','.join(a_reports)}'? ")

            self.add_report_variable(
                [time_stem_spec, f'[Clock].Today as {DATE}'],
                _data_table)

            dtf = self.run(_data_table).results
            columns = dtf.columns.tolist()
            if column not in columns:
                raise ValueError(f'Column {column} not found in the data table')
            obs_time = _obs[_obs_time_column]
            sdf = dtf[dtf[_obs_time_column].isin(obs_time)]
            if sdf.shape[0] != _obs.shape[0]:
                raise ValueError(
                    f"observed data does not match expected simulation results, apsim simulated data has ({sdf.shape[0]} rows)\n observed has ({_obs.shape[0]} rows)")
            _obs.sort_values(inplace=True, by=_time_step)
            ans = pd.DataFrame()
            if DATE != obs_time_column:
                if self.is_incomplete_date(obs_date):
                    ans[DATE] = sdf[DATE]
            ans[_time_step] = sdf[_obs_time_column]
            ans['apsim'] = sdf[output_column]
            ans['observed'] = _obs[output_column]

            return ans

        match obs:
            case pd.DataFrame():
                obs = obs.copy()
            case str() | Path():
                obs = pd.read_csv(str(obs))
            case _:
                raise TypeError(f"Unsupported type for 'obs': {type(obs)}")

        # validate if the data provided is present

        return _proc_df(obs, _data_table=data_table, column=output_column, _obs_time_column=obs_time_column,
                        _time_step=time_step)


if __name__ == "__main__":
    obs = r'D:\package\synthetic_observed.csv'
    df = pd.read_csv(obs)
    mod = Calibrator('Maize')
    ar = df.to_numpy(copy=True)
    df = mod._process_data(obs=df, data_table='Report', output_column='Yield', obs_time_column='year', time_step='year')
    mod.add_parameters('.Simulations.Simulation.Field.SurfaceOrganicMatter', InitialCNR='?', InitialCPR=10)
    mod._do_model_edit([23])
