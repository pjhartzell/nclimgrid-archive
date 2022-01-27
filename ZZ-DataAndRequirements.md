## Data
### Daily:
- 4 variables: prcp, tavg, tmax, tmin
- Daily data is grouped into monthly NetCDF files:
    - Pre-1970: all variables in single NetCDF
        - "ncdd-{YYYYMM}-grd-scaled.nc"
    - 1970-onward: Separate NetCDF for each variable
        - "prcp-{YYYYMM}-grd-scaled.nc"
        - "tavg-{YYYYMM}-grd-scaled.nc"
        - "tmin-{YYYYMM}-grd-scaled.nc"
        - "tmax-{YYYYMM}-grd-scaled.nc"
    - Current month:
        - "prcp-{YYYYMM}-grd-prelim.nc"
        - "tavg-{YYYYMM}-grd-prelim.nc"
        - "tmax-{YYYYMM}-grd-prelim.nc"
        - "tmin-{YYYYMM}-grd-prelim.nc"
- NetCDF file level metadata (not variable/dimension/coordinate metadata)
    - Pre-1970: Identical between all months, with the exception of creation date
    - 1970-onward: Identical between all months, with the exception of creation date
        - This includes the current month "prelim" files

### Monthly:
- 4 variables: prcp, tavg, tmax, tmin
- Monthly data contained in separate NetCDF files for each variable
    - "nclimgrid_prcp.nc"
    - "nclimgrid_tavg.nc"
    - "nclimgrid_tmax.nc"
    - "nclimgrid_tmin.nc"
- NetCDF file level metadata (not variable/dimension/coordinate metadata)
    - Identical between the 4 NetCDF files


## Data Updates
### Daily:
- Current month
    - The current "prelim" NetCDF is updated in place with a ~3 day lag
    - Missing/Future data is given a -999 value
    - Once the month is finished, NOAA replaces the "prelim" NetCDF file with a "scaled" NetCDF file
        - MS Azure retains the "prelim" files (messy, IMO)

- Past Months
    - The most recent 3 months of "scaled" NetCDF files are updated every month
    - Bulk updates exist:
        - From 197001 to 202003, all NetCDF files were updated on 6/14/2020
        - from 195101 to 196912, all NetCDF files were updated on 1/1/2021

### Monthly:
- Each NetCDF is updated in place when a new month is available
- Each NetCDF is updated in place on an annual basis:
    - "On an annual basis, approximately one year of "final" nClimGrid will be submitted to replace the initially supplied "preliminary" data for the same time period."
    - https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00332



## STACtools Subpackage Requirements:
### Daily:
1. Given a range of months, create a Collection of daily Items
    - Option to create COGS

2. Given a month, create an Item for each day
    - Option to create COGS
    - Each Item will have 1 or 4 NetCDF Asset(s) and 4 COG Assets

Notes:
- Handle either 1 or 4 NetCDF files
- Handle local or remote NetCDF data
- If COG option is False
    - Do not create COG Assets
    - Do not download NetCDF files if a remote href is passed
    - Check that NetCDF file(s) (local or remote) exist for the NetCDF assets


### Monthly:
1. Create a collection of monthly Items
    - Option to create COGS
2. Create an Item for each month
    - Option to create COGS
    - Each Item will have 4 NetCDF Assets and 4 COG Assets


