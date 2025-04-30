## use EKF to estimate the pos and vel of receiver

import numpy as np
from numpy.linalg import norm, lstsq, inv
from gnsscommon import *
from ionosphere import *
from troposphere import *
from read_mat import *

MAXITR = 10  # max number of iteration or point pos
REL_HUMI = 0.7  # relative humidity for Saastamoinen model
MIN_EL = np.deg2rad(5)  # min elevation for measurement

def state_transition(x, dt):
    """
    状态转移函数 - EKF预测步骤
    """
    F = np.eye(8)
    F[0, 4] = dt
    F[1, 5] = dt
    F[2, 6] = dt
    F[3, 7] = dt
    x_pred = F @ x
    return x_pred, F


def design_matrix_ekf(iter, ns, obs, eph, rs, dts, x):
    """
    为EKF构建设计矩阵和残差向量
    """
    v = np.zeros(ns * 2)
    H = np.zeros([ns * 2, 8])
    R = np.zeros([ns * 2, ns * 2])

    rr = x[0:3]
    dtr = x[3]
    rv = x[4:7]
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
            gpst2time(obs.week[i], obs.t[i])
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
        v[nv] = p_range - (r + dtr - rCST.CLIGHT * dts[i, 0] + dion + dtrp)
        H[nv, 0:3] = -e
        # design matrix for clock bias
        H[nv, 3] = 1
        R[nv, nv] = 1 / get_weight_based_elevation(el) * 3
        nv += 1
        # Doppler measurement
        if obs.D[i] == 0:
            continue
        doppler_measurement = -obs.D[i]  # * rCST.CLIGHT / rCST.GPS_L1_FREQ
        # range rate
        range_rate = np.sum((rs[i, :3] - rr) * (rs[i, 3:] - rv)) / r
        # clock rate
        clock_rate = dtrv - dts[i, 1] * rCST.CLIGHT
        # earth correction rate
        earth_correction_rate = rCST.OMGE * (
                    rs[i, 3] * rr[1] + rv[1] * rs[i, 0] - rs[i, 4] * rr[0] - rv[0] * rs[i, 1]) / rCST.CLIGHT
        # velocity components of design matrix
        H[nv, 0] = -ev[0] + e[0] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 1] = -ev[1] + e[1] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 2] = -ev[2] + e[2] * (e[0] * ev[0] + e[1] * ev[1] + e[2] * ev[2])
        H[nv, 4:7] = -e
        H[nv, 7] = 1  # clock drift
        v[nv] = doppler_measurement - (range_rate + clock_rate + earth_correction_rate)
        R[nv, nv] = R[nv - 1, nv - 1] / 5
        nv += 1
    v = v[:nv]
    H = H[:nv, :]
    R_valid = np.zeros((nv, nv))
    for i in range(nv):
        R_valid[i, i] = R[i, i]
    return nv, v, H, R_valid


def initialize_ekf_state():
    """
    初始化EKF状态向量和协方差矩阵
    """
    x = np.zeros(8)
    P = np.eye(8)
    P[0:3, 0:3] *= 1.0e4
    P[3, 3] = 1.0e4
    P[4:7, 4:7] *= 1.0e2
    P[7, 7] = 1.0e2
    return x, P


def init_process_noise(dt):
    """
    初始化过程噪声协方差矩阵
    """
    Q = np.zeros((8, 8))
    sp = 0.5  # m/sqrt(s)
    Q[0:3, 0:3] = np.eye(3) * (sp ** 2) * dt
    sv = 0.1
    Q[4:7, 4:7] = np.eye(3) * (sv ** 2) * dt
    Q[3, 3] = sp ** 2 / dt ** 2
    Q[7, 7] = sv ** 2 / dt ** 2
    return Q


def ekf_iteration(ns, obs, eph, rs, dts, x, P, dt):
    """
    执行一次EKF迭代
    """
    x_pred, F = state_transition(x, dt)
    Q = init_process_noise(dt)
    P_pred = F @ P @ F.T + Q
    for iter in range(MAXITR):
        nv, v, H, R = design_matrix_ekf(iter, ns, obs, eph, rs, dts, x_pred)

        if nv < 8:
            return x_pred, P_pred
        HP = H @ P_pred
        S = HP @ H.T + R
        K = P_pred @ H.T @ inv(S)
        dx = K @ v
        x_pred = x_pred + dx
        I_KH = np.eye(8) - K @ H
        P_pred = I_KH @ P_pred @ I_KH.T + K @ R @ K.T
        if norm(dx) < 1e-4:
            break
    return x_pred, P_pred


def EKF_pos_vel_estimation(obs_filename, eph_filename):
    """
    使用EKF估计位置和速度
    """
    out = []
    all_obs = read_obs_mat(obs_filename)
    all_eph = read_eph_mat(eph_filename)

    x, P = initialize_ekf_state()
    prev_time = None

    for i in range(len(all_obs)):
        obs = all_obs[i]
        ns = len(obs.sat)
        if ns < 4:
            continue
        rs, dts = satposs(obs, all_eph)

        current_time = obs.t[0]
        if prev_time is None:
            dt = 0.1
        else:
            dt = current_time - prev_time
        prev_time = current_time
        x, P = ekf_iteration(ns, obs, all_eph, rs, dts, x, P, dt)
        out.append([obs.t[0], x[0], x[1], x[2], x[4], x[5], x[6]])
    return out
