class CogifyError(Exception):
    """COG creation error."""


class FileExistError(Exception):
    """Local file does not exist."""


class HrefExistError(Exception):
    """Remote href does not exist."""


class MaybeAsyncError(Exception):
    """NetCDF variable data does not match in timespanspan. May originate from
    different NOAA updates."""


class BadInput(Exception):
    """Incorrect input."""


class DateNotFound(Exception):
    """Requested date not found in data."""
