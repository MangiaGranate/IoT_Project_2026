import matplotlib.pyplot as plt


def generate(x: list, y: list, title, xlabel, ylabel):
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, marker='o', color='b')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.show()

