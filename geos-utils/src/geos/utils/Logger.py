# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville, Jacques Franc
import logging
from typing import Any, Generator
from typing_extensions import Self

import os
import re
import tempfile
from contextlib import contextmanager

from vtkmodules.vtkCommonCore import vtkLogger
from geos.utils.Errors import VTKError

__doc__ = """
Logger module manages logging tools.

Code was modified from <https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output>

It also include adaptor strategy to make vtkLogger behave as a logging's logger.
Indeed, C++ adapted class is based on private Callback assignement which is not compatible
with logging python's logic.

Usage::

    # near logger definition
    from vtkmodules.vtkCommonCore import vtkLogger

    vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_TRACE)
    logger.addFilter(RegexExceptionFilter())

    ...

    # near VTK calls
    with VTKCaptureLog() as captured_log:
        vtkcalls..
        captured_log.seek(0)  # be kind let's just rewind
        captured = captured_log.read().decode()

    logger.error(captured.strip())

"""


class RegexExceptionFilter( logging.Filter ):
    """Class to regexp VTK messages rethrown into logger by VTKCaptureLog.

    This transforms silent VTK errors into catchable Python exceptions.
    """

    pattern: str = r'\bERR\|'  # Pattern captured that will raise a vtkError

    def __init__( self ) -> None:
        """Init filter with class based pattern as this is patch to logging logic."""
        super().__init__()
        self.regex = re.compile( self.pattern )

    def filter( self, record: logging.LogRecord ) -> bool:
        """Filter VTK Error from stdErr.

        Args:
            record(loggging.LogRecord) : record that logger will provide as evaluated

        Raises:
            VTKError(geos.utils.Error) if a pattern symbol is caught in the stderr.
        """
        message = record.getMessage()  # Intercepts every log record before it's emitted
        if self.regex.search( message ):
            raise VTKError( f"Log message matched forbidden pattern: {message}" )
        return True  # Allow other messages to pass


@contextmanager
def VTKCaptureLog() -> Generator[ Any, Any, Any ]:
    """Hard way of adapting C-like vtkLogger to logging class by throwing in stderr and reading back from it.

    Returns:
        Generator: Buffering os stderr.
    """
    # equiv to pyvista's
    # from pyvista.utilities import VtkErrorCatcher
    # with VtkErrorCatcher() as err:
    #     append_filter.Update()
    #     print(err)
    # originalStderrFd = sys.stderr.fileno()
    originalStderrFd = 2  # Standard stderr file descriptor, not dynamic like sys.stderr.fileno()
    savedStderrFd = os.dup( originalStderrFd )  # Backup original stderr

    # Create a temporary file to capture stderr
    with tempfile.TemporaryFile( mode='w+b' ) as tmp:
        os.dup2( tmp.fileno(), originalStderrFd )
        try:
            yield tmp
        finally:
            # Restore original stderr
            os.dup2( savedStderrFd, originalStderrFd )
            os.close( savedStderrFd )


class CountWarningHandler( logging.Handler ):
    """Create an handler to count the warnings logged."""

    def __init__( self: Self ) -> None:
        """Init the handler."""
        super().__init__()
        self.warningCount = 0

    def emit( self: Self, record: logging.LogRecord ) -> None:
        """Count all the warnings logged.

        Args:
            record (logging.LogRecord): Record.
        """
        if record.levelno == logging.WARNING:
            self.warningCount += 1


# Add the convenience method for the logger
def results( self: logging.Logger, message: str, *args: Any, **kws: Any ) -> None:
    """Logs a message with the custom 'RESULTS' severity level.

    This level is designed for summary information that should always be
    visible, regardless of the logger's verbosity setting.

    Args:
        self (logging.Logger): The logger instance.
        message (str): The primary log message, with optional format specifiers (e.g., "Found %d issues.").
        *args: The arguments to be substituted into the `message` string.
        **kws: Keyword arguments for special functionality.
    """
    if self.isEnabledFor( RESULTS_LEVEL_NUM ):
        self._log( RESULTS_LEVEL_NUM, message, args, **kws )


# Define logging levels at the module level so they are available for the Formatter class
DEBUG: int = logging.DEBUG
INFO: int = logging.INFO
WARNING: int = logging.WARNING
ERROR: int = logging.ERROR
CRITICAL: int = logging.CRITICAL

# Define and register the new level for check results
RESULTS_LEVEL_NUM: int = 60
RESULTS_LEVEL_NAME: str = "RESULTS"
logging.addLevelName( RESULTS_LEVEL_NUM, RESULTS_LEVEL_NAME )
logging.Logger.results = results  # type: ignore[attr-defined]

