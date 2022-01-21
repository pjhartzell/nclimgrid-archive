from email.policy import default
import logging
from datetime import datetime

import click

from stactools.nclimgrid import stac

from stactools.nclimgrid.utils import generate_months

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
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.argument("source")
    @click.argument('type',
                  type=click.Choice(['monthly', 'daily'], case_sensitive=False),
                  default='daily')
    @click.option("--start", "-s",
                  help="Earliest month for item creation in YYYYMM format",
                  default="195101")
    @click.option("--end", "-e",
                  help="Latest month for item creation in YYYYMM format",
                  default=datetime.today().strftime("%Y%m"))
    @click.option("--cogify", "-c", is_flag=True, help="Create COGs")
    def create_collection_command(destination: str,
                                  source: str,
                                  type: str,
                                  start: str,
                                  end: str,
                                  cogify: bool):
        """Creates a STAC Collection

        \b
        DESTINATION: An HREF for the Collection JSON
        SOURCE: A base HREF for the NetCDF file structure
        TYPE: Either a 'monthly' or 'daily' collection

        """
        months = generate_months(start, end)
 
        collection = stac.create_collection(source, destination, type, months, cogify)

        collection.set_self_href(destination)

        collection.save_object()

        return None

    # @nclimgrid.command("create-item", short_help="Create a STAC item")
    # @click.argument("day_date")
    # @click.argument("base_url")
    # @click.argument("destination")
    # def create_item_command(day_date: str, base_url: str, destination: str):
    #     """Creates a STAC Item

    #     Args:
    #         source (str): HREF of the Asset associated with the Item
    #         destination (str): An HREF for the STAC Collection
    #     """
    #     item = stac.create_item(day_date, base_url, destination)

    #     item.save_object(dest_href=destination)

    #     return None

    return nclimgrid
