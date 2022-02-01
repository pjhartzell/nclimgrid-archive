import glob
import os
import unittest
from tempfile import TemporaryDirectory

from stactools.nclimgrid import monthly_stac


class MonthlyStacTestLocal(unittest.TestCase):

    def test_create_items_nocogs(self):
        base_nc_href = 'tests/test-data/monthly'

        items = monthly_stac.create_monthly_items(base_nc_href)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "nclimgrid_189501")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_items_cogs(self):
        base_nc_href = 'tests/test-data/monthly'

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            items = monthly_stac.create_monthly_items(base_nc_href,
                                                      cog_dest=cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 8)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "nclimgrid_189501")
        self.assertEqual(len(items[0].assets), 8)

    def test_create_singleitem_nocog(self):
        base_nc_href = 'tests/test-data/monthly'
        year = 1895
        month = 2

        items = monthly_stac.create_monthly_items(base_nc_href,
                                                  year=year,
                                                  month=month)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "nclimgrid_189502")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_singleitem_cog(self):
        base_nc_href = 'tests/test-data/monthly'
        year = 1895
        month = 2

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            items = monthly_stac.create_monthly_items(base_nc_href,
                                                      year=year,
                                                      month=month,
                                                      cog_dest=cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "nclimgrid_189502")
        self.assertEqual(len(items[0].assets), 8)

    def test_create_collection_nocogs(self):
        base_nc_href = 'tests/test-data/monthly'
        start_month = '189501'
        end_month = '189502'
        destination = 'test'

        collection = monthly_stac.create_monthly_collection(
            base_nc_href, start_month, end_month)

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(len(list(collection.get_all_items())), 2)
        self.assertEqual(collection.id, "nclimgrid_monthly")

    def test_create_collection_cogs(self):
        destination = 'test'
        start_month = '189501'
        end_month = '189502'
        base_nc_href = 'tests/test-data/monthly'

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            collection = monthly_stac.create_monthly_collection(
                base_nc_href, start_month, end_month, cog_dest=cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(num_cogs, 8)
        self.assertEqual(len(list(collection.get_all_items())), 2)
        self.assertEqual(collection.id, "nclimgrid_monthly")
