from shapely.geometry import box, mapping


VARIABLES = ['prcp', 'tmin', 'tmax', 'tavg']

WGS84_BBOX = [-124.6875, 24.5625, -67.020836, 49.354168]
WGS84_GEOMETRY = mapping(box(*WGS84_BBOX))

