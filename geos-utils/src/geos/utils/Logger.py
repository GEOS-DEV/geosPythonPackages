# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
import logging
from typing import Union
from typing_extensions import Self

__doc__ = """
Logger module manages logging tools.

Code was modified from <https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output>
"""

# types redefinition to import logging.* from this module
Logger = logging.Logger  #: logger type

# Define logging levels at the module level so they are available for the Formatter class
DEBUG: int = logging.DEBUG
INFO: int = logging.INFO
WARNING: int = logging.WARNING
ERROR: int = logging.ERROR
CRITICAL: int = logging.CRITICAL


class CustomLoggerFormatter( logging.Formatter ):
    """Custom formatter for the logger.

    .. WARNING:: Colors do not work in the ouput message window of Paraview.

    To use it:

    .. code-block:: python

        logger = logging.getLogger( "Logger name", use_color=False )
        # Ensure handler is added only once, e.g., by checking logger.handlers
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setFormatter(CustomLoggerFormatter())
            logger.addHandler(ch)
    """
    # define color codes
    grey: str = "\x1b[38;20m"
    yellow: str = "\x1b[33;20m"
    red: str = "\x1b[31;20m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"

    # define prefix of log messages
    format1: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    format2: str = ( "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)" )

    #: format for each logger output type with colors
    FORMATS_COLOR: dict[ int, str ] = {
        DEBUG: grey + format2 + reset,
        INFO: grey + format1 + reset,
        WARNING: yellow + format1 + reset,
        ERROR: red + format1 + reset,
        CRITICAL: bold_red + format2 + reset,
    }

    #: format for each logger output type without colors (e.g., for Paraview)
    FORMATS_PLAIN: dict[ int, str ] = {
        DEBUG: format2,
        INFO: format1,
        WARNING: format1,
        ERROR: format1,
        CRITICAL: format2,
    }

    # Pre-compiled formatters for efficiency
    _compiled_formatters: dict[ int, logging.Formatter ] = {
        level: logging.Formatter( fmt )
        for level, fmt in FORMATS_PLAIN.items()
    }

    _compiled_color_formatters: dict[ int, logging.Formatter ] = {
        level: logging.Formatter( fmt )
        for level, fmt in FORMATS_COLOR.items()
    }

    def __init__( self: Self, use_color: bool = False ) -> None:
        """Initialize the log formatter.

        Args:
            use_color (bool): If True, use color-coded log formatters.
                            Defaults to False.
        """
        if use_color:
            self.active_formatters = self._compiled_color_formatters
        else:
            self.active_formatters = self._compiled_formatters

    def format( self: Self, record: logging.LogRecord ) -> str:
        """Return the format according to input record.

        Args:
            record (logging.LogRecord): record

        Returns:
            str: format as a string
        """
        # Defaulting to plain formatters as per original logic
        log_fmt_obj: Union[ logging.Formatter, None ] = self.active_formatters.get( record.levelno )
        if log_fmt_obj:
            return log_fmt_obj.format( record )
        else:
            # Fallback for unknown levels or if a level is missing in the map
            return logging.Formatter().format( record )


def getLogger( title: str, use_color: bool = False ) -> Logger:
    """Return the Logger with pre-defined configuration.

    This function is now idempotent regarding handler addition.
    Calling it multiple times with the same title will return the same
    logger instance without adding more handlers if one is already present.

    Example:

    .. code-block:: python

        # module import
        import Logger

        # logger instanciation
        logger :Logger.Logger = Logger.getLogger("My application")

        # logger use
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

    Args:
        title (str): Name of the logger.
        use_color (bool): If True, configure the logger to output with color.
                          Defaults to False.

    Returns:
        Logger: logger
    """
    logger: Logger = logging.getLogger( title )
    # Only configure the logger (add handlers, set level) if it hasn't been configured before.
    if not logger.hasHandlers():  # More Pythonic way to check if logger.handlers is empty
        logger.setLevel( INFO )  # Set the desired default level for this logger
        # Create and add the stream handler
        ch = logging.StreamHandler()
        ch.setFormatter( CustomLoggerFormatter( use_color ) )  # Use your custom formatter
        logger.addHandler( ch )
        # Optional: Prevent messages from propagating to the root logger's handlers
        logger.propagate = False
    # If you need to ensure a certain level is set every time getLogger is called,
    # even if handlers were already present, you can set the level outside the 'if' block.
    # However, typically, setLevel is part of the initial handler configuration.
    # logger.setLevel(INFO) # Uncomment if you need to enforce level on every call
    return logger
