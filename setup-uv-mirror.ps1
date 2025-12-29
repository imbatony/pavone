# 设置 uv 使用阿里云镜像加速
$env:UV_INDEX_URL = "https://mirrors.aliyun.com/pypi/simple/"

# 或者使用清华镜像
# $env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"

Write-Host "UV_INDEX_URL set to: $($env:UV_INDEX_URL)" -ForegroundColor Green
Write-Host ""
Write-Host "开始同步依赖..." -ForegroundColor Yellow
uv sync --group dev
Write-Host ""
Write-Host "依赖同步完成！" -ForegroundColor Green
