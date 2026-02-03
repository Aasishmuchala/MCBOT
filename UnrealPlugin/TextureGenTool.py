import unreal
import cv2
import numpy as np
from PIL import Image
import os

# --- CORE ENGINE (Adapted for Unreal) ---
# This matches the "Crazy Good" logic but simplified for direct memory usage if needed

def generate_maps_from_file(input_path):
    unreal.log(f"Processing: {input_path}")
    
    # Load
    img = cv2.imread(input_path)
    if img is None:
        unreal.log_error(f"Could not load {input_path}")
        return None
        
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img_float = img_gray.astype(np.float32) / 255.0
    
    # 1. Normal Map (Frequency Split)
    sobel_x_fine = cv2.Sobel(img_float, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y_fine = cv2.Sobel(img_float, cv2.CV_32F, 0, 1, ksize=3)
    
    blurred = cv2.GaussianBlur(img_float, (9, 9), 0)
    sobel_x_shape = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=5)
    sobel_y_shape = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=5)
    
    detail_w = 0.6
    shape_w = 0.4
    strength = 2.0
    
    sobel_x = (sobel_x_fine * detail_w) + (sobel_x_shape * shape_w)
    sobel_y = (sobel_y_fine * detail_w) + (sobel_y_shape * shape_w)
    
    sobel_x *= -strength * 4.0
    sobel_y *= -strength * 4.0
    
    z = np.ones_like(sobel_x)
    length = np.sqrt(sobel_x**2 + sobel_y**2 + z**2)
    
    nx = (sobel_x / length) * 0.5 + 0.5
    ny = (sobel_y / length) * 0.5 + 0.5
    nz = (z / length) * 0.5 + 0.5
    
    normal_map = (cv2.merge([nx, ny, nz]) * 255).astype(np.uint8)
    
    # 2. Roughness (Inverted + Contrast)
    roughness = img_float.copy()
    roughness = (roughness - 0.5) * 1.2 + 0.5 # Contrast
    roughness = 1.0 - roughness # Invert
    roughness = np.clip(roughness, 0.0, 1.0)
    roughness_map = (roughness * 255).astype(np.uint8)
    
    # 3. AO (Multi-scale)
    ao_accum = np.zeros_like(img_float)
    for r in [10, 30]:
        k = int(r) | 1
        b = cv2.GaussianBlur(img_float, (k, k), 0)
        diff = img_float - b
        valley = np.maximum(0, -diff)
        ao_accum += valley
    ao = 1.0 - (ao_accum * 1.5)
    ao = np.clip(ao, 0.0, 1.0)
    ao_map = (ao * 255).astype(np.uint8)
    
    # Save to same dir as input with suffixes
    base_path = os.path.splitext(input_path)[0]
    
    out_files = {}
    
    # Helper to save
    def save(arr, suffix, is_rgb=False):
        p = f"{base_path}_{suffix}.png"
        if is_rgb:
            Image.fromarray(arr).save(p)
        else:
            Image.fromarray(arr).convert("L").save(p)
        return p

    out_files["Normal"] = save(normal_map, "Normal", True)
    out_files["Roughness"] = save(roughness_map, "Roughness")
    out_files["AO"] = save(ao_map, "AO")
    # Base Color is just the input
    out_files["BaseColor"] = input_path 
    
    return out_files

# --- UNREAL INTEGRATION ---

@unreal.uclass()
class TextureGenAction(unreal.ToolMenuEntryScript):
    
    @unreal.ufunction(override=True)
    def execute(self, context):
        # Get Selected Assets
        utility = unreal.EditorUtilityLibrary()
        selected_assets = utility.get_selected_assets()
        
        for asset in selected_assets:
            if isinstance(asset, unreal.Texture2D):
                self.process_texture(asset)
                
    def process_texture(self, texture_asset):
        unreal.log(f"Generating PBR for: {texture_asset.get_name()}")
        
        # 1. Get Source File Path
        # Note: AssetImportData contains the path on disk
        import_data = texture_asset.get_editor_property("asset_import_data")
        source_file = import_data.get_first_filename()
        
        if not source_file or not os.path.exists(source_file):
            unreal.log_error("❌ Source file not found! Texture must be imported from disk.")
            return

        # 2. Generate Maps
        generated_files = generate_maps_from_file(source_file)
        if not generated_files:
            return
            
        # 3. Import New Maps
        asset_path = os.path.dirname(texture_asset.get_path_name())
        imported_assets = {}
        
        for map_type, file_path in generated_files.items():
            if map_type == "BaseColor": continue # Skip base color (it's the source)
            
            task = unreal.AssetImportTask()
            task.filename = file_path
            task.destination_path = asset_path
            task.destination_name = f"{texture_asset.get_name()}_{map_type}"
            task.replace_existing = True
            task.automated = True
            task.save = True
            
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            
            # Load and Setup
            new_asset = unreal.EditorAssetLibrary.load_asset(f"{asset_path}/{task.destination_name}")
            if new_asset:
                if map_type == "Normal":
                    new_asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                    new_asset.set_editor_property("srgb", False)
                elif map_type in ["Roughness", "AO", "Metallic"]:
                    new_asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                    new_asset.set_editor_property("srgb", False)
                
                # new_asset.post_edit_change() # Removed to prevent AttributeError
                unreal.EditorAssetLibrary.save_loaded_asset(new_asset)
                imported_assets[map_type] = new_asset

        # 4. Create Material
        self.create_material(texture_asset, imported_assets, asset_path)

    def create_material(self, base_tex, maps, folder):
        mat_name = f"M_{base_tex.get_name()}"
        
        # Create Basic Material
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat_factory = unreal.MaterialFactoryNew()
        mat = asset_tools.create_asset(mat_name, folder, unreal.Material, mat_factory)
        
        # Setup Material Graph
        # Note: In Python we can't easily add nodes visually, but we can creating a Material Instance 
        # is usually better IF we have a Master. But let's try to make a basic graph for "Best Ever" standalone.
        # Actually, standard practice is MI from Master.
        
        # Let's check for Master Material first.
        MASTER_PATH = "/Game/Materials/M_Master_Standard"
        master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
        
        if master:
            # Create Instance
            factory = unreal.MaterialInstanceConstantFactoryNew()
            inst = asset_tools.create_asset(f"MI_{base_tex.get_name()}", folder, unreal.MaterialInstanceConstant, factory)
            unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master)
            
            # Set Params
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst, "BaseColor", base_tex)
            for map_type, tex in maps.items():
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst, map_type, tex)
                
            unreal.log("✅ Material Instance Created!")
        else:
            unreal.log_warning(f"⚠️ Master Material not found at {MASTER_PATH}. Maps imported but material not built.")

# --- MENU REGISTRATION ---

def register_menu():
    menus = unreal.ToolMenus.get()
    
    # Add to Content Browser Context Menu for Textures
    menu = menus.find_menu("ContentBrowser.AssetContextMenu.Texture2D")
    if not menu:
        unreal.log_warning("Could not find Texture2D Context Menu")
        return
        
    entry = unreal.ToolMenuEntry(
        name="GeneratePBR",
        type=unreal.MultiBlockType.MENU_ENTRY,
        script_object=TextureGenAction()
    )
    entry.set_label("✨ Generate PBR Material")
    entry.set_tool_tip("Auto-generate Normal, Roughness, and AO from this texture.")
    
    menu.add_menu_entry("GetAssetActions", entry)
    menus.refresh_all_widgets()
    unreal.log("✅ TextureGen Pro Menu Registered!")

if __name__ == "__main__":
    register_menu()
