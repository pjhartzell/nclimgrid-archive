import os
from calendar import monthrange
from datetime import datetime, timezone
from posixpath import join as urljoin
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import xarray
from pystac import (Asset, CatalogType, Collection, Extent, Item, MediaType,
                    SpatialExtent, TemporalExtent)
from stactools.core.utils import href_exists

from stactools.nclimgrid.constants import (COG_ASSET_TITLE,
                                           DAILY_COLLECTION_DESCRIPTION,
                                           DAILY_COLLECTION_TITLE,
                                           NC_ASSET_TITLE, VARIABLES,
                                           WGS84_BBOX, WGS84_GEOMETRY, Status)
from stactools.nclimgrid.errors import (CogifyError, DateNotFound,
                                        FileExistError, HrefExistError,
                                        MaybeAsyncError)
from stactools.nclimgrid.utils import (cog_nc, daily_nc_url, download_nc,
                                       generate_years_months)


def create_daily_items(base_nc_href: str,
                       scaled_or_prelim: Union[str, Status],
                       year: int,
                       month: int,
                       day: Optional[int] = None,
                       cog_dest: Optional[str] = None) -> List[Item]:
    """Creates a list of daily Items for a given year and month, with each Item
    containing NetCDF and, optionally, COG Assets. The source NetCDF data files
    can be local or remote (https), but must follow the NOAA/Microsoft directory
    structure. If a day is passed along with the year and month, a single daily
    Item will be returned. This is not advised for remote data, as the entire
    month of NetCDF data would be downloaded for a single daily Item.

    Args:
        base_nc_href (str): the local or remote path/url to the base of the
            NetCDF data directory structure
        scaled_or_prelim (Union[str, Status]): either a string ('scaled' or
            'prelim') or enumeration specifying whether to use final (scaled) or
            preliminary (prelim) NetCDF data files
        year (int): year of interest (1951 to present)
        month (int): month for which to create daily Items
        day (Optional[int]): option to create a single daily Item for this day
        cog_dest (Optional[str]): if creating COGS, COGS storage location

    Returns:
        items (List[Item]): list of daily Items
    """
    status = Status(scaled_or_prelim)
    # if cog and not cog_dest:
    #     raise BadInput("'cog_dest' required when 'cog=True'")

    if urlparse(base_nc_href).scheme:
        with TemporaryDirectory() as temp_dir:
            nc_local_paths, nc_remote_urls = daily_remote_ncs(
                base_nc_href, temp_dir, year, month, status, cog_dest)
            items = daily_items(nc_local_paths, nc_remote_urls, year, month,
                                day, status, cog_dest)
    else:
        nc_local_paths, nc_remote_urls = daily_local_ncs(
            base_nc_href, year, month, status)
        items = daily_items(nc_local_paths, nc_remote_urls, year, month, day,
                            status, cog_dest)

    return items


def daily_items(nc_local_paths: Dict[str, str],
                nc_remote_urls: Dict[str, str],
                year: int,
                month: int,
                day: Optional[int],
                status: Status,
                cog_dest: Optional[str] = None) -> List[Item]:
    """Creates a list of daily Items for a given year and month, with each Item
    containing NetCDF and, optionally, COG Assets. If an integer day is passed,
    a single daily Item is created.
    """
    items = []

    # if 'prelim', not all days contain data
    if status is Status.PRELIM:
        num_days = num_valid_prelim_days(nc_local_paths)
    else:
        num_days = monthrange(year, month)[1]

    # set start and end days to handle a single day or an entire month
    if day is not None:
        if day > num_days:
            raise DateNotFound(
                f"Data for {year}{month:02d}{day:02d} not found.")
        start_day = day
        end_day = day
    else:
        start_day = 1
        end_day = num_days

    # an item for each day
    for item_day in range(start_day, end_day + 1):
        item = daily_base_item(year, month, item_day, status)
        # NetCDF and COG assets for each variable
        for var in VARIABLES:
            nc_key, nc_asset = daily_nc_asset(nc_local_paths[var],
                                              nc_remote_urls[var], year, var)
            item.assets[nc_key] = nc_asset

            if cog_dest is not None:
                cog_key, cog_asset = daily_cog_asset(nc_local_paths[var],
                                                     cog_dest, var, year,
                                                     item_day)
                item.assets[cog_key] = cog_asset

        item.validate()
        items.append(item)

    return items


