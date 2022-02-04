from datetime import datetime
from enum import Enum

from pystac import Link, Provider, ProviderRole
from pystac.extensions.scientific import Publication
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

LICENSE = "proprietary"
LICENSE_LINK = Link(
    rel="license",
    target="https://www.ngdc.noaa.gov/ngdcinfo/privacy.html#copyright",
    title="Copyright Notice - NCEI")
PROVIDERS = [
    Provider(name=("National Oceanic and Atmospheric Administration, "
                   "National Centers for Environmental Information"),
             roles=[
                 ProviderRole.PRODUCER, ProviderRole.PROCESSOR,
                 ProviderRole.HOST
             ],
             url=("https://www.ncei.noaa.gov/access/metadata/landing-page/bin/"
                  "iso?id=gov.noaa.ncdc:C00332"))
]

DAILY_COLLECTION_ID = "nclimgrid-daily"
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
DAILY_COLLECTION_KEYWORDS = [
    "Air Temperature", "Precipitation", "Surface Observations",
    "Daily Climatology", "CONUS"
]

MONTHLY_COLLECTION_ID = "nclimgrid-monthly"
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
MONTHLY_COLLECTION_KEYWORDS = [
    "Air Temperature", "Precipitation", "Surface Observations",
    "Monthly Climatology", "CONUS"
]
MONTHLY_DATA_DOI = "10.7289/V5SX6B56"
MONTHLY_DATA_CITATION = (
    "Vose, Russell S., Applequist, Scott, Squires, Mike, Durre, Imke, Menne, "
    "Matthew J., Williams, Claude N. Jr., Fenimore, Chris, Gleason, Karin, and "
    "Arndt, Derek (2014): NOAA Monthly U.S. Climate Gridded Dataset (NClimGrid)"
    ", Version 1. [indicate subset used]. NOAA National Centers for "
    "Environmental Information. DOI:10.7289/V5SX6B56 [access date].")
MONTHLY_DATA_PUBLICATIONS = [
    Publication("10.1175/JAMC-D-13-0248.1", (
        "Vose, R. S., Applequist, S., Squires, M., Durre, I., Menne, M. J., "
        "Williams, C. N., Jr., Fenimore, C., Gleason, K., & Arndt, D. (2014). "
        "Improved Historical Temperature and Precipitation Time Series for U.S."
        " Climate Divisions, Journal of Applied Meteorology and Climatology, "
        "53(5), 1232-1251."))
]
