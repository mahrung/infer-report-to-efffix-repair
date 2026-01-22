"""Tests for algorithm/utils/colored_logger.py"""

import logging
import pytest

from algorithm.utils.colored_logger import (
    ColoredFormatter,
    Colors,
    setup_colored_logging,
)


class TestColors:
    """Tests for Colors class constants."""

    def test_colors_are_escape_sequences(self):
        """Test that colors are ANSI escape sequences."""
        assert Colors.RESET.startswith("\033[")
        assert Colors.RED.startswith("\033[")
        assert Colors.GREEN.startswith("\033[")
        assert Colors.YELLOW.startswith("\033[")
        assert Colors.BLUE.startswith("\033[")
        assert Colors.CYAN.startswith("\033[")
        assert Colors.GRAY.startswith("\033[")

    def test_reset_code(self):
        """Test that reset code is correct."""
        assert Colors.RESET == "\033[0m"

    def test_all_colors_are_different(self):
        """Test that all colors have unique codes."""
        colors = [
            Colors.RED,
            Colors.GREEN,
            Colors.YELLOW,
            Colors.BLUE,
            Colors.MAGENTA,
            Colors.CYAN,
            Colors.WHITE,
            Colors.GRAY,
        ]
        assert len(colors) == len(set(colors))


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_colors_debug_level(self):
        """Test that DEBUG level gets correct color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.GRAY in formatted

    def test_colors_info_level(self):
        """Test that INFO level gets correct color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.GREEN in formatted

    def test_colors_warning_level(self):
        """Test that WARNING level gets correct color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.YELLOW in formatted

    def test_colors_error_level(self):
        """Test that ERROR level gets correct color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.RED in formatted

    def test_colors_critical_level(self):
        """Test that CRITICAL level gets correct color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.MAGENTA in formatted

    def test_colors_separator_lines(self):
        """Test that === separator lines get highlighted."""
        formatter = ColoredFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="=== Section Header ===",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.CYAN in formatted

    def test_colors_dash_separator_lines(self):
        """Test that --- separator lines get highlighted."""
        formatter = ColoredFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="--- Subsection ---",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.BLUE in formatted

    def test_colors_executing_messages(self):
        """Test that 'Executing' messages get highlighted."""
        formatter = ColoredFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Executing command: ls -la",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.YELLOW in formatted

    def test_colors_output_messages(self):
        """Test that 'output:' messages get highlighted."""
        formatter = ColoredFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Command output: success",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.WHITE in formatted

    def test_includes_reset_code(self):
        """Test that reset code is included after colors."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert Colors.RESET in formatted


class TestSetupColoredLogging:
    """Tests for setup_colored_logging function."""

    def test_sets_up_root_logger(self):
        """Test that root logger is configured."""
        # Save original state
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level

        try:
            setup_colored_logging(level=logging.DEBUG)

            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) == 1
            assert isinstance(
                root_logger.handlers[0].formatter, ColoredFormatter
            )
        finally:
            # Restore original state
            root_logger.handlers = original_handlers
            root_logger.setLevel(original_level)

    def test_sets_info_level_by_default(self):
        """Test that INFO level is set by default."""
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level

        try:
            setup_colored_logging()

            assert root_logger.level == logging.INFO
        finally:
            root_logger.handlers = original_handlers
            root_logger.setLevel(original_level)

    def test_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level

        try:
            # Add some handlers
            root_logger.addHandler(logging.StreamHandler())
            root_logger.addHandler(logging.StreamHandler())

            setup_colored_logging()

            # Should only have our single handler
            assert len(root_logger.handlers) == 1
        finally:
            root_logger.handlers = original_handlers
            root_logger.setLevel(original_level)
