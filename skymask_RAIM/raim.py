import numpy as np
from numpy.linalg import norm, lstsq
from gnsscommon import *
from ionosphere import *
from troposphere import *
from read_mat import *
from scipy.stats import chi2


# using RAIM algorithm to detect the error and calculating the Protection Levels

MAXITR = 10  # max number of iteration or point pos
REL_HUMI = 0.7  # relative humidity for Saastamoinen model
MIN_EL = np.deg2rad(5)  # min elevation for measurement
P_FA = 1e-2  # probability of false alarm
P_MD = 1e-7  # probability of missed detection
K_MD = 5.33  # k-factor corresponding to p_md = 10^-7
SIGMA_PR = 3.0  # pseudorange measurement sigma (m)


def compute_threshold(n_satellites):
    """
    Compute threshold based on chi-square distribution
    Returns: RAIM detection threshold
    """
    dof = n_satellites - 4
    threshold = chi2.ppf(1 - P_FA, dof)
    return sqrt(threshold)


def design_weight_matrix_raim(iter, ns, obs, eph, rs, dts, x):
    """
    Design matrix and weight matrix for weighted RAIM
    Returns: nv: Number of valid measurements
             v: Residuals
             H: Design matrix
             P: Weight matrix
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
        v[nv] = p_range - (r + dtr - rCST.CLIGHT * dts[i, 0] + dion + dtrp)
        # design matrix
        H[nv, 0:3] = -e
        H[nv, 3] = 1
        # weight matrix
        P[nv, nv] = get_weight_based_elevation(el)
        nv += 1
    return nv, v[:nv], H[:nv, :], P[:nv, :nv]


def compute_raim_statistic(H, P, v, K):
    """
    Compute RAIM test statistic (WSSE)
    Returns: sqrt(wsse): sqrt(Weighted Sum of Squared Errors)
    """
    proj_matrix = H @ K
    residuals = (np.eye(len(v)) - proj_matrix) @ v
    # Compute WSSE
    # wsse = residuals.T @ P @ residuals
    wsse = residuals.T @ residuals
    return sqrt(wsse)


def compute_slopes(H, P, K):
    """
    Compute slopes for each satellite
    Returns: v_slopes: Vertical slopes for each satellite
             h_slopes: Horizontal slopes for each satellite
    """
    n_satellites = H.shape[0]
    proj_matrix = H @ K
    v_slopes = np.zeros(n_satellites)
    h_slopes = np.zeros(n_satellites)
    for i in range(n_satellites):
        sigma_i = 1.0 / np.sqrt(P[i, i])
        v_slopes[i] = abs(K[2, i] * sigma_i) / np.sqrt(1 - proj_matrix[i, i])
        h_slopes[i] = np.sqrt((K[0, i] ** 2 + K[1, i] ** 2) * sigma_i ** 2) / np.sqrt(1 - proj_matrix[i, i])
    return v_slopes, h_slopes


def compute_protection_levels(H, P, K, threshold):
    """
    Compute vertical, horizontal, and 3D protection levels
    Returns: vpl: Vertical Protection Level
             hpl: Horizontal Protection Level
             pl_3d: 3D Protection Level
    """
    # Compute position error variances
    pos_cov = np.linalg.inv(H.T @ P @ H)
    sigma_v = np.sqrt(pos_cov[2, 2])
    sigma_h = np.sqrt(pos_cov[0, 0] + pos_cov[1, 1])
    v_slopes, h_slopes = compute_slopes(H, P, K)
    # Compute protection levels
    vpl = max(v_slopes) * np.sqrt(threshold) + K_MD * sigma_v
    hpl = max(h_slopes) * np.sqrt(threshold) + K_MD * sigma_h
    pl_3d = np.sqrt(vpl ** 2 + hpl ** 2)
    return vpl, hpl, pl_3d


def lst(H, P, v):
    """
    Least squares solution with weighting
    Returns: dx: Position updates
             K: Weighted pseudo-inverse of H
    """
    H_T = H.T
    HTPH = H_T @ P @ H
    HTPH_inv = np.linalg.inv(HTPH)
    K = HTPH_inv @ H_T @ P
    dx = K @ v
    return dx, K


def detect_exclude(H, P, v, x, max_iterations=3):
    """
    Detect and exclude faulty measurements
    Returns: x_final: Final position solution
             excluded_indices: Indices of excluded satellites
             wsse: Final test statistic
             pl_3d: 3D Protection Level
    """
    n_satellites = H.shape[0]
    excluded_indices = []
    iterations = 0
    x_final = x.copy()

    while iterations < max_iterations and n_satellites > 4:
        threshold = compute_threshold(n_satellites)
        dx, K = lst(H, P, v)
        x_final = x + dx
        wsse = compute_raim_statistic(H, P, v, K)
        if wsse <= threshold:
            break
        proj_matrix = H @ K
        residuals = (np.eye(n_satellites) - proj_matrix) @ v
        nsr = np.zeros(n_satellites)
        for i in range(n_satellites):
            nsr[i] = residuals[i] ** 2
        worst_sv_idx = np.argmax(nsr)

        # Exclude the satellite
        mask = np.ones(n_satellites, dtype=bool)
        mask[worst_sv_idx] = False
        excluded_indices.append(worst_sv_idx)
        H = H[mask]
        v = v[mask]
        P_new = np.zeros((n_satellites - 1, n_satellites - 1))
        idx_new = 0
        for i in range(n_satellites):
            if i != worst_sv_idx:
                P_new[idx_new, idx_new] = P[i, i]
                idx_new += 1
        P = P_new
        n_satellites -= 1
        iterations += 1
    threshold = compute_threshold(n_satellites)
    _, K = lst(H, P, v)
    vpl, hpl, pl_3d = compute_protection_levels(H, P, K, threshold)
    return x_final, excluded_indices, wsse, pl_3d


def estpos_raim(ns, obs, eph, rs, dts):
    """
    Estimate position with RAIM-based fault detection and exclusion

    Returns: x: Position solution
             excluded_sats: Indices of excluded satellites
             protection_level: 3D protection level
    """
    x = np.zeros(4)
    for iter in range(MAXITR):
        nv, v, H, P = design_weight_matrix_raim(iter, ns, obs, eph, rs, dts, x)
        if nv < 5:  # At least 5 satellites needed for RAIM
            continue
        if iter < MAXITR - 1:
            dx, K = lst(H, P, v)
            x += dx
        else:
            x, excluded_indices, wsse, pl_3d = detect_exclude(H, P, v, x)
            excluded_sats = []
            idx_map = {}

            valid_count = 0
            for i in range(ns):
                if norm(rs[i, :3]) < rCST.RE_WGS84:
                    continue
                r, e = geodist(rs[i, :3], x[0:3])
                if r < 0:
                    continue
                pos = ecef2pos(x[0:3])
                [az, el] = satazel(pos, e)
                if el < MIN_EL:
                    continue
                if obs.P[i] == 0:
                    continue
                idx_map[valid_count] = obs.sat[i]
                valid_count += 1
            for idx in excluded_indices:
                if idx in idx_map:
                    excluded_sats.append(idx_map[idx])
            return x, wsse, excluded_sats, pl_3d
    nv, v, H, P = design_weight_matrix_raim(MAXITR - 1, ns, obs, eph, rs, dts, x)
    dx, K = lst(H, P, v)
    x += dx
    wsse = compute_raim_statistic(H, P, v, K)
    threshold = compute_threshold(nv)
    _, _, pl_3d = compute_protection_levels(H, P, K, threshold)
    return x, wsse, [], pl_3d


def RAIM_WLS_pos_estimation(obs_filename, eph_filename):
    """
    Main function for RAIM-based WLS positioning
    """
    out = []
    position_errors = []
    protection_levels = []
    excluded_satellites = []

    x = np.zeros(4)
    all_obs = read_obs_mat(obs_filename)
    all_eph = read_eph_mat(eph_filename)

    for i in range(len(all_obs)):
        obs = all_obs[i]
        ns = len(obs.sat)

        if ns < 5:  # Need at least 5 satellites for RAIM
            continue

        rs, dts = satposs(obs, all_eph)
        x, wsse, excluded_sats, pl_3d = estpos_raim(ns, obs, all_eph, rs, dts)

        out.append([obs.t[0], x[0], x[1], x[2]])
        position_errors.append(wsse)
        protection_levels.append(pl_3d)
        excluded_satellites.append(excluded_sats)

    return out, position_errors, protection_levels, excluded_satellites


def generate_stanford_chart(position_errors, protection_levels, alarm_limit=50.0):
    """
    Generate Stanford Chart for integrity analysis
    """
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 8))
    plt.scatter(protection_levels, position_errors, alpha=0.5)

    max_val = max(np.max(position_errors), np.max(protection_levels), alarm_limit) * 1.1
    plt.plot([0, max_val], [0, max_val], 'r--')  # PE = PL line
    plt.axhline(y=alarm_limit, color='g', linestyle='--')  # AL horizontal line
    plt.axvline(x=alarm_limit, color='g', linestyle='--')  # AL vertical line

    plt.fill_between([0, alarm_limit], [0, 0], [alarm_limit, alarm_limit],
                     color='green', alpha=0.2, label='Normal Operation')
    plt.fill_between([alarm_limit, max_val], [0, 0], [alarm_limit, alarm_limit],
                     color='yellow', alpha=0.2, label='Misleading Information')
    plt.fill_between([0, alarm_limit], [alarm_limit, alarm_limit], [max_val, max_val],
                     color='orange', alpha=0.2, label='System Unavailable')
    plt.fill_between([alarm_limit, max_val], [alarm_limit, alarm_limit], [max_val, max_val],
                     color='red', alpha=0.2, label='Hazardous Misleading Information')

    normal = np.sum((position_errors < alarm_limit) & (protection_levels < alarm_limit))
    mi = np.sum((position_errors < alarm_limit) & (protection_levels >= alarm_limit))
    unavailable = np.sum((position_errors >= alarm_limit) & (protection_levels >= alarm_limit))
    hmi = np.sum((position_errors >= alarm_limit) & (protection_levels < alarm_limit))

    total_points = len(position_errors)
    legend_labels = [
        f'Normal Operation: {normal} ({normal / total_points * 100:.2f}%)',
        f'Misleading Information: {mi} ({mi / total_points * 100:.2f}%)',
        f'System Unavailable: {unavailable} ({unavailable / total_points * 100:.2f}%)',
        f'Hazardous Misleading Information: {hmi} ({hmi / total_points * 100:.2f}%)'
    ]

    plt.legend(legend_labels)

    plt.grid(True)
    plt.xlabel('Protection Level (m)')
    plt.ylabel('Position Error (m)')
    plt.title('Stanford Chart for GNSS Integrity Monitoring')

    plt.show()

