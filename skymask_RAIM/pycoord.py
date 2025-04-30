# WANG Yang did this in 2019
import math
import numpy as np

ELLIPSOIDS = {
    "wgs84": {
        "a": 6378137.,
        "f": 1 / 298.257223563,
    },
    "cgcs2000": {
        "a": 6378137.,
        "f": 1 / 298.257222101,
    },
    "grs80": {
        "a": 6378137.,
        "f": 1 / 298.257222100882711243,
    },
}

GEO_RE = 6371137  # 地球平均半径


GEO_PI = 3.14159265358979323846

# see P88 of IS-GPS-200D
GPS_LIGHT_SPEED = 2.99792458E8
GPS_UN_GRAV = 3.986005E14
GPS_F_RELAT = -4.442807633E-10


def degree2radian(deg):
    """
    Convert degree to radians.

    :param deg: decimal degree.
    :type deg: float
    :return: radians
    :rtype: float

    Example usage::

    >> degree2radian(45.)
    >>
    """
    return deg * GEO_PI / 180.


def radian2degree(rad):
    """
    Convert radians to degree.

    :param rad: radians
    :type rad: float
    :return: degree
    :rtype: float

    Example usage::

    >> radian2degree(3.14)
    >>
    """
    return rad * 180. / GEO_PI


def xyz2blh(xcoordinate, ycoordinate, zcoordinate, ell='wgs84'):
    """
    Convert Cartesian Coordinate system to geographical coordinate system.

    :param xcoordinate: x coordinate
    :type xcoordinate: float.
    :param ycoordinate: y coordinate
    :type ycoordinate: float.
    :param zcoordinate: z coordinate
    :type zcoordinate: float
    :param ell: ellipsoid name. Candidates are 'wgs84', 'cgcs2000'. see `ELLIPSOIDS`.
    :returns: (latitude, longitude, height). Latitude and longitude are in decimal degree.
    :rtype: (float, float, float)

    Example usage::

    >> xyz2blh(6378137., 0, 0, 'wgs84')
    >> (0.0, 0.0, 0.0)
    """

    a_ell = ELLIPSOIDS[ell]['a']
    f_ell = ELLIPSOIDS[ell]['f']
    e2_ell = f_ell * (2 - f_ell)
    # l = np.atan2(y,x)
    lon_ell = np.arctan2(ycoordinate, xcoordinate)
    p_ell = np.sqrt(xcoordinate**2 + ycoordinate**2)
    r_ell = np.sqrt(p_ell**2 + zcoordinate**2)
    u_ell = np.arctan2(zcoordinate * ((1 - f_ell) +
                                      e2_ell * a_ell / r_ell), p_ell)
    lat_ell = np.arctan2(zcoordinate * (1 - f_ell) + e2_ell * a_ell * np.sin(u_ell)
                         ** 3, (1 - f_ell) * (p_ell - e2_ell * a_ell * np.cos(u_ell)**3))

    height = p_ell * np.cos(lat_ell) + zcoordinate * np.sin(lat_ell) - \
        a_ell * np.sqrt(1 - e2_ell * np.sin(lat_ell)**2)
    lat_deg = radian2degree(lat_ell)  # / Deg2Rad
    lon_deg = radian2degree(lon_ell)  # / Deg2Rad
    return lat_deg, lon_deg, height


def blh2xyz(lat_deg, lon_deg, height, ell='wgs84'):
    """
    Convert geographical coordinate system to Cartesian Coordinate system.

    :param lat_deg:latitude in decimal degree
    :type lat_deg: float.
    :param lon_deg:longitude in decimal degree
    :type lon_deg: float.
    :param height:height
    :type height: float.
    :param ell: ellipsoid name. Candidates are 'wgs84', 'cgcs2000'. see `ELLIPSOIDS`.
    :return:(x, y, z) in Cartesian Coordinate system.
    :rtype: (float, float, float)

    Example usage::

    >> xyz2blh(6378137., 0, 0, 'wgs84')
    >> (0.0, 0.0, 0.0)
    """
    a_ell = ELLIPSOIDS[ell]['a']
    f_ell = ELLIPSOIDS[ell]['f']
    e2_ell = f_ell * (2 - f_ell)
    lat_radian = degree2radian(lat_deg)
    lon_radian = degree2radian(lon_deg)
    n_ell = a_ell / math.sqrt(1 - e2_ell * math.sin(lat_radian) * math.sin(lat_radian))
    xcoordinate = (n_ell + height) * math.cos(lat_radian) * math.cos(lon_radian)
    ycoordinate = (n_ell + height) * math.cos(lat_radian) * math.sin(lon_radian)
    zcoordinate = ((1 - e2_ell) * n_ell + height) * math.sin(lat_radian)
    return xcoordinate, ycoordinate, zcoordinate


