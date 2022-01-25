import os.path
from tempfile import TemporaryDirectory

from stactools.testing import CliTestCase

from stactools.nclimgrid.commands import create_nclimgrid_command
from stactools.nclimgrid.constants import VARIABLES


class CommandsTest(CliTestCase):

    def create_subcommand_functions(self):
        return [create_nclimgrid_command]

    def test_create_daily_cogs_pre1970(self):
        with TemporaryDirectory() as tmp_dir:
            base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
            base_cog_dest = tmp_dir
            start_month = "196902"
            end_month = "196902"
            status = 'scaled'

            result = self.run_command([
                "nclimgrid", "create-cogs", base_nc_href, base_cog_dest,
                start_month, end_month, "--status", status
            ])
            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            cog_names = [p for p in os.listdir(tmp_dir) if p.endswith(".tif")]
            self.assertEqual(len(cog_names), 112)
            expected_cog_names = [
                f"{var}-{start_month}{day:02d}-scaled-cog.tif"
                for var in VARIABLES for day in range(1, 29)
            ]
            self.assertEqual(set(cog_names), set(expected_cog_names))

    def test_create_daily_cogs_1970later(self):
        with TemporaryDirectory() as tmp_dir:
            base_nc_href = "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily"  # noqa
            base_cog_dest = tmp_dir
            start_month = "202102"
            end_month = "202102"
            status = 'scaled'
            result = self.run_command([
                "nclimgrid", "create-cogs", base_nc_href, base_cog_dest,
                start_month, end_month, "--status", status
            ])
            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            cog_names = [p for p in os.listdir(tmp_dir) if p.endswith(".tif")]
            self.assertEqual(len(cog_names), 112)
            expected_cog_names = [
                f"{var}-{start_month}{day:02d}-scaled-cog.tif"
                for var in VARIABLES for day in range(1, 29)
            ]
            self.assertEqual(set(cog_names), set(expected_cog_names))

    def test_create_monthly_cogs(self):
        with TemporaryDirectory() as tmp_dir:
            base_nc_href = "tests/test-data/monthly"
            base_cog_dest = tmp_dir
            start_month = "189501"
            end_month = "189502"

            result = self.run_command([
                "nclimgrid",
                "create-cogs",
                base_nc_href,
                base_cog_dest,
                start_month,
                end_month,
            ])
            self.assertEqual(result.exit_code,
                             0,
                             msg="\n{}".format(result.output))

            cog_names = [p for p in os.listdir(tmp_dir) if p.endswith(".tif")]
            self.assertEqual(len(cog_names), 8)
            expected_cog_names = [
                f"{var}-1895{month:02d}-cog.tif" for var in VARIABLES
                for month in range(1, 3)
            ]
            self.assertEqual(set(cog_names), set(expected_cog_names))
