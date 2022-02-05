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
  - [Item](examples/monthly/...json)
- Daily
  - [Collection](examples/daily/collection.json)
  - [Item](examples/daily/...json)

### Command-line usage

Create a single monthly Item with COG Assets for each NClimGrid variable: 'prcp', 'tavg', 'tmax', 'tmin'. This example references existing COGs found in the `tests/test-data/cog/daily` directory via the `base_cog_href` argument.

```bash
$ stac nclimgrid create-monthly-item examples 189501 tests/test-data/cog/monthly
```

If the COG assets do not exist, we supply an href to a root directory of NetCDF data using the `--base_nc_href`
option. In this case, the `base_cog_href` argument is where the new COGs will be saved.

```bash
$ stac nclimgrid create-monthly-item examples 189501 examples --base_nc_href tests/test-data/netcdf/monthly
```

Use `stac nclimgrid --help` to see all subcommands and options.
