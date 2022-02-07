import os
from calendar import monthrange
from datetime import datetime, timezone
from posixpath import join as urljoin
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional
from urllib.parse import urlparse

from dateutil import relativedelta
from pystac import Collection, Extent, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from stactools.core.io import ReadHrefModifier
from stactools.core.utils import href_exists

from stactools.nclimgrid import constants
from stactools.nclimgrid.constants import VARIABLES
from stactools.nclimgrid.errors import CogCreationError, ExistError
from stactools.nclimgrid.utils import (cog_nc, create_cog_asset, download_nc,
                                       generate_years_months)


def create_monthly_items(
        start_yyyymm: str,
        end_yyyymm: str,
        base_cog_href: str,
        base_nc_href: Optional[str] = None,
        read_href_modifier: Optional[ReadHrefModifier] = None) -> List[Item]:
    """Creates a list of monthly Items for a given month range, with each Item
    containing a COG Asset for each variable. The COG Assets can be created
    during Item creation if an href to the base of a NetCDF directory structure
    is supplied; if not supplied, COGs must already exist. COG storage
    (existing or new) is flat.

    Args:
        start_yyyymm (str): start month in YYYYMM format
        end_yyyymm (str): end month in YYYYMM format
        base_cog_href (str): COG storage location
        base_nc_href (Optional[str]): optional href to the base of a NetCDF
            directory structure
        read_href_modifier (Optional[ReadHrefModifier]): argument to modify
            remote hrefs

    Returns:
        List[Item]: list of monthly Items
    """
    indices = month_indices(start_yyyymm, end_yyyymm)

    # if cogging and NetCDF data is remote:
    #   -> download NetCDFs and and return their local paths
    #   -> create items, cogging on the fly
    if base_nc_href and urlparse(base_nc_href).scheme:
        with TemporaryDirectory() as temp_dir:
            nc_local_paths = get_remote_ncs(
                base_nc_href, temp_dir, read_href_modifier=read_href_modifier)
            items = monthly_items(indices,
                                  base_cog_href,
                                  nc_local_paths=nc_local_paths)
    # if cogging and NetCDF data is local:
    #   -> return local NetCDF paths
    #   -> create items, cogging on the fly
    elif base_nc_href:
        nc_local_paths = get_local_ncs(base_nc_href)
        items = monthly_items(indices,
                              base_cog_href,
                              nc_local_paths=nc_local_paths)
    # if not cogging:
    #   -> the cogs are assumed to already exist at base_cog_href
    #   -> create items, checking for cog existence for each asset
    else:
        items = monthly_items(indices,
                              base_cog_href,
                              read_href_modifier=read_href_modifier)

    return items


def monthly_items(
        indices: List[List[int]],
        base_cog_href: str,
        nc_local_paths: Optional[Dict[str, str]] = None,
        read_href_modifier: Optional[ReadHrefModifier] = None) -> List[Item]:
    """Creates the list of monthly items using the supplied index list.

    Args:
        indices (List[List[int]): list of each year and month in the time range
            and the number of months + 1 (serves as a 1-based index) since the
            start of the monthly data (January 1895).
        base_cog_href (str): COG storage location
        nc_local_paths (Optional[Dict[str, str]]): optional dictionary of local
            paths to each variable for creating COGs
        read_href_modifier (Optional[ReadHrefModifier]): argument to modify
            remote hrefs

    Returns:
        List[Item]: List of monthly Items
    """
    items = []

    # an item for each month
    for year, month, idx in indices:
        item = monthly_base_item(year, month)
        # a COG asset for each variable
        for var in VARIABLES:
            cog_href = get_cog_href(year, month, var, base_cog_href)

            # create cog if cogging
            if nc_local_paths:
                if cog_nc(nc_local_paths[var], cog_href, var, idx):
                    raise CogCreationError(
                        f"Failed to create '{cog_href}' for year {year}, month "
                        f"{month}, from '{nc_local_paths[var]}'.")

            # check that cog exists
            cog_href_mod = cog_href
            if read_href_modifier:
                cog_href_mod = read_href_modifier(cog_href)
            if not href_exists(cog_href_mod):
                raise ExistError(f"'{cog_href}' does not exist.")

            # add cog asset to item
            cog_key, cog_asset = create_cog_asset(cog_href, var)
            item.assets[cog_key] = cog_asset

        item.validate()
        items.append(item)

    return items


def get_cog_href(year: int, month: int, var: str, base_cog_href: str) -> str:
    """Generates a COG href.

    Args:
        year (int): data year
        month (int): data month
        var (str): weather variable ("prcp", "tavg", "tmax", or "tmin")
        base_cog_href (str): COG storage location

    Returns:
        str: the COG href
    """
    cog_filename = f"nclimgrid-{var}-{year}{month:02d}.tif"
    if urlparse(base_cog_href).scheme:
        cog_href = urljoin(base_cog_href, cog_filename)
    else:
        cog_href = os.path.join(base_cog_href, cog_filename)
    return cog_href


