import matplotlib.pyplot as plt


def quick_plot(**kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    plt.title("Objective Space")
    width = kwargs.get('width', 7)
    height = kwargs.get('height', 5)
    plt.figure(figsize=(width, height))
    #plt.plot(x, y, color='red', label='Line')
    plt.scatter(x, y, s=30, facecolors='none', edgecolors='blue')
    xlab = kwargs.get("xlabel", "x")
    ylab = kwargs.get('ylabel', 'y')
    plt.xlabel(xlab)  # Add x-axis label
    plt.ylabel(ylab)
    plt.show()
    plt.close()


