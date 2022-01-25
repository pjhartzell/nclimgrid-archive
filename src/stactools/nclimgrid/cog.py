import logging
import os
import subprocess
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import fsspec
import xarray

from stactools.nclimgrid.constants import VARIABLES
from stactools.nclimgrid.utils import cog_name, daily_nc_url, generate_months

BLOCKSIZE = 2**22

logger = logging.getLogger(__name__)


class Cogger:

    def __init__(self, nc_source: str, cog_dest: str):
        if 'monthly' in nc_source:
            self.type = 'monthly'
        elif 'daily' in nc_source:
            self.type = 'daily'
        else:
            raise ValueError(
                "base_href expected to contain 'daily' or 'monthly'")

        self.remote = False
        if urlparse(nc_source).scheme:
            self.remote = True

        self.nc_source = nc_source
        self.cog_dest = cog_dest

    def cog(self,
            start_month: str,
            end_month: str,
            status: Optional[str] = 'scaled') -> List[str]:

        self.start_month = start_month
        self.end_month = end_month
        self.cog_months = generate_months(self.start_month, self.end_month)

        if status != 'scaled' and status != 'prelim':
            raise ValueError("status must be 'scaled' or 'prelim'")
        self.status = status

        if self.type == 'monthly':
            cog_list = self._cog_monthly()
        else:
            cog_list = self._cog_daily()

        return cog_list

    def _cog_monthly(self) -> List[str]:
        cog_list = []
        for var in VARIABLES:
            # download if nc file is not local
            nc_filename = f"nclimgrid_{var}.nc"
            if self.remote:
                temp_dir, nc_local_path = self._download_nc(nc_filename)
            else:
                nc_local_path = os.path.join(self.nc_source, nc_filename)

            # list of months in the nc file
            nc_months = self._get_nc_months(nc_local_path)

            # create COG for each month
            for cog_month in self.cog_months:
                if cog_month['ym'] in nc_months:
                    index = nc_months.index(cog_month['ym']) + 1
                else:
                    logger.warning(
                        f"{cog_month['ym']} not found in {nc_local_path}")
                    continue

                cog_filename = cog_name(var, cog_month['year'],
                                        cog_month['month'])
                cog_path = os.path.join(self.cog_dest, cog_filename)

                if self._cog_nc(nc_local_path, cog_path, var, index) == 0:
                    cog_list.append(cog_path)

            if self.remote:
                temp_dir.cleanup()

        return cog_list

    def _cog_daily(self) -> List[str]:
        cog_list = []
        for month in self.cog_months:
            # pre-1970, all variables are in a single monthly file
            if month['year'] < 1970:
                nc_url_end = daily_nc_url(month['year'], month['month'],
                                          self.status, "")
                if self.remote:
                    temp_dir, nc_local_path = self._download_nc(nc_url_end)
                else:
                    nc_local_path = os.path.join(self.nc_source, nc_url_end)

                for var in VARIABLES:
                    for day in range(1, month['days'] + 1):
                        cog_filename = cog_name(var, month['year'],
                                                month['month'], day,
                                                self.status)
                        cog_path = os.path.join(self.cog_dest, cog_filename)
                        if self._cog_nc(nc_local_path, cog_path, var,
                                        day) == 0:
                            cog_list.append(cog_path)

                if self.remote:
                    temp_dir.cleanup()

            # 1970 and later, each variable is in its own monthly file
            else:
                for var in VARIABLES:
                    nc_url_end = daily_nc_url(month['year'], month['month'],
                                              self.status, var)
                    if self.remote:
                        temp_dir, nc_local_path = self._download_nc(nc_url_end)
                    else:
                        nc_local_path = os.path.join(self.nc_source,
                                                     nc_url_end)

                    for day in range(1, month['days'] + 1):
                        cog_filename = cog_name(var, month['year'],
                                                month['month'], day,
                                                self.status)
                        cog_path = os.path.join(self.cog_dest, cog_filename)
                        if self._cog_nc(nc_local_path, cog_path, var,
                                        day) == 0:
                            cog_list.append(cog_path)

                    if self.remote:
                        temp_dir.cleanup()

        return cog_list

    def _get_nc_months(self, nc_local_path: str) -> List[str]:
        with xarray.open_dataset(nc_local_path) as ds:
            years = ds.time.dt.year.data.tolist()
            months = ds.time.dt.month.data.tolist()

        nc_months = [
            f"{year}{month:02d}" for year, month in zip(years, months)
        ]

        return nc_months

    def _cog_nc(self, nc_path_in: str, cog_path_out: str, var: str,
                index: int) -> int:
        gdal_path = f"netcdf:{nc_path_in}:{var}"

        args = [
            "gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b",
            f"{index}"
        ]
        args.append(gdal_path)
        args.append(cog_path_out)

        result = subprocess.run(args, capture_output=True)

        if result.returncode != 0:
            logger.warning(f"{gdal_path} conversion to COG unsuccessful")

        return result.returncode

    def _download_nc(self, nc_filename: str) -> Tuple[TemporaryDirectory, str]:
        temp_dir = TemporaryDirectory()
        nc_remote_url = f"{self.nc_source.strip('/')}/{nc_filename}"
        nc_local_path = os.path.join(temp_dir.name, nc_filename)

        with fsspec.open(nc_remote_url) as source:
            with fsspec.open(nc_local_path, "wb") as target:
                data = True
                while data:
                    data = source.read(BLOCKSIZE)
                    target.write(data)

        return (temp_dir, nc_local_path)
