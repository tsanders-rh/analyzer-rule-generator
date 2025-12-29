# Logging and Debugging

The analyzer rule generator includes comprehensive logging capabilities to help with debugging, performance monitoring, and understanding decision-making during rule generation.

## Quick Start

### Enable Debug Mode

Set the `DEBUG` environment variable to enable verbose logging:

```bash
# Linux/macOS
export DEBUG=1
python scripts/generate_rules.py --guide migration-guide.md --source spring-boot-2 --target spring-boot-3

# Windows
set DEBUG=1
python scripts\generate_rules.py --guide migration-guide.md --source spring-boot-2 --target spring-boot-3
```

### Enable Performance Logging

Track execution time for major operations:

```bash
export DEBUG=1
export LOG_PERFORMANCE=1
python scripts/generate_rules.py --guide migration-guide.md --source spring-boot-2 --target spring-boot-3
```

### Enable API Call Logging

Log all LLM API calls with parameters:

```bash
export DEBUG=1
export LOG_API_CALLS=1
python scripts/generate_rules.py --guide migration-guide.md --source spring-boot-2 --target spring-boot-3
```

## Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `DEBUG` | `1`, `true`, `yes` | (disabled) | Enable debug mode with verbose logging |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | Set minimum log level |
| `LOG_PERFORMANCE` | `1`, `true`, `yes` | (disabled) | Log execution time for operations |
| `LOG_API_CALLS` | `1`, `true`, `yes` | (disabled) | Log all LLM API calls with parameters |

## Log Levels

Logs are output with different severity levels:

- **DEBUG**: Detailed information for diagnosing problems (only in debug mode)
- **INFO**: General informational messages about progress
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages about failures

## Log Format

### Normal Mode
```
[2025-01-15 10:30:45] INFO [rule_generator.extraction] Extracted 42 valid patterns from content
```

### Debug Mode
```
[2025-01-15 10:30:45] DEBUG [rule_generator.extraction:extract_patterns:240] Starting pattern extraction from 12,450 chars
```

Debug mode includes:
- Module name
- Function name
- Line number
- Color-coded log levels (in terminal)

## What Gets Logged

### Decision Logging

Important decisions made during rule generation are logged with rationale:

```
[2025-01-15 10:30:45] INFO [rule_generator.extraction] Decision: Auto-converting to combo rule - Component prop patterns require import verification to prevent false positives (pattern=Button isActive, language=javascript)
```

Common decisions logged:
- Converting simple patterns to combo rules
- Rejecting overly broad patterns
- Choosing provider types
- Handling deprecated APIs

### Performance Logging

When `LOG_PERFORMANCE=1`, execution times are logged:

```
[2025-01-15 10:30:45] INFO [rule_generator.extraction] Completed: pattern extraction from 12450 chars in 8.34s
```

Operations tracked:
- Pattern extraction
- LLM API calls
- Rule generation
- Validation
- File I/O

### API Call Logging

When `LOG_API_CALLS=1`, all LLM API calls are logged:

```
[2025-01-15 10:30:45] DEBUG [rule_generator.api] API Call: OpenAI.generate (model=gpt-4-turbo, temperature=0.0, max_tokens=4096)
[2025-01-15 10:30:53] DEBUG [rule_generator.llm] OpenAI API success: 2,845 tokens used
```

### Error Context

Errors include rich context for debugging:

```
[2025-01-15 10:30:45] ERROR [rule_generator.extraction] Error during OpenAI API call: RateLimitError: Rate limit exceeded (context: model=gpt-4-turbo, operation=generate)
```

In debug mode, full stack traces are included.

## Example: Full Debug Session

```bash
# Enable all logging
export DEBUG=1
export LOG_PERFORMANCE=1
export LOG_API_CALLS=1

# Run rule generation
python scripts/generate_rules.py \
    --guide https://example.com/migration-guide.md \
    --source patternfly-v5 \
    --target patternfly-v6 \
    --output examples/output/patternfly-v6/

# Output will show:
# - Detailed progress through each step
# - Performance metrics for major operations
# - Decision rationale for pattern transformations
# - API call parameters and token usage
# - Any errors with full context
```

## Programmatic Usage

If using the rule generator as a library, set up logging in your code:

```python
from rule_generator.logging_setup import setup_logging, get_logger, log_decision

# Initialize logging at startup
setup_logging()

# Get a logger for your module
logger = get_logger(__name__)

# Use standard logging
logger.info("Starting rule generation")
logger.warning("Pattern may be too broad")

# Log important decisions
log_decision(
    logger,
    "Using combo rule",
    "Component requires import verification",
    component="Button",
    prop="isActive"
)
```

## Performance Tracking

Use the `PerformanceTimer` context manager to track custom operations:

```python
from rule_generator.logging_setup import PerformanceTimer, get_logger

logger = get_logger(__name__)

with PerformanceTimer(logger, "processing large file"):
    # ... expensive operation
    process_file(large_file)

# Logs: "Completed: processing large file in 12.45s"
```

Or use the decorator for functions:

```python
from rule_generator.logging_setup import log_performance

@log_performance
def expensive_operation():
    # ... expensive work
    pass

# Automatically logs execution time when called
```

## Troubleshooting

### No logs appearing

- Check that `setup_logging()` is called at application startup
- Verify environment variables are set correctly
- Check that log level allows your messages (DEBUG < INFO < WARNING < ERROR)

### Too much output

- Reduce log level: `export LOG_LEVEL=WARNING`
- Disable performance logging: `unset LOG_PERFORMANCE`
- Disable API call logging: `unset LOG_API_CALLS`
- Disable debug mode: `unset DEBUG`

### Colors not showing in terminal

Colors are automatically disabled when output is redirected to a file. To force colors:

```bash
# Colors are automatic in terminal
python scripts/generate_rules.py ...

# No colors when redirected
python scripts/generate_rules.py ... > output.log

# Colors work
python scripts/generate_rules.py ...  # View in terminal

# Save logs without colors
python scripts/generate_rules.py ... 2> output.log
```

## Best Practices

1. **Development**: Enable all logging to understand behavior
   ```bash
   export DEBUG=1 LOG_PERFORMANCE=1 LOG_API_CALLS=1
   ```

2. **Production**: Use INFO level for normal operation
   ```bash
   export LOG_LEVEL=INFO
   ```

3. **Debugging Issues**: Enable DEBUG mode temporarily
   ```bash
   DEBUG=1 python scripts/generate_rules.py ...
   ```

4. **Performance Tuning**: Enable performance logging to find bottlenecks
   ```bash
   LOG_PERFORMANCE=1 python scripts/generate_rules.py ...
   ```

5. **API Cost Monitoring**: Track token usage with API call logging
   ```bash
   LOG_API_CALLS=1 python scripts/generate_rules.py ...
   ```
