from apsimNGpy.core.core import Models
model_lists = {}
def extract_models(model_namespace=None):
    """recursively extracts model types from Models namespace"""
    if model_namespace is None:
        model_namespace = Models
    if not hasattr(model_namespace, "__dict__"):
        return None  # Base case: Not a valid namespace
    for attr, value in model_namespace.__dict__.items():
        if isinstance(value, type(getattr(Models, "Clock", object))):
            model_lists[attr] = value
            continue

        if hasattr(value, "__dict__"):  # Recursively search nested namespaces
            result = extract_models(value)
            if result:
                model_lists[attr] = result
                continue

    return model_lists  # Model not found

if __name__ == "__main__":
    print(extract_models())