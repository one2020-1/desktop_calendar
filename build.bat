@echo off
echo ============================================
echo    Geek Calendar - Build Script
echo ============================================
echo.

echo [1/3] Installing PyInstaller and dependencies...
echo.

echo Trying mirror 1: Aliyun ...
python -m pip install pyinstaller PyQt5 lunar-python -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if not errorlevel 1 goto INSTALL_OK

echo.
echo Trying mirror 2: Tencent ...
python -m pip install pyinstaller PyQt5 lunar-python -i https://mirrors.cloud.tencent.com/pypi/simple/ --trusted-host mirrors.cloud.tencent.com
if not errorlevel 1 goto INSTALL_OK

echo.
echo Trying mirror 3: Tsinghua ...
python -m pip install pyinstaller PyQt5 lunar-python -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
if not errorlevel 1 goto INSTALL_OK

echo.
echo Trying official PyPI ...
python -m pip install pyinstaller PyQt5 lunar-python
if not errorlevel 1 goto INSTALL_OK

echo.
echo [ERROR] All mirrors failed. Please check your network/proxy/VPN settings.
pause
exit /b 1

:INSTALL_OK
echo.
echo [OK] Dependencies installed.

echo.
echo [2/4] Cleaning previous build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "GeekCalendar.spec" del /q "GeekCalendar.spec"
echo       Done.

echo.
echo [3/4] Generating EXE icon...
python generate_icon.py
if not exist "icon.ico" (
    echo [WARN] icon.ico not generated, will build without custom icon.
    set ICON_OPT=
) else (
    echo       Done.
    set ICON_OPT=--icon=icon.ico
)

echo.
echo [4/4] Building EXE, please wait 1-3 minutes...
echo ============================================
echo.

python -m PyInstaller --noconfirm --onefile --windowed --name "GeekCalendar" %ICON_OPT% --hidden-import winreg --collect-all lunar_python desktop_calendar.py

echo.
echo ============================================
if exist "dist\GeekCalendar.exe" (
    echo    [OK] Build Success!
    echo ============================================
    echo.
    echo    EXE Path:
    echo    %CD%\dist\GeekCalendar.exe
    echo.
    echo    Just double-click the exe to run, no Python needed.
    echo.
    explorer "dist"
) else (
    echo    [FAIL] Build failed. Please send the error log above.
    echo ============================================
)

pause
