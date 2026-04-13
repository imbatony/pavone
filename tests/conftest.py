"""共享测试 fixtures。"""

from pathlib import Path

import pytest

from pavone.config.configs import Config


@pytest.fixture
def config() -> Config:
    """测试用 Config 实例（默认配置）。"""
    return Config()


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """基于 tmp_path 的临时工作目录。"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def sample_metadata() -> dict:
    """示例元数据字典。"""
    return {
        "title": "Test Video",
        "code": "TEST-001",
        "actors": ["Actor A", "Actor B"],
        "tags": ["tag1", "tag2"],
        "release_date": "2026-01-01",
        "studio": "Test Studio",
        "duration": 120,
    }
