import numpy as np
import matplotlib.pyplot as plt
from pycoord import *

# task2 plot the NEU positioning results

def read_filename(filename):
    xyz = []
    with open(filename) as fopen:
        lines = fopen.readlines()
        for line in lines:
            line_data = line.split()
            xyz.append([float(line_data[1]), float(line_data[2]), float(line_data[3])])
    return xyz


def calculate_neu(x_mean,y_mean,z_mean,xyz):
    neu = []
    for i in range(len(xyz)):
        n, e, u = xyz2neu(x_mean, y_mean, z_mean, xyz[i][0], xyz[i][1], xyz[i][2])
        neu.append([n,e,u])
    return neu


def plot_neu(neu):
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = 12
    neu = np.array(neu)
    n = neu[:, 0]
    e = neu[:, 1]
    u = neu[:, 2]
    indices = range(len(n))
    plt.figure(figsize=(6, 4))
    plt.ylim(-400, 400)
    plt.plot(indices, n, marker='o', linestyle='-', color='r', label='N Coordinates (m)')
    plt.plot(indices, e, marker='s', linestyle='-', color='g', label='E Coordinates (m)')
    plt.plot(indices, u, marker='^', linestyle='-', color='b', label='U Coordinates (m)')

    plt.legend()
    plt.xlabel('Index', font='Times New Roman', fontsize=12)
    plt.ylabel('Coordinate Value', font='Times New Roman', fontsize=12)
    plt.title('Urban WLS positioning NEU with skymask', font='Times New Roman', fontsize=12)
    plt.grid(True)
    plt.show()


# Urban
filename = r"..\result\Urban\task2_pos.txt"
xyz = read_filename(filename)
true_b, true_l, true_h = 22.3198722, 114.209101777778, 3.0
true_x, true_y, true_z = blh2xyz(true_b, true_l, true_h)
neu = calculate_neu(true_x, true_y, true_z,xyz)
plot_neu(neu)

