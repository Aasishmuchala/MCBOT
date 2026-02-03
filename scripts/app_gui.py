import customtkinter as ctk
import tkinter
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import os
import threading
import time
from texture_engine import TextureEngine

# Set Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class TextureApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.engine = TextureEngine()
        self.title("TextureGen Pro | Industry Standard PBR")
        self.geometry("1400x900")
        
        # Grid Config
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0) # Right panel
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # Status bar

        # --- LEFT SIDEBAR (Controls) ---
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Header
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TEXTURE GEN PRO", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=(20, 10), padx=20)
        
        self.version_label = ctk.CTkLabel(self.sidebar, text="v2.0.0 (Build 2026)", text_color="gray")
        self.version_label.pack(pady=(0, 20))
        
        # Tabs
        self.tabview = ctk.CTkTabview(self.sidebar, width=300)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tab_gen = self.tabview.add("Generation")
        self.tab_export = self.tabview.add("Export")
        
        # -- GENERATION TAB --
        # Load Button
        self.btn_load = ctk.CTkButton(self.tab_gen, text="📥 Load Source Image", height=40, font=ctk.CTkFont(weight="bold"), command=self.load_image)
        self.btn_load.pack(pady=10, padx=10, fill="x")
        
        self.add_separator(self.tab_gen, "Map Settings")
        
        # Sliders
        self.sliders = {}
        self.create_slider(self.tab_gen, "Normal Intensity", 0.1, 5.0, 1.0)
        self.create_slider(self.tab_gen, "Micro Detail", 0.0, 1.0, 0.6)
        self.create_slider(self.tab_gen, "Roughness Contrast", 0.5, 3.0, 1.2)
        self.create_slider(self.tab_gen, "AO Radius", 10, 100, 30)
        self.create_slider(self.tab_gen, "Displacement Height", 0.1, 2.0, 1.0)
        
        self.chk_seamless = ctk.CTkCheckBox(self.tab_gen, text="Seamless Tiling (AI Fix)")
        self.chk_seamless.pack(pady=20, padx=10, anchor="w")
        
        # -- EXPORT TAB --
        self.add_separator(self.tab_export, "Output Configuration")
        
        self.lbl_export_path = ctk.CTkLabel(self.tab_export, text="No folder selected", text_color="gray")
        self.lbl_export_path.pack(pady=5)
        
        self.btn_select_folder = ctk.CTkButton(self.tab_export, text="📂 Select Output Folder", command=self.select_export_folder)
        self.btn_select_folder.pack(pady=5, fill="x")
        
        self.combo_format = ctk.CTkComboBox(self.tab_export, values=["PNG (Lossless)", "TGA (Unreal)", "JPG (Compact)"])
        self.combo_format.pack(pady=10, fill="x")
        self.combo_format.set("PNG (Lossless)")
        
        # Big Export Button
        self.btn_export = ctk.CTkButton(self.sidebar, text="🚀 EXPORT ALL MAPS", height=50, fg_color="#2ecc71", hover_color="#27ae60", font=ctk.CTkFont(size=16, weight="bold"), command=self.export_maps)
        self.btn_export.pack(pady=20, padx=20, fill="x", side="bottom")

        # --- CENTER (Viewport) ---
        self.viewport_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.viewport_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.viewport_label = ctk.CTkLabel(self.viewport_frame, text="2D PREVIEW", font=ctk.CTkFont(size=16))
        self.viewport_label.pack(pady=10)
        
        self.image_preview = ctk.CTkLabel(self.viewport_frame, text="[ Drop Image Here ]")
        self.image_preview.pack(expand=True, fill="both", padx=10, pady=10)

        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", anchor="w")
        self.status_label.pack(side="left", padx=10)

        # State
        self.current_image_path = None
        self.export_dir = None
        
    def add_separator(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        lbl.pack(pady=(15, 5), padx=5, anchor="w")
        
    def create_slider(self, parent, label, min_val, max_val, default):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=5)
        
        lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11))
        lbl.pack(anchor="w")
        
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, number_of_steps=100)
        slider.set(default)
        slider.pack(fill="x", pady=2)
        
        self.sliders[label] = slider

    def set_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)
        self.update_idletasks()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.tga")])
        if file_path:
            self.current_image_path = file_path
            self.set_status(f"Loaded: {os.path.basename(file_path)}")
            
            # Display Image
            try:
                pil_img = Image.open(file_path)
                # Resize for preview (keep aspect ratio)
                pil_img.thumbnail((1000, 800))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                
                self.image_preview.configure(image=ctk_img, text="")
                self.title(f"TextureGen Pro - {os.path.basename(file_path)}")
            except Exception as e:
                self.set_status(f"Error loading image: {e}", "red")

    def select_export_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.export_dir = path
            self.lbl_export_path.configure(text=f".../{os.path.basename(path)}")

    def export_maps(self):
        if not self.current_image_path:
            self.set_status("⚠️ No image loaded!", "orange")
            return
            
        target_dir = self.export_dir if self.export_dir else os.path.dirname(self.current_image_path)
        
        # Thread generation
        threading.Thread(target=self.run_generation, args=(target_dir,)).start()

    def run_generation(self, export_dir):
        self.btn_export.configure(state="disabled", text="Generating...")
        self.set_status("⏳ Generating Maps (High Fidelity)...", "#3498db")
        
        start_time = time.time()
        try:
            # Pass slider values to engine (future: update engine to accept these params dynamically)
            # For now, we use the default rigorous engine
            self.engine.process_pipeline(self.current_image_path, export_dir)
            
            elapsed = time.time() - start_time
            self.set_status(f"✅ Success! Generated 5 maps in {elapsed:.2f}s", "#2ecc71")
            
        except Exception as e:
            self.set_status(f"❌ Generation Failed: {e}", "red")
            print(e)
            
        self.btn_export.configure(state="normal", text="🚀 EXPORT ALL MAPS")

if __name__ == "__main__":
    app = TextureApp()
    app.mainloop()
