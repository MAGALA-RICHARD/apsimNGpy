from typing import Optional, Tuple, Union, Dict
from pydantic import BaseModel, ConfigDict
import numpy as np
import itertools
Number = Union[int, float]
MixedStrNone  =Union[str, bool, None]
MixedNumber = Union[Number, None]

class BaseInspector(BaseModel):
    """
    A base parameter container for continuous or bounded optimization variables.

    This class is intended to support APSIM-NG parameter definitions for
    optimization or calibration tasks. It handles:
      - APSIM model path references
      - Candidate parameters to modify
      - Starting values
      - Optional cultivar-specific parameters
      - Additional constraints or auxiliary arguments
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    path: str
    # values can be ints, floats, or strings but MUST be a tuple
    values: Optional[Tuple[Tuple[Number, ...], ...]] = None
    # Candidate parameter names must also be a tuple
    candidate_param: Tuple[str, ...]
    intervals: Optional[Tuple[MixedNumber, ...]] = None
    dist: Optional[Tuple[MixedStrNone, ...]] =None
    cultivar: Optional[bool] = False
    bounds: Optional[Tuple[Tuple[float, float], ...]] = None
    other_params: Optional[Dict[str, Union[int, float, str, bool]]] = None


    def __hash__(self):
        """Allow  all instances to be hashable."""
        return hash(
            (
                self.path,
                self.candidate_param,
                self.values,
                self.bounds,
            )
        )

    def additional_evaluation(self):
        """
        Validate parameter configuration and remove candidate parameters
        from auxiliary parameter mappings.

        This method performs consistency checks on user-provided attributes
        such as values, bounds, and distributions, and ensures that candidate
        parameters are not duplicated in ``other_params``.
        """
        n_params = len(self.candidate_param)
        data = self.values or self.bounds
        if not data:
            raise ValueError(f"provide either a list of values or bounds for each candidate parameter ({self.candidate_param})")

        def _check_length(obj, name):
            if obj is not None and len(obj) != n_params:
                raise AssertionError(
                    f"Length of '{name}' must equal number of candidate parameters ({n_params})"
                )

        # Length validations
        _check_length(self.values, "values")
        _check_length(self.bounds, "bounds")
        _check_length(self.dist, "dist")

        # Remove overlapping keys from other_params
        if self.other_params:
            keys = (
                self.candidate_param
                if isinstance(self.candidate_param, (list, tuple))
                else [self.candidate_param]
            )
            for key in keys:
                self.other_params.pop(key, None)

        return self

    def sample(self):
        data = []
        if self.values:
            # priority is given to values because with values user can also define parameters that take on strings
            return self.values
        if self.bounds:
            for b, step in zip(self.bounds, self.intervals):
                ar= np.arange(b[0], b[1], step=step)
                data.append(ar)
        return data


    def attach__factor(self, method='permutation'):
        """
        Yield factor dictionaries for each parameter combination.
        """

        self.additional_evaluation()

        path = self.path
        values = self.sample()
        if method == 'permutation':
            gen_data = permutation(path, params=self.candidate_param, values=values)
        else:
            gen_data = factor_wise(path, params=self.candidate_param, values=values)
        for vd in gen_data:
            yield vd


def permutation(path, params, values):
    if len(values) != len(params):
        raise ValueError("sample() output must align with parameters names")
    for i, combo in enumerate(itertools.product(*values)):
        yield {'path':path, **dict(zip(params, combo))}

def factor_wise(path, params, values):
    """
    Generate factor-wise values: one factor at a time, no combinations.

    Parameters
    ----------
    params : list | tuple
        Factor names.
    values : list[list]
        Values for each factor.

    Returns
    -------
    list of dict
        One dict per factor-value pair.
    """

    if len(params) != len(values):
        raise ValueError("params and values must have same length")

    data = []

    for p, vlist in zip(params, values):
        for v in vlist:
            data.append({p: v, 'path': path})

    return data








if __name__ == "__main__":
    bi = BaseInspector(**{'path':'th/2',
                          'dist': [None, None],
                          'intervals': [4, None],
                          'candidate_param':['Population', 'c'],
                          'bounds':[(0,100), (2,10)],
                        'values':([1,5,8],[7], )})
    bi.additional_evaluation()
    print(bi.values)
    print(bi.candidate_param)
    print(list(bi.attach__factor('factor_wise')))