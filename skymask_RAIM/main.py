import numpy as np

from wls import *
from ekf import *
from raim import *
from skymask import *

def output_data_to_file(data, filename):
    """
    output the pos/vel result to file
    """
    out_str = ""
    for i in range(len(data)):
        for j in range(len(data[i])):
            out_str += "%.3f  " % (data[i][j])
        out_str += "\n"
    with open(filename, 'w') as fopen:
        fopen.writelines(out_str)

def output_raim_result_to_file(data, position_errors, protection_levels, excluded_satellites, filename):
    """
    output raim result to file
    format: tow, x, y, z, position error, PL
    """
    out_str = ""
    for i in range(len(data)):
        for j in range(len(data[i])):
            out_str += "%.3f  " % (data[i][j])
        out_str += "%.3f %.3f " % (position_errors[i], protection_levels[i])
        # for j in range(len(excluded_satellites[i])):
        #     out_str += "%2d  " % (excluded_satellites[i][j])
        out_str += "\n"
    with open(filename, 'w') as fopen:
        fopen.writelines(out_str)

# Assignment1
def wls_method(obs_filename, eph_filename, output_filename, skymask_filename):
    """
    wls
    """
    out = WLS_pos_vel_estimation(obs_filename,eph_filename, skymask_filename)
    output_data_to_file(out, output_filename)

def ekf_method(obs_filename, eph_filename, output_filename):
    """
    EKF
    """
    out = EKF_pos_vel_estimation(obs_filename, eph_filename)
    output_data_to_file(out, output_filename)

# Assignment2
def wls_with_skymask(obs_filename, eph_filename, output_filename, skymask_filename):
    """
    task 2
    improve positioning accuracy with urban skymask
    """
    out = WLS_pos_estimation_skymask(obs_filename, eph_filename, skymask_filename)
    output_data_to_file(out, output_filename)

def gnss_raim(obs_filename, eph_filename, output_filename):
    """
    task3
    RAIM implementation and protection level calculation
    """
    out, position_errors, protection_levels, excluded_satellites = RAIM_WLS_pos_estimation(obs_filename, eph_filename)
    output_raim_result_to_file(out,  position_errors, protection_levels, excluded_satellites, output_filename)
    generate_stanford_chart(np.array(position_errors), np.array(protection_levels), alarm_limit=50.0)

def main():
    """
    main
    task2 Urban outputformat: tow,x,y,z
    task3 Opensky RAIM outputformat: tow,x,y,z,position error,PL
    """
    #task2
    urban_obs_filename = r".\data\Urban\obsData.mat"
    urban_eph_filename = r".\data\Urban\ephData.mat"
    urban_output_filename = r".\result\Urban\task2_pos.txt"
    skymask_filename = r".\data\Urban\skymask_A1_urban.csv"
    wls_with_skymask(urban_obs_filename, urban_eph_filename, urban_output_filename, skymask_filename)

    # task3
    opensky_obs_filename = r".\data\Opensky\obsData.mat"
    opensky_eph_filename = r".\data\Opensky\ephData.mat"
    opensky_output_filename = r".\result\Opensky\task3_raim.txt"
    gnss_raim(opensky_obs_filename, opensky_eph_filename, opensky_output_filename)

if __name__ == '__main__':
    main()
