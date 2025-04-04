import platform
import subprocess
import itertools
import math
import os
from collections import Counter
from typing import List, Union
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as ss


def open_file_in_window(filepath):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', filepath])
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filepath)
    elif platform.system() == 'Linux':  # Linux
        subprocess.call(['xdg-open', filepath])
    else:
        raise OSError('Unsupported operating system')



def conditional_entropy(
        x: List[Union[int, float]],
        y: List[Union[int, float]]
) -> float:
    """ Calculates conditional entropy """

    # Count unique values
    y_counter = Counter(y)  # Counts of unique values in y
    xy_counter = Counter(list(zip(x, y)))  # Counts of unique pairs from (x, y)
    # Calculate sum of y values
    total_occurrences = sum(y_counter.values())
    # (Re-)set entropy to 0
    entropy = 0

    # For every unique value pair of x and y
    for xy in xy_counter.keys():
        # Joint probability of x AND y
        p_xy = xy_counter[xy] / total_occurrences
        # Marginal probability of y
        p_y = y_counter[xy[1]] / total_occurrences
        # Conditional probability of x given y
        p_x_given_y = p_xy / p_y
        # Calculate the conditional entropy H(X|Y)
        entropy += p_xy * math.log(p_x_given_y, 2)  # Use base 2 instead of natural (base e)

    return -entropy


def theil_u(
        x: List[Union[int, float]],
        y: List[Union[int, float]]
) -> float:
    """ Calculate Theil U """

    # Calculate conditional entropy of x and y
    H_xy = conditional_entropy(x, y)

    # Count unique values
    x_counter = Counter(x)

    # Calculate sum of x values
    total_occurrences = sum(x_counter.values())

    # Convert all absolute counts of x values in x_counter to probabilities
    p_x = list(map(lambda count: count / total_occurrences, x_counter.values()))

    # Calculate entropy of single distribution x
    H_x = ss.entropy(p_x)

    return (H_x - H_xy) / H_x if H_x != 0 else 0


def get_theils_u_for_df(df: pd.DataFrame) -> pd.DataFrame:
    """ Compute Theil's U for every feature combination in the input df """

    # Create an empty dataframe to fill
    theilu = pd.DataFrame(index=df.columns, columns=df.columns)

    # Insert Theil U values into empty dataframe
    for var1, var2 in itertools.combinations(df.columns, 2):
        # if pd.api.types.is_numeric_dtype(df[var1]) and not pd.api.types.is_numeric_dtype(df[var2]) or not
        # pd.api.types.is_numeric_dtype(df[var1]) and pd.api.types.is_numeric_dtype(df[var2]):
        u = theil_u(df[var1], df[var2])
        theilu[var1][var2] = round(u, 2)  # fill lower diagonal

        u = theil_u(df[var2], df[var1])
        theilu[var2][var1] = round(u, 2)  # fill upper diagonal

        # Set 1s to diagonal where row index + column index == n - 1
    for i in range(0, len(theilu.columns)):
        for j in range(0, len(theilu.columns)):
            if i == j:
                theilu.iloc[i, j] = 1

    # Convert all values in the DataFrame to float
    return theilu.map(float)


def quick_plot(**kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    plt.title("Objective Space")
    width = kwargs.get('width', 7)
    height = kwargs.get('height', 5)
    plt.figure(figsize=(width, height))
    # plt.plot(x, y, color='red', label='Line')
    plt.scatter(x, y, s=30, facecolors='none', edgecolors='blue')
    xlab = kwargs.get("xlabel", "x")
    ylab = kwargs.get('ylabel', 'y')
    plt.xlabel(xlab)  # Add x-axis label
    plt.ylabel(ylab)
    plt.show()
    plt.close()


def contour_plot(preview_in_window=True, **kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    z = kwargs.get('z')
    orientation = kwargs.get("orientation")
    level_s = kwargs.get("n_levels", 20)
    c_map = kwargs.get("cmap")
    fig_name = kwargs.get("fig_name")
    show = kwargs.get("show", None)
    color_bar_label = kwargs.get("color_bar_label")
    y_label = kwargs.get("ylabel", 'Y')
    x_label = kwargs.get("xlabel", 'X')
    height = kwargs.get("height", 6)
    width = kwargs.get("width", 10)
    # Step 3: Create the contour plot
    if color_bar_label is None:
        color_bar_label = 'z values'
    plt.figure(figsize=(width, height))

    contour = plt.tricontourf(x, y, z, cmap=c_map, levels=level_s, vmin=z.min(),
                              vmax=z.max())  # Create filled contour plot
    colorbar = plt.colorbar(contour, label='Revenue', orientation=orientation)  # Add color bar with label
    colorbar.ax.tick_params(labelsize=16)  # Adjust fontsize of colorbar tick labels
    colorbar.set_label(color_bar_label, fontsize=18)
    plt.ylabel(y_label, fontsize=20)
    plt.xlabel(x_label, fontsize=20)
    # plt.title(' Buffer width and cost price comparison', fontsize=22)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.title(kwargs.get('title', ''), fontsize=20)
    plt.grid(False)
    plt.savefig(fig_name, dpi=450)
    if preview_in_window:
        open_file_in_window(fig_name)
    else:
        plt.show()
    return contour
