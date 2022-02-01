import subprocess
from datetime import datetime
from typing import List

import fsspec

from stactools.nclimgrid.constants import Status
from stactools.nclimgrid.errors import BadInput

BLOCKSIZE = 2**22


def cog_nc(nc_path: str, cog_path: str, var: str, index: int) -> int:
    """Create a COG for a given time index into a NetCDF variable"""
    gdal_path = f"netcdf:{nc_path}:{var}"
    args = [
        "gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b",
        f"{index}"
    ]
    args.append(gdal_path)
    args.append(cog_path)
    result = subprocess.run(args, capture_output=True)
    return result.returncode


def download_nc(nc_remote_url: str, nc_local_path: str):
    with fsspec.open(nc_remote_url) as source:
        with fsspec.open(nc_local_path, "wb") as target:
            data = True
            while data:
                data = source.read(BLOCKSIZE)
                target.write(data)


def daily_nc_url(year: int, month: int, status: Status, variable: str) -> str:
    """Use the directory structure used in NOAA's (and Microsoft's) online data
    storage to generate the url to a NetCDF file."""
    if year < 1970:
        url_end = (f"beta/by-month/{year}/{month:02d}/ncdd-{year}{month:02d}"
                   f"-grd-{status.value}.nc")
    else:
        url_end = (f"beta/by-month/{year}/{month:02d}/{variable}-{year}"
                   f"{month:02d}-grd-{status.value}.nc")
    return url_end


def generate_years_months(start_month_str: str,
                          end_month_str: str) -> List[List[int]]:
    """Create a list of lists containing the integer year and month combinations
    for the desired date range.

    Returns:
        years_months (List[List[int]]): list of lists of integer year and month
        values, e.g., [[2020, 09], [2020, 10], [2020, 11]].
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
