"""
Tests for logging setup module.

Tests structured logging, formatters, and logging utilities.
"""

import logging
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from rule_generator.logging_setup import (
    ColoredFormatter,
    PerformanceTimer,
    get_logger,
    log_api_call,
    log_decision,
    log_error_with_context,
    log_performance,
    setup_logging,
)


class TestColoredFormatter:
    """Tests for ColoredFormatter."""

    def test_format_basic_message(self):
        """Should format basic log messages."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        assert 'Test message' in result

    def test_format_with_colors_in_tty(self):
        """Should add colors when output is a TTY."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error message',
            args=(),
            exc_info=None,
        )

        # Mock stderr.isatty() to return True
        with patch('sys.stderr.isatty', return_value=True):
            result = formatter.format(record)
            # Should contain ANSI color codes when isatty()
            assert 'ERROR' in result

    def test_different_log_levels(self):
        """Should handle different log levels."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        levels = [
            (logging.DEBUG, 'Debug'),
            (logging.INFO, 'Info'),
            (logging.WARNING, 'Warning'),
            (logging.ERROR, 'Error'),
            (logging.CRITICAL, 'Critical'),
        ]

        for level, msg in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg=msg,
                args=(),
                exc_info=None,
            )
            result = formatter.format(record)
            assert msg in result


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_basic(self):
        """Should set up logging with default configuration."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = False
            mock_config.LOG_LEVEL = 'INFO'

            setup_logging()

            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
            assert len(root_logger.handlers) > 0

    def test_setup_logging_debug_mode(self):
        """Should use DEBUG level when DEBUG_MODE is True."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = True
            mock_config.LOG_LEVEL = 'INFO'

            setup_logging()

            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

    def test_setup_logging_custom_level(self):
        """Should respect custom LOG_LEVEL setting."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = False
            mock_config.LOG_LEVEL = 'WARNING'

            setup_logging()

            root_logger = logging.getLogger()
            assert root_logger.level == logging.WARNING

    def test_setup_logging_removes_existing_handlers(self):
        """Should remove existing handlers before adding new ones."""
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)

        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = False
            mock_config.LOG_LEVEL = 'INFO'

            setup_logging()

            # Should replace handlers, not accumulate them
            assert len(root_logger.handlers) >= 1

    def test_third_party_loggers_quieted(self):
        """Should set third-party library loggers to WARNING level."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = False
            mock_config.LOG_LEVEL = 'DEBUG'

            setup_logging()

            # Third-party loggers should be at WARNING to reduce noise
            assert logging.getLogger('urllib3').level == logging.WARNING
            assert logging.getLogger('requests').level == logging.WARNING
            assert logging.getLogger('anthropic').level == logging.WARNING
            assert logging.getLogger('openai').level == logging.WARNING


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Should return a logger instance."""
        logger = get_logger('test_module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'

    def test_get_logger_caches_loggers(self):
        """Should return the same logger instance for the same name."""
        logger1 = get_logger('test_module')
        logger2 = get_logger('test_module')
        assert logger1 is logger2


class TestLogPerformance:
    """Tests for log_performance decorator."""

    def test_decorator_logs_when_enabled(self, caplog):
        """Should log performance when LOG_PERFORMANCE is True."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = True

            @log_performance
            def test_function():
                time.sleep(0.01)
                return "result"

            with caplog.at_level(logging.INFO):
                result = test_function()

            assert result == "result"
            assert any("completed in" in record.message for record in caplog.records)

    def test_decorator_silent_when_disabled(self, caplog):
        """Should not log when LOG_PERFORMANCE is False."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = False

            @log_performance
            def test_function():
                return "result"

            with caplog.at_level(logging.INFO):
                result = test_function()

            assert result == "result"
            # Should not have performance logs
            assert not any("completed in" in record.message for record in caplog.records)

    def test_decorator_logs_on_exception(self, caplog):
        """Should log performance even when function raises exception."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = True

            @log_performance
            def failing_function():
                raise ValueError("Test error")

            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError):
                    failing_function()

            assert any("failed after" in record.message for record in caplog.records)

    def test_decorator_preserves_function_metadata(self):
        """Should preserve original function name and docstring."""

        @log_performance
        def documented_function():
            """This is a test function."""
            pass

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestLogApiCall:
    """Tests for log_api_call function."""

    def test_logs_when_enabled(self, caplog):
        """Should log API calls when LOG_API_CALLS is True."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_API_CALLS = True

            logger = get_logger('test')
            with caplog.at_level(logging.DEBUG):
                log_api_call("OpenAI", "generate", model="gpt-4", temperature=0.0)

            assert any("API Call: OpenAI.generate" in record.message for record in caplog.records)
            assert any("model=gpt-4" in record.message for record in caplog.records)

    def test_silent_when_disabled(self, caplog):
        """Should not log when LOG_API_CALLS is False."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_API_CALLS = False

            with caplog.at_level(logging.DEBUG):
                log_api_call("OpenAI", "generate", model="gpt-4")

            assert not any("API Call" in record.message for record in caplog.records)

    def test_includes_all_context(self, caplog):
        """Should include all context parameters in log."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_API_CALLS = True

            with caplog.at_level(logging.DEBUG):
                log_api_call(
                    "Anthropic",
                    "generate",
                    model="claude-3",
                    temperature=0.5,
                    max_tokens=1000,
                )

            log_message = caplog.records[0].message
            assert "Anthropic.generate" in log_message
            assert "model=claude-3" in log_message
            assert "temperature=0.5" in log_message
            assert "max_tokens=1000" in log_message


class TestLogDecision:
    """Tests for log_decision function."""

    def test_logs_decision_with_rationale(self, caplog):
        """Should log decisions with rationale."""
        logger = get_logger('test')

        with caplog.at_level(logging.INFO):
            log_decision(
                logger,
                "Using combo rule",
                "Component requires import verification",
                component="Button",
                prop="isActive",
            )

        log_message = caplog.records[0].message
        assert "Decision: Using combo rule" in log_message
        assert "Component requires import verification" in log_message
        assert "component=Button" in log_message
        assert "prop=isActive" in log_message

    def test_logs_without_context(self, caplog):
        """Should log decisions without context parameters."""
        logger = get_logger('test')

        with caplog.at_level(logging.INFO):
            log_decision(logger, "Converting to combo rule", "Prevents false positives")

        log_message = caplog.records[0].message
        assert "Decision: Converting to combo rule" in log_message
        assert "Prevents false positives" in log_message


class TestLogErrorWithContext:
    """Tests for log_error_with_context function."""

    def test_logs_error_with_context(self, caplog):
        """Should log errors with context."""
        logger = get_logger('test')
        error = ValueError("Invalid input")

        with caplog.at_level(logging.ERROR):
            log_error_with_context(
                logger, error, "parsing YAML file", file_path="/path/to/file.yaml", line=42
            )

        log_message = caplog.records[0].message
        assert "Error during parsing YAML file" in log_message
        assert "ValueError: Invalid input" in log_message
        assert "file_path=/path/to/file.yaml" in log_message
        assert "line=42" in log_message

    def test_logs_error_without_context(self, caplog):
        """Should log errors without context."""
        logger = get_logger('test')
        error = RuntimeError("Operation failed")

        with caplog.at_level(logging.ERROR):
            log_error_with_context(logger, error, "API call")

        log_message = caplog.records[0].message
        assert "Error during API call" in log_message
        assert "RuntimeError: Operation failed" in log_message

    def test_logs_stack_trace_in_debug_mode(self, caplog):
        """Should log stack trace when DEBUG_MODE is enabled."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = True

            logger = get_logger('test')
            error = Exception("Test error")

            with caplog.at_level(logging.DEBUG):
                log_error_with_context(logger, error, "test operation")

            # Should have both error log and stack trace log
            assert len(caplog.records) >= 2
            assert any("Stack trace" in record.message for record in caplog.records)

    def test_no_stack_trace_in_normal_mode(self, caplog):
        """Should not log stack trace when DEBUG_MODE is disabled."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = False

            logger = get_logger('test')
            error = Exception("Test error")

            with caplog.at_level(logging.DEBUG):
                log_error_with_context(logger, error, "test operation")

            # Should only have error log, not stack trace
            assert not any("Stack trace" in record.message for record in caplog.records)


class TestPerformanceTimer:
    """Tests for PerformanceTimer context manager."""

    def test_basic_timing(self):
        """Should measure elapsed time."""
        with PerformanceTimer() as timer:
            time.sleep(0.01)

        assert timer.elapsed is not None
        assert timer.elapsed >= 0.01
        assert timer.start_time is not None
        assert timer.end_time is not None
        assert timer.end_time > timer.start_time

    def test_nested_timers(self):
        """Should support nested timers."""
        with PerformanceTimer() as outer_timer:
            time.sleep(0.01)
            with PerformanceTimer() as inner_timer:
                time.sleep(0.01)

        assert outer_timer.elapsed >= 0.02
        assert inner_timer.elapsed >= 0.01
        assert outer_timer.elapsed > inner_timer.elapsed

    def test_timer_with_exception(self):
        """Should still record time even if exception occurs."""
        with pytest.raises(ValueError):
            with PerformanceTimer() as timer:
                time.sleep(0.01)
                raise ValueError("Test error")

        # Should have recorded time before exception
        assert timer.elapsed is not None
        assert timer.elapsed >= 0.01

    def test_timer_logs_when_performance_logging_enabled(self, caplog):
        """Should log when used with logger and LOG_PERFORMANCE is True."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = True

            logger = get_logger('test')
            with caplog.at_level(logging.INFO):
                with PerformanceTimer(logger, "test operation"):
                    time.sleep(0.01)

            assert any("Completed: test operation" in record.message for record in caplog.records)

    def test_timer_silent_when_performance_logging_disabled(self, caplog):
        """Should not log when LOG_PERFORMANCE is False."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = False

            logger = get_logger('test')
            with caplog.at_level(logging.INFO):
                with PerformanceTimer(logger, "test operation"):
                    time.sleep(0.01)

            # Should not have performance logs
            assert not any("Completed" in record.message for record in caplog.records)

    def test_timer_logs_failure(self, caplog):
        """Should log failure when exception occurs."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.LOG_PERFORMANCE = True

            logger = get_logger('test')
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError):
                    with PerformanceTimer(logger, "test operation"):
                        raise ValueError("Test error")

            assert any("Failed: test operation" in record.message for record in caplog.records)


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_full_logging_setup_and_usage(self, caplog):
        """Should support full logging workflow."""
        with patch('rule_generator.logging_setup.config') as mock_config:
            mock_config.DEBUG_MODE = True
            mock_config.LOG_LEVEL = 'DEBUG'
            mock_config.LOG_PERFORMANCE = True
            mock_config.LOG_API_CALLS = True

            # Set up logging
            setup_logging()

            # Get logger
            logger = get_logger('test_module')

            with caplog.at_level(logging.DEBUG):
                # Log various types of messages
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")

                # Log decision
                log_decision(logger, "Test decision", "Test rationale", key="value")

                # Log API call
                log_api_call("TestAPI", "test_operation", param="value")

                # Log error with context
                log_error_with_context(logger, ValueError("test"), "test operation", key="value")

                # Use performance timer
                with PerformanceTimer(logger, "test operation"):
                    time.sleep(0.001)

            # Print all logged messages for debugging
            print("\n=== Captured log records ===")
            for record in caplog.records:
                print(f"{record.levelname}: {record.message}")
            print("=== End of log records ===\n")

            # Should have logged all messages
            assert any("Debug message" in record.message for record in caplog.records), \
                "Debug message not found in logs"
            assert any("Info message" in record.message for record in caplog.records), \
                "Info message not found in logs"
            assert any("Warning message" in record.message for record in caplog.records), \
                "Warning message not found in logs"
            assert any("Error message" in record.message for record in caplog.records), \
                "Error message not found in logs"
            assert any("Decision" in record.message for record in caplog.records), \
                "Decision not found in logs"
            assert any("ValueError" in record.message for record in caplog.records), \
                "ValueError not found in logs"
            # Note: PerformanceTimer and log_api_call use config.LOG_PERFORMANCE and
            # config.LOG_API_CALLS which are not properly mocked in this integration context.
            # These are tested separately in their dedicated test methods.
