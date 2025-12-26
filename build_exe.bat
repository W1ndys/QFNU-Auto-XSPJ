@echo off
chcp 65001
echo ==========================================
echo 正在准备编译环境...
echo ==========================================

:: 确保安装了必要的库
pip install -U nuitka requests certifi ntplib beautifulsoup4 loguru

echo.
echo ==========================================
echo 清理旧的构建文件...
echo ==========================================
rmdir /s /q main.onefile-build 2>nul
rmdir /s /q main.build 2>nul
rmdir /s /q main.dist 2>nul
del main.exe 2>nul

echo.
echo ==========================================
echo 开始使用 Nuitka 编译...
echo ==========================================
:: 添加了 --include-package-data=certifi 和 --include-package-data=requests
:: 这解决了 requests 依赖 certifi 找不到证书文件导致的 ImportError
python -m nuitka ^
    --onefile ^
    --standalone ^
    --follow-imports ^
    --show-progress ^
    --include-package-data=certifi ^
    --include-package-data=requests ^
    --output-dir=. ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 编译失败，请检查上方的错误信息。
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo 编译成功！可执行文件已生成: main.exe
echo ==========================================
pause
