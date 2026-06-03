from apsimNGpy.core.core import Models
model_lists = []
from apsimNGpy.core.base_data import load_default_simulations
model = load_default_simulations(crop = 'maize')


import types

def extract_models(model_namespace=None, visited=None):
    """
    Recursively extracts all model class names from a given namespace,
    diving into all attributes including nested objects, modules, and classes.
    """
    if model_namespace is None:
        model_namespace = Models

    if visited is None:
        visited = set()

    models_found = []

    # Avoid processing the same object multiple times (handle circular refs)
    if id(model_namespace) in visited:
        return []

    visited.add(id(model_namespace))

    # Try to iterate through all attributes of the object
    try:
        attr_names = dir(model_namespace)
    except Exception:
        return []

    for attr_name in attr_names:
        if attr_name.startswith("__"):
            continue

        try:
            attr_value = getattr(model_namespace, attr_name)
        except Exception:
            continue  # Safely skip inaccessible attributes

        # If it's a class, store its full path
        if isinstance(attr_value, type):
            model_path = f"{attr_value.__module__}.{attr_value.__name__}"
            models_found.append(model_path)

        # If it's a module, class, or object with attributes — go deeper
        elif isinstance(attr_value, (types.ModuleType, object)) and not isinstance(attr_value, (int, float, str, list, dict, set, tuple)):
            models_found.extend(extract_models(attr_value, visited))

    return sorted(set(models_found))


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
              'Models.Soils.CERESSoilTemperature','Models.Series','Models.Factorial.ExperimentManager', 'Models.Factorial.Permutation',
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
