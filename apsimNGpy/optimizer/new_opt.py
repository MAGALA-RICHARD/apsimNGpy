from dataclasses import dataclass, field
from apsimNGpy.core.apsim import ApsimModel
from scipy.optimize import minimize

@dataclass
class Problem:
    apsim: ApsimModel
    simulation: str
    controls: list = field(default_factory=list)
    labels: list = field(default_factory=list)

    def add_control(self, model_type, model_name, parameter_name, label=None):
        self.controls.append({
            "model_type": model_type,
            "model_name": model_name,
            "parameter_name": parameter_name,
            "label": label or f"{model_type}_{model_name}_{parameter_name}"
        })

    def setUP(self, x):
        sim = self.apsim.inspect_model('Simulation', fullpath=False)[0]
        edit = self.apsim.edit_model
        for i, varR in enumerate(self.controls):
            print(x)
            edit(
                varR['model_type'],
                sim,
                varR['model_name'],
                **{varR['parameter_name']: x[i]}
            )

    def evaluate(self, x):
        self.setUP(x)
        result = self.apsim.run(verbose=True).results
        emissions = result.Yield  # placeholder
        return  10000 - emissions.mean()

    def minimize_problem(self, **kwargs):


        x0 = kwargs.pop("x0", [1] * len(self.controls))  # Starting guess
        result = minimize(self.evaluate, x0=x0, **kwargs)

        labels = [c['label'] for c in self.controls]
        result.x_vars = dict(zip(labels, result.x))
        return result

if __name__ == "__main__":
    model = ApsimModel('Maize')
    prob = Problem(model, "Simulation")
    prob.add_control('Manager', "Sow using a variable rule", 'Population', 'population')
    prob.add_control('Manager', "Fertilise at sowing", 'Amount', 'Nitrogen')
    ans  =prob.minimize_problem(x0=[1, 0], method  ='Powell', bounds =[(1,12), (0, 28)])
    print(ans)