def neu2xyz(ncoordinate, ecoordinate, ucoordinate, base_xcoordinate, base_ycoordinate, base_zcoordinate, ell='wgs84'):
    """
    Convert NEU coordinate system to Cartesian Coordinate system

    :param ncoordinate: north coordinate
    :type ncoordinate: float.
    :param ecoordinate: east coordinate
    :type ecoordinate: float.
    :param ucoordinate: up coordinate
    :type ucoordinate: float.
    :param base_xcoordinate: x coordinate of base station
    :type base_xcoordinate: float.
    :param base_ycoordinate: y coordinate of base station
    :type base_ycoordinate: float.
    :param base_zcoordinate: z coordinate of base station
    :type base_zcoordinate: float.
    :param ell: ellipsoid name. Candidates are 'wgs84', 'cgcs2000'. see `ELLIPSOIDS`.
    :return: (x, y, z) of rover station
    :rtype: (float, float, float)

    Example usage::

    >> neu2xyz(-1.3073, 0.4840, -2.2613, -2267823.811, 5009335.937, 3220977.864, 'wgs84')
    >> (0.0, 0.0, 0.0)
    """
    lat_deg, lon_deg, height = xyz2blh(base_xcoordinate, base_ycoordinate, base_zcoordinate, ell)
    lat_radian = degree2radian(lat_deg)
    lon_radian = degree2radian(lon_deg)
    neu_matrix = np.array([[ncoordinate], [ecoordinate], [ucoordinate]])
    base_coordinate = np.array([[base_xcoordinate], [base_ycoordinate], [base_zcoordinate]])
    transfer_matrix = np.array([[-math.sin(lat_radian) * math.cos(lon_radian), -math.sin(lon_radian),
                                 math.cos(lat_radian) * math.cos(lon_radian)],
                                [-math.sin(lat_radian) * math.sin(lon_radian), math.cos(lon_radian),
                                 math.cos(lat_radian) * math.sin(lon_radian)],
                                [math.cos(lat_radian), 0, math.sin(lat_radian)]])
    differcence_coordinate = np.dot(transfer_matrix, neu_matrix)
    rover_coordinate = differcence_coordinate + base_coordinate
    return rover_coordinate[0][0], rover_coordinate[1][0], rover_coordinate[2][0]


def xyz2neu(base_xcoordinate, base_ycoordinate, base_zcoordinate, rover_xcoordinate, rover_ycoordinate, rover_zcoordinate, ell='wgs84'):
    """
    Convert Cartesian Coordinate system to neu coordinate system

    :param base_xcoordinate: x coordinate of base station
    :type base_xcoordinate: float.
    :param base_ycoordinate: y coordinate of base station
    :type base_ycoordinate: float.
    :param base_zcoordinate: z coordinate of base station
    :type base_zcoordinate: float.
    :param rover_xcoordinate: x coordinate of rover station
    :type rover_xcoordinate: float.
    :param rover_ycoordinate: y coordinate of rover station
    :type rover_ycoordinate: float.
    :param rover_zcoordinate: z coordinate of rover station
    :type rover_zcoordinate: float.
    :param ell: ellipsoid name. Candidates are 'wgs84', 'cgcs2000'. see `ELLIPSOIDS`.
    :return: coordinate of (N, E, U)
    :rtype: (float, float, float)

    Example usage::

    >> xyz2neu(-2267823.811, 5009335.937, 3220977.864, -2267823.7225, 5009334.5679, 3220975.5893, 'wgs84')
    >> (-1.3073 0.4840 -2.2613)
    """
    lat_deg, lon_deg, height = xyz2blh(base_xcoordinate, base_ycoordinate, base_zcoordinate, ell)
    lat_radian = degree2radian(lat_deg)
    lon_radian = degree2radian(lon_deg)
    base_coordinate = np.array([[base_xcoordinate], [base_ycoordinate], [base_zcoordinate]])
    rover_coordinate = np.array([[rover_xcoordinate], [rover_ycoordinate], [rover_zcoordinate]])
    difference_coordinate = rover_coordinate - base_coordinate
    transfer_matrix = np.array(
        [[-math.sin(lat_radian) * math.cos(lon_radian), -math.sin(lat_radian) * math.sin(lon_radian),
          math.cos(lat_radian)], [-math.sin(lon_radian), math.cos(lon_radian), 0],
         [math.cos(lat_radian) * math.cos(lon_radian), math.cos(lat_radian) * math.sin(lon_radian),
          math.sin(lat_radian)]])
    neu_coordinate = np.dot(transfer_matrix, difference_coordinate)
    return neu_coordinate[0][0], neu_coordinate[1][0], neu_coordinate[2][0]
