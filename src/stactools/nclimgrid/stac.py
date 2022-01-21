import logging
from datetime import datetime, timezone
import os
from tempfile import TemporaryDirectory
from typing import List, Dict
from urllib.parse import urlparse

from pystac import (Asset, CatalogType, Collection, Extent, Item, MediaType,
                    Provider, ProviderRole, SpatialExtent, TemporalExtent)
from pystac.extensions.projection import ProjectionExtension

from stactools.nclimgrid.constants import VARIABLES, WGS84_BBOX, WGS84_GEOMETRY
from stactools.nclimgrid.utils import generate_url
from stactools.nclimgrid.cog import download_nc, get_cog_path, create_cog

logger = logging.getLogger(__name__)


def create_collection(base_href: str, dest_href: str, type: str, 
                      months: List, cogify:bool) -> Collection:
    """Create a STAC Collection

    This function includes logic to extract all relevant metadata from
    an asset describing the STAC collection and/or metadata coded into an
    accompanying constants.py file.

    See `Collection<https://pystac.readthedocs.io/en/latest/api.html#collection>`_.

    Returns:
        Collection: STAC Collection object
    """
    if type == "monthly":
        print('Not handling monthly yet.')

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

    # Time must be in UTC
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

    items = []
    for month in months:
        items.extend(create_daily_items(month, base_href, dest_href, cogify))

    for item in items:
        collection.add_item(item)

    return collection


def get_monthly_assets(month, base_href, destination, cogify):
    assets = dict()

    # --NetCDF Assets--
    # prior to 1970, all variables are in a single netcdf
    if month["year"] < 1970:
        nc_href = generate_url(base_href, month["year"], month["month"], "")
        for day in range(1, month["days"] + 1):
            for variable in VARIABLES:
                key = f"{day}-{variable}-nc"
                assets[key] = Asset(href=nc_href,
                                    media_type=MediaType.HDF5,
                                    roles=['data'],
                                    title="NetCDF data")

    # 1970 and later, each variable is in its own netcdf
    else:
        for variable in VARIABLES:
            nc_href = generate_url(base_href, month["year"], month["month"], variable)
            for day in range(1, month["days"] + 1):
                key = f"{day}-{variable}-nc"
                assets[key] = Asset(href=nc_href,
                                    media_type=MediaType.HDF5,
                                    roles=['data'],
                                    title="NetCDF data")

    # --COG Assets--
    if cogify:
        # prior to 1970, all variables are in a single netcdf
        if month["year"] < 1970:
            nc_href = generate_url(base_href, month["year"], month["month"], "")

            # if data is remote, download before cogifying
            if urlparse(nc_href).scheme:
                temporary_directory = TemporaryDirectory()
                local_nc_path = os.path.join(temporary_directory.name, os.path.basename(nc_href))
                download_nc(local_nc_path, nc_href)
            else:
                local_nc_path = nc_href

            # cog and create asset
            for day in range(1, month["days"] + 1):
                for variable in VARIABLES:
                    cog_path = get_cog_path(month, day, variable, destination)
                    create_cog(local_nc_path, cog_path, variable, day)
                    key = f"{day}-{variable}-cog"
                    assets[key] = Asset(href=cog_path,
                                        media_type=MediaType.COG,
                                        roles=['data'],
                                        title="COG image")

            # cleanup
            if urlparse(nc_href).scheme:
                temporary_directory.cleanup()

        # 1970 and later, each variable is in its own netcdf
        else:
            for variable in VARIABLES:
                nc_href = generate_url(base_href, month["year"], month["month"], variable)

                # if netcdf is remote, download before cogifying
                if urlparse(nc_href).scheme:
                    temporary_directory = TemporaryDirectory()
                    local_nc_path = os.path.join(temporary_directory.name, os.path.basename(nc_href))
                    download_nc(local_nc_path, nc_href)
                else:
                    local_nc_path = nc_href

                # cog and create asset
                for day in range(1, month["days"] + 1):
                    cog_path = get_cog_path(month, day, variable, destination)
                    create_cog(local_nc_path, cog_path, variable, day)
                    key = f"{day}-{variable}-cog"
                    assets[key] = Asset(href=cog_path,
                                        media_type=MediaType.COG,
                                        roles=['data'],
                                        title="COG image")

                # cleanup
                if urlparse(nc_href).scheme:
                    temporary_directory.cleanup()

    return assets


def create_item():
    pass


def create_daily_items(month: Dict, base_href: str, destination: str, cogify: bool) -> Item:
    """Create NClimGrid STAC Items with assets for 'prcp', 'tmin', 'tmax', and
    'tavg' for a month of days.
    """

    # generate all assets from the netcdf in one go
    assets = get_monthly_assets(month, base_href, destination, cogify)

    # now create an item for each day and add corresponding assets
    items = []
    for day in range(1, month['days'] + 1):
        item_id = f"{month['year']}{month['month']:02d}{day:02d}-grd-scaled"
        item_time = datetime(month['year'], month['month'], day, tzinfo=timezone.utc)

        item = Item(id=item_id,
                    properties={},
                    geometry=WGS84_GEOMETRY,
                    bbox=WGS84_BBOX,
                    datetime=item_time,
                    stac_extensions=[])
        
        # add cog and source netcdf assets for each variable
        for variable in VARIABLES:            
            if cogify:
                item.add_asset(f"{variable}-cog", assets[f"{day}-{variable}-cog"])
            item.add_asset(f"{variable}-nc", assets[f"{day}-{variable}-nc"])

        item.validate()

        items.append(item)

    return items
