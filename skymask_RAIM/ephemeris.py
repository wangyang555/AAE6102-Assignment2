"""

This functions in this file are from rtklibexplorer/rtklib-py/rtkcmn.py
url: https://github.com/rtklibexplorer/rtklib-py

"""

import numpy as np
from gnsscommon import *

# ephemeris parameters
MAX_ITER_KEPLER = 30
RTOL_KEPLER = 1e-13

def seleph(sat, all_eph):
    eph = Eph(0)
    for i in range(len(all_eph)):
        if sat == all_eph[i].sat:
            eph = all_eph[i]
            break
    return eph

def dtadjust(t1, t2, tw=604800):
    """ calculate delta time considering week-rollover """
    dt = t1 - t2
    if dt > tw:
        dt -= tw
    elif dt < -tw:
        dt += tw
    return dt


def sva2ura(sys, sva):
    """ variance by ura ephemeris """
    ura_nominal = [2.0, 2.8, 4.0, 5.76, 8.0, 11.3, 16.0, 32.0, 64.0, 128.0,
                   256.0, 512.0, 1024.0, 2048.0, 4096.0, 8192.0]
    if sva < 0 or sva > 15: return 500 ** 2
    return ura_nominal[int(sva) + 1]


def eph2pos(t, eph):
    """ broadcast ephemeris to satellite position and clock bias -------------
* compute satellite position and clock bias with broadcast ephemeris (gps,
* galileo, qzss)
* args   : gtime_t time     I   time (gpst)
*          eph_t *eph       I   broadcast ephemeris
*          double *rs       O   satellite position (ecef) {x,y,z} (m)
*          double *dts      O   satellite clock bias (s)
*          double *var      O   satellite position and clock variance (m^2)
* return : none
* notes  : see ref [1],[7],[8]
*          satellite clock includes relativity correction without code bias
*          (tgd or bgd) """
    tk = dtadjust(t, eph.toe)
    mu = rCST.MU_GPS
    omge = rCST.OMGE

    M = eph.M0 + (np.sqrt(mu / eph.A ** 3) + eph.deln) * tk
    E, Ek = M, 0
    for _ in range(MAX_ITER_KEPLER):
        if abs(E - Ek) < RTOL_KEPLER:
            break
        Ek = E
        E -= (E - eph.e * np.sin(E) - M) / (1.0 - eph.e * np.cos(E))

    sinE, cosE = np.sin(E), np.cos(E)
    nus = np.sqrt(1.0 - eph.e ** 2) * sinE
    nuc = cosE - eph.e
    nue = 1.0 - eph.e * cosE
    u = np.arctan2(nus, nuc) + eph.omg
    r = eph.A * nue
    i = eph.i0 + eph.idot * tk
    sin2u, cos2u = np.sin(2 * u), np.cos(2 * u)
    u += eph.cus * sin2u + eph.cuc * cos2u
    r += eph.crs * sin2u + eph.crc * cos2u
    i += eph.cis * sin2u + eph.cic * cos2u
    x = r * np.cos(u)
    y = r * np.sin(u)
    cosi = np.cos(i)
    O = eph.OMG0 + (eph.OMGd - omge) * tk - omge * eph.toes
    sinO, cosO = np.sin(O), np.cos(O)
    rs = [x * cosO - y * cosi * sinO, x * sinO + y * cosi * cosO, y * np.sin(i)]
    tk = dtadjust(t, eph.toc)
    dts = eph.f0 + eph.f1 * tk + eph.f2 * tk ** 2
    # relativity correction
    dts -= 2 * np.sqrt(mu * eph.A) * eph.e * sinE / rCST.CLIGHT ** 2
    return rs, dts


def ephpos(time, eph):
    tt = 1e-3  # delta t to calculate velocity
    rs = np.zeros(6)
    dts = np.zeros(2)

    rs[0:3], dts[0] = eph2pos(time, eph)
    # use delta t to determine velocity
    t = time + tt

    rs[3:6], dts[1] = eph2pos(t, eph)
    rs[3:6] = (rs[3:6] - rs[0:3]) / tt
    dts[1] = (dts[1] - dts[0]) / tt
    return rs, dts


def satpos(t, eph):
    return ephpos(t, eph)


def eph2clk(time, eph):
    """ calculate clock offset based on ephemeris """
    t = ts = time - eph.toc
    for _ in range(2):
        t = ts - (eph.f0 + eph.f1 * t + eph.f2 * t ** 2)
    dts = eph.f0 + eph.f1 * t + eph.f2 * t ** 2
    return dts


def ephclk(time, eph):
    return eph2clk(time, eph)


def satposs(obs, all_eph):
    """ satellite positions and clocks ----------------------------------------------
    * compute satellite positions, velocities and clocks
    * args     obs_t obs       I   observation data
    *          nav_t  nav      I   navigation data
    *          double rs       O   satellite positions and velocities (ecef)
    *          double dts      O   satellite clocks
    *          double var      O   sat position and clock error variances (m^2)
    *          int    svh      O   sat health flag (-1:correction not available)
    * return : none
    * notes  : rs [0:2] = obs[i] sat position {x,y,z} (m)
    *          rs [3:5] = obs[i] sat velocity {vx,vy,vz} (m/s)
    *          dts[0:1] = obs[i] sat clock {bias,drift} (s|s/s)
    *          var[i]   = obs[i] sat position and clock error variance (m^2)
    *          svh[i]    = obs[i] sat health flag
    *          if no navigation data, set 0 to rs[], dts[], var[] and svh[]
    *          satellite position and clock are values at signal transmission time
    *          satellite position is referenced to antenna phase center
    *          satellite clock does not include code bias correction (tgd or bgd)
    *          any pseudorange and broadcast ephemeris are always needed to get
    *          signal transmission time """
    n = len(obs.sat)
    rs = np.zeros((n, 6)) # pos, vel
    dts = np.zeros((n, 2)) # clock bias, rate

    for i in np.argsort(obs.sat):
        sat = obs.sat[i]
        pr = obs.P[i]
        # transmission time by satellite clock
        #t = timeadd(obs.t, -pr / rCST.CLIGHT)
        #t = obs.t[i] + (-pr / rCST.CLIGHT)
        t = obs.t[i]
        eph = seleph(sat, all_eph)
        if eph is None:
            continue
        # satellite clock bias by broadcast ephemeris
        dt = ephclk(t, eph)
        t = t + (-dt)
        # satellite position and clock at transmission time
        rs[i], dts[i] = satpos(t, eph)
    return rs, dts