def daily_cog_filename(nc_local_path: str, var: str, year: int,
                       day: int) -> str:
    """Create the COG filename."""
    nc_filename = os.path.splitext(os.path.basename(nc_local_path))[0]
    if year < 1970:
        prefix = nc_filename.replace("ncdd", f"{var}")
        cog_filename = f"{prefix}-{day:02d}.tif"
    else:
        cog_filename = f"{nc_filename}-{day:02d}.tif"
    return cog_filename


def daily_cog_asset(nc_local_path: str, cog_dest: str, var: str, year: int,
                    day: int) -> Tuple[str, Asset]:
    """Creates a COG Asset. Assumes cog_dest is local.

    Returns:
        key (str): key for eventual storage of Asset in Item
        asset (Asset): the created STAC Asset
    """
    key = f"{var}-cog"
    title = f"{var} {COG_ASSET_TITLE}"

    cog_filename = daily_cog_filename(nc_local_path, var, year, day)
    cog_path = os.path.join(cog_dest, cog_filename)
    if cog_nc(nc_local_path, cog_path, var, day) != 0:
        raise CogifyError(
            (f"Error creating COG for day {day}, variable '{var}' from NetCDF "
             f"file '{nc_local_path}'."))

    asset = Asset(href=cog_path,
                  media_type=MediaType.COG,
                  roles=['data'],
                  title=title)

    return key, asset


def daily_nc_asset(nc_local_path: str, nc_remote_url: str, year: int,
                   var: str) -> Tuple[str, Asset]:
    """Creates a NetCDF Asset.

    Returns:
        key (str): key for eventual storage of Asset in Item
        asset (Asset): the created STAC Asset
    """
    if year < 1970:
        key = "netcdf"
        title = NC_ASSET_TITLE
    else:
        key = f"{var}-netcdf"
        title = f"{var} {NC_ASSET_TITLE}"

    if not nc_remote_url:
        href = nc_local_path
    else:
        href = nc_remote_url

    asset = Asset(href=href,
                  media_type="application/netcdf",
                  roles=['data'],
                  title=title)

    return key, asset


def daily_base_item(year: int, month: int, day: int, status: Status) -> Item:
    """Creates an Item with all components except Assets."""
    # will need to check pre or post 1970 when inserting full metadata
    item_id = f"{year}{month:02d}-grd-{status.value}-{day:02d}"
    item_time = datetime(year, month, day, tzinfo=timezone.utc)
    item = Item(id=item_id,
                properties={},
                geometry=WGS84_GEOMETRY,
                bbox=WGS84_BBOX,
                datetime=item_time,
                stac_extensions=[])
    return item


