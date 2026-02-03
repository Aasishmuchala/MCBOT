import os
import sys
import numpy as np
import cv2
from PIL import Image

def check_dependencies():
    print("Checking dependencies...")
    try:
        import customtkinter
        import OpenGL
        import glfw
        import glm
        print("✅ GUI libs (customtkinter, pyopengl, glfw, glm) installed.")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    
    try:
        import cv2
        import numpy
        import PIL
        print("✅ Core libs (opencv, numpy, pillow) installed.")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    return True

def check_engine_integrity():
    print("\nChecking Texture Engine logic...")
    try:
        from texture_engine import TextureEngine
        engine = TextureEngine()
        
        # Create a dummy 256x256 gray image
        dummy = np.random.rand(256, 256).astype(np.float32)
        
        # Test methods
        n = engine.generate_normal_map(dummy)
        if n.shape != (256, 256, 3): 
            print("❌ Normal map shape mismatch")
            return False
            
        r = engine.generate_roughness_map(dummy)
        if r.shape != (256, 256):
            print("❌ Roughness map shape mismatch")
            return False
            
        print("✅ Engine logic passed sanity checks.")
        return True
    except Exception as e:
        print(f"❌ Engine failed: {e}")
        return False

def check_files():
    print("\nChecking file structure...")
    required = [
        "scripts/app_gui.py",
        "scripts/texture_engine.py",
        "scripts/unreal_importer.py"
    ]
    all_good = True
    for f in required:
        if os.path.exists(f):
            print(f"✅ Found {f}")
        else:
            print(f"❌ Missing {f}")
            all_good = False
    return all_good

if __name__ == "__main__":
    print("=== SYSTEM HEALTH CHECK ===")
    deps = check_dependencies()
    eng = check_engine_integrity()
    files = check_files()
    
    if deps and eng and files:
        print("\n🎉 ALL SYSTEMS GO. You can launch the app.")
        sys.exit(0)
    else:
        print("\n⚠️ ISSUES DETECTED. See above.")
        sys.exit(1)
