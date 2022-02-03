import glob
import os
import unittest
from tempfile import TemporaryDirectory

from stactools.nclimgrid import constants, daily_stac


class DailyStacTestLocal(unittest.TestCase):

    def test_create_singleitem_pre1970_createcogs(self):
        base_nc_href = 'tests/test-data/netcdf/daily'
        year = 1951
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.SCALED

        with TemporaryDirectory() as temp_dir:
            base_cog_href = temp_dir
            items = daily_stac.create_daily_items(year,
                                                  month,
                                                  scaled_or_prelim,
                                                  base_cog_href,
                                                  base_nc_href=base_nc_href,
                                                  day=day)
            num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_singleitem_pre1970_existingcogs(self):
        base_cog_href = 'tests/test-data/cog/daily'
        year = 1951
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.SCALED

        items = daily_stac.create_daily_items(year,
                                              month,
                                              scaled_or_prelim,
                                              base_cog_href,
                                              day=day)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_singleitem_1970onward_prelim_createcogs(self):
        base_nc_href = 'tests/test-data/netcdf/daily'
        year = 2022
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.PRELIM

        with TemporaryDirectory() as temp_dir:
            base_cog_href = temp_dir
            items = daily_stac.create_daily_items(year,
                                                  month,
                                                  scaled_or_prelim,
                                                  base_cog_href,
                                                  base_nc_href=base_nc_href,
                                                  day=day)
            num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-prelim-01")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_singleitem_1970onward_prelim_existingcogs(self):
        base_cog_href = 'tests/test-data/cog/daily'
        year = 2022
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.PRELIM

        items = daily_stac.create_daily_items(year,
                                              month,
                                              scaled_or_prelim,
                                              base_cog_href,
                                              day=day)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-prelim-01")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_collection_prelim_createcogs(self):
        start_yyyymm = "202201"
        end_yyyymm = "202201"
        scaled_or_prelim = constants.Status.PRELIM
        base_nc_href = 'tests/test-data/netcdf/daily'
        destination = "test_collection"

        with TemporaryDirectory() as temp_dir:
            base_cog_href = temp_dir
            collection = daily_stac.create_daily_collection(
                start_yyyymm,
                end_yyyymm,
                scaled_or_prelim,
                base_cog_href,
                base_nc_href=base_nc_href)
            num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(list(collection.get_all_items())), 1)
        self.assertEqual(collection.id, "nclimgrid-daily")

    def test_create_collection_prelim_existingcogs(self):
        base_cog_href = 'tests/test-data/cog/daily'
        start_yyyymm = "202201"
        end_yyyymm = "202201"
        destination = 'test_collection'
        scaled_or_prelim = constants.Status.PRELIM

        collection = daily_stac.create_daily_collection(
            start_yyyymm, end_yyyymm, scaled_or_prelim, base_cog_href)

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(len(list(collection.get_all_items())), 1)
        self.assertEqual(collection.id, "nclimgrid-daily")


# --Remote Data Tests: Not used for GitHub CI--
# class DailyStacTestRemote(unittest.TestCase):

#     def test_create_items_1970onward_createcogs(self):
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         year = 2021
#         month = 12
#         scaled_or_prelim = constants.Status.SCALED

#         with TemporaryDirectory() as temp_dir:
#             base_cog_href = temp_dir
#             items = daily_stac.create_daily_items(year,
#                                                   month,
#                                                   scaled_or_prelim,
#                                                   base_cog_href,
#                                                   base_nc_href=base_nc_href)
#             num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

#         for item in items:
#             item.validate()

#         num_days = monthrange(year, month)[1]
#         self.assertEqual(num_cogs, num_days * 4)
#         self.assertEqual(len(items), num_days)
#         self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
#         self.assertEqual(len(items[0].assets), 4)

#     def test_create_items_pre1970_createcogs(self):
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         year = 1951
#         month = 1
#         scaled_or_prelim = constants.Status.SCALED

#         with TemporaryDirectory() as temp_dir:
#             base_cog_href = temp_dir
#             items = daily_stac.create_daily_items(year,
#                                                   month,
#                                                   scaled_or_prelim,
#                                                   base_cog_href,
#                                                   base_nc_href=base_nc_href)
#             num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

#         for item in items:
#             item.validate()

#         num_days = monthrange(year, month)[1]
#         self.assertEqual(num_cogs, num_days * 4)
#         self.assertEqual(len(items), num_days)
#         self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
#         self.assertEqual(len(items[0].assets), 4)

#     def test_create_collection_createcogs(self):
#         start_month = "196912"
#         end_month = "197001"
#         scaled_or_prelim = constants.Status.SCALED
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         destination = "test_collection"

#         with TemporaryDirectory() as temp_dir:
#             base_cog_href = temp_dir
#             collection = daily_stac.create_daily_collection(
#                 start_month,
#                 end_month,
#                 scaled_or_prelim,
#                 base_cog_href,
#                 base_nc_href=base_nc_href)
#             num_cogs = len(glob.glob(os.path.join(base_cog_href, "*.tif")))

#         collection.normalize_hrefs(destination)
#         collection.validate()

#         self.assertEqual(num_cogs, 62 * 4)
#         self.assertEqual(len(list(collection.get_all_items())), 62)
#         self.assertEqual(collection.id, "nclimgrid-daily")
