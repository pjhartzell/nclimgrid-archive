VARS = ["prcp", "tavg", "tmax", "tmin"]
ASSET_TITLES = {
    "prcp": "Precipitation (mm)",
    "tavg": "Average Temperature (degree Celsius)",
    "tmax": "Maximmum Temperature (degree Celsius)",
    "tmin": "Minimum Temperature (degree Celsius)"
}

RASTER_BANDS = {
    "prcp": [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "mm",
            "spatial_resolution": 5000
        }
    ],
    "tavg": [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000
        }
    ],
    "tmax": [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000
        }
    ],
    "tmin": [
        {
            "data_type": "float32",
            "nodata": "nan",
            "unit": "degree Celsius",
            "spatial_resolution": 5000
        }
    ],
}
RASTER_EXTENSION_V11 = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
