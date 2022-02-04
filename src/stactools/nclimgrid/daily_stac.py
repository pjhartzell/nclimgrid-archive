import itertools as it
import os
from calendar import monthrange
from datetime import datetime, timezone
from posixpath import join as urljoin
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import xarray
from pystac import Collection, Extent, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from stactools.core.utils import href_exists

from stactools.nclimgrid import constants
from stactools.nclimgrid.constants import VARIABLES, Status
from stactools.nclimgrid.errors import ExistError, MaybeAsyncError
from stactools.nclimgrid.utils import (cog_nc, create_cog_asset, download_nc,
                                       generate_years_months)


def create_daily_items(year: int,
                       month: int,
                       scaled_or_prelim: Union[str, Status],
                       base_cog_href: str,
                       base_nc_href: Optional[str] = None,
                       day: Optional[int] = None) -> List[Item]:
    """Creates a list of daily Items for a given year and month, with each Item
    containing a COG Asset for each variable. The COG Assets can be created
    during Item creation if a path/url to the base of a NetCDF directory
    structure is supplied; if not supplied, COGs must already exist. COG storage
    (existing or new) is flat.

    Args:
        year (int): year of interest (1951 to present)
        month (int): month for which to create daily Items
        scaled_or_prelim (Union[str, Status]): either a string ("scaled" or
            "prelim") or enumeration specifying whether to generate final
            or preliminary COG Assets
        base_cog_href (str): COG storage location
        base_nc_href (Optional[str]): optional local path or remote url to the
            base of a NetCDF directory structure
        day (Optional[int]): option to create a single daily Item for this day

    Returns:
        List[Item]: List of daily Items
    """
    status = Status(scaled_or_prelim)

    # if cogging and NetCDF data is remote:
    #   -> download NetCDFs and and return their local paths
    #   -> create items, cogging on the fly
    if base_nc_href is not None and urlparse(base_nc_href).scheme:
        with TemporaryDirectory() as temp_dir:
            nc_local_paths = get_remote_ncs(base_nc_href, temp_dir, year,
                                            month, status)
            items = daily_items(year,
                                month,
                                status,
                                base_cog_href,
                                nc_local_paths=nc_local_paths,
                                day=day)
    # if cogging and NetCDF data is local:
    #   -> return local NetCDF paths
    #   -> create items, cogging on the fly
    elif base_nc_href is not None:
        nc_local_paths = get_local_ncs(base_nc_href, year, month, status)
        items = daily_items(year,
                            month,
                            status,
                            base_cog_href,
                            nc_local_paths=nc_local_paths,
                            day=day)
    # if not cogging:
    #   -> the cogs are assumed to already exist at base_cog_href
    #   -> create items, checking for cog existence for each asset
    else:
        items = daily_items(year, month, status, base_cog_href, day=day)

    return items


# create daily items, cogging as we go, with option to limit to a single day
def daily_items(year: int,
                month: int,
                status: Status,
                base_cog_href: str,
                nc_local_paths: Optional[Dict[str, str]] = None,
                day: Optional[int] = None) -> List[Item]:
    """Creates the list of daily items for the supplied month. If an integer
    day is supplied, the list will contain a single item for that day.


    Args:
        year (int): year of interest (1951 to present)
        month (int): month for which to create daily Items
        status (Status): enumeration specifying whether to generate final or
            preliminary COG Assets
        base_cog_href (str): COG storage location
        nc_local_paths (Optional[Dict[str, str]]): optional dictionary of local
            paths to each variable for creating COGs
        day (Optional[int]): option to create a single daily Item for this day

    Returns:
        List[Item]: List of daily Items
    """
    items = []

    # if "prelim", not all days contain data
    if status is Status.PRELIM:
        if nc_local_paths is not None:
            num_days = num_nc_prelim_days(nc_local_paths)
        else:
            num_days = num_cog_prelim_days(year, month, base_cog_href)
        if num_days == 0:
            raise ExistError(
                f"No 'prelim days found in month {year}{month:02d}.")
    else:
        num_days = monthrange(year, month)[1]

    # set start and end days to handle a single day or an entire month
    if day is not None:
        if day > num_days:
            raise ExistError(
                f"Data for day {day} in month {year}{month:02d} does not exist."
            )
        start_day = day
        end_day = day
    else:
        start_day = 1
        end_day = num_days

    # an item for each day
    for item_day in range(start_day, end_day + 1):
        item = daily_base_item(year, month, item_day, status)
        # a COG asset for each variable
        for var in VARIABLES:
            cog_href = get_cog_href(year, month, item_day, var, status,
                                    base_cog_href)

            # create cog if cogging
            if nc_local_paths is not None:
                cog_nc(nc_local_paths[var], cog_href, var, item_day)

            # check that cog exists
            if not href_exists(cog_href):
                raise ExistError(f"'{cog_href}' does not exist.")

            cog_key, cog_asset = create_cog_asset(cog_href, var)
            item.assets[cog_key] = cog_asset

        item.validate()
        items.append(item)

    return items


