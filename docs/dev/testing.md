# 测试指南

## 测试框架

本项目使用 **pytest** 作为主要的测试框架。

## 运行测试

### 运行所有测试
```bash
python -m pytest tests/ -v
```

### 运行特定测试文件
```bash
python -m pytest tests/test_downloader.py -v
```

### 运行特定测试类或方法
```bash
python -m pytest tests/test_downloader.py::TestDownloader -v
python -m pytest tests/test_downloader.py::TestDownloader::test_basic -v
```

### 显示最慢的测试
```bash
python -m pytest tests/ -v --durations=10
```

### 生成测试覆盖率报告
```bash
# 运行测试并生成 HTML 覆盖率报告
python -m pytest tests/ --cov=pavone --cov-report=html

# 打开 HTML 报告
open htmlcov/index.html  # macOS
start htmlcov\index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### 并行运行测试
```bash
# 需要先安装 pytest-xdist
pip install pytest-xdist

# 使用 4 个 worker 并行运行
python -m pytest tests/ -n 4
```

## 测试结构

```
tests/
├── __init__.py
├── test_downloader.py          # 下载器测试
├── test_extractor_base.py      # 提取器基类测试
├── test_*_extractor.py         # 各个提取器的测试
├── test_missav_plugin.py       # MissAV统一插件测试（包含搜索、元数据、提取三个功能）
├── test_logging_config.py      # 日志配置测试
├── test_code_extract_utils.py  # 代码提取工具测试
├── data/                        # 测试数据
│   ├── text_movie_ids.txt
│   └── ...
├── metadata/                    # 元数据测试文件
│   ├── movie1.nfo
│   └── movie2.nfo
└── sites/                       # 网站测试数据
    ├── missav.html
    ├── missav.m3u8
    └── ...
```

## 编写测试

### 测试文件命名
- 测试文件必须以 `test_` 前缀或 `_test` 后缀命名
- 示例：`test_downloader.py`, `downloader_test.py`

### 测试类编写
```python
import pytest
from pavone.core.downloader.http_downloader import HTTPDownloader

class TestHTTPDownloader:
    """HTTP 下载器测试类"""
    
    def setup_method(self):
        """测试前的准备工作"""
        self.downloader = HTTPDownloader()
    
    def teardown_method(self):
        """测试后的清理工作"""
        pass
    
    def test_basic_download(self):
        """测试基本下载功能"""
        # Arrange - 准备
        url = "https://example.com/file.txt"
        
        # Act - 执行
        result = self.downloader.download(url)
        
        # Assert - 断言
        assert result is not None
```

### 使用 Fixtures
```python
import pytest

@pytest.fixture
def downloader():
    """提供下载器实例"""
    from pavone.core.downloader.http_downloader import HTTPDownloader
    return HTTPDownloader()

def test_with_fixture(downloader):
    """使用 fixture 的测试"""
    assert downloader is not None
```

### 参数化测试
```python
import pytest

@pytest.mark.parametrize("url,expected", [
    ("https://example.com/file1.mp4", True),
    ("https://example.com/file2.m3u8", True),
    ("invalid_url", False),
])
def test_download_various_urls(url, expected):
    """测试各种 URL"""
    from pavone.core.downloader.http_downloader import HTTPDownloader
    downloader = HTTPDownloader()
    result = downloader.download(url) is not None
    assert result == expected
```

### 异常测试
```python
import pytest

def test_invalid_url():
    """测试无效 URL 处理"""
    from pavone.core.downloader.http_downloader import HTTPDownloader
    downloader = HTTPDownloader()
    
    with pytest.raises(ValueError):
        downloader.download("invalid_url")
```

### Mock 和 Patch
```python
from unittest.mock import Mock, patch, MagicMock
import pytest

