import matplotlib.pyplot as plt


def plot_data(x, y, plot_type='line', xlabel = 'X-axis', ylabel = "Y-axis"):
    """
    Plot data points.

    Parameters:
    x (list or array-like): X-axis data.
    y (list or array-like): Y-axis data.
    plot_type (str): Type of plot ('line', 'scatter', 'bar', 'hist', 'box', 'pie').
    """
    if plot_type == 'line':
        plt.plot(x, y, label=ylabel)
    elif plot_type == 'scatter':
        plt.scatter(x, y, label=ylabel)
    elif plot_type == 'bar':
        plt.bar(x, y, label='Bar Plot')
    elif plot_type == 'hist':
        plt.hist(y, bins=10, label='Histogram')
    elif plot_type == 'box':
        plt.boxplot(y, vert=False, labels=['Box Plot'])
    elif plot_type == 'pie':
        plt.pie(y, labels=x, autopct='%1.1f%%', startangle=90)
    else:
        print("Invalid plot type. Available types: 'line', 'scatter', 'bar', 'hist', 'box', 'pie'")
        return

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f'{plot_type.capitalize()} Plot')
    plt.legend()
    plt.show()
    plt.savefig("plotted.png")


if __name__ == "__main__":
    # Example usage:
    x_data = [1, 2, 3, 4, 5]
    y_data = [10, 7, 5, 2, 8]
    plot_type = 'line'  # Change this to the desired plot type
    plot_data(x_data, y_data, plot_type)
