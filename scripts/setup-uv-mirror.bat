@echo off
REM 设置 uv 使用阿里云镜像加速
set UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

REM 或者使用清华镜像
REM set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

echo UV_INDEX_URL set to: %UV_INDEX_URL%
echo.
echo 开始同步依赖...
uv sync --group dev
echo.
echo 依赖同步完成！