def get_cog_href(year: int, month: int, day: int, var: str, status: Status,
                 base_cog_href: str) -> str:
    """Generates a COG filename and path/url.

    Args:
        year (int): data year
        month (int): data month
        day (int): data data
        var (str): weather variable ("prcp", "tavg", "tmax", or "tmin")
        status (Status): enumeration specifying whether final or preliminary
            data
        base_cog_href (str): COG storage location

    Returns:
        str: the COG path/url
    """
    cog_filename = f"{var}-{year}{month:02d}-grd-{status.value}-{day:02d}.tif"
    if urlparse(base_cog_href).scheme:
        cog_href = urljoin(base_cog_href, cog_filename)
    else:
        cog_href = os.path.join(base_cog_href, cog_filename)
    return cog_href


def daily_base_item(year: int, month: int, day: int, status: Status) -> Item:
    """Creates an Item with all components except Assets.

    Args:
        year (int): data year
        month (int): data month
        day (int): data data
        status (Status): enumeration specifying whether final or preliminary
            data

    Returns:
        Item: STAC Item
    """
    # will need to check pre or post 1970 when inserting full metadata
    item_id = f"{year}{month:02d}-grd-{status.value}-{day:02d}"
    item_start_time = datetime(year, month, day, tzinfo=timezone.utc)
    item_end_time = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)

    item = Item(
        id=item_id,
        properties={},
        geometry=constants.WGS84_GEOMETRY,
        bbox=constants.WGS84_BBOX,
        datetime=item_start_time,  # start of day is nominal
        stac_extensions=[])

    item.common_metadata.start_datetime = item_start_time
    item.common_metadata.end_datetime = item_end_time

    # Projection extension
    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = constants.EPSG
    projection.shape = constants.SHAPE
    projection.transform = constants.TRANSFORM

    return item


