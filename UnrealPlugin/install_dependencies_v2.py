import unreal
import sys
import subprocess
import os

def install_libs_safe():
    unreal.log("==========================================")
    unreal.log("   Sthyra Toolset Dependency Installer    ")
    unreal.log("==========================================")

    # 1. Locate the Python Binary specifically (not the Editor)
    # Inside UE5, sys.executable often points to UnrealEditor.exe. We need python.exe.
    
    # Common path pattern: Engine/Binaries/ThirdParty/Python3/Win64/python.exe
    # We can deduce it from sys.base_prefix
    
    python_home = sys.base_prefix
    possible_exes = [
        os.path.join(python_home, "bin", "python.exe"),
        os.path.join(python_home, "python.exe"),
        os.path.join(python_home, "Scripts", "python.exe"),
    ]
    
    target_exe = None
    for p in possible_exes:
        if os.path.exists(p):
            target_exe = p
            break
            
    if not target_exe:
        # Fallback: try calling 'python' from the scripts folder directly if we are in it
        unreal.log_warning("⚠️ Could not find exact python.exe path. Using sys.executable (might spawn window).")
        target_exe = sys.executable

    unreal.log(f"Target Python: {target_exe}")

    # 2. Install Packages
    pkgs = ["opencv-python", "numpy", "Pillow"]
    
    for pkg in pkgs:
        unreal.log(f"Installing {pkg}...")
        
        # Use STARTUPINFO to hide the window on Windows
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            # We run pip as a module (-m pip)
            process = subprocess.Popen(
                [target_exe, "-m", "pip", "install", pkg, "--upgrade", "--no-warn-script-location"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=si # Hides the window
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                unreal.log(f"✅ {pkg} INSTALLED.")
            else:
                unreal.log_error(f"❌ Failed to install {pkg}.\nOutput: {stdout}\nError: {stderr}")
                
        except Exception as e:
            unreal.log_error(f"❌ Exception during install of {pkg}: {e}")

    unreal.log("==========================================")
    unreal.log("   Installation Complete. Please Restart. ")
    unreal.log("==========================================")

if __name__ == "__main__":
    install_libs_safe()
