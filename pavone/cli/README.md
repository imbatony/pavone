# CLI Module Structure

This document describes the new modular CLI structure for PAVOne.

## Directory Structure

```
pavone/
├── cli.py                    # Legacy entry point (for backward compatibility)
└── cli/
    ├── __init__.py          # Main CLI entry point
    ├── utils.py             # Shared utility functions
    └── commands/
        ├── __init__.py      # Commands module initialization
        ├── init.py          # Init command and configuration setup
        ├── download.py      # Download-related commands
        ├── config.py        # Configuration display command
        ├── search.py        # Search command
        └── organize.py      # Organize command
```

## Benefits of the New Structure

### 1. **Modularity**
- Each command is in its own dedicated module
- Easy to add new commands without touching existing code
- Clear separation of concerns

### 2. **Maintainability**
- Smaller, focused files are easier to understand and maintain
- Reduced complexity in individual modules
- Better code organization

### 3. **Reusability**
- Common functionality extracted to `utils.py`
- Consistent user interface patterns across commands
- Shared helper functions for CLI operations

### 4. **Extensibility**
- Easy to add new commands by creating new modules in `commands/`
- Plugin-like architecture for command management
- Clear patterns for new contributors to follow

### 5. **Backward Compatibility**
- Original `cli.py` still works as before
- Gradual migration path for existing code
- No breaking changes for end users

## Command Modules

### `init.py`
- Handles PAVOne configuration initialization
- Interactive configuration setup
- Configuration validation and summary display

### `download.py`
- Single URL download command with comprehensive options
- Batch download command with file input support
- Advanced download configuration options:
  - Custom output filename and directory
  - HTTP headers and proxy support
  - Download quality and format selection
  - Concurrent threads and retry settings
  - Auto-organize after download
- Progress reporting and error handling

### `config.py`
- Display current configuration
- Configuration file location information
- Formatted output of all settings

### `search.py`
- Video search functionality
- Search result formatting
- Multiple search provider support

### `organize.py`
- File organization commands
- Directory structure management
- Metadata-based file sorting

## Utility Functions

The `utils.py` module provides common CLI utilities:

- `echo_success()`, `echo_error()`, `echo_warning()`, `echo_info()` - Consistent message formatting
- `confirm_action()` - User confirmation prompts
- `prompt_choice()` - Multiple choice prompts
- `prompt_int_range()` - Integer range input validation
- `read_urls_from_file()`, `read_urls_from_input()` - URL list handling

## Adding New Commands

To add a new command:

1. Create a new module in `commands/` directory
2. Define your command using the `@click.command()` decorator
3. Import and register the command in `cli/__init__.py`
4. Use utility functions from `utils.py` for consistency

Example:
```python
# commands/my_command.py
import click
from ..utils import echo_success

@click.command()
@click.argument('param')
def my_command(param):
    """My new command description"""
    echo_success(f"Executed with parameter: {param}")

# cli/__init__.py
from .commands.my_command import my_command
main.add_command(my_command)
```

## Download Command Options

The download commands support a comprehensive set of options to customize the download behavior:

### Basic Options
- `--auto-select, -a` - Automatically select the first download option without user interaction
- `--silent, -s` - Silent mode, suppress download progress display
- `--filename, -f TEXT` - Specify custom output filename
- `--output-dir, -o PATH` - Specify output directory

### Network Options
- `--header TEXT` - Add custom HTTP headers (can be used multiple times, format: "Key: Value")
- `--proxy TEXT` - Use HTTP proxy (format: http://proxy:port)
- `--timeout INTEGER` - Connection timeout in seconds (5-300)

### Download Control
- `--threads, -t INTEGER` - Number of download threads (1-16)
- `--retry, -r INTEGER` - Number of retry attempts on failure (0-10)

### Post-processing
- `--organize` - Automatically organize files after download

### Usage Examples

```bash
# Basic download
pavone download "https://example.com/video.mp4"

# Download with custom filename and directory
pavone download "https://example.com/video.mp4" -f "my_video.mp4" -o "/downloads"

# Download with custom headers
pavone download "https://example.com/video.mp4" --header "Referer: https://example.com" --header "Authorization: Bearer token"

# Download through proxy
pavone download "https://example.com/video.mp4" --proxy "http://proxy.example.com:8080"

# Download with auto-organize
pavone download "https://example.com/video.mp4" --organize

# Batch download from file
pavone batch-download -f urls.txt --threads 4 --organize

# Silent batch download with retry
pavone batch-download -f urls.txt --silent --retry 3
```

## Migration Notes

- The original `cli.py` file now acts as a compatibility layer
- All new development should use the modular structure
- Existing imports and entry points continue to work unchanged
- Consider migrating custom CLI extensions to use the new utility functions
