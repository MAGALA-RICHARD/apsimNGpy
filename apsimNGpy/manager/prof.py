import numpy as np
def soilvar_perdep_cor(nlayers, soil_bottom=200, a=0.5, b=0.5):  # has potential to cythonize
    depthn = np.arange(1, nlayers + 1, 1)
    if a < 0:
        print("Target parameter can not be negative")  # a * e^(-b * x).
    elif (a > 0 and b != 0):
        ep = -b * depthn
        term1 = (a * depthn) * np.exp(ep)
        result = term1 / term1.max()
        return (result)
    elif (a == 0 and b != 0):
        ep = -b * depthn
        result = np.exp(ep) / np.exp(-b)
        return result
    elif (a == 0, b == 0):
        ans = [1] * len_layers
        return ans
    
def cal_dul(dul, bd, KS, ll15, nlayers = 10):
     DUL = dul *soilvar_perdep_cor(nlayers)
     DUL[0] = dul
     BD = bd *soilvar_perdep_cor(nlayers)
     BD[0] = bd
     LL15 =  ll15 * soilvar_perdep_cor(nlayers)
     LL15[0] = ll15
     ks = [KS] * nlayers
     
