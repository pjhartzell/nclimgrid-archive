import glob
import os
import unittest
from tempfile import TemporaryDirectory

from stactools.nclimgrid import monthly_stac


class MonthlyStacTestLocal(unittest.TestCase):

    def test_create_items_createcogs(self):
        base_nc_href = 'tests/test-data/netcdf/monthly'
        start_yyyymm = "189501"
        end_yyyymm = "189502"

        with TemporaryDirectory() as temp_dir:
            base_cog_href = temp_dir
            items = monthly_stac.create_monthly_items(
                start_yyyymm,
                end_yyyymm,
                base_cog_href,
                base_nc_href=base_nc_href)
            num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 8)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "nclimgrid-189501")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_items_existingcogs(self):
        base_cog_href = 'tests/test-data/cog/monthly'
        start_yyyymm = "189501"
        end_yyyymm = start_yyyymm

        items = monthly_stac.create_monthly_items(start_yyyymm, end_yyyymm,
                                                  base_cog_href)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "nclimgrid-189501")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_items_existingcogs_with_read_href_modifier(self):
        did_it = False

        def do_it(href: str) -> str:
            nonlocal did_it
            did_it = True
            return href

        base_cog_href = 'tests/test-data/cog/monthly'
        start_yyyymm = "189501"
        end_yyyymm = start_yyyymm

        monthly_stac.create_monthly_items(start_yyyymm,
                                          end_yyyymm,
                                          base_cog_href,
                                          read_href_modifier=do_it)
        assert did_it

    def test_create_collection_createcogs(self):
        base_nc_href = "tests/test-data/netcdf/monthly"
        start_yyyymm = "189501"
        end_yyyymm = "189502"
        destination = "test_collection"

        with TemporaryDirectory() as temp_dir:
            base_cog_href = temp_dir
            collection = monthly_stac.create_monthly_collection(
                start_yyyymm,
                end_yyyymm,
                base_cog_href,
                base_nc_href=base_nc_href)
            num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(num_cogs, 8)
        self.assertEqual(len(list(collection.get_all_items())), 2)
        self.assertEqual(collection.id, "nclimgrid-monthly")

    def test_create_collection_existingcogs(self):
        start_yyyymm = "189501"
        end_yyyymm = "189501"
        destination = "test_collection"

        base_cog_href = "tests/test-data/cog/monthly"
        collection = monthly_stac.create_monthly_collection(
            start_yyyymm, end_yyyymm, base_cog_href)

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(len(list(collection.get_all_items())), 1)
        self.assertEqual(collection.id, "nclimgrid-monthly")
