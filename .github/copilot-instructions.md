# Copilot Instructions for PAVOne

## Build, Test, and Lint

```bash
uv sync                                    # Install/sync all dependencies
uv run pytest tests/ -v                    # Run unit tests (integration tests excluded by default)
uv run pytest tests/test_foo.py::test_bar  # Run a single test
uv run pytest -m integration               # Run integration tests only
uv run black pavone/ tests/                # Format code
uv run isort pavone/ tests/                # Sort imports
uv run flake8 pavone/ tests/               # Lint
uv run pyright pavone/                     # Type check
make -f scripts/Makefile check             # Run all checks (format + lint + type-check + test)
```

## Architecture

PAVOne is a plugin-based CLI video management tool built with Click.

- **CLI layer** (`pavone/cli/`): Click command group entry point in `__init__.py`. Individual commands live in `cli/commands/`. The CLI entry catches `PavoneError` subclasses and maps them to `ExitCode` constants.
- **Plugin system** (`pavone/plugins/`): All plugins extend `BasePlugin` (`plugins/base.py`) which provides logger, config access, and a priority system (0–100, lower = higher priority). Plugin categories:
  - `extractors/` — extract video URLs from web pages
  - `metadata/` — fetch video metadata from various sites (30+ providers, many ported from metatube-sdk-go)
  - `search/` — unified search across sites
- **Core** (`pavone/core/`): `BaseDownloader` abstract class, downloader implementations, metadata extractors, and the exception hierarchy (`PavoneError` → `NetworkError`, `DownloadError`, `ExtractError`, `PluginError`, `ConfigError`, `MetadataError`).
- **Config** (`pavone/config/`): Pydantic-based configuration models. Settings accessed via `get_config_manager()`.
- **Jellyfin integration** (`pavone/jellyfin/`): Integration with self-hosted Jellyfin media servers.

## Key Conventions

- **Dependency management**: Use only `uv add` / `uv sync`. Never use `pip install` or `uv pip install`.
- **No `print()`**: Use `click.echo()` for user-facing output, `logger.*()` for logging.
- **Exceptions**: All application exceptions must inherit from `PavoneError`. Use the domain-specific subclasses (`NetworkError`, `DownloadError`, etc.). Exit codes use `ExitCode` constants from `pavone.core.exit_codes`.
- **Type annotations**: Required on all new code. Checked with `uv run pyright pavone/`.
- **Formatting**: Black + isort, both with line length 127 and black profile.
- **Tests**: All tests live in `tests/`. Use `conftest.py` for shared fixtures. Mark integration tests with `@pytest.mark.integration` and network tests with `@pytest.mark.network`.
- **Comments/docstrings**: Written in Chinese when needed. Prefer clear naming over comments.
- **Logging**: Obtain loggers via `pavone.config.logging_config.get_logger()`.
- **SSL**: Verification enabled by default. Add a comment explaining the reason if disabling.
