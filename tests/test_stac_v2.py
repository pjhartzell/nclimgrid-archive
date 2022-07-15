import os
from tempfile import TemporaryDirectory


from stactools.nclimgrid import stac_v2


def test_create_items_not_latest_only() -> None:
    # This should produce all possible Items (and COGs) from the nc file
    #   -> should not produce Items (or COGs) for empty placeholder data in the nc file
    #   -> should overwrite any existing COGs in cog_dir

    nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
    cog_dir = "tests/data-files/cog/monthly"

    with TemporaryDirectory() as temp_dir:
        cog_dir = os.path.join(temp_dir, "cogs")


def test_create_items_latest_only() -> None:
    # This should only produce Items (and COGs) for the latest data in the nc file
    # for which no COGs were found. This is, more or less, a demo of one way to
    # handle the in-place updates that are applied to the nc files.
    #   -> should not produce Items (or COGs) for empty placeholder data in the nc file
    #   -> will need to work backwards in time, checking for COG existence as
    #      the control on Item and COG creation.
    #   -> should bail once an existing set of COGs is found
    pass


def test_create_single_item() -> None:
    nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
    cog_hrefs = [
        "tests/data-files/cog/monthly/nclimgrid-prcp-189501.tif",
        "tests/data-files/cog/monthly/nclimgrid-tavg-189501.tif",
        "tests/data-files/cog/monthly/nclimgrid-tmax-189501.tif",
        "tests/data-files/cog/monthly/nclimgrid-tmin-189501.tif",
    ]
    item = stac_v2.create_item(nc_href, cog_hrefs)
    assert item.id == "test"
    assert len(item.assets) == 5
    item.validate()


def test_create_cog() -> None:
    nc_href = "tests/data-files/netcdf/monthly/nclimgrid_prcp.nc"
    with TemporaryDirectory() as temp_dir:
        cog_path = os.path.join(temp_dir, "test_cog.tif")
        result = stac_v2.cog_nc(nc_href, cog_path, "prcp", 1)
        assert result == 0






# Maybe we should not worry about the problem of the nc files being updated in
# place. Let the user worry about that. They can use either COG existence and/or
# Item existence control whether a new Item should be created.
#   - This will require a public function to create COGs for a single date and a
#     public function to create a single Item from an nc_href and a list of cog
#     hrefs.
# If it is super simple to add to create Items, we can turn this on with a flag
