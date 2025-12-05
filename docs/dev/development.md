# 开发指南

## 开发环境设置

### 前置要求
- Python 3.9+
- Git
- 一个代码编辑器（推荐 VS Code）

### 克隆和初始化

```bash
# 克隆仓库
git clone https://github.com/imbatony/pavone.git
cd pavone

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"
```

### IDE 配置

#### VS Code
推荐扩展：
- **Pylance**: Python 类型检查和代码智能
- **Python**: Python 开发支持
- **Black Formatter**: 代码格式化
- **Better Comments**: 注释高亮

配置 `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.rulers": [88]
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.analysis.typeCheckingMode": "strict"
}
```

## 代码质量标准

### 类型检查
所有代码必须通过 Pylance 严格模式的类型检查。

```bash
pyright pavone/
```

### 代码格式化
使用 Black 格式化，行宽为 88 字符。

```bash
black pavone/ tests/ --line-length 88
isort pavone/ tests/
```

### 代码风格检查
```bash
flake8 pavone/ tests/ --max-line-length 88
pylint pavone/
```

### 代码审查检查清单
- [ ] 代码通过 Pylance 严格类型检查
- [ ] 通过 Black 格式化
- [ ] 有适当的单元测试
- [ ] 更新了相关文档
- [ ] 没有新的 linting 警告

## 贡献流程

### 1. 创建功能分支
```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/*`: 新功能
- `fix/*`: 缺陷修复
- `docs/*`: 文档更新
- `refactor/*`: 代码重构
- `test/*`: 测试改进

### 2. 开发和测试
```bash
# 在开发时定期运行测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_something.py::TestClass::test_method -v

# 生成覆盖率报告
python -m pytest tests/ --cov=pavone --cov-report=html
```

### 3. 提交更改
```bash
# 添加更改
git add .

# 提交（包含描述性消息）
git commit -m "feat: add new feature"
git commit -m "fix: resolve issue with xyz"
git commit -m "docs: update API documentation"
```

提交消息规范（Conventional Commits）：
- `feat:` 新功能
- `fix:` 缺陷修复
- `docs:` 文档更新
- `test:` 测试添加或修改
- `refactor:` 代码重构
- `perf:` 性能优化
- `chore:` 构建过程或依赖更新

### 4. 推送并创建 Pull Request
```bash
git push origin feature/your-feature-name
```

创建 Pull Request 时，请包含：
- 清晰的功能描述
- 相关的 issue 号
- 测试结果证明

## 测试

### 运行所有测试
```bash
python -m pytest tests/ -v
```

### 运行特定测试文件
```bash
python -m pytest tests/test_downloader.py -v
```

### 运行特定测试
```bash
python -m pytest tests/test_downloader.py::TestDownloader::test_basic -v
```

### 生成覆盖率报告
```bash
# 生成 HTML 覆盖率报告
python -m pytest tests/ --cov=pavone --cov-report=html

# 打开报告
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### 测试编写指南

在 `tests/` 目录中创建测试文件，命名为 `test_*.py`。

示例测试结构：
```python
import pytest
from pavone.core.downloader.http_downloader import HTTPDownloader

class TestHTTPDownloader:
    """HTTP 下载器测试类"""
    
    def test_basic_download(self):
        """测试基本下载功能"""
        downloader = HTTPDownloader()
        # 测试代码
        assert True
    
    def test_with_proxy(self):
        """测试代理功能"""
        # 测试代码
        assert True
    
    @pytest.mark.slow
    def test_large_file_download(self):
        """测试大文件下载（标记为慢速测试）"""
        # 测试代码
        assert True
```

## 代码组织原则

### 导入顺序
```python
# 1. 标准库
import os
import sys
from typing import Optional, Dict

# 2. 第三方库
import pytest
from pydantic import BaseModel

# 3. 本地应用
from pavone.core.base import BaseOperation
from pavone.models.metadata import Metadata
```

### 类型注解
所有函数和变量都应该有类型注解：

```python
def download(
    url: str,
    filename: Optional[str] = None,
    timeout: int = 30,
) -> bool:
    """下载文件。
    
    Args:
        url: 下载 URL
        filename: 保存文件名，如未指定则自动生成
        timeout: 超时时间（秒）
    
    Returns:
        是否下载成功
    """
    pass
```

### 文档字符串
使用 Google 风格的文档字符串：

```python
class MyClass:
    """一行简介。
    
    更详细的描述（可选）。
    
    Attributes:
        name: 名称
        value: 值
    """
    
    def method(self, param: str) -> Dict[str, int]:
        """方法说明。
        
        Args:
            param: 参数说明
        
        Returns:
            返回值说明
        
        Raises:
            ValueError: 异常说明
        """
        pass
```

## 调试技巧

### 启用详细日志
```bash
pavone --verbose download "url"
```

### 在 VS Code 中调试
在 `.vscode/launch.json` 中添加：
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

### 使用 pdb 调试
```python
import pdb
pdb.set_trace()  # 在这里设置断点
```

## 常见任务

### 添加新的提取器

1. 在 `pavone/plugins/extractors/` 创建新文件，例如 `my_extractor.py`
2. 继承 `BaseExtractor`
3. 实现所需方法

```python
from pavone.plugins.extractors.base import BaseExtractor
from pavone.models.metadata import Metadata

class MyExtractor(BaseExtractor):
    """我的提取器"""
    
    @property
    def name(self) -> str:
        return "my_extractor"
    
    def extract(self, url: str) -> Metadata:
        """提取元数据"""
        # 实现提取逻辑
        pass
```

4. 在 `pavone/plugins/extractors/__init__.py` 中注册

### 添加新配置选项

1. 在 `pavone/config/configs.py` 中的相应模型添加字段
2. 在 `pavone/config/validator.py` 中添加验证逻辑
3. 更新 `docs/config.md` 文档

## 发布流程

### 版本号
遵循 Semantic Versioning (MAJOR.MINOR.PATCH)

### 发布步骤
1. 更新 `pyproject.toml` 中的版本号
2. 更新 `CHANGELOG.md`
3. 创建 Git 标签并推送
4. 发布到 PyPI（待实现）

## 获取帮助

- 查看现有的 GitHub Issues
- 在 Discussions 中提问
- 查看文档：[docs/](../docs/)
- 查看项目架构：[docs/dev/architecture.md](architecture.md)
