import os
import logging


def test_logs_directory_exists():
    """Test that logs directory is created."""
    assert os.path.exists('logs')
    assert os.path.isdir('logs')


def test_logging_config_can_be_imported():
    """Test that logging configuration can be imported successfully."""
    from config.logging_config import logger
    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_log_file_exists():
    """Test that log file exists after importing the logging config."""
    from config.logging_config import logger
    assert os.path.exists('logs/app.log') 