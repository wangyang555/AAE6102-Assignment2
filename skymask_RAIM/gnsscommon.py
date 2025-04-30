"""

This functions in this file are from rtklibexplorer/rtklib-py/rtkcmn.py
url: https://github.com/rtklibexplorer/rtklib-py

"""

from copy import copy
from math import floor, sin, cos, sqrt, asin, atan2, fabs
import numpy as np
from numpy.linalg import norm, inv

gpst0 = [1980, 1, 6, 0, 0, 0]

class rCST():
    """ class for constants """
    CLIGHT = 299792458.0
    MU_GPS = 3.9860050E14
    MU_GAL = 3.986004418E14
    MU_GLO = 3.9860044E14
    GME = 3.986004415E+14
    GMS = 1.327124E+20
    GMM = 4.902801E+12
    OMGE = 7.2921151467E-5
    OMGE_GAL = 7.2921151467E-5
    OMGE_GLO = 7.292115E-5
    RE_WGS84 = 6378137.0
    RE_GLO = 6378136.0
    FE_WGS84 = (1.0/298.257223563)
    J2_GLO = 1.0826257E-3  # 2nd zonal harmonic of geopot
    AU = 149597870691.0
    D2R = 0.017453292519943295
    AS2R = D2R/3600.0
    DAY_SEC = 86400.0
    CENTURY_SEC = DAY_SEC*36525.0
    GPS_L1_FREQ = 1575.42E6

class gtime_t():
    """ class to define the time """

    def __init__(self, time=0, sec=0.0):
        self.time = time
        self.sec = sec

class Obs():
    """ class to define the observation """
    def __init__(self):
        self.sat = []
        self.t = []
        self.week = []
        self.P = []
        self.corP = []
        self.D = []
        self.SNR = []

class Eph():
    """ class to define GPS/GAL/QZS/CMP ephemeris """
    sat = 0
    iode = 0
    iodc = 0
    f0 = 0.0
    f1 = 0.0
    f2 = 0.0
    toc = 0
    toe = 0
    tot = 0
    week = 0
    crs = 0.0
    crc = 0.0
    cus = 0.0
    cuc = 0.0
    cis = 0.0
    cic = 0.0
    e = 0.0
    i0 = 0.0
    A = 0.0
    deln = 0.0
    M0 = 0.0
    OMG0 = 0.0
    OMGd = 0.0
    omg = 0.0
    idot = 0.0
    tgd = [0.0, 0.0]
    sva = 0
    health = 0
    fit = 0
    toes = 0

    def __init__(self, sat=0):
        self.sat = sat

def epoch2time(ep):
    """ calculate time from epoch """
    doy = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    time = gtime_t()
    year = int(ep[0])
    mon = int(ep[1])
    day = int(ep[2])

    if year < 1970 or year > 2099 or mon < 1 or mon > 12:
        return time
    days = (year-1970)*365+(year-1969)//4+doy[mon-1]+day-2
    if year % 4 == 0 and mon >= 3:
        days += 1
    sec = int(ep[5])
    time.time = days*86400+int(ep[3])*3600+int(ep[4])*60+sec
    time.sec = ep[5]-sec
    return time


def gpst2utc(tgps, leaps_=-18):
    """ calculate UTC-time from gps-time """
    tutc = timeadd(tgps, leaps_)
    return tutc

def utc2gpst(tutc, leaps_=-18):
    """ calculate UTC-time from gps-time """
    tgps = timeadd(tutc, -leaps_)
    return tgps


def timeadd(t: gtime_t, sec: float):
    """ return time added with sec """
    tr = copy(t)
    tr.sec += sec
    tt = floor(tr.sec)
    tr.time += int(tt)
    tr.sec -= tt
    return tr


def timediff(t1: gtime_t, t2: gtime_t):
    """ return time difference """
    dt = t1.time - t2.time
    dt += (t1.sec - t2.sec)
    return dt


def gpst2time(week, tow):
    """ convert to time from gps-time """
    t = epoch2time(gpst0)
    if tow < -1e9 or tow > 1e9:
        tow = 0.0
    t.time += 86400*7*week+int(tow)
    t.sec = tow-int(tow)
    return t


def time2gpst(t: gtime_t):
    """ convert to gps-time from time """
    t0 = epoch2time(gpst0)
    sec = t.time-t0.time
    week = int(sec/(86400*7))
    tow = sec-week*86400*7+t.sec
    return week, tow


def time2epoch(t):
    """ convert time to epoch """
    mday = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28, 31, 30, 31,
            30, 31, 31, 30, 31, 30, 31, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31,
            30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    days = int(t.time/86400)
    sec = int(t.time-days*86400)
    day = days % 1461
    for mon in range(48):
        if day >= mday[mon]:
            day -= mday[mon]
        else:
            break
    ep = [0, 0, 0, 0, 0, 0]
    ep[0] = 1970+days//1461*4+mon//12
    ep[1] = mon % 12+1
    ep[2] = day+1
    ep[3] = sec//3600
    ep[4] = sec % 3600//60
    ep[5] = sec % 60+t.sec
    return ep


