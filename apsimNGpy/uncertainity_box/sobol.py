
from SALib.sample import sobol
import os
from apsimNGpy.core.apsim import ApsimModel
import numpy as np
from apsimNGpy.experiment.variable import BoundedVariable, DiscreteVariable
import shutil

def  sobol_samples(problem_specifics):
    sobo, n_s_f, problem_= problem_specifics.sobol_seq, problem_specifics.sample_factor,  problem_specifics.problem_summary
    for i in ['num_vars', 'bounds', 'names']:
        if i not in problem_:
            raise ValueError(f"problem is missing {i} can't proceed")
    if len(problem_.get('bounds')) != problem_['num_vars']:
        raise ValueError(f"bounds length not equal to the specified {problem_['num_vars']}")
    k_Samples  =[]
    n_s = sobo.shape[0]
    sob_sequence = sobo
    for i in range(int(problem_.get('num_vars'))):
        bv = BoundedVariable(bounds=problem_.get('bounds')[i], place_holder_name=problem_.get('names')[i], sample_size=n_s)
        bv.samples = sob_sequence[:, i]
        k_Samples.append(bv)
    return k_Samples


def generate_initial_data(w_d, xdata, file):
    for var_ in xdata:
        assert isinstance(var_, (
        DiscreteVariable, BoundedVariable)), f'variables should be of class {DiscreteVariable} or {BoundedVariable}'
    model = ApsimModel(file)
    samples = [X.samples for X in xdata]

    if os.path.exists(w_d):
        w_dr = os.path.join(w_d, 'ClonedSamplesFiles')
        if not os.path.exists(w_dr):
            os.mkdir(w_dr)
    else:
        raise FileNotFoundError(f'{w_d} does not exist on your drive')
    number_of_sims = samples[0].shape[0]
    print('Copying:', number_of_sims, "files")

    files = [os.path.join(w_dr, f"sim_id_{fi}.apsimx") for fi in range(number_of_sims)]
    W_files = [os.path.join(w_dr,f"sim_id_{fi}.met") for fi in range(number_of_sims)]
    model = [ApsimModel(model = None, out_path=out) for out in files]

    filePath = tuple(files)
    parameters = np.column_stack(samples)
    pNames = [xdat.name for xdat in xdata]
    del files
    return ((dict(zip(pNames, parameters[ever])), {'file':filePath[ever]}) for ever in range(number_of_sims))

def replace_samples(xdata, wf, wd):
    """xdata is sobol sample sequence"""
    if os.path.exists(wd):
        w_dr = os.path.join(wd, 'ClonedSamplesFiles')
        if not os.path.exists(w_dr):
            os.mkdir(w_dr)
    else:
        raise FileNotFoundError(f'{wd} does not exist on your drive')
    for var_ in xdata:
        assert isinstance(var_, (
        DiscreteVariable, BoundedVariable)), f'variables should be of class {DiscreteVariable} or {BoundedVariable}'

    samples = [X.samples for X in xdata]
    num_sims = samples[0].shape[0]
    wf= [shutil.copyfile(wf, os.path.join(w_dr, f'w{im}.met')) for im in range(num_sims)]
    apsim_files= [os.path.join(w_dr,f'sim_{fi}.apsimx') for fi in range(num_sims)]
    return ((samples[idx], wf[idx], apsim_files[idx]) for idx in range(num_sims))

# example;
if __name__ == '__main__':
    problem = {'names': ['N', 'R', 'IC', 'ICNR'],
               'bounds': [[50, 360], [0, 1], [1, 4], [60, 140]],
               'num_vars': 4}
