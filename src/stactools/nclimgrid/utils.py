import os


def generate_url(base_url, year, month, variable):
    # check for file existence?
    if year < 1960:
        url = os.path.join(
            f"{base_url}", 
            f"beta/by-month/{year}/{month:02d}/ncdd-{year}{month:02d}-grd-scaled.nc"
        )
    else:
        url = os.path.join(
            f"{base_url}", 
            f"beta/by-month/{year}/{month:02d}/{variable}-{year}{month:02d}-grd-scaled.nc"
        )
    return url
