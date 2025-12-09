import os.path
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.pythonet_config import Models


class OptimizationBase(ApsimModel):

    def __init__(self, model: Union[Path, dict, str], out_path: Union[str, Path] = None, out: Union[str, Path] = None,
                 lonlat: tuple = None, soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,
                 thickness_values: list = None, set_wd=None, **kwargs):

        super().__init__(model, out_path, set_wd, **kwargs)
        self.soil_type = None
        self.SWICON = None
        self.lonlat = lonlat
        self.n_layers = bottomdepth / thickness
        bm = bottomdepth * 10

        self.soil_series = soil_series
        self.thickness = thickness
        self.out_path = out_path or out
        self._thickness_values = thickness_values
        self.copy = True
        self.parameters = []
        self.params = []

        if not isinstance(thickness_values, np.ndarray):
            self.thickness_values = np.array(self._thickness_values,
                                             dtype=np.float64)
        else:
            self.thickness_values = self._thickness_values
        if kwargs.get('experiment', False):
            self.create_experiment()

    def check_kwargs(self, path, **kwargs):
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

    def add_parameters(self, path: str, *, bounds=None, v_type, **kwargs):
        """
        Add a parameter set associated with a given APSIM model path.

        Parameters
        ----------
        path : str
            The full APSIM component path where the parameters should be edited.
        **kwargs :
            Key-value pairs of parameters to be updated. One and only one value should be
            designated ("?", '', "") to indicate the parameter to be optimized. remember '' is not the same as ''

        Notes
        -----
        - Only one parameter per call should be marked with either "?" or 'fill' (to be filled or edited during calibration).
        - Duplicate entries are ignored.
        @param v_type: var type e.g., int, str, float, bool
        @param bounds: lower and upper limits of x variable
        """
        # Pre-check parameter keys/values for validity in APSIM context
        self.check_kwargs(path, **kwargs)

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
        args = (path, bounds, v_type, kwargs)
        out_args = dict(zip(['path', "v_type", 'bounds', 'kwargs'], args))
        if out_args not in self.params:
            self.params.append(out_args)

    def set_param(self, path, x_value):
        st = path.split('.')
        param_name = st[-1]
        base_path = st[:-1]
        base_path = '.'.join(base_path)
        self.edit_model_by_path(base_path, **{param_name: x_value})

    @timer
    def _do_model_edit(self, x):
        """Objective function: apply `x` values to APSIM model during parameter optimization or calibration."""
        if not self.parameters:
            raise ValueError("No parameters defined for calibration.")

        if len(x) != len(self.parameters):
            raise ValueError(f"Expected {len(self.parameters)} parameters' values, but got {len(x)}.")

        for i, value in enumerate(x):
            path, param_dict = self.parameters[i]
            updated_params = {k: value for k in param_dict.keys() if param_dict[k] in ('?', "")}
            pp = param_dict | updated_params  # Python 3.9+: right-hand overrides left-hand

            self.edit_model_by_path(path=path, **pp)

    @staticmethod
    def is_incomplete_date(series: pd.Series) -> bool:
        """
        Determine if a pandas datetime series was likely created from year, month or days only values.
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

    @property
    def n_vars(self):
        return len(self.parameters)

    def clean_data(self, obs: Union[pd.DataFrame, str, Path], *,
                   data_table: str,
                   output_column: str,
                   time_step: str = 'Year',
                   obs_time_column: str = 'year'):
        """
        Align observed data with APSIM simulation results.

        Parameters
        ----------
        obs : Union[pd.DataFrame, str, Path]
            The observed data, either as a DataFrame or a file path to a CSV.
        data_table : str
            The name of the APSIM report table to extract simulation results from.
        output_column : str
            The output column of interest from the APSIM results.
        time_step : str, default 'Year'
            One of {'Year', 'Month', 'Day'} or full date.
        obs_time_column : str, default 'year'
            The time column in the observed data.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns: [date, time_step, apsim, observed]
        """
        DATE = 'date'

        # Accept a file path or DataFrame
        match obs:
            case pd.DataFrame():
                obs = obs.copy(deep=True)
            case str() | Path():
                obs = pd.read_csv(str(obs))
            case _:
                raise TypeError(f"Unsupported type for 'obs': {type(obs)}")

        if obs_time_column not in obs.columns:
            raise KeyError(f"Column '{obs_time_column}' not found in observed data")

        obs_date = pd.to_datetime(obs[obs_time_column])

        def _proc_df(_obs, _data_table, column, _time_step, _obs_time_column):
            time = _time_step.capitalize()
            if time not in {'Year', 'Month', 'Day'}:
                raise ValueError("`time_step` must be one of {'Year', 'Month', 'Day'}")

            # Clock variable to add to APSIM
            if self.is_incomplete_date(obs_date):
                clock_variable = f'[Clock].Today.{time} as {_obs_time_column}'
            else:
                clock_variable = f'[Clock].Today as {_obs_time_column}'

            # Validate report existence
            available_reports = self.inspect_model('Models.Report', fullpath=False)
            if not isinstance(_data_table, str):
                raise TypeError("Data table name must be a string")
            if not available_reports:
                raise ValueError("No report tables found in the APSIM model")
            if _data_table not in available_reports:
                suggestion = 'Did you mean' if len(available_reports) == 1 else 'Did you mean any of'
                raise ValueError(
                    f"Data table '{_data_table}' not found. {suggestion} '{', '.join(available_reports)}'?"
                )

            # Inject Clock variable to report
            self.add_report_variable(
                [clock_variable, f'[Clock].Today as {DATE}'],
                _data_table
            )

            dtf = self.run(_data_table).results

            if column not in dtf.columns:
                raise ValueError(f"Column '{column}' not found in simulation output table.")

            obs_time = _obs[_obs_time_column]
            sdf = dtf[dtf[_obs_time_column].isin(obs_time)]

            if sdf.shape[0] != _obs.shape[0]:
                raise ValueError(
                    f"Mismatch in row count:\nSimulated: {sdf.shape[0]}\nObserved: {_obs.shape[0]}"
                )

            _obs.sort_values(by=_obs_time_column, inplace=True)

            result = pd.DataFrame()
            if DATE != _obs_time_column and self.is_incomplete_date(obs_date):
                result[DATE] = sdf[DATE]
            elif self.is_incomplete_date(obs_date):
                result[DATE] = _obs[_obs_time_column]

            result[_time_step] = sdf[_obs_time_column]
            result['apsim'] = sdf[output_column]
            result['observed'] = _obs[output_column]

            return result

        return _proc_df(obs, _data_table=data_table, column=output_column,
                        _time_step=time_step, _obs_time_column=obs_time_column)
