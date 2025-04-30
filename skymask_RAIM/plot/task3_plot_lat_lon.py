from gnsscommon import *
import numpy as np
import matplotlib.pyplot as plt


# task3 plot the positioning results (latitude, longitude)

def read_filename(filename):
    lat = []
    lon = []
    with open(filename) as fopen:
        lines = fopen.readlines()
        for line in lines:
            line_data = line.split()
            xyz = np.array([float(line_data[1]), float(line_data[2]), float(line_data[3])])
            pos = ecef2pos(xyz)
            lat.append(np.rad2deg(pos[0]))
            lon.append(np.rad2deg(pos[1]))
    return lat, lon


def plot_lat_lon(truth_lat, truth_lon, lat, lon, size):
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = 12
    plt.scatter(lon, lat, label='Data Points', color='blue')
    plt.scatter(truth_lon, truth_lat, label='True Value', color='red', marker='^', s=200)

    plt.xlim(truth_lon - size, truth_lon + size)
    plt.ylim(truth_lat - size, truth_lat + size)
    plt.title('Opensky WLS Positioning Result using RAIM')
    plt.xlabel('Longitude (degree)')
    plt.ylabel('Latitude (degree)')
    plt.grid(True)
    plt.show()

"""
Opensky
22.328444770087565, 114.1713630049711
"""

truth_lat = 22.328444770087565
truth_lon = 114.1713630049711
filename = r"..\result\Opensky\task3_raim.txt"
lat, lon = read_filename(filename)
plot_lat_lon( truth_lat, truth_lon, lat, lon, 0.0002)