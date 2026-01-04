import pandas as pd

from apsimNGpy.core.experimentmanager import ExperimentManager, AUTO_PATH
from apsimNGpy.senstivity.sampler import define_problem, create_factor_specs
from SALib import ProblemSpec
class BaseFactory(ExperimentManager):
    def __init__(self, model, out_path=AUTO_PATH):
        super().__init__(model=model, out_path=out_path)
        self.Y = None
        self.groups = None
        self.dist = None
        self.params = None
        self.names= None
        self.problem = None
        self.cpu_count=12
        self.agg_var=None



    def setup(self, permutation, base_simulation, params, y, cpu_count=12,
              names=None, dist=None, groups=None,
              agg_var=None):
        # In the parent class, these are optional, we make them compulsory here
        self.init_experiment(permutation=permutation, base_simulation=base_simulation)
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

    def  evaluate_multiple(self, X):
        def create_jobs(X):
            for sp in X:
             jobs = []
        ...
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




if __name__ == '__main__':
    rowSpacing = '[Sow using a variable rule].Script.RowSpacing'
    par = {'[Sow using a variable rule].Script.Population': (2, 10),
           rowSpacing: (650, 750)}
    with BaseFactory('Maize') as model:
        print(model.inspect_model_parameters('Manager', 'Sow using a variable rule'))
        model.setup(permutation=False, base_simulation='Simulation', params=par, y='Yield')
        sp = model.get_problem()
        si = sp.sample_sobol(16).evaluate(model.evaluate).analyze_sobol()
        df =model.results


