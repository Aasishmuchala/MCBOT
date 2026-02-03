import unreal
import os
import sys

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
# Path where the app exports textures
# CHANGE THIS to your actual export folder from the Windows App
IMPORT_DIR = "C:/Users/User/Documents/TextureGen_Exports" 

# Unreal Path
DESTINATION_PATH = "/Game/AI_Generated_Materials"

# Master Material Path
# You MUST have a material at this path in Unreal Project.
# It needs Texture Parameters named: 'BaseColor', 'Normal', 'Roughness', 'Metallic', 'AO', 'Displacement'
MASTER_MATERIAL_PATH = "/Game/Materials/M_Master_Standard"

# ------------------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------------------

def create_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def get_texture_setting(name):
    """
    Returns (CompressionSettings, sRGB, ParameterName) based on filename.
    """
    s = name.lower()
    
    if any(x in s for x in ["basecolor", "albedo", "diffuse", "color"]):
        return (unreal.TextureCompressionSettings.TC_DEFAULT, True, "BaseColor")
        
    elif "normal" in s:
        return (unreal.TextureCompressionSettings.TC_NORMALMAP, False, "Normal")
        
    elif "roughness" in s:
        return (unreal.TextureCompressionSettings.TC_MASKS, False, "Roughness")
        
    elif "metallic" in s or "metalness" in s:
        return (unreal.TextureCompressionSettings.TC_MASKS, False, "Metallic")
        
    elif "ao" in s or "ambient" in s or "occlusion" in s:
        return (unreal.TextureCompressionSettings.TC_MASKS, False, "AO")
        
    elif "height" in s or "displacement" in s:
        return (unreal.TextureCompressionSettings.TC_GRAYSCALE, False, "Displacement")
        
    return (unreal.TextureCompressionSettings.TC_DEFAULT, True, None)

def import_texture(file_path, dest_path):
    name = os.path.splitext(os.path.basename(file_path))[0]
    task = unreal.AssetImportTask()
    task.filename = file_path
    task.destination_path = dest_path
    task.destination_name = name
    task.replace_existing = True
    task.automated = True
    task.save = True

    factory = unreal.TextureFactory()
    task.factory = factory
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])
    
    # Post-Import Setup (Compression/sRGB)
    asset_path = f"{dest_path}/{name}"
    texture = unreal.EditorAssetLibrary.load_asset(asset_path)
    
    if texture:
        compression, srgb, param_name = get_texture_setting(name)
        
        texture.compression_settings = compression
        texture.srgb = srgb
        texture.post_edit_change() # Apply changes
        unreal.EditorAssetLibrary.save_asset(asset_path)
        
        return texture, param_name
    
    return None, None

def create_material_instance(name, folder, textures):
    # Check for Master Material
    master_mat = unreal.EditorAssetLibrary.load_asset(MASTER_MATERIAL_PATH)
    if not master_mat:
        unreal.log_error(f"❌ ERROR: Master Material not found at {MASTER_MATERIAL_PATH}")
        unreal.log_error("Please create a Material in Unreal at that path with Texture Parameters.")
        return

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mic_name = f"MI_{name}"
    mic_path = f"{folder}/{mic_name}"
    
    # Check if exists
    if unreal.EditorAssetLibrary.does_asset_exist(mic_path):
        mic_asset = unreal.EditorAssetLibrary.load_asset(mic_path)
    else:
        # Create MIC
        mic_factory = unreal.MaterialInstanceConstantFactoryNew()
        mic_asset = asset_tools.create_asset(mic_name, folder, unreal.MaterialInstanceConstant, mic_factory)
    
    unreal.MaterialEditingLibrary.set_material_instance_parent(mic_asset, master_mat)
    
    # Connect Textures
    connected_count = 0
    for tex_asset, param_name in textures:
        if param_name:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mic_asset, param_name, tex_asset
            )
            connected_count += 1
            
    unreal.EditorAssetLibrary.save_asset(mic_asset.get_path_name())
    unreal.log(f"✅ SUCCESS: Created Material Instance '{mic_name}' with {connected_count} textures.")

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

def run_pipeline():
    if not os.path.exists(IMPORT_DIR):
        unreal.log_warning(f"Import directory {IMPORT_DIR} does not exist. Please edit the script configuration.")
        return

    # Group files by 'Material Name' 
    # Logic: "MyTexture_Albedo.png" -> Group "MyTexture"
    groups = {}
    
    for fname in os.listdir(IMPORT_DIR):
        if fname.lower().endswith(('.png', '.jpg', '.tga', '.exr')):
            # Split by last underscore to find base name
            # e.g. "Wood_Table_Albedo.png" -> "Wood_Table"
            if "_" in fname:
                base_name = fname.rsplit('_', 1)[0]
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append(os.path.join(IMPORT_DIR, fname))

    create_directory(DESTINATION_PATH)

    for mat_name, files in groups.items():
        unreal.log(f"Processing Material Group: {mat_name} ({len(files)} files)")
        
        imported_textures = []
        mat_folder = f"{DESTINATION_PATH}/{mat_name}"
        create_directory(mat_folder)
        
        for f in files:
            tex, param = import_texture(f, mat_folder)
            if tex:
                imported_textures.append((tex, param))
        
        if imported_textures:
            create_material_instance(mat_name, mat_folder, imported_textures)

if __name__ == "__main__":
    run_pipeline()
