import logging
from typing import Optional

import click

from stactools.nclimgrid import daily_stac, monthly_stac

logger = logging.getLogger(__name__)


def create_nclimgrid_command(cli):
    """Creates the stactools-nclimgrid command line utility."""

    @cli.group(
        "nclimgrid",
        short_help=("Commands for working with stactools-nclimgrid"),
    )
    def nclimgrid():
        pass

    @nclimgrid.command(
        "create-daily-collection",
        short_help="Create a STAC collection of daily NClimGrid data",
    )
    @click.argument("destination", type=str)
    @click.argument("base_nc_href", type=str)
    @click.argument("start_month", type=str)
    @click.argument("end_month", type=str)
    @click.option("-c",
                  "--cog_dest",
                  type=str,
                  help="option to create COGS at this destination")
    def create_daily_collection_command(destination: str,
                                        base_nc_href: str,
                                        start_month: str,
                                        end_month: str,
                                        cog_dest: Optional[str] = None):
        """Create a STAC Collection of daily NClimGrid data. COG creation is
        optional.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        BASE_NC_HREF (str): Local or https base href for the NetCDF file structure
        START_MONTH (str): Start month in 'YYYYMM' format
        END_MONTH (str): End month in 'YYYYMM' format
        """
        collection = daily_stac.create_daily_collection(base_nc_href,
                                                        start_month,
                                                        end_month,
                                                        cog_dest=cog_dest)

        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.validate()
        collection.save()

    @nclimgrid.command(
        "create-monthly-collection",
        short_help="Create a STAC collection of monthly NClimGrid data",
    )
    @click.argument("destination", type=str)
    @click.argument("base_nc_href", type=str)
    @click.argument("start_month", type=str)
    @click.argument("end_month", type=str)
    @click.option("-c",
                  "--cog_dest",
                  type=str,
                  help="option to create COGS at this destination")
    def create_monthly_collection_command(destination: str,
                                          base_nc_href: str,
                                          start_month: str,
                                          end_month: str,
                                          cog_dest: Optional[str] = None):
        """Create a STAC Collection of monthly NClimGrid data. COG creation is
        optional.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        BASE_NC_HREF (str): Local or https base href for the NetCDF file structure
        START_MONTH (str): Start month in 'YYYYMM' format
        END_MONTH (str): End month in 'YYYYMM' format
        """
        collection = monthly_stac.create_monthly_collection(base_nc_href,
                                                            start_month,
                                                            end_month,
                                                            cog_dest=cog_dest)

        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.validate()
        collection.save()

    return nclimgrid
