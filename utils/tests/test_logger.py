"""
Tests for logger module.
"""

import logging
import tempfile
from pathlib import Path
from utils.logger import (
    setup_logging, get_logger, set_level, 
    get_log_dir, Colors, ColoredFormatter
)


class TestLogger:
    """Test suite for logger module."""
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger(__name__)
        assert isinstance(logger, logging.Logger)
        assert logger.name == __name__
    
    def test_logger_default_configuration(self):
        """Test logger with default configuration."""
        logger = get_logger('test_module')
        assert logger.level <= logging.INFO
    
    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        # Reset configuration
        import utils.logger as logger_module
        logger_module._configured = False
        
        setup_logging(level=logging.DEBUG)
        logger = get_logger('test')
        
        # Check that logger is configured
        assert len(logging.getLogger().handlers) > 0
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import utils.logger as logger_module
            logger_module._configured = False
            
            setup_logging(level=logging.INFO, log_dir=temp_dir)
            logger = get_logger('test_file')
            
            logger.info("Test message")
            
            log_file = Path(temp_dir) / 'vidinie.log'
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
    
    def test_setup_logging_no_colors(self):
        """Test logging setup without colors."""
        import utils.logger as logger_module
        logger_module._configured = False
        
        setup_logging(level=logging.INFO, use_colors=False)
        root_logger = logging.getLogger()
        
        # Check that console handler doesn't use ColoredFormatter
        console_handler = None
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                console_handler = handler
                break
        
        assert console_handler is not None
        assert not isinstance(console_handler.formatter, ColoredFormatter)
    
    def test_set_level(self):
        """Test changing log level dynamically."""
        import utils.logger as logger_module
        logger_module._configured = False
        
        setup_logging(level=logging.INFO)
        logger = get_logger('test_level')
        
        set_level(logging.DEBUG)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_get_log_dir(self):
        """Test getting log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import utils.logger as logger_module
            logger_module._configured = False
            logger_module._log_dir = None
            
            setup_logging(log_dir=temp_dir)
            log_dir = get_log_dir()
            assert log_dir == temp_dir
    
    def test_get_log_dir_none(self):
        """Test get_log_dir when no file logging."""
        import utils.logger as logger_module
        logger_module._configured = False
        logger_module._log_dir = None
        
        setup_logging()
        log_dir = get_log_dir()
        assert log_dir is None
    
    def test_multiple_loggers(self):
        """Test creating multiple loggers."""
        logger1 = get_logger('module1')
        logger2 = get_logger('module2')
        logger3 = get_logger('module1')  # Same as logger1
        
        assert logger1.name == 'module1'
        assert logger2.name == 'module2'
        assert logger1 is logger3  # Should be the same instance


class TestColoredFormatter:
    """Test suite for ColoredFormatter."""
    
    def test_colored_formatter_initialization(self):
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        assert formatter is not None
    
    def test_colored_formatter_format(self):
        """Test formatting with colors."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Create a log record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert 'Test message' in formatted
        assert Colors.GREEN in formatted or Colors.RESET in formatted
    
    def test_colored_formatter_different_levels(self):
        """Test formatting different log levels."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        levels = [
            (logging.DEBUG, 'Debug message'),
            (logging.INFO, 'Info message'),
            (logging.WARNING, 'Warning message'),
            (logging.ERROR, 'Error message'),
            (logging.CRITICAL, 'Critical message')
        ]
        
        for level, msg in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg=msg,
                args=(),
                exc_info=None
            )
            
            formatted = formatter.format(record)
            assert msg in formatted
            # Should contain ANSI codes
            assert '\033[' in formatted


class TestColors:
    """Test suite for Colors class."""
    
    def test_color_codes_defined(self):
        """Test that all color codes are defined."""
        assert hasattr(Colors, 'RESET')
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'YELLOW')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'MAGENTA')
        assert hasattr(Colors, 'CYAN')
        assert hasattr(Colors, 'GREY')
    
    def test_color_codes_are_strings(self):
        """Test that color codes are strings."""
        assert isinstance(Colors.RESET, str)
        assert isinstance(Colors.RED, str)
        assert isinstance(Colors.GREEN, str)
    
    def test_color_codes_are_ansi(self):
        """Test that color codes are ANSI escape sequences."""
        assert Colors.RESET.startswith('\033[')
        assert Colors.RED.startswith('\033[')
        assert Colors.GREEN.startswith('\033[')


def test_logging_integration():
    """Test complete logging workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import utils.logger as logger_module
        logger_module._configured = False
        
        setup_logging(level=logging.DEBUG, log_dir=temp_dir)
        
        logger = get_logger('integration_test')
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        log_file = Path(temp_dir) / 'vidinie.log'
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content

