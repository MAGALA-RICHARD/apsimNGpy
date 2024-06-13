
from SALib.sample import sobol

from apsimNGpy.experiment.variable import BoundedVariable

def  sobol_samples(n_s_f, problem_):
    for i in ['num_vars', 'bounds', 'names']:
        if i not in problem_:
            raise ValueError(f"problem is missing {i} can't proceed")
    if len(problem_.get('bounds')) != problem_['num_vars']:
        raise ValueError(f"bounds length not equal to the specified {problem_['num_vars']}")
    kSamples  =[]
    sobo = sobol.sample(problem_, 2**n_s_f)
    n_s = sobo.shape[0]
    for i in range(int(problem_.get('num_vars'))):
        bv = BoundedVariable(bounds=problem_.get('bounds')[i], place_holder_name=problem_.get('names')[i], sample_size=n_s)
        bv.samples = sobo[:, i]
        kSamples.append(bv)
    return kSamples

# example;
if __name__ == '__main__':
    problem = {'names': ['N', 'R', 'IC', 'ICNR'],
               'bounds': [[50, 360], [0, 1], [1, 4], [60, 140]],
               'num_vars': 4}
    kSamples = sobol_samples(5, problem)