def test_download_with_mock():
    """使用 mock 的测试"""
    from pavone.core.downloader.http_downloader import HTTPDownloader
    
    downloader = HTTPDownloader()
    
    # Mock requests.get
    with patch('pavone.core.downloader.http_downloader.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"file content"
        mock_get.return_value = mock_response
        
        result = downloader.download("https://example.com/file.mp4")
        
        assert result is not None
        mock_get.assert_called_once()
```

## 测试标记

使用 pytest 标记来分类测试：

```python
import pytest

@pytest.mark.slow
def test_large_file_download():
    """标记为慢速测试"""
    pass

@pytest.mark.network
def test_with_network_call():
    """标记为需要网络的测试"""
    pass

@pytest.mark.skip(reason="功能尚未实现")
def test_future_feature():
    """跳过的测试"""
    pass

@pytest.mark.xfail(reason="已知的失败")
def test_known_issue():
    """预期失败"""
    pass
```

运行特定标记的测试：
```bash
# 运行标记为 'slow' 的测试
python -m pytest -m slow

# 运行不包含 'slow' 标记的测试
python -m pytest -m "not slow"

# 运行多个标记
python -m pytest -m "slow or network"
```

## 代码质量检查

### 类型检查
```bash
# 使用 Pyright/Pylance 进行类型检查
pyright pavone/

# 严格模式
pyright pavone/ --pythonversion 3.9
```

### 代码格式化
```bash
# 使用 Black 格式化代码
black pavone/ tests/

# 检查是否符合 Black 风格（不修改）
black pavone/ tests/ --check

# 自动排序导入
isort pavone/ tests/
```

### 代码风格检查
```bash
# 使用 Flake8 进行风格检查
flake8 pavone/ tests/ --max-line-length 88

# 使用 Pylint 进行深度检查
pylint pavone/
```

## 持续集成

### GitHub Actions 工作流
项目配置了自动 CI/CD 流程：

1. **CI 流程** (`.github/workflows/ci.yml`)
   - 运行所有测试
   - 生成覆盖率报告
   - 检查代码质量

2. **代码质量检查** (`.github/workflows/code-quality.yml`)
   - Pylance 类型检查
   - Black 代码格式化
   - Flake8 风格检查
   - Pylint 深度检查

## 测试覆盖率目标

- **总体覆盖率**: 80% 或以上
- **关键模块**: 90% 或以上
  - `core/downloader/`
  - `plugins/extractors/`
  - `config/`

## 本地测试

### 快速测试
```bash
# 只运行单位测试（不包括集成测试）
python -m pytest tests/ -v -m "not integration"
```

### 完整测试
```bash
# 运行所有测试并生成报告
python -m pytest tests/ -v --cov=pavone --cov-report=html --durations=10
```

### 调试测试
```bash
# 显示打印输出
python -m pytest tests/ -v -s

# 进入 pdb 调试器
python -m pytest tests/ -v --pdb

# 显示本地变量
python -m pytest tests/ -v -l
```

## 测试性能优化

### 问题案例

如果测试运行缓慢，检查：

1. **网络调用**: 使用 Mock 替代实际网络请求
   ```python
   from unittest.mock import patch, Mock
   
   @patch('requests.get')
   def test_with_mock(mock_get):
       mock_get.return_value = Mock(status_code=200)
       # 测试代码
   ```

2. **数据库调用**: 使用内存数据库或 fixtures
   ```python
   @pytest.fixture
   def temp_db():
       # 创建临时数据库
       yield db
       # 清理
   ```

3. **文件 I/O**: 使用 `tmp_path` fixture
   ```python
   def test_with_temp_dir(tmp_path):
       temp_file = tmp_path / "test.txt"
       # 测试代码
   ```

## 故障排除

### 常见问题

**Q: 测试在本地通过但在 CI 上失败**
- 检查 Python 版本差异
- 检查操作系统差异（Windows vs Linux）
- 检查依赖版本

**Q: 测试运行太慢**
- 使用 `--durations` 找到最慢的测试
- 使用 Mock 替代网络/文件 I/O
- 使用 `pytest-xdist` 并行运行

**Q: 随机失败**
- 检查是否有依赖于执行顺序的测试
- 检查是否修改了全局状态
- 使用 `--random-order` 测试随机顺序

## 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [unittest.mock 文档](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov 覆盖率](https://pytest-cov.readthedocs.io/)
