# read obs and eph file of .mat format from matlab
import scipy.io
import numpy as np
from gnsscommon import *
from ephemeris import *

def read_eph_mat(mat_filename):
    mat_data = scipy.io.loadmat(mat_filename, squeeze_me=True, struct_as_record=False)
    ephData = mat_data['ephData']
    all_eph = []
    try:
        for i in range(len(ephData.gpsl1)):
            if isinstance(ephData.gpsl1[i].IODE_sf2, np.ndarray):
                continue
            eph = Eph(i + 1)
            eph.iode = ephData.gpsl1[i].IODE_sf2
            eph.iodc = ephData.gpsl1[i].IODC
            eph.f0 = ephData.gpsl1[i].a_f0
            eph.f1 = ephData.gpsl1[i].a_f1
            eph.f2 = ephData.gpsl1[i].a_f2
            eph.toc = ephData.gpsl1[i].t_oc
            eph.toe = ephData.gpsl1[i].t_oe
            # eph.tot = ephData.gpsl1[0].
            eph.week = ephData.gpsl1[i].weekNumber + 1024
            eph.crs = ephData.gpsl1[i].C_rs
            eph.crc = ephData.gpsl1[i].C_rc
            eph.cuc = ephData.gpsl1[i].C_uc
            eph.cus = ephData.gpsl1[i].C_us
            eph.cic = ephData.gpsl1[i].C_ic
            eph.cis = ephData.gpsl1[i].C_is
            eph.e = ephData.gpsl1[i].e
            eph.i0 = ephData.gpsl1[i].i_0
            eph.A = ephData.gpsl1[i].sqrtA ** 2
            eph.deln = ephData.gpsl1[i].deltan
            eph.M0 = ephData.gpsl1[i].M_0
            eph.OMG0 = ephData.gpsl1[i].omega_0
            eph.OMGd = ephData.gpsl1[i].omegaDot
            eph.omg = ephData.gpsl1[i].omega
            eph.idot = ephData.gpsl1[i].iDot
            eph.tgd = ephData.gpsl1[i].T_GD
            eph.health = ephData.gpsl1[i].health
            eph.toes = eph.toe
            all_eph.append(eph)
    except (IndexError, AttributeError):
        pass
    return all_eph

def read_obs_mat(mat_filename):
    mat_data = scipy.io.loadmat(mat_filename, squeeze_me=True,struct_as_record=False)
    obs_data = mat_data['obsData']
    all_obs = []
    for i in range(len(obs_data)):
        try:
            tmp_obs = Obs()
            for j in range(len(obs_data[i].gpsl1.channel)):
                channel = obs_data[i].gpsl1.channel[j]
                if isinstance(channel.rawP, np.ndarray) or np.isnan(channel.rawP):
                    continue
                tmp_obs.sat.append(channel.SvId.satId)
                tmp_obs.t.append(channel.transmitTime)
                tmp_obs.week.append(channel.week + 1024)
                tmp_obs.P.append(channel.rawP)
                tmp_obs.corP.append(channel.corrP)
                tmp_obs.D.append(-channel.doppler)
                tmp_obs.SNR.append(channel.SNR)
            all_obs.append(tmp_obs)
        except (IndexError, AttributeError):
            pass
    return all_obs

