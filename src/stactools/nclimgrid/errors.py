class CogifyError(Exception):
    """COG creation error."""


class FileExistError(Exception):
    """Local file does not exist."""


class HrefExistError(Exception):
    """Remote href does not exist."""