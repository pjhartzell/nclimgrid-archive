import os
import subprocess
from tempfile import TemporaryDirectory
from typing import Dict
from urllib.parse import urlparse

import fsspec


BLOCKSIZE = 2**22


def download_nc(local_nc_path, nc_href):
    with fsspec.open(nc_href) as source:
        with fsspec.open(local_nc_path, "wb") as target:
            data = True
            while data:
                data = source.read(BLOCKSIZE)
                target.write(data)


def create_cog(nc_path, cog_path, variable, day):
    gdal_path = f"netcdf:{nc_path}:{variable}"

    args = ["gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b", f"{day}"]
    args.append(gdal_path)
    args.append(cog_path)

    result = subprocess.run(args, capture_output=True)
    print(result)


def get_cog_path(month, day, variable, destination):
    cog_filename = f"{month['year']}{month['month']:02d}{day:02d}-grd-scaled-{variable}-cog.tif"
    cog_path = os.path.join(os.path.dirname(destination), cog_filename)
    return cog_path