def time2doy(t):
    """ convert time to epoch """
    ep = time2epoch(t)
    ep[1] = ep[2] = 1.0
    ep[3] = ep[4] = ep[5] = 0.0
    return timediff(t, epoch2time(ep))/86400+1

def geodist(rs, rr):
    """
    geometric distance ----------------------------------------------------------
    * compute geometric distance and receiver-to-satellite unit vector
    * args   : double *rs       satellite position (ecef at transmission) (m)
    *          double *rr       receiver position (ecef at reception) (m)
    *          double *e        line-of-sight vector (ecef)
    * return : geometric distance (m) (0>:error/no satellite position)
    * notes  : distance includes sagnac effect correction
    """
    e = rs - rr
    r = norm(e)
    e /= r
    r += rCST.OMGE * (rs[0] * rr[1] -rs[1] * rr[0]) / rCST.CLIGHT
    return r, e

def geodist_v(rs, rr, r):
    """
    geometric distance ----------------------------------------------------------
    * compute geometric distance and receiver-to-satellite unit vector
    * args   : double *rs       satellite position (ecef at transmission) (m)
    *          double *rr       receiver position (ecef at reception) (m)
    *          double *e        line-of-sight vector (ecef)
    * return : geometric distance (m) (0>:error/no satellite position)
    * notes  : distance includes sagnac effect correction
    """
    e = rs - rr
    e /= r
    return e

def get_weight_based_elevation(el):
    """"
    根据高度角定权，采用的是gamit的高度角定权模型，其中a、b是经验值
    """
    if el <= 0.0:
        return 0.0
    a = 0.1
    b = 0.1
    weight = a ** 2 + (b / np.sin(el)) ** 2
    return 1 / weight


def get_weight_based_SNR(snr):
    """
    根据信噪比定权，a为经验值，在spp定位中a并不影响结果，因为a和信号频率有关
    """
    a = 0.00224
    weight = a * pow(10, -snr / 10)
    return 1 / weight

def xyz2enu(pos):
    """ return ECEF to ENU conversion matrix from LLH
        pos is LLH
    """
    sp = sin(pos[0])
    cp = cos(pos[0])
    sl = sin(pos[1])
    cl = cos(pos[1])
    E = np.array([[-sl, cl, 0],
                  [-sp*cl, -sp*sl, cp],
                  [cp*cl, cp*sl, sp]])
    return E


def ecef2pos(r):
    """  ECEF to LLH position conversion """
    pos = np.zeros(3)
    e2 = rCST.FE_WGS84*(2-rCST.FE_WGS84)
    r2 = r[0]**2+r[1]**2
    v = rCST.RE_WGS84
    z = r[2]
    zk = 0
    while abs(z - zk) >= 1e-4:
        zk = z
        sinp = z / np.sqrt(r2+z**2)
        v = rCST.RE_WGS84 / np.sqrt(1 - e2 * sinp**2)
        z = r[2] + v * e2 * sinp
    pos[0] = np.arctan(z / np.sqrt(r2)) if r2 > 1e-12 else np.pi / 2 * np.sign(r[2])
    pos[1] = np.arctan2(r[1], r[0]) if r2 > 1e-12 else 0
    pos[2] = np.sqrt(r2 + z**2) - v
    return pos


def pos2ecef(pos, isdeg: bool = False):
    """ LLH (rad/deg) to ECEF position conversion  """
    if isdeg:
        s_p = sin(pos[0]*np.pi/180.0)
        c_p = cos(pos[0]*np.pi/180.0)
        s_l = sin(pos[1]*np.pi/180.0)
        c_l = cos(pos[1]*np.pi/180.0)
    else:
        s_p = sin(pos[0])
        c_p = cos(pos[0])
        s_l = sin(pos[1])
        c_l = cos(pos[1])
    e2 = rCST.FE_WGS84 * (2.0 - rCST.FE_WGS84)
    v = rCST.RE_WGS84 / sqrt(1.0 - e2 * s_p**2)
    r = np.array([(v + pos[2]) * c_p*c_l,
                  (v + pos[2]) * c_p*s_l,
                  (v * (1.0 - e2) + pos[2]) * s_p])
    return r


def ecef2enu(pos, r):
    """ relative ECEF to ENU conversion """
    E = xyz2enu(pos)
    e = E @ r
    return e

def enu2ecef(pos, e):
    """ relative ECEF to ENU conversion """
    E = xyz2enu(pos)
    r = E.T @ e
    return r

def satazel(pos, e):
    """ calculate az/el from LOS vector in ECEF (e) """
    if pos[2] > -rCST.RE_WGS84 + 1:
        enu = ecef2enu(pos, e)
        az = atan2(enu[0], enu[1]) if np.dot(enu, enu) > 1e-12 else 0
        az = az if az > 0 else az + 2 * np.pi
        el = asin(enu[2])
        return [az, el]
    else:
        return [0, np.pi / 2]

def interpc(coef, lat):
    """ linear interpolation (lat step=15) """
    i = int(lat / 15.0)
    if i < 1:
        return coef[:, 0]
    if i > 4:
        return coef[:, 4]
    d = lat / 15.0 - i
    return coef[:, i-1] * (1.0 - d) + coef[:, i] * d
