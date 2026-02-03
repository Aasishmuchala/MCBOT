import cv2
import numpy as np
from PIL import Image

class TextureEngine:
    """
    High-Fidelity PBR Texture Generation Engine.
    Uses frequency separation and multi-scale analysis for "Crazy Good" results.
    """
    
    def __init__(self):
        pass

    def _load_image_as_float(self, image_path):
        """Loads image, converts to 0-1 float, handles high-res."""
        # OpenCV loads as BGR. Convert to RGB.
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img.astype(np.float32) / 255.0

    def _to_grayscale(self, img_rgb):
        """Perceptual luminance conversion."""
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    def delight_albedo(self, img_rgb, shadow_strength=0.5, highlight_strength=0.8):
        """
        Removes baked-in shadows and highlights to create a pure Albedo map.
        Uses a high-pass frequency method to equalize luminance.
        """
        # 1. Convert to LAB color space to separate Luminance
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l_channel, a, b = cv2.split(lab)

        # 2. Estimate the "Lighting Field" (Low Frequency Luminance)
        # We use a massive blur to find the overall light gradient
        h, w = l_channel.shape[:2]
        kernel_size = int(min(h, w) * 0.05) | 1 # ~5% of image size, odd number
        lighting_field = cv2.GaussianBlur(l_channel, (kernel_size, kernel_size), 0)

        # 3. Flatten the lighting (High Pass)
        # Result = L / Lighting * Average_L
        avg_l = np.mean(l_channel)
        delighted_l = (l_channel / (lighting_field + 1e-6)) * avg_l
        
        # 4. Blend back based on strength (don't over-flatten)
        final_l = cv2.addWeighted(l_channel, 1.0 - shadow_strength, delighted_l, shadow_strength, 0)
        
        # 5. Recombine
        merged = cv2.merge([final_l, a, b])
        delighted_rgb = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
        
        return np.clip(delighted_rgb, 0.0, 1.0)

    def generate_normal_map(self, img_gray, strength=1.0, detail_weight=0.6, shape_weight=0.4):
        """
        Generates a high-quality normal map using Frequency Separation.
        Combines fine details (pores) and large shapes (structure) separately.
        """
        # Frequency Separation
        # 1. Micro-Details (High Freq)
        # Sobel on raw image captures noise and pores
        sobel_x_fine = cv2.Sobel(img_gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y_fine = cv2.Sobel(img_gray, cv2.CV_32F, 0, 1, ksize=3)
        
        # 2. Macro-Structure (Low Freq)
        # Blur first, then Sobel to capture big slopes without noise
        blurred = cv2.GaussianBlur(img_gray, (9, 9), 0)
        sobel_x_shape = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=5)
        sobel_y_shape = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=5)
        
        # 3. Blend Frequencies
        sobel_x = (sobel_x_fine * detail_weight) + (sobel_x_shape * shape_weight)
        sobel_y = (sobel_y_fine * detail_weight) + (sobel_y_shape * shape_weight)
        
        # Apply Global Strength
        sobel_x *= -strength * 4.0 # Boost factor for visibility
        sobel_y *= -strength * 4.0
        
        # 4. Construct Vectors
        # Normal = normalize(x, y, 1.0)
        z = np.ones_like(sobel_x)
        length = np.sqrt(sobel_x**2 + sobel_y**2 + z**2)
        
        nx = (sobel_x / length) * 0.5 + 0.5
        ny = (sobel_y / length) * 0.5 + 0.5
        nz = (z / length) * 0.5 + 0.5
        
        normal_map = cv2.merge([nx, ny, nz])
        return np.clip(normal_map, 0.0, 1.0)

    def generate_roughness_map(self, img_gray, contrast=1.2, brightness=0.0, invert=True):
        """
        Smart Roughness. Detects edges to make cracks/crevices rougher (or shinier).
        """
        # 1. Curvature Detection (Edges often behave differently than flat surfaces)
        laplacian = cv2.Laplacian(img_gray, cv2.CV_32F)
        curvature = np.abs(laplacian)
        
        # 2. Base Roughness from Luminance (Darker = Smoother usually, or vice versa)
        roughness = img_gray.copy()
        
        # 3. Mix Curvature (Edges are usually rougher/dustier)
        roughness = roughness + (curvature * 0.3)
        
        # 4. Contrast/Brightness Curve
        roughness = (roughness - 0.5) * contrast + 0.5 + brightness
        
        # 5. Invert? (White = Rough, Black = Smooth)
        if invert:
            roughness = 1.0 - roughness
            
        return np.clip(roughness, 0.0, 1.0)

    def generate_ao_map(self, img_gray, radius=20, strength=1.5):
        """
        Screen-Space Ambient Occlusion (SSAO) approx using Multi-Scale Blurring.
        Darkens crevices.
        """
        # Invert image (0=Deep, 1=High)
        height = img_gray.copy()
        
        # High-pass approach for AO:
        # The difference between the pixel and the local average tells us if it's a valley.
        # If Pixel < Average, it's a valley -> Occluded.
        
        ao_accum = np.zeros_like(img_gray)
        
        # Multi-scale loop
        for r in [radius * 0.5, radius, radius * 2.0]:
            k = int(r) | 1
            blurred = cv2.GaussianBlur(height, (k, k), 0)
            # Difference: Positive if pixel is higher than average (Peak), Negative if lower (Valley)
            diff = height - blurred
            # We only care about Valleys (negative diff)
            valley_mask = np.maximum(0, -diff)
            ao_accum += valley_mask
            
        # Normalize
        ao = 1.0 - (ao_accum * strength)
        return np.clip(ao, 0.0, 1.0)

    def generate_height_map(self, img_gray, low_freq_boost=True):
        """
        Displacement map.
        Needs to emphasize large shapes over fine noise to prevent "spiky" meshes.
        """
        if low_freq_boost:
            # Boost low frequencies to give "body" to the displacement
            blurred = cv2.GaussianBlur(img_gray, (31, 31), 0)
            height = cv2.addWeighted(img_gray, 0.4, blurred, 0.6, 0)
        else:
            height = img_gray
            
        return np.clip(height, 0.0, 1.0)

    def process_pipeline(self, image_path, output_dir="."):
        """Runs the full suite."""
        print(f"Loading {image_path}...")
        raw_img = self._load_image_as_float(image_path)
        
        # 1. Delighting (Create Base Color)
        print("Delighting Albedo...")
        albedo = self.delight_albedo(raw_img)
        
        # 2. Grayscale conversion for data maps
        gray = self._to_grayscale(raw_img) # Use original detail for data maps
        
        # 3. Generate Maps
        print("Generating Normals...")
        normal = self.generate_normal_map(gray)
        print("Generating Roughness...")
        rough = self.generate_roughness_map(gray)
        print("Generating AO...")
        ao = self.generate_ao_map(gray)
        print("Generating Height...")
        height = self.generate_height_map(gray)
        
        # 4. Save
        import os
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        self._save(albedo, f"{output_dir}/{base_name}_Albedo.png")
        self._save(normal, f"{output_dir}/{base_name}_Normal.png")
        self._save(rough, f"{output_dir}/{base_name}_Roughness.png", is_gray=True)
        self._save(ao, f"{output_dir}/{base_name}_AO.png", is_gray=True)
        self._save(height, f"{output_dir}/{base_name}_Displacement.png", is_gray=True)
        print("Done.")

    def _save(self, img_float, path, is_gray=False):
        img_uint8 = (img_float * 255).astype(np.uint8)
        if is_gray:
            Image.fromarray(img_uint8).save(path)
        else:
            Image.fromarray(img_uint8).save(path)

# Self-test
if __name__ == "__main__":
    engine = TextureEngine()
    # Assuming test image exists from previous turn
    if os.path.exists("input_images/test_texture.jpg"):
        engine.process_pipeline("input_images/test_texture.jpg", "generated_maps")
