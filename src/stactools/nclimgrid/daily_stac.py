import os
import subprocess
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from posixpath import join as urljoin
from charset_normalizer import logging
import fsspec

from pystac import Asset, Item, MediaType
from stactools.core.utils import href_exists

from stactools.nclimgrid.constants import VARIABLES, WGS84_BBOX, WGS84_GEOMETRY, COG_ASSET_TITLE, NC_ASSET_TITLE
from stactools.nclimgrid.errors import CogifyError, FileExistError, HrefExistError
from stactools.nclimgrid.utils import daily_nc_url, daily_cog_filename

BLOCKSIZE = 2**22

logger = logging.getLogger(__name__)

# TODO:
# - change from month dictionary to integer year and month
# - add prelim data check and return items in daily_items()


def create_daily_items(base_nc_href, month, status, cog_dest=None, cog=False):
    """
    - Operates on a single month of daily data
    - The data can be remote or local, but must follow the remote directory
      structure if local
    - Returns a list of items that can be added to a collection
    """
    if urlparse(base_nc_href).scheme:
        with TemporaryDirectory() as temp_dir:
            nc_local_paths, nc_remote_urls = daily_remote_ncs(base_nc_href, temp_dir, month, status, cog)
            items = daily_items(nc_local_paths, nc_remote_urls, month, status, cog_dest, cog)
    else:
        nc_local_paths, nc_remote_urls = daily_local_ncs(base_nc_href, month, status)
        items = daily_items(nc_local_paths, nc_remote_urls, month, status, cog_dest, cog)

    return items


def daily_items(nc_local_paths, nc_remote_urls, month, status, cog_dest, cog):
    items = []

    # if 'prelim', get max valid day and use that to control the loop.


    # an item for each day
    for day in range(1, month['days'] + 1):


        # if 'prelim', we need to check if any data exists for this day; return with current items if no data


        item = daily_base_item(month, day, status)
        # an asset for each variable
        for var in VARIABLES:
            if cog:
                cog_key, cog_asset = daily_cog_asset(nc_local_paths[var], cog_dest, var, month['year'], day)
                item.assets[cog_key] = cog_asset

            nc_key, nc_asset = daily_nc_asset(nc_local_paths[var], nc_remote_urls[var], month['year'], var)
            item.assets[nc_key] = nc_asset

        items.append(item)

    return items


def daily_cog_asset(nc_local_path, cog_dest, var, year, day):
    """Assumes only local path for cog_dest"""
    key = f"{var}-cog"
    title = f"{var} {COG_ASSET_TITLE}"

    cog_filename = daily_cog_filename(nc_local_path, var, year, day)
    cog_path = os.path.join(cog_dest, cog_filename)
    if cog_nc(nc_local_path, cog_path, var, day) != 0:
        raise CogifyError(f"Error creating COG for day {day:02d}, variable {var} in NetCDF file '{nc_local_path}'.")

    asset = Asset(href=cog_path,
                  media_type=MediaType.COG,
                  roles=['data'],
                  title=title)

    return key, asset


def daily_nc_asset(nc_local_path, nc_remote_url, year, var):
    if year < 1970:
        key = "netcdf"
        title = NC_ASSET_TITLE
    else:
        key = f"{var}-netcdf"
        title = f"{var} {NC_ASSET_TITLE}"

    if nc_remote_url is None:
        href = nc_local_path
    else:
        href = nc_remote_url

    asset = Asset(href=href,
                  media_type="application/netcdf",
                  roles=['data'],
                  title=title)

    return key, asset


def daily_base_item(month, day, status):
    # will need to check pre or post 1970 when inserting real metadata
    item_id = f"{month['year']}{month['month']:02d}-grd-{status}-{day:02d}"
    item_time = datetime(month['year'],
                         month['month'],
                         day,
                         tzinfo=timezone.utc)
    item = Item(id=item_id,
                properties={},
                geometry=WGS84_GEOMETRY,
                bbox=WGS84_BBOX,
                datetime=item_time,
                stac_extensions=[])
    return item


def daily_remote_ncs(base_nc_href, temp_dir, month, status, cog):
    """"
    If COGS are to be created, cownload remote NetCDFs and return paths to
    downloaded files. Pre-1970, all variables are in a single file, so all
    'variable' paths will be the same for pre-1970 months.
    """
    def _download(nc_remote_url, nc_local_path):
        with fsspec.open(nc_remote_url) as source:
            with fsspec.open(nc_local_path, "wb") as target:
                data = True
                while data:
                    data = source.read(BLOCKSIZE)
                    target.write(data)

    nc_local_paths = dict()
    nc_remote_urls = dict()
    pre1970_downloaded = False
    for var in VARIABLES:
        nc_url_end = daily_nc_url(month['year'], month['month'], status, var)
        nc_local_paths[var] = os.path.join(temp_dir, nc_url_end)
        nc_remote_urls[var] = urljoin(base_nc_href, nc_url_end)

        # whether creating COGs or not, we need a valid remote href
        if not href_exists(nc_remote_urls[var]):
            raise HrefExistError(f"NetCDF file at '{nc_remote_urls[var]}' does not exist.")

        # only download if creating COGs
        if cog:
            if month['year'] >= 1970 or not pre1970_downloaded:
                _download(nc_remote_urls[var], nc_local_paths[var])
                pre1970_downloaded = True

    return nc_local_paths, nc_remote_urls


def daily_local_ncs(base_nc_href, month, status):
    """
    Generate paths for a local directory structure of NClimGrid NetCDFs.
    Pre-1970, all variables are in a single file, so all 'variable' paths will
    be the same.
    """
    nc_local_paths = dict()
    nc_remote_urls = dict()
    for var in VARIABLES:
        nc_url_end = daily_nc_url(month['year'], month['month'], status, var)
        nc_local_path = os.path.join(base_nc_href, nc_url_end)
        if not os.path.exists(nc_local_path):
            raise FileExistError(f"NetCDF file '{nc_local_path}' does not exist.")
        nc_local_paths[var] = nc_local_path
        nc_remote_urls[var] = None

    return nc_local_paths, nc_remote_urls


def cog_nc(nc_path, cog_path, var, index):
    gdal_path = f"netcdf:{nc_path}:{var}"
    args = [
        "gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b",
        f"{index}"
        ]
    args.append(gdal_path)
    args.append(cog_path)
    result = subprocess.run(args, capture_output=True)
    return result.returncode