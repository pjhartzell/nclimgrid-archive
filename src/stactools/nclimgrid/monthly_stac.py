import os
from datetime import datetime, timezone
from posixpath import join as urljoin
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import xarray
from pystac import (Asset, CatalogType, Collection, Extent, Item, MediaType,
                    SpatialExtent, TemporalExtent)

from stactools.nclimgrid.constants import (COG_ASSET_TITLE,
                                           MONTHLY_COLLECTION_DESCRIPTION,
                                           MONTHLY_COLLECTION_TITLE,
                                           NC_ASSET_TITLE, VARIABLES,
                                           WGS84_BBOX, WGS84_GEOMETRY)
from stactools.nclimgrid.errors import (BadInput, CogifyError, DateNotFound,
                                        FileExistError, MaybeAsyncError)
from stactools.nclimgrid.utils import (cog_nc, download_nc,
                                       generate_years_months)


def create_monthly_items(base_nc_href: str,
                         year: Optional[int] = None,
                         month: Optional[int] = None,
                         cog_dest: Optional[str] = None) -> List[Item]:
    """Creates a list of month Items from monthly NClimGrid NetCDF data, with
    each Item containing NetCDF and, optionally, COG Assets. The source NetCDF
    data files can be local or remote (https), but must follow the
    NOAA/Microsoft directory structure. If a year and month is passed, a single
    Item will be returned. This is not advised for remote data, as the entire
    NetCDF file containing all months since 1895 data would be downloaded for a
    single month Item.

    Args:
        base_nc_href (str): the local or remote path/url to the base of the
            NetCDF data directory structure
        year (Optional[int]): optional year of interest (1895-01 to present)
        month (Optional[int]): optional month of interest
        cog_dest (Optional[str]): if creating COGS, COG storage location

    Returns:
        items (List[Item]): list of monthly Items
    """
    if type(year) != type(month):
        raise BadInput(
            "Integer year and month input must be both omitted or both included."
        )

    if urlparse(base_nc_href).scheme:
        with TemporaryDirectory() as temp_dir:
            nc_local_paths, nc_remote_urls = monthly_remote_ncs(
                base_nc_href, temp_dir)
            items = monthly_items(nc_local_paths, nc_remote_urls, year, month,
                                  cog_dest)
    else:
        nc_local_paths, nc_remote_urls = monthly_local_ncs(base_nc_href)
        items = monthly_items(nc_local_paths, nc_remote_urls, year, month,
                              cog_dest)

    return items


def monthly_items(nc_local_paths: Dict[str, str],
                  nc_remote_urls: Dict[str, str],
                  year: Optional[int],
                  month: Optional[int],
                  cog_dest: Optional[str] = None) -> List[Item]:
    """Creates a list of monthly Items for all months in the NetCDF files, with
    each Item containing NetCDF and, optionally, COG Assets. If a year and month
    are passed, a single monthly Item is created.
    """
    items = []

    # get dates and indices into the NetCDF DataArrays
    indices = month_indices(nc_local_paths, year, month)

    # an item for each month
    for index in indices:
        item = monthly_base_item(index['year'], index['month'])
        # an asset for each variable
        for var in VARIABLES:
            nc_key, nc_asset = monthly_nc_asset(nc_local_paths[var],
                                                nc_remote_urls[var], var)
            item.assets[nc_key] = nc_asset

            if cog_dest is not None:
                cog_key, cog_asset = monthly_cog_asset(nc_local_paths[var],
                                                       cog_dest, var,
                                                       index['year'],
                                                       index['month'],
                                                       index['index'])
                item.assets[cog_key] = cog_asset

        item.validate()
        items.append(item)

    return items


def monthly_cog_filename(nc_local_path: str, year: int, month: int) -> str:
    """Create the COG filename"""
    nc_filename = os.path.splitext(os.path.basename(nc_local_path))[0]
    cog_filename = f"{nc_filename}_{year}{month:02d}.tif"
    return cog_filename


def monthly_cog_asset(nc_local_path: str, cog_dest: str, var: str, year: int,
                      month: int, index: int) -> Tuple[str, Asset]:
    """Creates a COG Asset. Assumes cog_dest is local.

    Returns:
        key (str): key for eventual storage of Asset in Item
        asset (Asset): the created STAC Asset
    """
    key = f"{var}-cog"
    title = f"{var} {COG_ASSET_TITLE}"

    cog_filename = monthly_cog_filename(nc_local_path, year, month)
    cog_path = os.path.join(cog_dest, cog_filename)
    if cog_nc(nc_local_path, cog_path, var, index) != 0:
        raise CogifyError(
            (f"Error creating COG for year {year}, month {month}, variable "
             f"{var} in NetCDF file '{nc_local_path}'."))

    asset = Asset(href=cog_path,
                  media_type=MediaType.COG,
                  roles=['data'],
                  title=title)

    return key, asset


