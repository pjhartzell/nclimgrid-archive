from calendar import monthrange
from curses import start_color
from datetime import datetime, timezone
import os
import shutil
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from posixpath import join as urljoin
from typing import Any, Dict, Optional, Tuple, List
import logging
import subprocess

from pystac.extensions.projection import ProjectionExtension
from pystac import Asset, Item, MediaType
import fsspec
import xarray

from stactools.nclimgrid.constants import VARIABLES
from stactools.nclimgrid import constants
from stactools.nclimgrid.errors import CogCreationError

logger = logging.getLogger(__name__)


def get_nc_hrefs(href: str) -> Tuple[List[str], bool]:
    base, filename = os.path.split(href)
    if "nclimgrid" in filename:  # monthly
        filenames = [f"nclimgrid_{var}.nc" for var in VARIABLES]
        daily = False
    elif "ncdd" in filename:  # daily pre-1970
        filenames = [filename]
        daily = True
    else:  # daily 1970-onward
        suffix = filename[4:]
        filenames = [f"{var}{suffix}" for var in VARIABLES]
        daily = True

    if urlparse(href).scheme:
        hrefs = [urljoin(base, f) for f in filenames]
    else:
        hrefs = [os.path.join(base, f) for f in filenames]

    return hrefs, daily


def download_nc(nc_url: str, local_nc_dir: str) -> str:
    """Downloads an online NetCDF.

    Args:
        nc_remote_url (str): online NetCDF location
        nc_local_path (str): location to download NetCDF file
    """
    local_nc_path = os.path.join(local_nc_dir, os.path.split(nc_url)[1])
    logger.info(f"  - Downloading file {nc_url}...")
    with fsspec.open(nc_url) as source:
        with fsspec.open(local_nc_path, "wb") as target:
            # data = True
            # while data:
                # data = source.read(BLOCKSIZE)
                # target.write(data)
            data = source.read()
            target.write(data)
    return local_nc_path


def get_var_name(nc_href: str) -> str:
    filename = os.path.split(nc_href)[1]
    for var in VARIABLES:
        if var in filename:
            value = var
    if "ncdd" in filename:
        value = "ncdd"
    return value


def get_days(local_nc_paths: Dict[str, str]) -> List[int]:
    local_nc_path = local_nc_paths[VARIABLES[0]]
    with xarray.open_dataset(local_nc_path) as ds:
        days = list(range(1, len(ds["time"] + 1)))
        if "prelim" in local_nc_path:
            var_mean = ds[VARIABLES[0]].mean(dim=("lat", "lon"), skipna=True).values
            num_valid_days = (var_mean > -900).sum()
            days = list(range(1, num_valid_days + 1))
    return days


def get_month_indices(local_nc_paths: Dict[str, str]) -> List[Dict[str, Any]]:
    local_nc_path = local_nc_paths[VARIABLES[0]]
    with xarray.open_dataset(local_nc_path) as ds:
        years = ds.time.dt.year.data.tolist()
        months = ds.time.dt.month.data.tolist()
    indices = [{"idx": i, "yyyymm": f"{y}{m:02d}"} for i, (y, m) in enumerate(zip(years, months), start=1)]
    return indices


def get_local_cog_paths(local_nc_paths: Dict[str, str],
                        tmp_dir: str,
                        day: Optional[int] = None,
                        yyyymm: Optional[str] = None) -> Dict[str, str]:
    if yyyymm is not None:
        cog_filenames = {var: f"nclimgrid-{var}-{yyyymm}.tif" for var in VARIABLES}
    elif day is not None:
        local_nc_path = next(iter(local_nc_paths.values()))
        base = os.path.splitext(os.path.basename(local_nc_path))[0][5:]
        cog_filenames = {var: f"{var}-{base}-{day:02d}.tif" for var in VARIABLES}
    local_cog_paths = {var: os.path.join(tmp_dir, cog_filenames[var]) for var in VARIABLES}
    return local_cog_paths


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
        "gdal_translate", "-of", "COG", "-a_srs", f"EPSG:{constants.EPSG}",
        "-co", "compress=deflate", "-b", f"{index}"
    ]
    args.append(gdal_path)
    args.append(cog_path)
    logger.info(f"Running {args}")
    result = subprocess.run(args, capture_output=True)
    logger.info(result.stdout.decode('utf-8').strip())
    if result.returncode != 0:
        logger.error(result.stderr.decode('utf-8').strip())
    else:
        logger.info(result.stderr.decode('utf-8').strip())
    return result.returncode


# def upload_cogs(local_cog_paths: Dict[str, str], base_cog_href: str) -> Dict[str, str]:
#     cog_hrefs = {}

#     for var in VARIABLES:
#         cog_filename = os.path.basename(local_cog_paths[var])
#         if urlparse(base_cog_href).scheme:
#             cog_hrefs[var] = urljoin(base_cog_href, cog_filename)
#             logger.info(f"Uploading COG to {cog_filename}...")
#             with fsspec.open(local_cog_paths[var]) as source:
#                 with fsspec.open(cog_hrefs[var]) as target:
#                     data = source.read()
#                     target.write(data)
#             logger.info("...done uploading COG")
#         else:
#             logger.info(f"Copying COG to {cog_filename}...")
#             cog_hrefs[var] = os.path.join(base_cog_href, cog_filename)
#             shutil.copy(local_cog_paths[var], cog_hrefs[var])
#             logger.info("...done copying COG")

