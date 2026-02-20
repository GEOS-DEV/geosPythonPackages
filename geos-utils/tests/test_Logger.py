# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
import random
import logging

import geos.utils.Logger as internLogger


def test_CountWarningHandler() -> None:
    """Test the verbosity counter handler class and its methods for the verbosity warning."""
    loggerTest: logging.Logger = logging.getLogger( "Test CountWarningHandler" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    countWarningHandler: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    countWarningHandler.setLevel( logging.INFO )

    loggerTest.addHandler( countWarningHandler )

    nbWarnings: int = random.randint( 0, 10 )
    for warning in range( nbWarnings ):
        loggerTest.warning( f"Warning number { warning }." )
    assert countWarningHandler.warningCount == nbWarnings

    additionalWarnings: int = random.randint( 1, 10 )
    countWarningHandler.addExternalWarningCount( additionalWarnings )
    assert countWarningHandler.warningCount == nbWarnings + additionalWarnings

    resetValue: int = random.randint( 0, 10 )
    countWarningHandler.resetWarningCount( resetValue )
    assert countWarningHandler.warningCount == resetValue

    loggerTest.warning( "Add a warning after the handler reset." )
    assert countWarningHandler.warningCount == resetValue + 1


def test_CountErrorHandler() -> None:
    """Test the verbosity counter handler class and its methods for the verbosity error and higher."""
    loggerTest: logging.Logger = logging.getLogger( "Test CountErrorHandler" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    countErrorHandler: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    countErrorHandler.setLevel( logging.INFO )

    loggerTest.addHandler( countErrorHandler )

    nbErrors: int = random.randint( 0, 10 )
    for error in range( nbErrors ):
        loggerTest.error( f"Error number { error }." )
    assert countErrorHandler.errorCount == nbErrors

    additionalErrors: int = random.randint( 1, 10 )
    countErrorHandler.addExternalErrorCount( additionalErrors )
    assert countErrorHandler.errorCount == nbErrors + additionalErrors

    resetValue: int = random.randint( 0, 10 )
    countErrorHandler.resetErrorCount( resetValue )
    assert countErrorHandler.errorCount == resetValue

    loggerTest.error( "Add an error after the handler reset." )
    assert countErrorHandler.errorCount == resetValue + 1

    loggerTest.critical( "Add a critical error, higher than error but style an error." )
    assert countErrorHandler.errorCount == resetValue + 2


def test_getLoggerHandlerType() -> None:
    """Test the function to get a logger's handler with a certain type."""
    loggerTest: logging.Logger = logging.getLogger( "Test getLoggerHandlerType" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    handler1: logging.Handler = logging.Handler()
    handler1.setLevel( logging.INFO )
    handlerType1: type = type( handler1 )
    loggerTest.addHandler( handler1 )

    handler2: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    handler2.setLevel( logging.INFO )
    handlerType2: type = type( handler2 )
    loggerTest.addHandler( handler2 )

    handler3: logging.Handler = logging.Handler()
    handler3.setLevel( logging.INFO )
    handlerType3: type = type( handler3 )
    loggerTest.addHandler( handler3 )

    handlerTest1: logging.Handler = internLogger.getLoggerHandlerType( handlerType1, loggerTest )
    handlerTest2: logging.Handler = internLogger.getLoggerHandlerType( handlerType2, loggerTest )
    handlerTest3: logging.Handler = internLogger.getLoggerHandlerType( handlerType3, loggerTest )

    assert type( handlerTest1 ) is handlerType1
    assert type( handlerTest2 ) is handlerType2
    assert type( handlerTest3 ) is handlerType3
    assert handlerTest3.__dict__ == handler1.__dict__  # If multiple Handler have the same type the first one is return


def test_getLoggerHandlerTypeValueError() -> None:
    """Test the ValueError raises of the getLoggerHandlerType function."""
    loggerTest: logging.Logger = logging.getLogger( "Test getLoggerHandlerType raises" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    handler1: logging.Handler = logging.Handler()
    handler1.setLevel( logging.INFO )
    handlerType1: type = type( handler1 )

    # Test with a empty logger
    with pytest.raises( ValueError ):
        internLogger.getLoggerHandlerType( handlerType1, loggerTest )

    loggerTest.addHandler( handler1 )

    handler2: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    handler2.setLevel( logging.INFO )
    handlerType2: type = type( handler2 )

    # Test with a logger with an other type of handler
    with pytest.raises( ValueError ):
        internLogger.getLoggerHandlerType( handlerType2, loggerTest )


def test_hasLoggerHandlerType() -> None:
    """Test the function to check if a logger has a handler of a certain type."""
    loggerTest: logging.Logger = logging.getLogger( "Test hasLoggerHandlerType" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    handler1: logging.Handler = logging.Handler()
    handler1.setLevel( logging.INFO )
    handlerType1: type = type( handler1 )
    loggerTest.addHandler( handler1 )

    handler2: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    handler2.setLevel( logging.INFO )
    handlerType2: type = type( handler2 )

    assert internLogger.hasLoggerHandlerType( handlerType1, loggerTest )
    assert not internLogger.hasLoggerHandlerType( handlerType2, loggerTest )


def test_isHandlerInLogger() -> None:
    """Test the function to check if a logger has a handler."""
    loggerTest: logging.Logger = logging.getLogger( "Test isHandlerInLogger" )
    loggerTest.setLevel( logging.INFO )
    loggerTest.propagate = False

    handler1: logging.Handler = logging.Handler()
    handler1.setLevel( logging.INFO )
    loggerTest.addHandler( handler1 )

    handler2: internLogger.CountVerbosityHandler = internLogger.CountVerbosityHandler()
    handler2.setLevel( logging.INFO )

    handler3: logging.Handler = logging.Handler()
    handler3.setLevel( logging.INFO )

    assert internLogger.isHandlerInLogger( handler1, loggerTest )
    assert not internLogger.isHandlerInLogger( handler2, loggerTest )
    assert not internLogger.isHandlerInLogger( handler3, loggerTest )  # Same type but the handler is different
