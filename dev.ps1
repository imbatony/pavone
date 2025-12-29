# PAVOne 开发脚本

param(
    [Parameter(Position=0)]
    [string]$Command
)

# 设置控制台输出编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

switch ($Command) {
    "install" {
        Write-Host "安装项目依赖..." -ForegroundColor Green
        uv sync
        uv install -e .
    }
    "test" {
        Write-Host "运行测试..." -ForegroundColor Green
        uv run pytest tests/ -v
    }
    "lint" {
        Write-Host "运行代码检查..." -ForegroundColor Green
        uv run black .
        uv run flake8 pavone/
    }
    "clean" {
        Write-Host "清理缓存文件..." -ForegroundColor Green
        Get-ChildItem -Path . -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force
        Get-ChildItem -Path . -Recurse -Name "*.pyc" | Remove-Item -Force
        Get-ChildItem -Path . -Recurse -Name "*.pyo" | Remove-Item -Force
        Get-ChildItem -Path . -Recurse -Name ".pytest_cache" | Remove-Item -Recurse -Force
    }
    "run" {
        Write-Host "运行PAVOne..." -ForegroundColor Green
        pavone --help
    }
    "build" {
        Write-Host "构建项目..." -ForegroundColor Green
        uv build
    }
    "dev" {
        Write-Host "启动开发环境..." -ForegroundColor Green
        if (!(Test-Path ".venv")) {
            Write-Host "创建虚拟环境..." -ForegroundColor Yellow
            uv venv
        }
        .\.venv\Scripts\Activate.ps1
        Write-Host "虚拟环境已激活!" -ForegroundColor Green
    }
    default {
        Write-Host @"
PAVOne 开发脚本

用法: .\dev.ps1 <command>

可用命令:
  install   - 安装项目依赖
  test      - 运行测试
  lint      - 运行代码检查和格式化
  clean     - 清理缓存文件
  run       - 运行PAVOne
  build     - 构建项目
  dev       - 启动开发环境

示例:
  .\dev.ps1 install
  .\dev.ps1 test
  .\dev.ps1 dev
"@ -ForegroundColor Cyan
    }
}