def monthly_base_item(year: int, month: int) -> Item:
    """Creates an Item with all components except Assets.

    Args:
        year (int): data year
        month (int): data month

    Returns:
        Item: STAC Item
    """
    item_id = f"nclimgrid-{year}{month:02d}"
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

    return item


def month_indices(start_yyyymm: str, end_yyyymm: str) -> List[List[int]]:
    """Creates a list of [year, month, index] lists, where the index is a
    1-based index value indicating the number of months since January 1895.

    Args:
        start_yyyymm (str): start month in YYYYMM format
        end_yyyymm (str): end month in YYYYMM format

    Returns:
        List[List[int]]: list of lists of integer year, integer month, and
            integer index, e.g., [[1895, 1, 1], [1895, 2, 2], [1895, 3, 3]].
    """
    indices = []
    years_months = generate_years_months(start_yyyymm, end_yyyymm)
    for year, month in years_months:
        delta = relativedelta.relativedelta(datetime(year, month, 1),
                                            constants.MONTHLY_START)
        delta_months = delta.years * 12 + delta.months
        # cog creation uses 1-based indexing
        indices.append([year, month, delta_months + 1])
    return indices


def get_remote_ncs(
        base_nc_href: str,
        temp_dir: str,
        read_href_modifier: Optional[ReadHrefModifier] = None
) -> Dict[str, str]:
    """Downloads remote NetCDF files.

    Args:
        base_nc_href (str): remote url to the base of a NetCDF directory
            structure
        temp_dir (str): temporary local directory to store downloaded NetCDFs
            for COG creation
        read_href_modifier (Optional[ReadHrefModifier]): argument to modify
            remote hrefs

    Returns:
        Dict[str, str]: dictionary of the downloaded file paths, keyed by
            variable name
    """
    nc_local_paths = dict()
    for var in VARIABLES:
        nc_filename = f"nclimgrid_{var}.nc"
        nc_remote_url = urljoin(base_nc_href, nc_filename)
        if read_href_modifier:
            nc_remote_url = read_href_modifier(nc_remote_url)
        nc_local_paths[var] = os.path.join(temp_dir, nc_filename)
        download_nc(nc_remote_url, nc_local_paths[var])

    return nc_local_paths


def get_local_ncs(base_nc_href: str) -> Dict[str, str]:
    """Generates a dictionary of local NetCDF file paths for each variable

    Args:
        base_nc_href (str): local path to the base of a NetCDF directory
            structure

    Returns:
        Dict[str, str]: dictionary of the local file paths, keyed by variable
            name
    """
    nc_local_paths = dict()
    for var in VARIABLES:
        nc_filename = f"nclimgrid_{var}.nc"
        nc_local_paths[var] = os.path.join(base_nc_href, nc_filename)

    return nc_local_paths


def create_monthly_collection(
        start_yyyymm: str,
        end_yyyymm: str,
        base_cog_href: str,
        base_nc_href: Optional[str] = None,
        read_href_modifier: Optional[ReadHrefModifier] = None) -> Collection:
    """Creates a collection of monthly Items for all months in the range from
    start_yyyymm to end_yyyymm.

    Args:
        start_yyyymm (str): start month in YYYYMM format
        end_yyyymm (str): end month in YYYYMM format
        base_cog_href (str): COG storage location
        base_nc_href (Optional[str]): optional href to the base of a NetCDF
            directory structure
        read_href_modifier (Optional[ReadHrefModifier]): argument to modify
            remote hrefs

    Returns:
        Collection: STAC Collection with Items for each month between the start
            and end months
    """
    items = create_monthly_items(start_yyyymm,
                                 end_yyyymm,
                                 base_cog_href,
                                 base_nc_href=base_nc_href,
                                 read_href_modifier=read_href_modifier)

    extent = Extent.from_items(items)

    collection = Collection(
        id=constants.MONTHLY_COLLECTION_ID,
        title=constants.MONTHLY_COLLECTION_TITLE,
        description=constants.MONTHLY_COLLECTION_DESCRIPTION,
        license=constants.LICENSE,
        extent=extent,
        keywords=constants.MONTHLY_COLLECTION_KEYWORDS,
        providers=constants.PROVIDERS,
    )
    collection.add_items(items)

    item_assets = dict()
    for key, asset in items[0].get_assets().items():
        asset_as_dict = asset.to_dict()
        asset_as_dict.pop("href")
        item_assets[key] = AssetDefinition(asset_as_dict)
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = constants.MONTHLY_DATA_DOI
    scientific.citation = constants.MONTHLY_DATA_CITATION
    scientific.publications = constants.MONTHLY_DATA_PUBLICATIONS

    collection_projection = ProjectionExtension.summaries(collection,
                                                          add_if_missing=True)
    collection_projection.epsg = [constants.EPSG]

    collection.add_link(constants.LICENSE_LINK)

    return collection
