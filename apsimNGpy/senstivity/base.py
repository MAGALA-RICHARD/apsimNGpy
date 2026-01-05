import pandas as pd
from collections import defaultdict
from apsimNGpy.core.experimentmanager import ExperimentManager, AUTO_PATH
from apsimNGpy.senstivity.sampler import define_problem, create_factor_specs
from SALib import ProblemSpec
class BaseFactory:
    def __init__(self):
        self.Y = None
        self.groups = None
        self.dist = None
        self.params = None
        self.names= None
        self.problem = None
        self.cpu_count=12
        self.agg_var=None
        self.param_keys =[]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    def setup(self,  params, y, cpu_count=12,
              names=None, dist=None, groups=None,
              agg_var=None):
        # In the parent class, these are optional, we make them compulsory here
        # carry the remain parameters forward
        self.params = params
        self.names = names
        self.agg_var = agg_var
        self.cpu_count=cpu_count
        self.Y = y
        if dist is None:
            dist= ['unif'] * len(params)
        self.dist = dist
        self.groups = groups

    def get_problem(self):
        problem = define_problem(self.params) if self.names is None else define_problem(self.params, self.names)
        problem['dist'] = self.dist
        if self.groups is not None:
            problem['groups'] = self.groups
        self.problem = problem
        return ProblemSpec(**problem)

    def extract_param_keys(self):
        # self.params is a dict with bounded values
        for key in self.params.keys():
            base, _, attr = key.rpartition(".")
            self.param_keys.append(attr)

        print(self.param_keys)
    def attach_values(self, values):
        """
         Generate APSIM factor specifications by grouping candidate parameters
        according to their APSIM base paths.

        Parameters:
        _____________
        values: n.ndarray

        Returns
        --------
        a generator[dict]
        """
        if values.ndim != 2:
            raise ValueError('Values must have 2 dimension, hence a two dimensional array expected')
        # ---- Group parameters by base path ----
        grouped = group_candidate_params(self.params.keys())

        n_params = len(self.params)
        #loop through rows and attach values
        for index in range(values.shape[0]):
            row = values[index]
            if len(row) != n_params:
                raise ValueError(
                    f"Each value row must have {n_params} values "
                    f"(got {len(row)})"
                )

            # Map full param → value
            param_value_map = dict(zip(self.param_keys, row))

            # Emit one factor per base path
            for base_path, attrs in grouped.items():
                yield {
                    "path": base_path,
                    **{
                        attr: param_value_map[f"{base_path}{attr}"]
                        for attr in attrs
                    },
                }


    def evaluate(self, X):
        print(X.shape)
        specs = create_factor_specs(problem=self.problem, params=self.params, X=X, immediate=False)
        for sp in specs:
            print(sp)
            self.add_factor(**sp)
        self.run( cpu_count=self.cpu_count, timeout=X.shape[0] *40)

        names =self.problem.get('names')
        if names:
            names= list(names)
        res = self.results
        print(res[[*names, "Yield"]])
        res.dropna(inplace=True)
        # the control vars are returned by APSIM as strings, converting them to float to match with X
        res[[*names]] = res[[*names]].astype('float')
        if isinstance(self.Y, str):
            self.Y = [self.Y]

        if self.agg_var is not None:
            df = (res.groupby([*names, self.agg_var])[self.Y].mean())
            df_param = (
                df.groupby(level=names, sort=False).mean()
            )

        else:
            base = res[[*names, *self.Y]].copy()

            df_param =base.set_index([*names], drop=True)
            df_param = df_param.groupby(level=names, sort=False).mean()

       # df =model.results.set_index(names)


        # Re-align to SALib X order
        X_index = pd.MultiIndex.from_arrays(
            X.T,
            names=names
        )

        Y = df_param.reindex(X_index).to_numpy()
        print(Y)

        return Y



def split_apsim_path(full_path: str) -> tuple[str, str]:
    """
    Split an APSIM parameter path into base path and attribute name.

    Example
    -------
    '[Sow].Script.Population' →
        ('[Sow].Script.', 'Population')
    """
    base, _, attr = full_path.rpartition(".")
    if not base:
        raise ValueError(f"Invalid APSIM path: {full_path}")
    return base + ".", attr


def group_candidate_params(candidate_param):
    """
    Group APSIM parameter paths by their base path.

    Returns
    -------
    dict[str, list[str]]
        Mapping of base_path → list of attribute names
    """
    groups = defaultdict(list)

    for p in candidate_param:
        base, attr = split_apsim_path(p)
        groups[base].append(attr)

    return dict(groups)


if __name__ == '__main__':
    rowSpacing = '[Sow using a variable rule].Script.RowSpacing'
    par = {'[Sow using a variable rule].Script.Population': (2, 10),
           rowSpacing: (650, 750)}
    with BaseFactory('Maize') as model:
        print(model.inspect_model_parameters('Manager', 'Sow using a variable rule'))
        model.setup(permutation=False, base_simulation='Simulation', params=par, y='Yield')
        sp = model.get_problem()
        xp = model.extract_param_keys()
        print(xp)
        #si = sp.sample_sobol(16).evaluate(model.evaluate).analyze_sobol()
        #df =model.results


