import os
from calendar import monthrange
from datetime import datetime


def generate_url(base_url, year, month, variable):
    # check for file existence?
    if year < 1970:
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


def month_list(start_year, end_year, start_month, end_month):
    month_list = [{"year": year, "month": month, "days": monthrange(year, month)[1]}
                  for year in range(start_year, end_year + 1)
                  for month in range(start_month, end_month + 1)]
    return month_list


def generate_months(start, end):
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


