from calendar import monthrange
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from pystac import Item
from urllib.parse import urlparse
import xarray
from stactools.core.utils.convert import cogify
import stactools.core.create
from dateutil import parser

from stactools.nclimgrid.constants_v2 import VARS

logger = logging.getLogger(__name__)


def nc_href_dict(nc_href: str) -> Tuple[Dict[str, str], bool]:
    base, filename = os.path.split(nc_href)

    if "nclimgrid" in filename:  # monthly
        filenames = {var: f"nclimgrid_{var}.nc" for var in VARS}
        daily = False
    elif "ncdd" in filename:  # daily pre-1970
        filenames = {var: filename for var in VARS}
        daily = True
    else:  # daily 1970-onward
        suffix = filename[4:]
        filenames = {var: f"{var}{suffix}" for var in VARS}
        daily = True

    href_dict = {var: os.path.join(base, f) for var, f in filenames.items()}

    return (href_dict, daily)


def day_indices(nc_href: str) -> List[int]:
    href = nc_href
    if urlparse(nc_href).scheme.startswith("http"):
        href += "#mode=bytes"

    with xarray.open_dataset(href) as dataset:
        min_prcp = dataset.prcp.min(dim=("lat", "lon"), skipna=True)
        days = sum(min_prcp>=0).values

    return range(days, 0, -1)


def month_indices(nc_href: str) -> List[Dict[str, Any]]:
    href = nc_href
    if urlparse(nc_href).scheme.startswith("http"):
        href += "#mode=bytes"

    with xarray.open_dataset(href) as ds:
        years = ds.time.dt.year.data.tolist()
        months = ds.time.dt.month.data.tolist()

    indices = []
    for idx, (year, month) in enumerate(zip(years, months), start=1):
        indices.append({"idx": idx, "date": f"{year}{month:02d}"})

    return indices


def cog_daily(nc_hrefs: Dict[str, str], cog_dir: str, day: int) -> Dict[str, str]:
    cog_paths = {}
    for var in VARS:
        basename = os.path.splitext(os.path.basename(nc_hrefs[var]))[0]
        cog_paths[var] = os.path.join(cog_dir, f"{basename}-{day:02d}.tif")

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    profile = {"crs": "epsg:4326", "nodata": "nan"}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], day, profile)

    return cog_paths


def cog_monthly(nc_hrefs: Dict[str, str], cog_dir: str, month: Dict[str, Any]) -> Dict[str, str]:
    filenames = {var: f"nclimgrid-{var}-{month['date']}.tif" for var in VARS}
    cog_paths = {var: os.path.join(cog_dir, filenames[var]) for var in VARS}

    mode = ""
    if urlparse(nc_hrefs["prcp"]).scheme.startswith("http"):
        mode = "#mode=bytes"

    augmented_nc_hrefs = {}
    profile = {"crs": "epsg:4326", "nodata": "nan"}
    for var in VARS:
        augmented_nc_hrefs[var] = f"netcdf:{nc_hrefs[var]}{mode}:{var}"
        cogify(augmented_nc_hrefs[var], cog_paths[var], month["idx"], profile)

    return cog_paths


def create_item(cog_hrefs: List[str], daily, nc_hrefs) -> Item:
    basename = os.path.splitext(os.path.basename(cog_hrefs["prcp"]))[0]

    nominal_datetime: Optional[datetime] = None
    if not basename.startswith("nclimgrid"):  # daily
        id = basename[5:]
        year = int(id[0:4])
        month = int(id[4:6])
        day = int(id[-2:])
        start_datetime = datetime(year, month, day)
        end_datetime = datetime(year, month, day, 23, 59, 59)
        nominal_datetime = start_datetime
    else:  # monthly
        id = f"nclimgrid-{basename[-6:]}"
        year = int(id[-6:-2])
        month = int(id[-2:])
        start_datetime = datetime(year, month, 1)
        end_datetime = datetime(year, month, monthrange(year, month)[1])
        nominal_datetime = None

    item = stactools.core.create.item(cog_hrefs["prcp"])
    item.id = id
    item.datetime = nominal_datetime
    item.common_metadata.start_datetime = start_datetime
    item.common_metadata.end_datetime = end_datetime
    item.common_metadata.created = datetime.now(tz=timezone.utc)
    







def create_items(nc_href: str, cog_dir: str, latest_only: bool=False) -> List[Item]:
    nc_hrefs, daily = nc_href_dict(nc_href)

    items = []
    if daily:
        days = day_indices(nc_hrefs["prcp"])
        for day in days:
            cog_paths = cog_daily(nc_hrefs, cog_dir, day)
            items.append(create_item(cog_paths, daily, nc_hrefs))

    else:
        months = month_indices(nc_hrefs["prcp"])
        for month in months:
            cog_paths = cog_monthly(nc_hrefs, cog_dir, month)
            items.append(create_item(cog_paths, daily, nc_hrefs))


nc_href = "tests/data-files/netcdf/daily/beta/by-month/2022/01/prcp-202201-grd-prelim.nc"
nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily/beta/by-month/2022/06/prcp-202206-grd-prelim.nc"
cog_dir = "test_cogs"
create_items(nc_href, cog_dir)