def num_nc_prelim_days(nc_local_paths: Dict[str, str]) -> int:
    """Get number of days in the month in the NetCDF file that are not populated
    with nodata values (-999). This should be the same number for each variable;
    if not, it is possible the NetCDF files are not from the same NOAA update.

    Args:
        nc_local_paths (Dict[str, str]): local path to each variable's NetCDF
            file

    Returns:
        int: number of valid days in the preliminary data timestack
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


def num_cog_prelim_days(year: int, month: int, base_cog_href: str) -> int:
    """Checks for existence of preliminary COGS for each variable for each day
    of the month. Stops when a COG file is not found or all days have been
    checked. If the number of COGS for each variable is not equal, it is
    possible that the COGS were generated from NetCDF files originating from
    different updates.

    Args:
        year (int): data year
        month (int): data month
        base_cog_href (str): COG storage location

    Returns:
        int: number of days where a COG exists for each variable.
    """
    num_month_days = monthrange(year, month)[1]
    num_var_days = {var: 0 for var in VARIABLES}
    for day, var in it.product(range(1, num_month_days + 1), VARIABLES):
        cog_href = get_cog_href(year, month, day, var, Status.PRELIM,
                                base_cog_href)
        if not href_exists(cog_href):
            num_month_days = day - 1
            break
        num_var_days[var] += 1

    if len(set(num_var_days.values())) != 1:
        raise MaybeAsyncError(
            "Preliminary data variables differ in number of days with valid data."
        )

    return num_month_days


def get_remote_ncs(base_nc_href: str, temp_dir: str, year: int, month: int,
                   status: Status) -> Dict[str, str]:
    """Downloads an online NetCDF files for each variable.

    Args:
        base_nc_href (str): remote url to the base of a NetCDF directory
            structure
        temp_dir (str): temporary local directory to store downloaded NetCDFs
            for COG creation
        year (int): data year
        month (int): data month
        status (Status): enumeration specifying whether final or preliminary
            data

    Returns:
        Dict[str, str]: dictionary of the downloaded file paths, keyed by
            variable name
    """
    nc_local_paths = dict()
    pre1970_downloaded = False
    for var in VARIABLES:
        nc_url_end = daily_nc_url(year, month, status, var)
        nc_remote_url = urljoin(base_nc_href, nc_url_end)
        nc_local_paths[var] = os.path.join(temp_dir, nc_url_end)
        # 1970 and later, we need to download each variable
        # Pre-1970, we only need to download once
        if year >= 1970 or not pre1970_downloaded:
            download_nc(nc_remote_url, nc_local_paths[var])
            pre1970_downloaded = True

    return nc_local_paths


def get_local_ncs(base_nc_href: str, year: int, month: int,
                  status: Status) -> Dict[str, str]:
    """Generates a dictionary of local NetCDF file paths for each variable

    Args:
        base_nc_href (str): local path to the base of a NetCDF directory
            structure
        year (int): data year
        month (int): data month
        status (Status): enumeration specifying whether final or preliminary
            data

    Returns:
        Dict[str, str]: dictionary of the local file paths, keyed by variable
            name
    """
    nc_local_paths = dict()
    for var in VARIABLES:
        nc_url_end = daily_nc_url(year, month, status, var)
        nc_local_paths[var] = os.path.join(base_nc_href, nc_url_end)

    return nc_local_paths


def daily_nc_url(year: int, month: int, status: Status, variable: str) -> str:
    """Use the directory structure used in NOAA's (and Microsoft's) online data
    storage to generate the path to a NetCDF file.

    Args:
        year (int): data year
        month (int): data month
        status (Status): enumeration specifying whether final or preliminary
            data
        variable (str): weather variable ("prcp", "tavg", "tmax", or "tmin")

    Returns:
        str: path to NetCDF file
    """
    if year < 1970:
        url_end = (f"beta/by-month/{year}/{month:02d}/ncdd-{year}{month:02d}"
                   f"-grd-{status.value}.nc")
    else:
        url_end = (f"beta/by-month/{year}/{month:02d}/{variable}-{year}"
                   f"{month:02d}-grd-{status.value}.nc")
    return url_end


def create_daily_collection(start_yyyymm: str,
                            end_yyyymm: str,
                            scaled_or_prelim: Union[str, Status],
                            base_cog_href: str,
                            base_nc_href: Optional[str] = None) -> Collection:
    """Create a collection of daily Items for each month in the range from
    start_month to end_month.

    Args:
        start_yyyymm (str): start month in YYYYMM format
        end_yyyymm (str): end month in YYYYMM format
        scaled_or_prelim (Union[str, Status]): either a string ("scaled" or
            "prelim") or enumeration specifying whether to generate final
            or preliminary COG Assets
        base_cog_href (str): COG storage location
        base_nc_href (Optional[str]): optional local path or remote url to the
            base of a NetCDF directory structure

    Returns:
        Collection: STAC Collection with Items for each day between the start
            and end months
    """
    years_months = generate_years_months(start_yyyymm, end_yyyymm)
    status = Status(scaled_or_prelim)

    items = []
    for year, month in years_months:
        items.extend(
            create_daily_items(year,
                               month,
                               status,
                               base_cog_href,
                               base_nc_href=base_nc_href))

    extent = Extent.from_items(items)

    collection = Collection(
        id=constants.DAILY_COLLECTION_ID,
        title=constants.DAILY_COLLECTION_TITLE,
        description=constants.DAILY_COLLECTION_DESCRIPTION,
        license=constants.LICENSE,
        extent=extent,
        keywords=constants.DAILY_COLLECTION_KEYWORDS,
        providers=constants.PROVIDERS,
    )
    collection.add_items(items)

    # ItemAssets extension
    item_assets = dict()
    for key, asset in items[0].get_assets().items():
        asset_as_dict = asset.to_dict()
        asset_as_dict.pop("href")
        item_assets[key] = AssetDefinition(asset_as_dict)
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    # summary - projection
    collection_projection = ProjectionExtension.summaries(collection,
                                                          add_if_missing=True)
    collection_projection.epsg = [constants.EPSG]

    collection.add_link(constants.LICENSE_LINK)

    return collection
