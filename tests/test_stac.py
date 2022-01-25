import unittest

from stactools.nclimgrid import stac
from stactools.nclimgrid.utils import generate_months


class StacTest(unittest.TestCase):

    def test_create_daily_item_pre1970(self):
        base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"
        base_cog_href = "COGS"
        month = generate_months("196902", "196902")[0]
        item = stac.create_daily_item(base_nc_href, base_cog_href, month, 1)
        self.assertEqual(item.id, "19690201-grd-static")
        self.assertEqual(len(item.assets), 5)
        item.validate()

    def test_create_daily_item_1970later(self):
        base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"
        base_cog_href = "COGS"
        month = generate_months("202102", "202102")[0]
        item = stac.create_daily_item(base_nc_href, base_cog_href, month, 1)
        self.assertEqual(item.id, "20210201-grd-static")
        self.assertEqual(len(item.assets), 8)
        item.validate()

    def test_create_monthly_item(self):
        base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly"  # noqa
        base_cog_href = "COGS"
        month = generate_months("202102", "202102")[0]
        item = stac.create_monthly_item(base_nc_href, base_cog_href, month)
        self.assertEqual(item.id, "202102-nclimgrid")
        self.assertEqual(len(item.assets), 8)
        item.validate()

    def test_create_daily_collection(self):
        base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"
        base_cog_href = "COGS"
        start_month = "202102"
        end_month = "202103"
        collection = stac.create_daily_collection(base_nc_href, base_cog_href,
                                                  start_month, end_month)
        collection.set_self_href("")
        collection.normalize_hrefs("")
        self.assertEqual(collection.id, "my-collection-id")
        self.assertEqual(len(collection.links), 61)
        collection.validate()

    def test_create_monthly_collection(self):
        base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-monthly"  # noqa
        base_cog_href = "COGS"
        start_month = "202102"
        end_month = "202112"
        collection = stac.create_monthly_collection(base_nc_href,
                                                    base_cog_href, start_month,
                                                    end_month)
        collection.set_self_href("")
        collection.normalize_hrefs("")
        self.assertEqual(collection.id, "my-collection-id")
        self.assertEqual(len(collection.links), 13)
        collection.validate()
