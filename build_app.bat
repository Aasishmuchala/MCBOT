@echo off
echo ===================================================
echo   Building TextureGen Pro for Windows
echo ===================================================

echo [1/3] Installing Build Tools...
python -m pip install -r requirements_app.txt

echo.
echo [2/3] Compiling to .EXE (This may take a minute)...
:: Using python -m PyInstaller is safer on Windows (avoids PATH issues)
python -m PyInstaller --noconfirm --onefile --windowed --name "TextureGenPro" --add-data "scripts/texture_engine.py;." --hidden-import "PIL._tkinter_finder"  scripts/app_gui.py

echo.
echo [3/3] Cleanup...
if exist build rmdir /s /q build
if exist TextureGenPro.spec del TextureGenPro.spec

echo.
echo ===================================================
echo   SUCCESS! 
echo   Your app is ready at: dist\TextureGenPro.exe
echo ===================================================
pause