def monthly_nc_asset(nc_local_path: str, nc_remote_url: str,
                     var: str) -> Tuple[str, Asset]:
    """Creates a NetCDF Asset.

    Returns:
        key (str): key for eventual storage of Asset in Item
        asset (Asset): the created STAC Asset
    """
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


def monthly_base_item(year: int, month: int) -> Item:
    """Creates an Item with all components except Assets."""
    item_id = f"nclimgrid_{year}{month:02d}"
    item_time = datetime(year, month, 1, tzinfo=timezone.utc)
    item = Item(id=item_id,
                properties={},
                geometry=WGS84_GEOMETRY,
                bbox=WGS84_BBOX,
                datetime=item_time,
                stac_extensions=[])
    return item


def month_indices(nc_local_paths: Dict[str, str], year: Optional[int],
                  month: Optional[int]) -> List[Dict[str, int]]:
    """Generates a list of dictionaries with 1-based index information to each
    year/month location in the NetCDF variable timestacks. Also checks that each
    NetCDF variable file contains the same number of timesteps (months).

    Returns:
        index_list (List[Dict[str, int]]): list of dictionaries with the index
            into the NetCDF timestacks for each year/month date.
    """
    num_months = []
    for var in VARIABLES:
        with xarray.open_dataset(nc_local_paths[var]) as ds:
            years = ds.time.dt.year.data.tolist()
            months = ds.time.dt.month.data.tolist()
            years_months = [[y, m] for y, m in zip(years, months)]
            num_months.append(len(years_months))

    if len(set(num_months)) != 1:
        raise MaybeAsyncError(
            "NetCDF variable files differ in number of timesteps (months).")

    # single month
    if year is not None and month is not None:
        if [year, month] in years_months:
            index = years_months.index([year, month]) + 1
            index_list = [{'year': year, 'month': month, 'index': index}]
        else:
            raise DateNotFound("Requested year and month not found.")
    # all years, all months
    else:
        indices = range(1, len(years_months) + 1)
        index_list = [{
            'year': y,
            'month': m,
            'index': i
        } for y, m, i in zip(years, months, indices)]

    return index_list


def monthly_remote_ncs(base_nc_href: str,
                       temp_dir: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """"Downloads remote NetCDFs and returns paths to downloaded files. The
    remote NetCDFs are always downloaded, even if COGs will not be created, to
    check that variables contain the same number of dates to determine the
    number of months within the NetCDFs timestacks.

    Returns:
        nc_local_paths (Dict[str, str]): dictionary of local paths to downloaded
            NetCDF files, keyed by variable name
        nc_remote_urls (Dict[str, str]): dictionary of remote urls to source
            files, keyed by variable name
    """
    nc_local_paths = dict()
    nc_remote_urls = dict()
    for var in VARIABLES:
        nc_filename = f"nclimgrid_{var}.nc"
        nc_local_paths[var] = os.path.join(temp_dir, nc_filename)
        nc_remote_urls[var] = urljoin(base_nc_href, nc_filename)

        download_nc(nc_remote_urls[var], nc_local_paths[var])

    return nc_local_paths, nc_remote_urls


def monthly_local_ncs(
        base_nc_href: str) -> Tuple[Dict[str, str], Dict[str, str]]:
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
        nc_filename = f"nclimgrid_{var}.nc"
        nc_local_path = os.path.join(base_nc_href, nc_filename)
        if not os.path.exists(nc_local_path):
            raise FileExistError(
                f"NetCDF file '{nc_local_path}' does not exist.")
        nc_local_paths[var] = nc_local_path
        nc_remote_urls[var] = ""

    return nc_local_paths, nc_remote_urls


def create_monthly_collection(
    base_nc_href: str,
    start_month: str,
    end_month: str,
    cog_dest: Optional[str] = None,
) -> Collection:
    """Create a collection of monthly Items for all months in the range from
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
        id="nclimgrid_monthly",
        title=MONTHLY_COLLECTION_TITLE,
        description=MONTHLY_COLLECTION_DESCRIPTION,
        license="CC-0",
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    years_months = generate_years_months(start_month, end_month)

    for year, month in years_months:
        items = create_monthly_items(base_nc_href,
                                     year=year,
                                     month=month,
                                     cog_dest=cog_dest)
        collection.add_items(items)

    collection.update_extent_from_items()

    return collection
