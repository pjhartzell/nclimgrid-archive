import os
from calendar import monthrange
from datetime import datetime



def daily_nc_url(year, month, status, variable):
    if year < 1970:
        url_end = f"beta/by-month/{year}/{month:02d}/ncdd-{year}{month:02d}-grd-{status}.nc"
    else:
        url_end = f"beta/by-month/{year}/{month:02d}/{variable}-{year}{month:02d}-grd-{status}.nc"
    return url_end


def monthly_cog_filename(nc_local_path, month):
    nc_filename = os.path.splitext(os.path.basename(nc_local_path))[0]
    cog_filename = f"{nc_filename}_{month:02d}.tif"
    return cog_filename


def daily_cog_filename(nc_local_path, var, year, day):
    nc_filename = os.path.splitext(os.path.basename(nc_local_path))[0]
    if year < 1970:
        cog_filename = f"{nc_filename}-{var}-{day:02d}.tif"
    else:
        cog_filename = f"{nc_filename}-{day:02d}.tif"
    return cog_filename


def generate_months(start: str, end: str):
    try:
        start_date = datetime.strptime(start, "%Y%m")
        start_year = start_date.year
        start_month = start_date.month
    except ValueError:
        raise ValueError("Incorrect start date format, should be YYYYMM")

    try:
        end_date = datetime.strptime(end, "%Y%m")
        end_year = end_date.year
        end_month = end_date.month
    except ValueError:
        raise ValueError("Incorrect end date format, should be YYYYMM")

    if start_date > end_date:
        raise ValueError("End date must be >= start date")

    def month_list(start_year: int, end_year: int, start_month: int,
                   end_month: int):
        month_list = []
        for year in range(start_year, end_year + 1):
            for month in range(start_month, end_month + 1):
                month_list.append({
                    "year": year,
                    "month": month,
                    "days": monthrange(year, month)[1],
                })
        return month_list

    if start_year == end_year:
        months = month_list(start_year, end_year, start_month, end_month)
    elif end_year - start_year == 1:
        months = month_list(start_year, start_year, start_month, 12)
        months.extend(month_list(end_year, end_year, 1, end_month))
    else:
        months = month_list(start_year, start_year, start_month, 12)
        months.extend(month_list(start_year + 1, end_year - 1, 1, 12))
        months.extend(month_list(end_year, end_year, 1, end_month))

    return months
