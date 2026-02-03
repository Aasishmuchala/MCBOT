@echo off
echo ===================================================
echo   Building TextureGen Pro for Windows
echo ===================================================

echo [1/3] Installing Build Tools...
pip install -r requirements_app.txt

echo.
echo [2/3] Compiling to .EXE (This may take a minute)...
pyinstaller --noconfirm --onefile --windowed --name "TextureGenPro" --add-data "scripts/texture_engine.py;." --hidden-import "PIL._tkinter_finder"  scripts/app_gui.py

echo.
echo [3/3] Cleanup...
rmdir /s /q build
del TextureGenPro.spec

echo.
echo ===================================================
echo   SUCCESS! 
echo   Your app is ready at: dist\TextureGenPro.exe
echo ===================================================
pause
