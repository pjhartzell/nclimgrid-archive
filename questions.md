# README Stuff

## Collections
There are two collections: one for the monthly data and one for the daily data.

## Items
### Monthly Items
Each item is single month with 8 assets:
1. prcp cog
2. prcp source nc
3. tmin cog
4. tmin source nc
5. tmax cog
6. tmax source nc
7. tavg cog
8. tavg source nc

### Daily Items
Each item is a single day. Pre-1970 data will have five assets per item:
1. prcp cog
2. tmin cog
3. tmax cog
4. tavg cog
5. source nc

1970 and later data will have 8 assets per item:
1. prcp cog
2. prcp source nc
3. tmin cog
4. tmin source nc
5. tmax cog
6. tmax source nc
7. tavg cog
8. tavg source nc

### Approach to COGS and Items
- Since each daily NetCDF file contains data for multiple items, batching COG and item creation by month is necessary to avoid downloading the same NetCDF files repeatedly. Similar is true for monthly NetCDF data.
- It felt cleaner to me to COG all the data first. Item creation is then just a matter of creating links to existing NetCDF and COG files, with no batching required.
    - The potential weakness in this approach is that if items require information (metadata, perhaps) from their source NetCDF files, you are out of luck.
    - However, the NClimGrid NetCDF metadata is (almost) identical within their type (monthly, pre-1970 daily, 1970-onward daily).
    - The only metadata item that is different is the NetCDF creation date. I'm not certain it needs to be included in the items. Note that the NetCDF creation date **_is_** included in the COG metadata.

## Questions
1. Will we be indexing the current month of daily data, where the NetCDF file is marked as 'prelim'?. The prelim data is pre-populated with nodata values (-999) that are replaced with preliminary values as time moves forward. Once the month is done, the prelim file is superseded by a NetCDF file marked as "scaled" within a week or so after the month ends.
2. The COG band names are not great. Do we format them?
    - Example: `Band 1: time=80353 (days since 1800-01-01 00:00:00)`
3. Do we check for asset existence (local file or remote blob) during item asset creation?
4. Do we point at where the COGS will eventually live? Or is that updated later?

## Notes
1. The daily COG tests take several minutes because they pull remote data. Files with sizes in the tens of MB seem too large for the `tests/test-data` directory.
2. The Cogger class only handles a local flat file destination
3. If you COG a 'prelim' daily NetCDF, it creates blank COGS for days not yet populated with actual data
4. The Cogger class is not robust to missing files or directories
    - it fails when the NetCDF file (local or remote) is not found
    - it fails when local cog directory does not exist
5. Handling of 'prelim' data is not fully functional.
     - You can COG 'prelim' or 'scaled' NetCDF files
     - But item creation hard-codes 'scaled' into the filename
     - Will clean this up if necessary (may not be necessary for historical ingest)

## Have To-Do List
1. Get real metadata, properties, etc into the collections and items.
2. Document code

## Potential To-Do List
- Add Pete's logging errors back into cog creation
- Handle COGs located on blob storage when creating assets for items
- Web url vs local paths is not robust:
    - urls use /
    - local paths will use / or \, depending on os
        - os.path.normpath?
        - IIRC, Windows is OK with paths with mixed slashes
