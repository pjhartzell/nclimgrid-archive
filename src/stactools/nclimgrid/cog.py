from typing import List


def cog(infile: str, outdir: str, new_only: True) -> List[str]:
    """
    Args:
        infile (str): Path to NetCDF file
        outdir (str): Directory for COGs

    Returns:
        List[str]: A list of created COG HREFs


    1. generate indices and COG filenames for all dates in the NC file
    2. working backwards in time:
        if new_only:
            if href_exists(idx):
                return 0
        create_cog
        append to cog_hrefs list
    """
    pass



def cog_new():
    """
    1. Pull all dates out of netcdf and build list of all COGS that can be created from the netcdf
    2. Working backwards in time, check if the COG already exists. If not, create the COG
    3. Stop once an existing COG is encountered
    """
    pass


def cog_all():
    """
    1. index all the dates in the netcdf
    2. create a cog for each index and upload, overwriting any existing cogs
    """
    pass