#     return cog_hrefs


def create_nclimgrid_item(cog_urls: Dict[str, str], daily: bool) -> Item:
    cog_url = next(iter(cog_urls.values()))
    cog_filename = os.path.splitext(os.path.basename(cog_url))[0]

    if daily:
        item_id = cog_filename[5:]

        year = int(item_id[0:4])
        month = int(item_id[4:6])
        day = int(item_id[-2:])
        item_datetime = datetime(year, month, day, tzinfo=timezone.utc)
        item_start_datetime = datetime(year, month, day,
                                    tzinfo=timezone.utc).isoformat().replace(
                                        "+00:00", "Z")
        item_end_datetime = datetime(year,
                                    month,
                                    day,
                                    23,
                                    59,
                                    59,
                                    tzinfo=timezone.utc).isoformat().replace(
                                        "+00:00", "Z")

        item = Item(id=item_id,
                    properties={
                        "start_datetime": item_start_datetime,
                        "end_datetime": item_end_datetime,
                    },
                    geometry=constants.WGS84_GEOMETRY,
                    bbox=constants.WGS84_BBOX,
                    datetime=item_datetime,
                    stac_extensions=[])

    else:
        item_id = f"nclimgrid-{cog_filename[-6:]}"

        year = int(item_id[-6:-2])
        month = int(item_id[-2:])
        item_start_datetime = datetime(year, month, 1,
                                       tzinfo=timezone.utc).isoformat().replace(
                                       "+00:00", "Z")
        item_end_datetime = datetime(year,
                                    month,
                                    monthrange(year, month)[1],
                                    23,
                                    59,
                                    59,
                                    tzinfo=timezone.utc).isoformat().replace(
                                        "+00:00", "Z")

        item = Item(id=item_id,
                    properties={
                        "start_datetime": item_start_datetime,
                        "end_datetime": item_end_datetime,
                    },
                    geometry=constants.WGS84_GEOMETRY,
                    bbox=constants.WGS84_BBOX,
                    datetime=None,
                    stac_extensions=[])

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = constants.EPSG
    projection.shape = constants.SHAPE
    projection.transform = constants.TRANSFORM

    for var in VARIABLES:
        item.assets[f"{var}-cog"] = Asset(href=cog_urls[var],
                                          media_type=MediaType.COG,
                                          roles=["data"],
                                          title=constants.COG_ASSET_TITLE[var])

    return item


def create_items(href: str, base_cog_href: str) -> List[Item]:
    nc_hrefs, daily = get_nc_hrefs(href)

    with TemporaryDirectory() as tmp_dir:
        # get the nc data
        local_nc_paths = {}
        if urlparse(href).scheme:
            local_nc_dir = os.path.join(tmp_dir, "nc")
            os.makedirs(local_nc_dir)
            for nc_href in nc_hrefs:
                download_path = download_nc(nc_href, local_nc_dir)
                var = get_var_name(download_path)
                local_nc_paths[var] = download_path
        else:
            for nc_href in nc_hrefs:
                var = get_var_name(nc_href)
                local_nc_paths[var] = download_path

        # makes life eaiser downstream
        if "ncdd" in local_nc_paths.keys():
            for var in VARIABLES:
                local_nc_paths[var] = local_nc_paths["ncdd"]
            local_nc_paths.pop("ncdd")

        # create COGSs and an Item for each day
        if daily:
            local_cog_dir = os.path.join(tmp_dir, "cog/daily")
            os.makedirs(local_cog_dir)

            items = []
            days = get_days(local_nc_paths)
            for day in days:
                # COGs
                local_cog_paths = get_local_cog_paths(local_nc_paths,
                                                      local_cog_dir,
                                                      day=day)

                for var in VARIABLES:
                    if cog_nc(local_nc_paths[var],
                              local_cog_paths[var],
                              var,
                              day):
                        raise CogCreationError(
                            f"Failed to create '{local_cog_paths[var]}' from "
                            f"'{local_nc_paths[var]}'.")

                    # Item
                    cog_hrefs = upload_cogs(local_cog_paths, base_cog_href)
                    item = create_nclimgrid_item(cog_hrefs, daily)
                    item.validate()
                    items.append(item)

        # or for each month
        else:
            local_cog_dir = os.path.join(tmp_dir, "cog/monthly")
            os.makedirs(local_cog_dir)

            items = []
            indices = get_month_indices(local_nc_paths)
            for idx in indices:
                # COGs
                local_cog_paths = get_local_cog_paths(local_nc_paths,
                                                      local_cog_dir,
                                                      yyyymm=idx["yyyymm"])
                for var in VARIABLES:
                    if cog_nc(local_nc_paths[var],
                              local_cog_paths[var],
                              var,
                              idx["idx"]):
                        raise CogCreationError(
                            f"Failed to create '{local_cog_paths[var]}' from "
                            f"'{local_nc_paths[var]}'.")
                cog_hrefs = upload_cogs(local_cog_paths, base_cog_href)

                # Item
                item = create_nclimgrid_item(cog_hrefs, daily)
                item.validate()
                items.append(item)

    return items


# TODO: Does base_cog_href have to be local?
