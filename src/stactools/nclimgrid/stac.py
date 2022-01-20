import logging
from datetime import datetime, timezone
import os

from pystac import (Asset, CatalogType, Collection, Extent, Item, MediaType,
                    Provider, ProviderRole, SpatialExtent, TemporalExtent)
from pystac.extensions.projection import ProjectionExtension

from stactools.nclimgrid.constants import VARIABLES, WGS84_BBOX, WGS84_GEOMETRY
from stactools.nclimgrid.utils import generate_url
from stactools.nclimgrid.cog import my_cogify

logger = logging.getLogger(__name__)


def create_collection() -> Collection:
    """Create a STAC Collection

    This function includes logic to extract all relevant metadata from
    an asset describing the STAC collection and/or metadata coded into an
    accompanying constants.py file.

    See `Collection<https://pystac.readthedocs.io/en/latest/api.html#collection>`_.

    Returns:
        Collection: STAC Collection object
    """
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

    return collection


def create_item(day_date: str, base_url: str, destination: str) -> Item:
    """Create a NClimGrid STAC Item with assets for 'prcp', 'tmin', 'tmax', and
    'tavg'.

    Args:
        day_date (str): Date in YYYYMMDD format

        base_href (str): The HREF pointing to the base NetCDF data directory
        structure.
        Daily NClimGrid base href examples:
        1. Microsoft Azure blob storage:
            https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily/
        2. NOAA storage:
            https://www1.ncdc.noaa.gov/pub/data/daily-grids/
        Monthly NClimGird base href examples:
        1. Microsoft Azure blob storage:
            https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly/
        2. NOAA storage:
            https://www.ncei.noaa.gov/data/nclimgrid-monthly/access/

        destination (str): file path for item json

    Returns:
        Item: STAC Item object
    """

    # split day_date into integer year, month, and day values
    if len(day_date) != 8:
        raise ValueError("day_date must be formatted as YYYYMMDD.")
    else:
        year = int(day_date[0:4])
        month = int(day_date[4:6])
        day = int(day_date[6:])

    # item time
    day_time = datetime(year, month, day, tzinfo=timezone.utc)

    # item id
    id = f"{day_date}-grd-scaled"

    item = Item(
        id=id,
        properties={},
        geometry=WGS84_GEOMETRY,
        bbox=WGS84_BBOX,
        datetime=day_time,
        stac_extensions=[],
    )

    # add assets
    for v in VARIABLES:
        url = generate_url(base_url, year, month, v)

        # Add source NetCDF file as asset
        item.add_asset(
            f"{v}_nc",
            Asset(href=url,
                  media_type=MediaType.HDF5,
                  roles=['data'],
                  title="NetCDF data variable"))

        # create COG for day and variable
        cog_path = my_cogify(url, os.path.dirname(destination), v, day, id)

        # Add new COG as asset
        item.add_asset(
            f"{v}_cog",
            Asset(
                href=cog_path,
                media_type=MediaType.COG,
                roles=["data"],
                title="COG",
            ),
        )

    return item
