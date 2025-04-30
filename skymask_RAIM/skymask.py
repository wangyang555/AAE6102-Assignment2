import numpy as np
import pandas as pd
from numpy.linalg import norm, lstsq
from gnsscommon import *
from ionosphere import *
from troposphere import *
from read_mat import *

# using skymask to improve the positioning accuracy

MAXITR =    10          #  max number of iteration or point pos
REL_HUMI =  0.7         #  relative humidity for Saastamoinen model
MIN_EL = np.deg2rad(5)  #  min elevation for measurement


def read_skymask_csv(filepath):
    """
    read skymask file (az, el)
    """
    df = pd.read_csv(filepath)
    azimuths = df["Azimuth_angle_deg"].to_numpy()
    elevations = df["Elevation_angle_deg"].to_numpy()
    return azimuths, elevations

def interpolate_elevation(azimuths, elevations, query_azimuth):
    """
    Interpolate the altitude angle based on the given azimuth angle.
    """
    query_azimuth = np.asarray(query_azimuth) % 360
    # Because some masks may not be completely closed at 0 and 360 degrees, they need to be supplemented.
    # In this experiment, they are closed and can be ignored.
    if azimuths[0] != 0 or azimuths[-1] != 360:
        azimuths = np.concatenate([azimuths, [azimuths[0]+360]])
        elevations = np.concatenate([elevations, [elevations[0]]])
    tmp_el = np.interp(query_azimuth, azimuths, elevations)
    return tmp_el

def design_wetight_matrix_wls_skymask(iter, ns, obs, eph, rs, dts, x, sky_azs, sky_els):
    """
    positioning using prange with skymask
    """
    v = np.zeros(ns)
    H = np.zeros([ns, 4])
    P = np.zeros([ns, ns])

    rr = x[0:3]
    dtr = x[3]
    pos = ecef2pos(rr)
    nv = 0

    for i in range(ns):
        if norm(rs[i, :3]) < rCST.RE_WGS84:
            continue
        r, e = geodist(rs[i, :3], rr)
        if r < 0:
            continue
        [az, el] = satazel(pos, e)
        if el < MIN_EL:
            continue
        # Data smaller than the elevation angle mask will not be included in the calculation
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
        tmp_el_mask = interpolate_elevation(sky_azs, sky_els, np.rad2deg(az))
        tmp_el_mask = np.deg2rad(tmp_el_mask)
        if el <= tmp_el_mask:
            P[nv, nv] = P[nv, nv] / 100000
        nv += 1
    return nv, v, H, P

def lsq_skymask(H, P, v):
    H_T = H.T
    HTPH = H_T @ P @ H
    #cond_num = np.linalg.cond(HTPH)
    HTPH_inv = np.linalg.inv(HTPH)
    HTPv = H_T @ P @ v
    dx = HTPH_inv @ HTPv
    return dx

def estpos_skymask(ns, obs, eph, rs, dts, sky_azs, sky_els):
    """ estimate position and clock errors with standard precision """
    x = np.zeros(4)
    v = np.zeros(ns)
    H = np.zeros([ns, 4])
    P = np.zeros([ns, ns])
    for iter in range(MAXITR):
        nv, v, H, P = design_wetight_matrix_wls_skymask(iter, ns, obs, eph, rs, dts, x, sky_azs, sky_els)
        if nv < 4:
            continue
        v1 = v[:nv]
        H1 = H[:nv, :4]
        P1 = P[:nv, :nv]
        dx = lsq_skymask(H1, P1, v1)
        x += dx
        if norm(dx) < 1e-4:
            break
    return x

def WLS_pos_estimation_skymask(obs_filename, eph_filename, skymask_filename):
    out = []
    x = np.zeros(4)
    all_obs = read_obs_mat(obs_filename)
    all_eph = read_eph_mat(eph_filename)
    sky_azs, sky_els = read_skymask_csv(skymask_filename)
    for i in range(len(all_obs)):
        obs = all_obs[i]
        ns = len(obs.sat)
        if ns < 4:
            continue
        rs, dts = satposs(obs, all_eph)
        x = estpos_skymask(ns, obs, all_eph, rs, dts, sky_azs, sky_els)
        out.append([obs.t[0], x[0], x[1], x[2]])
    return out
