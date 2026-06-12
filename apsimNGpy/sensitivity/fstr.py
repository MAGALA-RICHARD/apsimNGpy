import numpy as np
import pandas as pd
from apsimNGpy import is_scalar


def _clean_array(arr):
    """Convert SALib outputs to numpy arrays and remove masks."""
    if np.ma.isMaskedArray(arr):
        arr = arr.filled(np.nan)

    return np.asarray(arr)


def format_salib_results(ans, method=None, outputs=None):
    data = []
    response_name = 'Response'

    def create_df(i):
        for k, v in i.items():
            v = list(v) if not is_scalar(v) else v
            edf[k] = v
        return edf

    method_lower_case = method.lower()
    match method_lower_case:
        case 'morris' | 'fast' | 'sobol' | 'delta':
            edf = pd.DataFrame()
            if isinstance(ans, list):
                morris = ans
                for i in morris:
                    create_df(i)
            elif isinstance(ans, dict):
                create_df(ans)

            edf[response_name] = outputs
            edf['Method'] = method_lower_case
            if {"ST", 'S1'}.issubset(edf.columns):
                edf['ST-S1'] = edf['ST'] - edf['S1']
            return edf
        case _:
            return ans
