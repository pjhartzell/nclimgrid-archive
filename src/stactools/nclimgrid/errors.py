class ExistError(Exception):
    """File or data does not exist."""


class MaybeAsyncError(Exception):
    """NetCDF variable data does not match in timespanspan. May originate from
    different NOAA updates."""


class BadInput(Exception):
    """Incorrect input."""


class CogCreationError(Exception):
    """COG creation failed."""
