import numpy as np
import matplotlib.pyplot as plt
from pycoord import *


# task3 plot the positioning results (NEU)
# average XYZ results as reference

def read_filename(filename):
    xyz = []
    with open(filename) as fopen:
        lines = fopen.readlines()
        for line in lines:
            line_data = line.split()
            xyz.append([float(line_data[1]), float(line_data[2]), float(line_data[3])])
    return xyz

def calculate_average(xyz):
    xyz_array = np.array(xyz)
    x_mean = np.mean(xyz_array[:, 0])
    y_mean = np.mean(xyz_array[:, 1])
    z_mean = np.mean(xyz_array[:, 2])
    return x_mean, y_mean, z_mean

def calculate_neu(x_mean,y_mean,z_mean,xyz):
    neu = []
    for i in range(len(xyz)):
        n, e, u = xyz2neu(x_mean, y_mean, z_mean, xyz[i][0], xyz[i][1], xyz[i][2])
        neu.append([n,e,u])
    return neu


def plot_lat_lon(neu):
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = 12
    neu = np.array(neu)
    n = neu[:, 0]
    e = neu[:, 1]
    u = neu[:, 2]
    indices = range(len(n))
    plt.figure(figsize=(10, 6))
    plt.ylim(-20, 20)
    plt.plot(indices, n, marker='o', linestyle='-', color='r', label='N Coordinates (m)')
    plt.plot(indices, e, marker='s', linestyle='-', color='g', label='E Coordinates (m)')
    plt.plot(indices, u, marker='^', linestyle='-', color='b', label='U Coordinates (m)')

    plt.legend()
    plt.xlabel('Index')
    plt.ylabel('Coordinate Value')
    plt.title('Opensky WLS NEU Result using RAIM')
    plt.grid(True)
    plt.show()

filename = r"..\result\Opensky\task3_raim.txt"
xyz = read_filename(filename)
x_mean, y_mean, z_mean = calculate_average(xyz)
neu = calculate_neu(x_mean,y_mean,z_mean,xyz)
plot_lat_lon(neu)
