import unreal
import os
import sys

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
# Path where the external AI pipeline dumps the generated textures
# (We will watch this folder or call this script pointing to files here)
IMPORT_DIR = "/Users/aasishmuchala/.openclaw/workspace/generated_maps" 

# Unreal Destination Path
DESTINATION_PATH = "/Game/AI_Generated_Materials"

# Master Material Path (Must exist in project!)
# It should have Texture Parameters named: 'BaseColor', 'Normal', 'Roughness', 'Metallic', 'AO'
MASTER_MATERIAL_PATH = "/Game/Materials/M_Master_Standard"

# ------------------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------------------

def create_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def get_texture_setting(suffix):
    """
    Returns (CompressionSettings, sRGB, ParameterName) based on filename suffix.
    """
    s = suffix.lower()
    
    if "basecolor" in s or "albedo" in s or "diffuse" in s:
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
        return (unreal.TextureCompressionSettings.TC_GRAYSCALE, False, "Height")
        
    return (unreal.TextureCompressionSettings.TC_DEFAULT, True, "Unknown")

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
        suffix = name.split('_')[-1] # Assuming name format: MyMat_BaseColor
        compression, srgb, param_name = get_texture_setting(suffix)
        
        texture.compression_settings = compression
        texture.srgb = srgb
        texture.post_edit_change() # Apply changes
        unreal.EditorAssetLibrary.save_asset(asset_path)
        
        return texture, param_name
    
    return None, None

def create_material_instance(name, folder, textures):
    master_mat = unreal.EditorAssetLibrary.load_asset(MASTER_MATERIAL_PATH)
    if not master_mat:
        unreal.log_error(f"Master Material not found at {MASTER_MATERIAL_PATH}")
        return

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mic_name = f"MI_{name}"
    
    # Create MIC
    mic_factory = unreal.MaterialInstanceConstantFactoryNew()
    mic_asset = asset_tools.create_asset(mic_name, folder, unreal.MaterialInstanceConstant, mic_factory)
    
    unreal.MaterialEditingLibrary.set_material_instance_parent(mic_asset, master_mat)
    
    # Connect Textures
    for tex_asset, param_name in textures:
        if param_name and param_name != "Unknown":
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mic_asset, param_name, tex_asset
            )
            
    unreal.EditorAssetLibrary.save_asset(mic_asset.get_path_name())
    unreal.log(f"Created Material Instance: {mic_asset.get_path_name()}")

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
# Example usage: Call this with a list of file paths from the generator
# For now, let's assume we scan the IMPORT_DIR

def run_pipeline():
    if not os.path.exists(IMPORT_DIR):
        unreal.log_warning(f"Import directory {IMPORT_DIR} does not exist.")
        return

    # Group files by 'Material Name' (prefix before the last underscore)
    # Example: 'Wood_01_BaseColor.png' -> Group 'Wood_01'
    
    groups = {}
    
    for fname in os.listdir(IMPORT_DIR):
        if fname.lower().endswith(('.png', '.jpg', '.tga', '.exr')):
            name_parts = os.path.splitext(fname)[0].split('_')
            if len(name_parts) > 1:
                mat_name = "_".join(name_parts[:-1])
                if mat_name not in groups:
                    groups[mat_name] = []
                groups[mat_name].append(os.path.join(IMPORT_DIR, fname))

    create_directory(DESTINATION_PATH)

    for mat_name, files in groups.items():
        unreal.log(f"Processing Material: {mat_name}")
        
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
