import unreal
import subprocess
import sys
import os

def install_libs():
    # Get the python executable used by Unreal
    # Usually located in Engine/Binaries/ThirdParty/Python3...
    python_exe = sys.executable
    
    unreal.log(f"Installing dependencies to: {python_exe}")
    
    # We need opencv-python and numpy
    # Note: Unreal's python can be tricky with binary extensions, but opencv usually works if ABI matches.
    # We use --target to install into the script folder if site-packages is locked, 
    # but standard install is better if allowed.
    
    pkgs = ["opencv-python", "numpy", "Pillow"]
    
    for pkg in pkgs:
        unreal.log(f"Installing {pkg}...")
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", pkg, "--upgrade"])
            unreal.log(f"✅ {pkg} installed successfully.")
        except Exception as e:
            unreal.log_error(f"❌ Failed to install {pkg}: {e}")

if __name__ == "__main__":
    install_libs()
