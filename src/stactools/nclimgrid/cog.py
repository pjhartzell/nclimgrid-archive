import os
import subprocess
from tempfile import TemporaryDirectory
from typing import Dict
from urllib.parse import urlparse

import fsspec


BLOCKSIZE = 2**22

def my_cogify(nc_href: str,
              destination: str,
              variable: str,
              day: int,
              id: str) -> str:
    """
    hack of pete's cogify
    """

    def _cogify(path):
        gdal_path = f"netcdf:{path}:{variable}"
        cog_path = os.path.join(destination, f"{id}-{variable}-cog.tif")

        args = ["gdal_translate", "-of", "COG", "-co", "compress=deflate", "-b", f"{day}"]
        args.append(gdal_path)
        args.append(cog_path)

        result = subprocess.run(args, capture_output=True)
        print(result)

        return cog_path

    if urlparse(nc_href).scheme:
        with TemporaryDirectory() as temporary_directory:
            local_path = os.path.join(temporary_directory, os.path.basename(nc_href))
            with fsspec.open(nc_href) as source:
                with fsspec.open(local_path, "wb") as target:
                    data = True
                    while data:
                        data = source.read(BLOCKSIZE)
                        target.write(data)
            return _cogify(local_path)
    else:
        return _cogify(nc_href)

