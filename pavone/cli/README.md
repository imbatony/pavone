# CLI Module Structure

This document describes the new modular CLI structure for PAVOne.

## Directory Structure

```
pavone/
├── cli.py                    # Legacy entry point (for backward compatibility)
└── cli/
    ├── __init__.py          # Main CLI entry point with unified architecture
    ├── utils.py             # Shared utility functions
    └── commands/
        ├── __init__.py      # Commands module initialization
        ├── init.py          # Init command and configuration setup
        ├── download.py      # Download-related commands (OperationItem-based)
        ├── config.py        # Configuration display command
        ├── search.py        # Search command
        └── organize.py      # Organize command
```

## Benefits of the New Structure

### 1. **Unified Architecture Integration**
- All commands now use the new OperationItem/ExecutionManager architecture
- Consistent data models (DownloadOption, OperationItem) across all operations
- Seamless integration with the plugin system

### 2. **Modularity**
- Each command is in its own dedicated module
- Easy to add new commands without touching existing code
- Clear separation of concerns

### 3. **Maintainability**
- Smaller, focused files are easier to understand and maintain
- Reduced complexity in individual modules
- Better code organization with consistent patterns

### 4. **Reusability**
- Common functionality extracted to `utils.py`
- Consistent user interface patterns across commands
- Shared helper functions for CLI operations

### 5. **Extensibility**
- Easy to add new commands by creating new modules in `commands/`
- Plugin-like architecture for command management
- Clear patterns for new contributors to follow

### 6. **Backward Compatibility**
- Original `cli.py` still works as before
- Gradual migration path for existing code
- No breaking changes for end users

## Command Modules

### `init.py`
- Handles PAVone configuration initialization using the new config system
- Interactive configuration setup with validation
- Configuration summary display with proper formatting

### `download.py`
- **Single URL download** - Creates OperationItem from URL, uses ExecutionManager
- **Batch download** - Processes multiple URLs, creates OperationItems for each
- **Advanced download configuration options**:
  - Custom output filename and directory
  - HTTP headers and proxy support (via DownloadOption)
  - Download quality and format selection
  - Concurrent execution through ExecutionManager
  - Auto-organize after download
- **Progress reporting** - Integrated with ExecutionManager's progress system
- **Error handling** - Comprehensive error handling with retry logic

### `config.py`
- Display current configuration using the new Config model
- Configuration file location information
- Formatted output of all settings with proper validation status

### `search.py`
- Video search functionality using search plugins
- Search result formatting and display
- Multiple search provider support through plugin system

### `organize.py`
- File organization commands using organize plugins
- Directory structure management
- Metadata-based file sorting with OperationItem integration

## Utility Functions

The `utils.py` module provides common CLI utilities integrated with the new architecture:

- `echo_success()`, `echo_error()`, `echo_warning()`, `echo_info()` - Consistent message formatting
- `confirm_action()` - User confirmation prompts
- `prompt_choice()` - Multiple choice prompts
- `prompt_int_range()` - Integer range input validation
- `read_urls_from_file()`, `read_urls_from_input()` - URL list handling
- `create_operation_from_url()` - Helper to create OperationItem from URL
- `setup_execution_manager()` - Helper to configure ExecutionManager with CLI options

## Adding New Commands

To add a new command that integrates with the unified architecture:

1. Create a new module in `commands/` directory
2. Import necessary models: `OperationItem`, `ExecutionManager`, `DownloadOption`
3. Define your command using the `@click.command()` decorator
4. Use ExecutionManager for any operation execution
5. Import and register the command in `cli/__init__.py`
6. Use utility functions from `utils.py` for consistency

Example:
```python
# commands/my_command.py
import click
from ..utils import echo_success, create_operation_from_url, setup_execution_manager
from pavone.manager.execution import ExecutionManager
from pavone.models.operation import OperationItem

@click.command()
@click.argument('url')
@click.option('--threads', '-t', default=1, help='Number of threads')
def my_command(url, threads):
    """My new command that downloads using the unified architecture"""
    try:
        # Create operation from URL
        operation = create_operation_from_url(url)
        
        # Setup execution manager
        manager = setup_execution_manager(threads=threads)
        manager.add_operation(operation)
        
        # Execute
        results = manager.execute_all()
        
        if results:
            echo_success(f"Command executed successfully: {url}")
        else:
            echo_error("Command execution failed")
            
    except Exception as e:
        echo_error(f"Error: {e}")

# cli/__init__.py
from .commands.my_command import my_command
main.add_command(my_command)
```

## Download Command Options

The download commands support a comprehensive set of options to customize the download behavior, all integrated with the new OperationItem/ExecutionManager architecture:

### Basic Options
- `--auto-select, -a` - Automatically select the first download option without user interaction
- `--silent, -s` - Silent mode, suppress download progress display
- `--filename, -f TEXT` - Specify custom output filename (sets DownloadOption.filename)
- `--output-dir, -o PATH` - Specify output directory (sets DownloadOption.output_dir)

### Network Options
- `--header TEXT` - Add custom HTTP headers (can be used multiple times, format: "Key: Value")
- `--proxy TEXT` - Use HTTP proxy (format: http://proxy:port, sets DownloadOption.proxy_url)
- `--timeout INTEGER` - Connection timeout in seconds (5-300, sets DownloadOption.timeout)

### Execution Control
- `--threads, -t INTEGER` - Number of concurrent operations in ExecutionManager (1-16)
- `--retry, -r INTEGER` - Number of retry attempts on failure (0-10, sets DownloadOption.max_retries)

### Post-processing
- `--organize` - Automatically organize files after download using organize plugins

### Architecture Integration
All options are processed through:
1. **DownloadOption creation** - CLI options populate DownloadOption fields
2. **OperationItem wrapping** - DownloadOptions are wrapped in OperationItems
3. **ExecutionManager execution** - OperationItems are executed through ExecutionManager
4. **Progress tracking** - Real-time progress updates through the manager's progress system

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
- All new development should use the modular structure with OperationItem/ExecutionManager
- Existing imports and entry points continue to work unchanged
- Consider migrating custom CLI extensions to use the new architecture:
  - Use `OperationItem` for operation representation
  - Use `ExecutionManager` for operation execution
  - Use `DownloadOption` for download configuration
  - Leverage the plugin system for extensibility
- New utility functions provide helpers for the unified architecture integration
