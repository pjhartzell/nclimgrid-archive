from pystac.catalog import CatalogType

# from stactools.nclimgrid.stac import (create_cogs, create_daily_collection,
#                                       create_monthly_collection)
from stactools.nclimgrid.utils import generate_months
from stactools.nclimgrid.daily_stac import create_daily_items


# base_nc_href = "/Users/pjh/data/nclimgrid-dev/daily"
base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"

# start_month = "202112"
# end_month = "202112"
start_month = "195101"
end_month = "195101"

cog_dest = "cogs-daily"
cog = False

months = generate_months(start_month, end_month)
items = create_daily_items(base_nc_href, months[0], 'scaled', cog_dest, cog)
import pprint
pprint.pprint(items)
import json
print(json.dumps(items[5].to_dict(), indent=2))


# --Daily Collection--
# base_nc_href = "/Users/pjh/data/nclimgrid-dev/daily"
# base_cog_href = "COGS"
# start_month = "202112"
# end_month = "202112"

# daily_collection = create_daily_collection(base_nc_href, base_cog_href, start_month, end_month)
# daily_collection.update_extent_from_items()

# # Normalize hrefs
# stac_path = "STAC-Daily"
# daily_collection.normalize_hrefs(stac_path)

# # Save the collection
# daily_collection.save(catalog_type=CatalogType.SELF_CONTAINED)
# print(f'STAC written to {stac_path}')



# --Monthly Collection--
# base_nc_href = "/Users/pjh/data/nclimgrid-dev/monthly"
# base_cog_href = "COGS"
# start_month = "202009"
# end_month = "202011"

# monthly_collection = create_monthly_collection(base_nc_href, base_cog_href, start_month, end_month)

# # Normalize hrefs
# stac_path = "STAC-Monthly"
# monthly_collection.normalize_hrefs(stac_path)

# # Save the collection
# monthly_collection.save(catalog_type=CatalogType.SELF_CONTAINED)
# print(f'STAC written to {stac_path}')



# --COGS--
# from stactools.nclimgrid.stac import create_cogs

# # nc_source = "/Users/pjh/data/nclimgrid-dev/monthly"
# # nc_source = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly"
# nc_source = "/Users/pjh/data/nclimgrid-dev/daily"
# # nc_source = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"
# cog_dest = "COGS"
# start_month = "202112"
# end_month = "202112"
# status = "scaled"

# cogs = create_cogs(nc_source, cog_dest, start_month, end_month, status)



# # --Monthly COGS--
# from stactools.nclimgrid.stac import create_cogs

# nc_base_href = "/Users/pjh/data/nclimgrid-dev/monthly"
# cog_dest = "co"
# cogs = create_cogs(nc_base_href, cog_dest, start_month, end_month, status)


# stac nclimgrid create-monthly-collection "STAC-Monthly" "/Users/pjh/data/nclimgrid-dev/monthly" "COGS" 202009 202011
