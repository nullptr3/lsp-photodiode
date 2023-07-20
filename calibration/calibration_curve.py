# include date and time support libraries
from datetime import datetime
from datetime import timedelta

# include graphing libraries
import matplotlib.pyplot as plt

# best fit function libraries
import numpy as np
from scipy.optimize import curve_fit

#PST vs PDT (8-hour UTC shift, 7-hour UTC shift)

def parse_sort(parsedData):
    n = len(parsedData)

    s = False
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if parsedData[j][0] > parsedData[j + 1][0]:
                s = True
                parsedData[j], parsedData[j + 1] = parsedData[j + 1], parsedData[j]

    if not s:
        return


def get_par(filename):
    par_data = []

    file = open(filename, "r")
    for line in file:
        data = line.split()
        if data[0] == "1":
            try:
                date = datetime.strptime(
                    data[1] + " " + data[2][0:-3], "%Y-%m-%d %H:%M"
                )
                par_data.append([date, float(data[3])])
            except ValueError:
                continue

    file.close()
    return par_data


def get_ada(filename):
    ada_data = []

    file = open(filename, "r")
    for line in file:
        data = line.split(",")
        try:
            date = datetime.strptime(data[3][0:-7], "%Y-%m-%d %H:%M")
            date = date - timedelta(hours=7)
            ada_data.append([date, float(data[1])])
        except ValueError:
            continue

    file.close()
    return ada_data


def setup(par_filename, ada_filename, truncate):
    data = [[], []]

    par = get_par(par_filename)
    ada = get_ada(ada_filename)

    parse_sort(par)
    parse_sort(ada)

    par = par[truncate:-1]
    ada = ada[truncate:-1]

    for par_entry in par:
        for ada_entry in ada:
            if par_entry[0] == ada_entry[0]:
                data[0].append(ada_entry[1])
                data[1].append(par_entry[1])
            elif par_entry[0] < ada_entry[0]:
                break

    return data


def bestfit(data):
    popt, pcov = curve_fit(
        lambda t, a, b, c: t / a + np.exp((t - c) / b),
        data[0],
        data[1],
        p0=(13.6, 61, 1400),
    )

    return popt[0], popt[1], popt[2]


if __name__ == "__main__":
    data = setup("June2QuantumData.txt", "Photodiode_(mV)-20230602-2322.csv", 500)
    a, b, c = bestfit(data)

    plt.scatter(data[0], data[1], s=1)

    x = np.linspace(min(data[0]), max(data[0]), 1000)

    plt.plot(x, x / a + np.exp((x - c) / b), "-k")

    plt.title("Photodiode Calibration Curve")
    plt.xlabel("Photodiode (mV)")
    plt.ylabel("PAR")
    
    corr_matrix = np.corrcoef(data[1], data[1] / a + np.exp((data[1] - c) / b))
    corr = corr_matrix[0, 1]
    R_sq = corr**2

    print(f"f(x) = x / {a} + e^((x - {c}) / {b})")
    print("R_sq:", R_sq)
    
    plt.savefig("plot.png")