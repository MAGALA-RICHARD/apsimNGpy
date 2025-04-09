from apsimNGpy.core.core import Models
model_lists = []
from apsimNGpy.core.base_data import load_default_simulations
model = load_default_simulations(crop = 'maize')
def extract_models(model_namespace=None):
    """recursively extracts model types from Models namespace"""
    if model_namespace is None:
        model_namespace = Models
    if not hasattr(model_namespace, "__dict__"):
        return None  # Base case: Not a valid namespace
    for attr, value in model_namespace.__dict__.items():

        if isinstance(value, type(getattr(Models, "Clock", object))):
            if not attr.startswith("__"):
                mod = f"{value.__module__}.{value.__name__}"
                model_lists.append(mod)
            continue

        if hasattr(value, "__dict__"):  # Recursively search nested namespaces
            result = extract_models(value)
            continue
    model_lists.sort()
    return model_lists  # Model not found

if __name__ == "__main__":
    print(extract_models())
    from collections import defaultdict
    model.add_crop_replacements("Maize")
    model.create_experiment()
    # Your flat list of paths
    paths = model.inspect_model(Models.Core.Model)
    def filter_out():
        import Models
        data = []
        nd = ['Models.Core.Simulation', 'Models.Soils.Soil', 'Models.PMF.Plant', 'Models.Manager',
              'Models.Climate.Weather', 'Models.Report', 'Models.Clock', 'Models.Core.Folder', 'Models.Soils.Solute',
              'Models.Soils.Swim3','Models.Soils.SoilCrop', 'Models.Soils.Water','Models.Summary', 'Models.Core.Zone',
              'Models.Soils.CERESSoilTemperature','Models.Series','Models.Factorial.Experiment', 'Models.Factorial.Permutation',
              'Models.Factorial.Factors',
              'Models.Sobol','Models.Operations', 'Models.Morris', 'Models.Fertiliser','Models.Core.Events','Models.Core.VariableComposite',
              'Models.Soils.Physical', 'Models.Soils.Chemical', 'Models.Soils.Organic']
        for i in nd:

            ans =model.inspect_model(eval(i))
            if not 'Replacements' in ans and 'Folder' in i:
                continue
            data.extend(ans)
        return data
    paths = filter_out()
    # Build a nested tree structure
    def build_tree(paths):
        tree = lambda: defaultdict(tree)
        root = tree()
        for path in paths:
            parts = path.strip('.').split('.')
            current = root
            for part in parts:
                current = current[part]
        return root


    # Recursively print the tree
    def print_tree(node, indent=0, full_path=""):
        for key in sorted(node.keys()):
            current_path = f"{full_path}.{key}" if full_path else key
            print("    " * indent + f"- {key}: .{current_path}")
            print_tree(node[key], indent + 1, current_path)


    # Build and print
    tree = build_tree(paths)
    print_tree(tree)
