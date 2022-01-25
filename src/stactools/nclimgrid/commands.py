import logging

import click

from stactools.nclimgrid import stac

logger = logging.getLogger(__name__)


def create_nclimgrid_command(cli):
    """Creates the stactools-nclimgrid command line utility."""

    @cli.group(
        "nclimgrid",
        short_help=("Commands for working with stactools-nclimgrid"),
    )
    def nclimgrid():
        pass

    @nclimgrid.command("create-cogs",
                       short_help="Create COGs from NetCDF data")
    @click.argument("base_nc_href")
    @click.argument("cog_dest")
    @click.argument("start_month")
    @click.argument("end_month")
    @click.option("--status",
                  default="scaled",
                  help="create COGS from 'scaled' or 'prelim' NetCDF data")
    def create_cogs_command(base_nc_href: str, cog_dest: str, start_month: str,
                            end_month: str, status: str):
        """
        Creates COGs for each day or month of daily or monthly NClimGrid
        NetCDF data.

        \b
        BASE_NC_HREF (str): Local or https base href for the NetCDF file structure
        COG_DEST (str): Local, existing path to where COGs will be flat stored
        START_MONTH (str): Earliest month for COG creation in 'YYYYMM' format
        END_MONTH (str): Latest month for COG creation in 'YYYYMM' format.
        """
        stac.create_cogs(base_nc_href, cog_dest, start_month, end_month,
                         status)

    @nclimgrid.command(
        "create-daily-collection",
        short_help="Create a STAC collection of daily NClimGrid data",
    )
    @click.argument("destination")
    @click.argument("base_nc_href")
    @click.argument("base_cog_href")
    @click.argument("start_month")
    @click.argument("end_month")
    def create_daily_collection_command(destination: str, base_nc_href: str,
                                        base_cog_href: str, start_month: str,
                                        end_month: str):
        """Create a STAC Collection of daily NClimGrid data from *existing*
        NetCDF and COG files.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        BASE_NC_HREF (str): Local or https base href for the NetCDF file structure
        BASE_COG_HREF (str): Local or https base href for a flat directory of COGS
                             created with the 'create-cogs' command
        START_MONTH (str): Start month in 'YYYYMM' format
        END_MONTH (str): End month in 'YYYYMM' format
        """
        collection = stac.create_daily_collection(base_nc_href, base_cog_href,
                                                  start_month, end_month)

        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.save()

        collection.validate()

    @nclimgrid.command(
        "create-monthly-collection",
        short_help="Create a STAC collection of monthly NClimGrid data",
    )
    @click.argument("destination")
    @click.argument("base_nc_href")
    @click.argument("base_cog_href")
    @click.argument("start_month")
    @click.argument("end_month")
    def create_monthly_collection_command(destination: str, base_nc_href: str,
                                          base_cog_href: str, start_month: str,
                                          end_month: str):
        """Create a STAC Collection of monthly NClimGrid data from *existing*
        NetCDF and COG files.

        \b
        DESTINATION (str): An HREF for the Collection JSON
        BASE_NC_HREF (str): Local or https base href for the NetCDF file structure
        BASE_COG_HREF (str): Local or https base href for a flat directory of COGS
                             created with the 'create-cogs' command
        START_MONTH (str): Start month in 'YYYYMM' format
        END_MONTH (str): End month in 'YYYYMM' format
        """
        collection = stac.create_monthly_collection(base_nc_href,
                                                    base_cog_href, start_month,
                                                    end_month)

        collection.set_self_href(destination)
        collection.normalize_hrefs(destination)
        collection.save()

        collection.validate()

    return nclimgrid
