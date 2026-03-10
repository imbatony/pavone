# PAVOne 开发脚本

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string[]]$Arguments
)

# 设置控制台输出编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 检查命令执行结果
function Test-CommandSuccess {
    param($Message)
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $Message" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
        return $false
    }
}

switch ($Command) {
    "install" {
        Write-Host "📦 安装项目依赖..." -ForegroundColor Green
        uv sync
        Test-CommandSuccess "依赖安装完成"
    }
    
    "test" {
        Write-Host "🧪 运行单元测试 (不包括集成测试)..." -ForegroundColor Green
        if ($Arguments) {
            uv run pytest -v -m "not integration" --tb=short $Arguments
        } else {
            uv run pytest tests/ -v -m "not integration" --tb=short
        }
        Test-CommandSuccess "单元测试完成"
    }
    
    "test-all" {
        Write-Host "🧪 运行所有测试 (包括集成测试)..." -ForegroundColor Green
        if ($Arguments) {
            uv run pytest -v --tb=short $Arguments
        } else {
            uv run pytest tests/ -v --tb=short
        }
        Test-CommandSuccess "所有测试完成"
    }
    
    "test-cov" {
        Write-Host "🧪 运行测试并生成覆盖率报告..." -ForegroundColor Green
        if ($Arguments) {
            uv run pytest -v -m "not integration" --cov=pavone --cov-report=html --cov-report=term-missing $Arguments
        } else {
            uv run pytest tests/ -v -m "not integration" --cov=pavone --cov-report=html --cov-report=term-missing
        }
        Test-CommandSuccess "测试覆盖率报告已生成到 htmlcov/"
    }
    
    "format" {
        Write-Host "🎨 格式化代码..." -ForegroundColor Green
        Write-Host "  运行 Black..." -ForegroundColor Cyan
        uv run black pavone/ tests/
        Test-CommandSuccess "Black 格式化完成"
        
        Write-Host "  运行 isort..." -ForegroundColor Cyan
        uv run isort pavone/ tests/
        Test-CommandSuccess "isort 导入排序完成"
    }
    
    "format-check" {
        Write-Host "🎨 检查代码格式 (不修改文件)..." -ForegroundColor Green
        $success = $true
        
        Write-Host "  检查 Black 格式..." -ForegroundColor Cyan
        uv run black --check --diff pavone/ tests/
        if (-not (Test-CommandSuccess "Black 格式检查")) { $success = $false }
        
        Write-Host "  检查 isort 导入排序..." -ForegroundColor Cyan
        uv run isort --check-only --diff pavone/ tests/
        if (-not (Test-CommandSuccess "isort 检查")) { $success = $false }
        
        if (-not $success) {
            Write-Host "`n提示: 运行 '.\dev.ps1 format' 自动修复格式问题" -ForegroundColor Yellow
            exit 1
        }
    }
    
    "lint" {
        Write-Host "🔍 运行代码检查..." -ForegroundColor Green
        $success = $true
        
        Write-Host "  运行 flake8 (严重错误检查)..." -ForegroundColor Cyan
        uv run flake8 pavone/ tests/ --select=E9,F63,F7,F82
        if (-not (Test-CommandSuccess "flake8 严重错误检查")) { $success = $false }
        
        Write-Host "  运行 flake8 (代码质量检查)..." -ForegroundColor Cyan
        uv run flake8 pavone/ tests/ --exit-zero
        Test-CommandSuccess "flake8 代码质量检查完成"
        
        if (-not $success) { exit 1 }
    }
    
    "type-check" {
        Write-Host "🔎 运行类型检查..." -ForegroundColor Green
        Write-Host "  运行 Pyright (Pylance 后端)..." -ForegroundColor Cyan
        uv run pyright pavone/
        Test-CommandSuccess "Pyright 类型检查完成"
    }
    
    "check" {
        Write-Host "✨ 运行完整代码质量检查..." -ForegroundColor Green
        $success = $true
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        Write-Host "1/3 代码格式检查" -ForegroundColor Yellow
        Write-Host "="*50 -ForegroundColor Gray
        & $PSCommandPath format-check
        if ($LASTEXITCODE -ne 0) { $success = $false }
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        Write-Host "2/3 代码质量检查 (Lint)" -ForegroundColor Yellow
        Write-Host "="*50 -ForegroundColor Gray
        & $PSCommandPath lint
        if ($LASTEXITCODE -ne 0) { $success = $false }
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        Write-Host "3/3 类型检查" -ForegroundColor Yellow
        Write-Host "="*50 -ForegroundColor Gray
        & $PSCommandPath type-check
        if ($LASTEXITCODE -ne 0) { $success = $false }
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        if ($success) {
            Write-Host "✅ 所有检查通过!" -ForegroundColor Green
        } else {
            Write-Host "❌ 部分检查失败，请修复后重试" -ForegroundColor Red
            exit 1
        }
    }
    
    "ci" {
        Write-Host "🚀 运行 CI 流程 (本地模拟)..." -ForegroundColor Green
        $success = $true
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        Write-Host "阶段 1: 代码质量检查" -ForegroundColor Yellow
        Write-Host "="*50 -ForegroundColor Gray
        & $PSCommandPath check
        if ($LASTEXITCODE -ne 0) { $success = $false }
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        Write-Host "阶段 2: 单元测试" -ForegroundColor Yellow
        Write-Host "="*50 -ForegroundColor Gray
        & $PSCommandPath test-cov
        if ($LASTEXITCODE -ne 0) { $success = $false }
        
        Write-Host "`n" + "="*50 -ForegroundColor Gray
        if ($success) {
            Write-Host "✅ CI 流程通过!" -ForegroundColor Green
        } else {
            Write-Host "❌ CI 流程失败" -ForegroundColor Red
            exit 1
        }
    }
    
    "clean" {
        Write-Host "🧹 清理缓存文件..." -ForegroundColor Green
        Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
        Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
        Get-ChildItem -Path . -Recurse -Filter "*.pyo" | Remove-Item -Force
        Get-ChildItem -Path . -Recurse -Filter ".pytest_cache" | Remove-Item -Recurse -Force
        if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
        if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
        if (Test-Path "coverage.xml") { Remove-Item -Force "coverage.xml" }
        Write-Host "✅ 清理完成" -ForegroundColor Green
    }
    
    "run" {
        Write-Host "▶️  运行 PAVOne..." -ForegroundColor Green
        if ($Arguments) {
            uv run pavone $Arguments
        } else {
            uv run pavone --help
        }
    }
    
    "build" {
        Write-Host "📦 构建项目..." -ForegroundColor Green
        uv build
        Test-CommandSuccess "项目构建完成"
    }
    
    "dev" {
        Write-Host "🔧 启动开发环境..." -ForegroundColor Green
        if (!(Test-Path ".venv")) {
            Write-Host "  创建虚拟环境..." -ForegroundColor Yellow
            uv venv
        }
        .\.venv\Scripts\Activate.ps1
        Write-Host "✅ 虚拟环境已激活!" -ForegroundColor Green
    }
    
    default {
        Write-Host @"
🎯 PAVOne 开发脚本

用法: .\dev.ps1 <command> [args]

📦 环境管理:
  install      - 安装项目依赖
  dev          - 启动开发环境 (激活虚拟环境)
  clean        - 清理缓存文件

🧪 测试命令:
  test [args]      - 运行单元测试 (不包括集成测试)
  test-all [args]  - 运行所有测试 (包括集成测试)
  test-cov [args]  - 运行测试并生成覆盖率报告

🎨 代码质量:
  format       - 格式化代码 (black + isort)
  format-check - 检查代码格式 (不修改)
  lint         - 运行 lint 检查 (flake8)
  type-check   - 运行类型检查 (pyright)
  check        - 运行完整代码质量检查 (format + lint + type-check)

🚀 CI/CD:
  ci           - 运行完整 CI 流程 (本地模拟)

📦 其他:
  run [args]   - 运行 PAVOne
  build        - 构建项目

示例:
  .\dev.ps1 install                         # 安装依赖
  .\dev.ps1 format                          # 格式化代码
  .\dev.ps1 test                            # 运行单元测试
  .\dev.ps1 test tests/test_filename_parser.py  # 运行指定测试文件
  .\dev.ps1 test -k test_extract            # 运行名称匹配的测试
  .\dev.ps1 test --maxfail=1                # 第一个失败后停止
  .\dev.ps1 check                           # 运行所有检查
  .\dev.ps1 ci                              # 本地模拟 CI
  .\dev.ps1 run search av01                 # 运行 pavone 命令
"@ -ForegroundColor Cyan
    }
}
