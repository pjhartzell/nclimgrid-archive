import logging
import os
from typing import Optional

import click

from stactools.nclimgrid import daily_stac, monthly_stac
from stactools.nclimgrid.constants import Status

logger = logging.getLogger(__name__)


def create_nclimgrid_command(cli):
    """Creates the stactools-nclimgrid command line utility."""

    @cli.group(
        "nclimgrid",
        short_help=("Commands for working with stactools-nclimgrid"),
    )
    def nclimgrid():
        pass

    @nclimgrid.command("create-daily-collection",
                       short_help="Create a daily NClimGrid STAC collection")
    @click.argument("destination", type=str)
    @click.argument("start_yyyymm", type=str)
    @click.argument("end_yyyymm", type=str)
    @click.argument("scaled_or_prelim",
                    type=click.Choice([status.value for status in Status]))
    @click.argument("base_cog_href", type=str)
    @click.option("--base_nc_href",
                  type=str,
                  help="option to create COGS from NetCDFs found at this href")
    def create_daily_collection_command(destination: str,
                                        start_yyyymm: str,
                                        end_yyyymm: str,
                                        scaled_or_prelim: str,
                                        base_cog_href: str,
                                        base_nc_href: Optional[str] = None):
        """Create a STAC collection of daily NClimGrid data with optional COG
        creation from NetCDF data.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        START_YYYYMM (str): Start month in "YYYYMM" format
        END_YYYYMM (str): End month in "YYYYMM" format
        SCALED_OR_PRELIM (str): Choice to use "scaled" or "prelim" data
        BASE_COG_HREF (str): Flat file COG location (COGS are existing or,
                             optionally, created from NetCDF data)
        """
        collection = daily_stac.create_daily_collection(
            start_yyyymm,
            end_yyyymm,
            scaled_or_prelim,
            base_cog_href,
            base_nc_href=base_nc_href)

        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.validate()
        collection.save()

    @nclimgrid.command(
        "create-daily-item",
        short_help="Create a single daily NClimGrid STAC item",
    )
    @click.argument("destination", type=str)
    @click.argument("year", type=int)
    @click.argument("month", type=int)
    @click.argument("day", type=int)
    @click.argument("scaled_or_prelim",
                    type=click.Choice([status.value for status in Status]))
    @click.argument("base_cog_href", type=str)
    @click.option("--base_nc_href",
                  type=str,
                  help="option to create COGS from NetCDFs found at this href")
    def create_daily_item_command(destination: str,
                                  year: int,
                                  month: int,
                                  day: int,
                                  scaled_or_prelim: str,
                                  base_cog_href: str,
                                  base_nc_href: Optional[str] = None):
        """Create a STAC Item for a single day of daily NClimGrid data with
        optional COG creation from NetCDF data.

        \b
        DESTINATION (str): A directory where the STAC Item JSON file will be
                           saved
        YEAR (int): STAC Item year
        MONTH (int): STAC Item month
        DAY (int): STAC Item day
        SCALED_OR_PRELIM (str): Choice to use "scaled" or "prelim" data
        BASE_COG_HREF (str): Flat file COG location (COGS are existing or,
                             optionally, created from NetCDF data)
        """
        item = daily_stac.create_daily_items(year,
                                             month,
                                             scaled_or_prelim,
                                             base_cog_href,
                                             base_nc_href=base_nc_href,
                                             day=day)[0]

        item_path = os.path.join(destination, f"{item.id}.json")
        item.set_self_href(item_path)
        item.validate()
        item.save_object()

    @nclimgrid.command(
        "create-monthly-collection",
        short_help="Create a monthly NClimGrid STAC collection",
    )
    @click.argument("destination", type=str)
    @click.argument("start_yyyymm", type=str)
    @click.argument("end_yyyymm", type=str)
    @click.argument("base_cog_href", type=str)
    @click.option("--base_nc_href",
                  type=str,
                  help="option to create COGS from NetCDFs found at this href")
    def create_monthly_collection_command(destination: str,
                                          start_yyyymm: str,
                                          end_yyyymm: str,
                                          base_cog_href: str,
                                          base_nc_href: Optional[str] = None):
        """Create a STAC Collection of monthly NClimGrid data with optional COG
        creation from NetCDF data.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        START_YYYYMM (str): Start month in "YYYYMM" format
        END_YYYYMM (str): End month in "YYYYMM" format
        BASE_COG_HREF (str): Flat file COG location (COGS are existing or,
                             optionally, created from NetCDF data)
        """
        collection = monthly_stac.create_monthly_collection(
            start_yyyymm, end_yyyymm, base_cog_href, base_nc_href=base_nc_href)
        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.validate()
        collection.save()

    @nclimgrid.command(
        "create-monthly-item",
        short_help="Create a single monthly NClimGrid STAC item",
    )
    @click.argument("destination", type=str)
    @click.argument("yyyymm", type=str)
    @click.argument("base_cog_href", type=str)
    @click.option("--base_nc_href",
                  type=str,
                  help="option to create COGS from NetCDFs found at this href")
    def create_monthly_item_command(destination: str,
                                    yyyymm: str,
                                    base_cog_href: str,
                                    base_nc_href: Optional[str] = None):
        """Create a STAC Item for a single month of monthly NClimGrid data with
        optional COG creation from NetCDF data.

        \b
        DESTINATION (str): A directory where the STAC Item JSON file will be
                           saved
        YYYYMM (str): Year and month of desired STAC Item
        BASE_COG_HREF (str): Flat file COG location (COGS are existing or,
                             optionally, created from NetCDF data)
        """
        item = monthly_stac.create_monthly_items(yyyymm,
                                                 yyyymm,
                                                 base_cog_href,
                                                 base_nc_href=base_nc_href)[0]

        item_path = os.path.join(destination, f"{item.id}.json")
        item.set_self_href(item_path)
        item.validate()
        item.save_object()

    return nclimgrid
