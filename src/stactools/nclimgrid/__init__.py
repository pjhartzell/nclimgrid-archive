import stactools.core

from stactools.nclimgrid.daily_stac import (create_daily_collection,
                                            create_daily_items)
from stactools.nclimgrid.monthly_stac import (create_monthly_collection,
                                              create_monthly_items)

__all__ = [
    'create_daily_items', 'create_daily_collection', 'create_monthly_items',
    'create_monthly_collection'
]

stactools.core.use_fsspec()


def register_plugin(registry):
    from stactools.nclimgrid import commands
    registry.register_subcommand(commands.create_nclimgrid_command)


__version__ = "0.1.0"