# types redefinition to import logging.* from this module
Logger = logging.Logger  # logger type
class GEOSFormatter( logging.Formatter ):

    # define color codes
    green: str = "\x1b[32;20m"
    grey: str = "\x1b[38;20m"
    yellow: str = "\x1b[33;20m"
    red: str = "\x1b[31;20m"
    bold_red: str = "\x1b[31;1m"
    reset: str = "\x1b[0m"

    # define prefix of log messages
    format_short: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    format_long: str = ( "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)" )
    format_results: str = "%(name)s - %(levelname)s - %(message)s"

    #: format for each logger output type without colors (e.g., for Paraview)
    _formatDict : dict[int, str ] = {
        DEBUG: grey + format_long + reset,
        INFO: green + format_short + reset,
        WARNING: yellow + format_short + reset,
        ERROR: red + format_short + reset,
        CRITICAL: bold_red + format_long + reset,
        RESULTS_LEVEL_NUM: green + format_results + reset,
    }

    def __init__(self, fmt = None, datefmt = None, style = "%", validate = True, *, defaults = None) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self : Self, record : logging.LogRecord) -> str:
        return logging.Formatter( fmt= self._formatDict.get( record.levelno, []) ).format(record)

    @staticmethod
    def TrimColor(msg : str) -> str:
        return  msg[8:-5]


class GEOSHandler(logging.StreamHandler):

    def __init__(self, level = 0):
        super().__init__(level)

    def setLevel(self, level):
        return super().setLevel(level)

    @staticmethod
    def get_vtk_level(level : int):
        if level >= ERROR:
            return vtkLogger.VERBOSITY_ERROR
        elif level >= WARNING:
            return vtkLogger.VERBOSITY_WARNING
        elif level >= INFO:
            return vtkLogger.VERBOSITY_INFO
        elif level >= DEBUG:
            return vtkLogger.VERBOSITY_TRACE
        else:
            return vtkLogger.VERBOSITY_MAX

    def emit(self, record):
        try:
            msg = self.format(record)
            lvl = GEOSHandler.get_vtk_level(record.levelno)

            from vtkmodules.vtkCommonCore import vtkOutputWindow as win
            outwin= win.GetInstance()
            if outwin:
                #see https://www.paraview.org/paraview-docs/v5.13.3/python/_modules/paraview/detail/loghandler.html#VTKHandler
                prevMode = outwin.GetDisplayMode()
                outwin.SetDisplayModeToNever()
                
                if lvl == ERROR:
                    outwin.DisplayErrorText(GEOSFormatter.TrimColor(msg))
                elif lvl == WARNING:
                    outwin.DisplayErrorText(GEOSFormatter.TrimColor(msg))
                else:
                    outwin.DisplayText(GEOSFormatter.TrimColor(msg))
 
                outwin.SetDisplayMode(prevMode)

        except Exception:
            self.handleError(record)

 

def getLogger( title: str, use_color=False ) -> Logger:
    """Return the Logger with pre-defined configuration.

    This function is now idempotent regarding handler addition.
    Calling it multiple times with the same title will return the same
    logger instance without adding more handlers if one is already present.

    Example:

    .. code-block:: python

        # module import
        import Logger

        # logger instantiation
        logger :Logger.Logger = Logger.getLogger("My application")

        # logger use
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")
        logger.results("results message")

    Args:
        title (str): Name of the logger.
        use_color (bool): If True, configure the logger to output with color.
                          Defaults to False.

    Returns:
        Logger: logger
    """
    logger = logging.getLogger( title )
    # Only configure the logger (add handlers, set level) if it hasn't been configured before.
    if len( logger.handlers ) == 0:
        logger.setLevel( DEBUG )  # Set the desired default level for this logger
        # Create and add the stream handler
        geos_handler = GEOSHandler()
        geos_handler.setFormatter(GEOSFormatter())
        geos_handler.setLevel(logger.getEffectiveLevel())
        logger.addHandler( geos_handler )
        
        cli_handle = logging.StreamHandler()
        cli_handle.setFormatter(GEOSFormatter())
        cli_handle.setLevel(logger.getEffectiveLevel())
        logger.addHandler(cli_handle)

        # Optional: Prevent messages from propagating to the root logger's handlers
        logger.propagate = True

    # If you need to ensure a certain level is set every time getLogger is called,
    # even if handlers were already present, you can set the level outside the 'if' block.
    # However, typically, setLevel is part of the initial handler configuration.
    # logger.setLevel(INFO) # Uncomment if you need to enforce level on every call
    return logger