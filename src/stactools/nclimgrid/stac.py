import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

from pystac import (Asset, CatalogType, Collection, Extent, Item, MediaType,
                    Provider, ProviderRole, SpatialExtent, TemporalExtent)

from stactools.nclimgrid.cog import Cogger
from stactools.nclimgrid.constants import VARIABLES, WGS84_BBOX, WGS84_GEOMETRY
from stactools.nclimgrid.utils import cog_name, daily_nc_url, generate_months

logger = logging.getLogger(__name__)


def create_cogs(base_nc_href: str, cog_dest: str, start_month: str,
                end_month: str, prelim: bool) -> List[str]:
    cogger = Cogger(base_nc_href, cog_dest)
    cog_list = cogger.cog(start_month, end_month, prelim)
    return cog_list


def create_daily_collection(base_nc_href: str, base_cog_href: str,
                            start_month: str, end_month: str) -> Collection:
    if 'daily' not in base_nc_href:
        raise ValueError("base_nc_href expected to contain 'daily'")

    providers = [
        Provider(
            name="The OS Community",
            roles=[
                ProviderRole.PRODUCER, ProviderRole.PROCESSOR,
                ProviderRole.HOST
            ],
            url="https://github.com/stac-utils/stactools",
        )
    ]

    demo_time = datetime.now(tz=timezone.utc)
    extent = Extent(
        SpatialExtent([[-180., 90., 180., -90.]]),
        TemporalExtent([demo_time, None]),
    )

    collection = Collection(
        id="my-collection-id",
        title="A dummy STAC Collection",
        description="Used for demonstration purposes",
        license="CC-0",
        providers=providers,
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    months = generate_months(start_month, end_month)
    for month in months:
        for day in range(1, month['days'] + 1):
            item = create_daily_item(base_nc_href, base_cog_href, month, day)
            collection.add_item(item)
    collection.update_extent_from_items()

    return collection


def create_daily_item(base_nc_href: str, base_cog_href: str,
                      month: Dict[str, Any], day: int) -> Item:
    """
    - Assumes no 'prelim" data (hardcodes 'scaled' in nc hrefs)
    - Does not check for asset existence (does that file or blob exist?)
    """
    item_id = f"{month['ym']}{day:02d}-grd-static"
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

    # nc assets
    if month['year'] < 1970:
        # only one nc asset for all variables
        nc_url_end = daily_nc_url(month['year'], month['month'], 'scaled', '')
        if urlparse(base_nc_href).scheme:
            nc_href = f"{base_nc_href.strip('/')}/{nc_url_end}"
        else:
            nc_href = os.path.join(base_nc_href, nc_url_end)

        asset = Asset(href=nc_href,
                      media_type="application/netcdf",
                      roles=['data'],
                      title="NetCDF file")
        item.add_asset("netcdf", asset)
    else:
        # unique nc asset for each variable
        for var in VARIABLES:
            nc_url_end = daily_nc_url(month['year'], month['month'], 'scaled',
                                      var)
            if urlparse(base_nc_href).scheme:
                nc_href = f"{base_nc_href.strip('/')}/{nc_url_end}"
            else:
                nc_href = os.path.join(base_nc_href, nc_url_end)

            asset = Asset(href=nc_href,
                          media_type="application/netcdf",
                          roles=['data'],
                          title=f"{var} NetCDF file")
            item.add_asset(f"{var}-netcdf", asset)

    # always a unique cog asset for each variable
    for var in VARIABLES:
        cog_filename = cog_name(var, month['year'], month['month'], day,
                                'scaled')
        if urlparse(base_cog_href).scheme:
            cog_href = f"{base_cog_href.strip('/')}/{cog_filename}"
        else:
            cog_href = os.path.join(base_cog_href, cog_filename)

        asset = Asset(href=cog_href,
                      media_type=MediaType.COG,
                      roles=['data'],
                      title=f"{var} COG image")
        item.add_asset(f"{var}-cog", asset)

    item.validate()

    return item


def create_monthly_collection(base_nc_href: str, base_cog_href: str,
                              start_month: str, end_month: str) -> Collection:
    if 'monthly' not in base_nc_href:
        raise ValueError("base_nc_href expected to contain 'monthly'")

    providers = [
        Provider(
            name="The OS Community",
            roles=[
                ProviderRole.PRODUCER, ProviderRole.PROCESSOR,
                ProviderRole.HOST
            ],
            url="https://github.com/stac-utils/stactools",
        )
    ]

    demo_time = datetime.now(tz=timezone.utc)
    extent = Extent(
        SpatialExtent([[-180., 90., 180., -90.]]),
        TemporalExtent([demo_time, None]),
    )

    collection = Collection(
        id="my-collection-id",
        title="A dummy STAC Collection",
        description="Used for demonstration purposes",
        license="CC-0",
        providers=providers,
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    months = generate_months(start_month, end_month)
    for month in months:
        item = create_monthly_item(base_nc_href, base_cog_href, month)
        collection.add_item(item)
    collection.update_extent_from_items()

    return collection


def create_monthly_item(base_nc_href: str, base_cog_href: str,
                        month: Dict[str, Any]) -> Item:
    """
    - Does not check for asset existence (does that file or blob exist?)
    """
    item_id = f"{month['ym']}-nclimgrid"
    item_datetime = datetime(month['year'],
                             month['month'],
                             1,
                             tzinfo=timezone.utc)

    item = Item(id=item_id,
                properties={},
                geometry=WGS84_GEOMETRY,
                bbox=WGS84_BBOX,
                datetime=item_datetime,
                stac_extensions=[])

    item.common_metadata.start_datetime = datetime(month['year'],
                                                   month['month'],
                                                   1,
                                                   tzinfo=timezone.utc)
    item.common_metadata.end_datetime = datetime(month['year'],
                                                 month['month'],
                                                 month['days'],
                                                 tzinfo=timezone.utc)

    # unique nc and cog for each variable
    for var in VARIABLES:
        nc_filename = f"nclimgrid_{var}.nc"
        if urlparse(base_nc_href).scheme:
            nc_href = f"{base_nc_href.strip('/')}/{nc_filename}"
        else:
            nc_href = os.path.join(base_nc_href, nc_filename)
        asset = Asset(href=nc_href,
                      media_type="application/netcdf",
                      roles=['data'],
                      title=f"{var} NetCDF file")
        item.add_asset(f"{var}-netcdf", asset)

        cog_filename = cog_name(var, month['year'], month['month'])
        if urlparse(base_cog_href).scheme:
            cog_href = f"{base_cog_href.strip('/')}/{cog_filename}"
        else:
            cog_href = os.path.join(base_cog_href, cog_filename)
        asset = Asset(href=cog_href,
                      media_type=MediaType.COG,
                      roles=['data'],
                      title=f"{var} COG image")
        item.add_asset(f"{var}-cog", asset)

    item.validate()

    return item
