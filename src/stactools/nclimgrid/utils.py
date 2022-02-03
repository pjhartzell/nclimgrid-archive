import subprocess
from datetime import datetime
from typing import List, Tuple

import fsspec
from pystac import Asset, MediaType

from stactools.nclimgrid.constants import COG_ASSET_TITLE
from stactools.nclimgrid.errors import BadInput

BLOCKSIZE = 2**22


def cog_nc(nc_path: str, cog_path: str, var: str, index: int) -> int:
    """Create a COG for a given time index into a NetCDF variable.

    Args:
        nc_path (str): local path to NetCDF file
        cog_path (str): local path to COG storage location
        var (str): weather variable ("prcp", "tavg", "tmax", or "tmin")
        index (int): 1-based index into NetCDF timestack

    Returns:
        int: COG creation status (0=success)
    """
    gdal_path = f"netcdf:{nc_path}:{var}"
    args = [
        "gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b",
        f"{index}"
    ]
    args.append(gdal_path)
    args.append(cog_path)
    result = subprocess.run(args, capture_output=True)
    return result.returncode


def create_cog_asset(cog_href: str, var: str) -> Tuple[str, Asset]:
    """Creates a COG Asset.

    Args:
        cog_href (str): COG location
        var (str): weather variable ("prcp", "tavg", "tmax", or "tmin")

    Returns:
        str: Asset key
        Asset: STAC Asset
    """
    key = f"{var}-cog"
    title = f"{var} {COG_ASSET_TITLE}"

    asset = Asset(href=cog_href,
                  media_type=MediaType.COG,
                  roles=["data"],
                  title=title)

    return key, asset


def download_nc(nc_remote_url: str, nc_local_path: str) -> None:
    """Downloads an online NetCDF.

    Args:
        nc_remote_url (str): online NetCDF location
        nc_local_path (str): location to download NetCDF file
    """
    with fsspec.open(nc_remote_url) as source:
        with fsspec.open(nc_local_path, "wb") as target:
            data = True
            while data:
                data = source.read(BLOCKSIZE)
                target.write(data)


def generate_years_months(start_month_str: str,
                          end_month_str: str) -> List[List[int]]:
    """Generates the year and month combinations between (inclusive) the desired
    start and end YYYYMM dates.

    Args:
        start_month_str (str): start date in YYYYMM format
        end_month_str (str): end date in YYYYMM format

    Returns:
        (List[List[int]]): list of lists of integer year and month
        values, e.g., [[2020, 9], [2020, 10], [2020, 11]].
    """
    try:
        start_date = datetime.strptime(start_month_str, "%Y%m")
        start_year = start_date.year
        start_month = start_date.month
    except ValueError:
        raise BadInput("Incorrect start date format, should be YYYYMM")

    try:
        end_date = datetime.strptime(end_month_str, "%Y%m")
        end_year = end_date.year
        end_month = end_date.month
    except ValueError:
        raise BadInput("Incorrect end date format, should be YYYYMM")

    if start_date > end_date:
        raise BadInput("End date must be >= start date")

    def month_list(start_year: int, end_year: int, start_month: int,
                   end_month: int):
        month_list = []
        for year in range(start_year, end_year + 1):
            for month in range(start_month, end_month + 1):
                month_list.append([year, month])
        return month_list

    if start_year == end_year:
        years_months = month_list(start_year, end_year, start_month, end_month)
    elif end_year - start_year == 1:
        years_months = month_list(start_year, start_year, start_month, 12)
        years_months.extend(month_list(end_year, end_year, 1, end_month))
    else:
        years_months = month_list(start_year, start_year, start_month, 12)
        years_months.extend(month_list(start_year + 1, end_year - 1, 1, 12))
        years_months.extend(month_list(end_year, end_year, 1, end_month))

    return years_months
