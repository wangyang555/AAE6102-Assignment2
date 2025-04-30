"""

This functions in this file are from rtklibexplorer/rtklib-py/rtkcmn.py
url: https://github.com/rtklibexplorer/rtklib-py

"""

from math import sin, cos
import numpy as np
from gnsscommon import time2gpst, rCST

"""
    0.1118D-07  0.0000D+00 -0.5960D-07  0.0000D+00          ION ALPHA           
    0.9011D+05  0.0000D+00 -0.1966D+06  0.0000D+00          ION BETA 
"""
ion_default = np.array([ # 2021/10/14
    [0.1118E-07,0.0000E+00,-0.5960E-07, 0.0000E+00],
    [0.9011E+05,0.0000E+00,-0.1966E+06, 0.0000E+00]])

def ionmodel(t, pos, az, el, ion=ion_default):
    """ klobuchar model of ionosphere delay estimation """
    psi = 0.0137 / (el / np.pi + 0.11) - 0.022
    phi = pos[0] / np.pi + psi * cos(az)
    phi = np.max((-0.416, np.min((0.416, phi))))
    lam = pos[1]/np.pi + psi * sin(az) / cos(phi * np.pi)
    phi += 0.064 * cos((lam - 1.617) * np.pi)
    #_, tow = time2gpst(t)
    tow = t
    tt = 43200.0 * lam + tow  # local time
    tt -= np.floor(tt / 86400) * 86400
    f = 1.0 + 16.0 * np.power(0.53 - el/np.pi, 3.0)  # slant factor

    h = [1, phi, phi**2, phi**3]
    amp = np.dot(h, ion[0, :])
    per = np.dot(h, ion[1, :])
    amp = max(amp, 0)
    per = max(per, 72000.0)
    x = 2.0 * np.pi * (tt - 50400.0) / per
    if np.abs(x) < 1.57:
        v = 5e-9 + amp * (1.0 + x * x * (-0.5 + x * x / 24.0))
    else:
        v = 5e-9
    diono = rCST.CLIGHT * f * v
    return diono
