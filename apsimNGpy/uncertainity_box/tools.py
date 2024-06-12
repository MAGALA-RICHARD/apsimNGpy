import numpy as np
x = np.linspace(0, 10, 550)
def model(*params):
    a_est, b_est = params

    # Run simulation
    sim = a_est * x + b_est
    return sim

class CustomComparator:
   def __init__(self, value, comparison_direction='gt'):
    """
    Initialize the CustomComparator.

    Parameters:
    -----------
    value : int or float
        The value to be compared.
    comparison_direction : str
        The direction of comparison. Acceptable values are 'gt' for greater than
        and 'lt' for less than. Default is 'gt'.
    """
    self.value = value
    self.comparison_direction = comparison_direction

   def compare(self, other):
    """
    Compare the current value with another value based on the comparison direction.

    Parameters:
    -----------
    other : int or float
        The value to compare against.

    Returns:
    --------
    bool
        The result of the comparison.
    """
    if self.comparison_direction == 'gt':
     return self.value > other
    elif self.comparison_direction == 'lt':
     return self.value < other
    else:
     raise ValueError("Invalid comparison direction. Use 'gt' for greater than or 'lt' for less than.")

   def __repr__(self):
    return f"CustomComparator(value={self.value}, comparison_direction='{self.comparison_direction}')"
