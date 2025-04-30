"""

This functions in this file are from rtklibexplorer/rtklib-py/rtkcmn.py
url: https://github.com/rtklibexplorer/rtklib-py

"""

import numpy as np
from gnsscommon import time2doy, interpc

# troposhere model
nmf_coef = np.array([
    [1.2769934E-3, 1.2683230E-3, 1.2465397E-3, 1.2196049E-3, 1.2045996E-3],
    [2.9153695E-3, 2.9152299E-3, 2.9288445E-3, 2.9022565E-3, 2.9024912E-3],
    [62.610505E-3, 62.837393E-3, 63.721774E-3, 63.824265E-3, 64.258455E-3],
    [0.0000000E-0, 1.2709626E-5, 2.6523662E-5, 3.4000452E-5, 4.1202191E-5],
    [0.0000000E-0, 2.1414979E-5, 3.0160779E-5, 7.2562722E-5, 11.723375E-5],
    [0.0000000E-0, 9.0128400E-5, 4.3497037E-5, 84.795348E-5, 170.37206E-5],
    [5.8021897E-4, 5.6794847E-4, 5.8118019E-4, 5.9727542E-4, 6.1641693E-4],
    [1.4275268E-3, 1.5138625E-3, 1.4572752E-3, 1.5007428E-3, 1.7599082E-3],
    [4.3472961E-2, 4.6729510E-2, 4.3908931E-2, 4.4626982E-2, 5.4736038E-2]])
nmf_aht = [2.53E-5, 5.49E-3, 1.14E-3] # height correction

def mapf(el, a, b, c):
    """ simple tropospheric mapping function """
    sinel = np.sin(el)
    return (1.0 + a / (1.0 + b / (1.0 + c))) / (sinel + (a / (sinel + b / (sinel + c))))


def tropmapf(t, pos, el):
    """ tropospheric mapping function Neil (NMF)  """
    if pos[2] < -1e3 or pos[2] > 20e3 or el <= 0.0:
        return 0.0, 0.0

    aht = nmf_aht
    lat = np.rad2deg(pos[0])
    # year from doy 28, add half a year for southern latitudes
    y = (time2doy(t) - 28.0) / 365.25
    y += 0.5 if lat < 0 else 0
    cosy = np.cos(2.0 * np.pi * y)
    c = interpc(nmf_coef, np.abs(lat))
    ah = c[0:3] - c[3:6] * cosy
    aw = c[6:9]
    # ellipsoidal height is used instead of height above sea level
    dm = (1.0 / np.sin(el) - mapf(el, aht[0], aht[1], aht[2])) * pos[2] * 1e-3
    mapfh = mapf(el, ah[0], ah[1], ah[2]) + dm
    mapfw = mapf(el, aw[0], aw[1], aw[2])

    return mapfh, mapfw


def tropmodel(pos, el, humi):
    """ saastamonien tropospheric delay model """
    temp0 = 15  # temparature at sea level
    if pos[2] < -100 or pos[2] > 1e4 or el <= 0:
        return 0, 0, 0
    hgt = max(pos[2], 0)
    # standard atmosphere
    pres = 1013.25 * np.power(1 - 2.2557e-5 * hgt, 5.2568)
    temp = temp0 - 6.5e-3 * hgt + 273.16
    e = 6.108 * humi * np.exp((17.15 * temp - 4684.0) / (temp - 38.45))
    # saastamoinen model
    z = np.pi / 2.0 - el
    trop_hs = 0.0022768 * pres / (1.0 - 0.00266 * np.cos(2 * pos[0]) -
                                  0.00028e-3 * hgt) / np.cos(z)
    trop_wet = 0.002277 * (1255.0 / temp + 0.05) * e / np.cos(z)
    return trop_hs, trop_wet, z
