import matplotlib.pyplot as plt
from apsimx.apsimx2py import ApsimSoil
from apsimx.remote import apsimx_prototype
class ApsimxVisuals(ApsimSoil):
    def __init__(self, model: Union[str, Simulations], copy=True, out_path=None, read_from_string=True, lonlat=None):
        super().__init__(model, copy, out_path)

    def plot_objectives(self, x, *args):
        idex = []
        for obj, objectives in enumerate(args):
            idex.append(obj)
        obj_pairs = [comb for comb in combinations(idex, 2)]
        for comb in obj_pairs:
            x, y = comb
            plt.figure(figsize=(7, 5))
            plt.scatter(solutions[:, x], solutions[:, y], s=30, facecolors='none', edgecolors='blue')
            plt.title("Bi-objecitve comparisons")
            plt.xlabel(f"{args[x]}")  # Add x-axis label
            plt.ylabel(f"{args[y]}")
            plt.show()