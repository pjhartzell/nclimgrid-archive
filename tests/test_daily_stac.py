import glob
import os
import unittest
from tempfile import TemporaryDirectory

from stactools.nclimgrid import constants, daily_stac


class DailyStacTestLocal(unittest.TestCase):

    def test_create_singleitem_pre1970_cogs(self):
        base_nc_href = 'tests/test-data/daily'
        year = 1951
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.SCALED

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            items = daily_stac.create_daily_items(base_nc_href,
                                                  scaled_or_prelim,
                                                  year,
                                                  month,
                                                  day=day,
                                                  cog_dest=cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
        self.assertEqual(len(items[0].assets), 5)

    def test_create_singleitem_pre1970_nocogs(self):
        base_nc_href = 'tests/test-data/daily'
        year = 1951
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.SCALED

        items = daily_stac.create_daily_items(base_nc_href,
                                              scaled_or_prelim,
                                              year,
                                              month,
                                              day=day)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
        self.assertEqual(len(items[0].assets), 1)

    def test_create_singleitem_1970onward_prelim_cogs(self):
        base_nc_href = 'tests/test-data/daily'
        year = 2022
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.PRELIM

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            items = daily_stac.create_daily_items(base_nc_href,
                                                  scaled_or_prelim,
                                                  year,
                                                  month,
                                                  day=day,
                                                  cog_dest=cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        for item in items:
            item.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-prelim-01")
        self.assertEqual(len(items[0].assets), 8)

    def test_create_singleitem_1970onward_nocogs(self):
        base_nc_href = 'tests/test-data/daily'
        year = 2022
        month = 1
        day = 1
        scaled_or_prelim = constants.Status.PRELIM

        items = daily_stac.create_daily_items(base_nc_href,
                                              scaled_or_prelim,
                                              year,
                                              month,
                                              day=day)

        for item in items:
            item.validate()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, f"{year}{month:02d}-grd-prelim-01")
        self.assertEqual(len(items[0].assets), 4)

    def test_create_collection_cogs(self):
        destination = 'test'
        base_nc_href = 'tests/test-data/daily'
        start_month = "202201"
        end_month = "202201"

        with TemporaryDirectory() as temp_dir:
            cog_dest = temp_dir
            collection = daily_stac.create_daily_collection(
                base_nc_href, start_month, end_month, cog_dest)
            num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(num_cogs, 4)
        self.assertEqual(len(list(collection.get_all_items())), 1)
        self.assertEqual(collection.id, "nclimgrid-daily")

    def test_create_collection_nocogs(self):
        destination = 'test'
        base_nc_href = 'tests/test-data/daily'
        start_month = "202201"
        end_month = "202201"

        collection = daily_stac.create_daily_collection(
            base_nc_href, start_month, end_month)

        collection.normalize_hrefs(destination)
        collection.validate()

        self.assertEqual(len(list(collection.get_all_items())), 1)
        self.assertEqual(collection.id, "nclimgrid-daily")


# # More complete tests can be run with remote data, but not used for GitHub CI
# class DailyStacTestRemote(unittest.TestCase):

#     def test_create_items_1970onward_cogs(self):
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         year = 2021
#         month = 12
#         num_days = monthrange(year, month)[1]
#         scaled_or_prelim = constants.Status.SCALED
#         cog = True

#         with TemporaryDirectory() as temp_dir:
#             cog_dest = temp_dir
#             items = daily_stac.create_daily_items(base_nc_href,
#                                                   scaled_or_prelim,
#                                                   year,
#                                                   month,
#                                                   cog=cog,
#                                                   cog_dest=cog_dest)
#             num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

#         for item in items:
#             item.validate()

#         self.assertEqual(num_cogs, num_days * 4)
#         self.assertEqual(len(items), num_days)
#         self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
#         self.assertEqual(len(items[0].assets), 8)

#     def test_create_items_pre1970_cogs(self):
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         year = 1969
#         month = 12
#         num_days = monthrange(year, month)[1]
#         scaled_or_prelim = constants.Status.SCALED
#         cog = True

#         with TemporaryDirectory() as temp_dir:
#             cog_dest = temp_dir
#             items = daily_stac.create_daily_items(base_nc_href,
#                                                   scaled_or_prelim,
#                                                   year,
#                                                   month,
#                                                   cog=cog,
#                                                   cog_dest=cog_dest)
#             num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))

#         for item in items:
#             item.validate()

#         self.assertEqual(num_cogs, num_days * 4)
#         self.assertEqual(len(items), num_days)
#         self.assertEqual(items[0].id, f"{year}{month:02d}-grd-scaled-01")
#         self.assertEqual(len(items[0].assets), 5)

#     def test_create_items_prelim_cogs(self):
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         year = 2022
#         month = 1
#         scaled_or_prelim = constants.Status.PRELIM
#         cog = True

#         with TemporaryDirectory() as temp_dir:
#             cog_dest = temp_dir
#             items = daily_stac.create_daily_items(base_nc_href,
#                                                   scaled_or_prelim,
#                                                   year,
#                                                   month,
#                                                   cog=cog,
#                                                   cog_dest=cog_dest)
#             num_cogs = len(glob.glob(os.path.join(cog_dest, "*.tif")))
#             print(num_cogs)

#         for item in items:
#             item.validate()

#         self.assertEqual(items[0].id, f"{year}{month:02d}-grd-prelim-01")
#         self.assertEqual(len(items[0].assets), 8)

#     def test_create_collection_nocogs(self):
#         destination = "test"
#         base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
#         start_month = "196912"
#         end_month = "197001"
#         cog = False

#         collection = daily_stac.create_daily_collection(
#             base_nc_href, start_month, end_month, cog)

#         collection.normalize_hrefs(destination)
#         collection.validate()

#         self.assertEqual(len(list(collection.get_all_items())), 62)
#         self.assertEqual(collection.id, "nclimgrid-daily")
