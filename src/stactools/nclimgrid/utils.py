from calendar import monthrange
from datetime import datetime


def daily_nc_url(year, month, status, variable):
    if year < 1970:
        url_end = f"beta/by-month/{year}/{month:02d}/ncdd-{year}{month:02d}-grd-{status}.nc"
    else:
        url_end = f"beta/by-month/{year}/{month:02d}/{variable}-{year}{month:02d}-grd-{status}.nc"
    return url_end


def cog_name(var, year, month, day=None, status=None):
    # monthly cog
    if not day:
        name = f"{var}-{year}{month:02d}-cog.tif"
    # daily cog
    else:
        if not status:
            raise ValueError("daily COG status must be 'scaled' or 'prelim'")
        else:
            name = f"{var}-{year}{month:02d}{day:02d}-{status}-cog.tif"

    return name


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
                    "ym": f"{year}{month:02d}"
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
