# TextureGen Pro

A high-fidelity PBR texture generation suite. Choose your workflow:
1. **Windows App:** Standalone dashboard with live preview.
2. **Unreal Plugin:** Right-click context menu inside UE5.

## 1. Windows App (Standalone)
**Best for:** Batch processing, visual tweaking, and artists without Unreal open.

### Installation
1. Download this repository.
2. Double-click `build_app.bat` to generate the `.exe`.
3. Open `dist/TextureGenPro.exe`.

### Usage
- Load an image.
- Adjust "Normal Strength", "Roughness", etc.
- Click **EXPORT ALL MAPS**.

---

## 2. Unreal Engine Plugin (Native)
**Best for:** Instant "Click-and-Done" inside the engine.

### Setup (One-Time)
1. **Enable Python:** In Unreal, go to **Edit -> Plugins** and enable **"Python Editor Script Plugin"**. Restart.
2. **Install Script:** Copy `UnrealPlugin/TextureGenTool.py` to your project's `Content/Python` folder. (Create the folder if it doesn't exist).
3. **Install Libs:** 
   - Open Unreal Output Log.
   - Switch cmd to **Python**.
   - Paste the code from `UnrealPlugin/install_dependencies.py` and run it. (Installs OpenCV).

### Usage
1. In Content Browser, **Right-Click** any Texture.
2. Select **"✨ Generate PBR Material"**.
3. Done. Maps and Material Instance created instantly.

*(Note: Requires a Master Material at `/Game/Materials/M_Master_Standard` with parameters: BaseColor, Normal, Roughness, AO).*
