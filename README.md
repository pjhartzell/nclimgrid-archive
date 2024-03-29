# stactools-nclimgrid

- Name: nclimgrid
- Package: `stactools.nclimgrid`
- Owner: @pjhartzell
- Dataset homepage: http://github.com/stactools-packages/nclimgrid
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
  - [item-assets](https://github.com/stac-extensions/item-assets)
  - [scientific](https://github.com/stac-extensions/scientific)
- Extra fields: None

Create STAC Items and Collections for NOAA NCEI gridded surface climate data.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stactools-packages/nclimgrid/main?filepath=docs/installation_and_basic_usage.ipynb)

## Examples

### STAC objects

- Monthly
  - [Collection](examples/monthly/collection.json)
  - [Item](examples/monthly/nclimgrid-189501/nclimgrid-189501.json)
- Daily
  - [Collection](examples/daily/collection.json)
  - [Item](examples/daily/202201-grd-prelim-01/202201-grd-prelim-01.json)

### Command-line usage

Create a single monthly Item with COG Assets for each NClimGrid variable: 'prcp', 'tavg', 'tmax', 'tmin'. This example references existing COGs found in the `tests/test-data/cog/monthly` directory.

```bash
$ stac nclimgrid create-monthly-item examples 189501 tests/test-data/cog/monthly
```

If the COG assets do not exist, we supply an href to a root directory of NetCDF data using the `--base_nc_href`
option.

```bash
$ stac nclimgrid create-monthly-item examples 189501 examples --base_nc_href tests/test-data/netcdf/monthly
```

Use `stac nclimgrid --help` to see all subcommands and options.


### Creating the examples directory

To re-create the `examples` directory, run the following:

```shell
$ stac nclimgrid create-monthly-collection examples/monthly 189501 189501 tests/test-data/cog/monthly
$ stac nclimgrid create-daily-collection examples/daily 202201 202201 prelim tests/test-data/cog/daily
```
