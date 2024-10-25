import matplotlib.pyplot as plt

import os
import platform
import subprocess
from apsimNGpy.visual import visual
def open_file_in_window(filepath):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', filepath])
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filepath)
    elif platform.system() == 'Linux':  # Linux
        subprocess.call(['xdg-open', filepath])
    else:
        raise OSError('Unsupported operating system')



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


def contour_plot(preview_in_window =True, **kwargs):
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
