from datetime import datetime
from enum import Enum

from shapely.geometry import box, mapping


class Status(Enum):
    SCALED = "scaled"
    PRELIM = "prelim"


VARIABLES = ["prcp", "tavg", "tmax", "tmin"]
MONTHLY_START = datetime(1895, 1, 1)

WGS84_BBOX = [-124.6875, 24.5625, -67.020836, 49.354168]
WGS84_GEOMETRY = mapping(box(*WGS84_BBOX))

COG_ASSET_TITLE = "COG image"
NC_ASSET_TITLE = "NetCDF file"

DAILY_COLLECTION_TITLE = "NOAA Daily U.S. Climate Gridded Dataset (NClimGrid-d)"
DAILY_COLLECTION_DESCRIPTION = """The NOAA Daily U.S. Climate Gridded Dataset
(NClimGrid-d) consists of four climate variables derived from the Global
Historical Climatology Network Daily dataset (GHCN-D): maximum temperature,
minimum temperature, average temperature, and precipitation. Daily values in a
1/24 degree lat/lon (nominal 5x5 kilometer) grid are provided for the
Continental United States. Daily data is available from 1951 to the present.

On an annual basis, approximately one year of “final” nClimGrid will be
submitted to replace the initially supplied “preliminary” data for the same
time period. Users should be sure to ascertain which level of data is required
for their research."""

MONTHLY_COLLECTION_TITLE = "NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid)"
MONTHLY_COLLECTION_DESCRIPTION = """The NOAA Monthly U.S. Climate Gridded Dataset
(NClimGrid) consists of four climate variables derived from the Global
Historical Climatology Network Daily dataset (GHCN-D): maximum temperature,
minimum temperature, average temperature, and precipitation. Monthly values in a
in a 1/24 degree lat/lon (nominal 5x5 kilometer) grid are provided for the
Continental United States. Monthly data is available from 1895 to the present.

On an annual basis, approximately one year of “final” nClimGrid will be
submitted to replace the initially supplied “preliminary” data for the same
time period. Users should be sure to ascertain which level of data is required
for their research."""
