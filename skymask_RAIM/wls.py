import numpy as np
from numpy.linalg import norm, lstsq
from gnsscommon import *
from ionosphere import *
from troposphere import *
from read_mat import *


MAXITR =    10          #  max number of iteration or point pos
REL_HUMI =  0.7         #  relative humidity for Saastamoinen model
MIN_EL = np.deg2rad(5)  #  min elevation for measurement


def design_wetight_matrix_wls(iter, ns, obs, eph, rs, dts, x):
    """
    prange and doppler

    """
    v = np.zeros(ns * 2)
    H = np.zeros([ns * 2, 8])
    P = np.zeros([ns * 2, ns * 2])

    rr = x[0:3]
    rv = x[4:7]
    dtr = x[3]
    dtrv = x[7]
    pos = ecef2pos(rr)
    nv = 0

    for i in range(ns):
        if norm(rs[i, :3]) < rCST.RE_WGS84:
            continue
        r, e = geodist(rs[i, :3], rr)
        ev = geodist_v(rs[i, 3:6], rv, r)
        if r < 0:
            continue
        [az, el] = satazel(pos, e)
        if el < MIN_EL:
            continue
        if iter > 0:
            # ionospheric correction
            dion = ionmodel(obs.t[0], pos, az, el)
            # tropospheric correction
            trop_hs, trop_wet, _ = tropmodel(pos, el, REL_HUMI)
            mapfh, mapfw = tropmapf(gpst2time(obs.week[i], obs.t[i]), pos, el)
            dtrp = mapfh * trop_hs + mapfw * trop_wet
        else:
            dion = dtrp = 0
        # TGD correction
        if obs.P[i] == 0:
            continue
        tmp_eph = seleph(obs.sat[i], eph)
        p_range = obs.P[i] - tmp_eph.tgd * rCST.CLIGHT
        # pseudorange residual
        v[nv] = p_range - (r + dtr - rCST.CLIGHT * dts[i,0] + dion + dtrp)
        # design matrix
        H[nv, 0:3] = -e
        H[nv, 3] = 1
        # weight matrix
        P[nv, nv] = get_weight_based_elevation(el)
        nv += 1
        # Doppler measurement
        if obs.D[i] == 0:
            continue
        doppler_measurement = -obs.D[i] #* rCST.CLIGHT / rCST.GPS_L1_FREQ
        # range rate
        range_rate = np.sum((rs[i,:3] - rr) * (rs[i,3:] - rv)) / r
        # clock rate
        clock_rate = dtrv - dts[i,1] * rCST.CLIGHT
        # earth correction rate
        earth_correction_rate = rCST.OMGE * (rs[i,3] * rr[1] + rv[1] * rs[i,0] - rs[i,4] * rr[0] - rv[0] * rs[i,1]) / rCST.CLIGHT
        H[nv, 0] = -ev[0] + e[0] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 1] = -ev[1] + e[1] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 2] = -ev[2] + e[2] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 4:7] = -e
        H[nv, 7] = 1
        v[nv] = doppler_measurement - (range_rate + clock_rate + earth_correction_rate)
        P[nv, nv] = P[nv-1, nv-1] * 5
        nv += 1
    return nv, v, H, P

def lst(H, P, v):
    H_T = H.T
    HTPH = H_T @ P @ H
    HTPH_inv = np.linalg.inv(HTPH)
    HTPv = H_T @ P @ v
    dx = HTPH_inv @ HTPv
    return dx

def estpos(ns, obs, eph, rs, dts):
    """ estimate position and clock errors with standard precision """
    x = np.zeros(8)
    v = np.zeros(ns * 2)
    H = np.zeros([ns * 2, 8])
    P = np.zeros([ns * 2, ns * 2])
    for iter in range(MAXITR):
        nv, v, H, P = design_wetight_matrix_wls(iter, ns, obs, eph, rs, dts, x)
        if nv < 8:
            continue
        v1 = v[:nv]
        H1 = H[:nv, :8]
        P1 = P[:nv, :nv]
        dx = lst(H1, P1, v1)
        x += dx
        if norm(dx) < 1e-4:
            break
    return x

def WLS_pos_vel_estimation(obs_filename, eph_filename):
    out = []
    x = np.zeros(8)
    all_obs = read_obs_mat(obs_filename)
    all_eph = read_eph_mat(eph_filename)
    for i in range(len(all_obs)):
        obs = all_obs[i]
        ns = len(obs.sat)
        if ns < 4:
            continue
        rs, dts = satposs(obs, all_eph)
        x = estpos(ns, obs, all_eph, rs, dts)
        out.append([obs.t[0], x[0], x[1], x[2], x[4], x[5], x[6]])
    return out

