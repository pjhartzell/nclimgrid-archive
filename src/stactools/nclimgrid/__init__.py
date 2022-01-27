import stactools.core

from stactools.nclimgrid.stac import (create_cogs, create_daily_collection,
                                      create_monthly_collection,
                                      create_daily_item, create_monthly_item)
from stactools.nclimgrid.cog import Cogger

__all__ = [
    'create_cogs', 'create_daily_collection', 'create_monthly_collection',
    'create_daily_item', 'create_monthly_item', 'Cogger'
]

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.nclimgrid import commands
    registry.register_subcommand(commands.create_nclimgrid_command)


__version__ = "0.1.0"