def daily_remote_ncs(
        base_nc_href: str,
        temp_dir: str,
        year: int,
        month: int,
        status: Status,
        cog_dest: Optional[str] = None
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """"If COGS are to be created or data is preliminary, download remote
    NetCDFs and return paths to the downloaded files. Preliminary data must
    be accessed to determine the time range of valid data.

    Returns:
        nc_local_paths (Dict[str, str]): dictionary of local paths to downloaded
            NetCDF files, keyed by variable name
        nc_remote_urls (Dict[str, str]): dictionary of remote urls to source
            files, keyed by variable name
    """
    nc_local_paths = dict()
    nc_remote_urls = dict()
    pre1970_downloaded = False
    for var in VARIABLES:
        nc_url_end = daily_nc_url(year, month, status, var)
        nc_local_paths[var] = os.path.join(temp_dir, nc_url_end)
        nc_remote_urls[var] = urljoin(base_nc_href, nc_url_end)

        # whether creating COGs or not, we need a valid remote href
        if not href_exists(nc_remote_urls[var]):
            raise HrefExistError(
                f"NetCDF file at '{nc_remote_urls[var]}' does not exist.")

        # only download if creating COGs or if the data is "prelim"
        if cog_dest is not None or status is Status.PRELIM:
            # 1970 and later, we need to download each variable
            # Pre-1970, we only need to download once
            if year >= 1970 or not pre1970_downloaded:
                download_nc(nc_remote_urls[var], nc_local_paths[var])
                pre1970_downloaded = True

    return nc_local_paths, nc_remote_urls


def daily_local_ncs(base_nc_href: str, year: int, month: int,
                    status: Status) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Generate paths to local NetCDF files. Since the data is local, remote paths
    are assigned a 'None' value.

    Returns:
        nc_local_paths (Dict[str, str]): dictionary of local paths to NetCDF
            files, keyed by variable name
        nc_remote_urls (Dict[str, str]): dictionary of remote urls to source
            files, keyed by variable name.
    """
    nc_local_paths = dict()
    nc_remote_urls = dict()
    for var in VARIABLES:
        nc_url_end = daily_nc_url(year, month, status, var)
        nc_local_path = os.path.join(base_nc_href, nc_url_end)
        if not os.path.exists(nc_local_path):
            raise FileExistError(
                f"NetCDF file '{nc_local_path}' does not exist.")
        nc_local_paths[var] = nc_local_path
        nc_remote_urls[var] = ""

    return (nc_local_paths, nc_remote_urls)


def num_valid_prelim_days(nc_local_paths: Dict[str, str]) -> int:
    """Get number of days in the month are not populated with nodata values
    (-999). This should be the same number for each variable. If not, it is
    possible that the NetCDF files are not from the same NOAA update.

    Returns:
        num_valid_days (int): number of valid days in the preliminaray data
            timestack
    """
    var_valid_days = []
    for var in VARIABLES:
        with xarray.open_dataset(nc_local_paths[var]) as ds:
            var_mean = ds[var].mean(dim=("lat", "lon"), skipna=True).values
            var_valid_days.append((var_mean > -900).sum())

    if len(set(var_valid_days)) != 1:
        raise MaybeAsyncError(
            "Preliminary data variables differ in number of days with valid data."
        )

    num_valid_days = var_valid_days[0]
    return num_valid_days


def create_daily_collection(base_nc_href: str,
                            start_month: str,
                            end_month: str,
                            cog_dest: Optional[str] = None) -> Collection:
    """Create a collection of daily Items for each month in the range from
    start_month to end_month.

    Args:
        start_month (str): start month in YYYYMM format
        end_month (str): end month in YYYYMM format
    """
    temp_time = datetime.now(tz=timezone.utc)
    extent = Extent(
        SpatialExtent([[-180., 90., 180., -90.]]),
        TemporalExtent([temp_time, None]),
    )

    collection = Collection(
        id="nclimgrid-daily",
        title=DAILY_COLLECTION_TITLE,
        description=DAILY_COLLECTION_DESCRIPTION,
        license="CC-0",
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    years_months = generate_years_months(start_month, end_month)

    for year, month in years_months:
        status = get_status(base_nc_href, year, month)
        items = create_daily_items(base_nc_href,
                                   status,
                                   year,
                                   month,
                                   cog_dest=cog_dest)
        collection.add_items(items)

    collection.update_extent_from_items()

    return collection


def get_status(base_nc_href: str, year: int, month: int) -> Status:

    def _uri_exists(status: Status) -> bool:
        # assumes if one variable file exists -> all exist
        nc_url_end = daily_nc_url(year, month, status, 'prcp')
        if urlparse(base_nc_href).scheme:
            uri = urljoin(base_nc_href, nc_url_end)
        else:
            uri = os.path.join(base_nc_href, nc_url_end)
        return href_exists(uri)

    delta = datetime.now() - datetime(year, month, 1)

    if delta.days < 60:
        if _uri_exists(Status.SCALED):
            return Status.SCALED
        elif _uri_exists(Status.PRELIM):
            return Status.PRELIM
        else:
            raise DateNotFound(f"NetCDF file for {year}{month:02d} not found.")
    else:
        return Status.SCALED
