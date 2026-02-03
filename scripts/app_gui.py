import customtkinter as ctk
import tkinter
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import threading
from texture_engine import TextureEngine  # Import our core engine

# Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class TextureApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.engine = TextureEngine()
        self.title("OpenClaw Texture Generator Pro")
        self.geometry("1200x800")
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar (Controls)
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TEXTURE GEN PRO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Load Button
        self.btn_load = ctk.CTkButton(self.sidebar, text="Load Image", command=self.load_image)
        self.btn_load.grid(row=1, column=0, padx=20, pady=10)
        
        # Sliders
        self.create_slider("Normal Strength", 0.1, 5.0, 1.0, 2)
        self.create_slider("Detail Balance", 0.0, 1.0, 0.5, 3)
        self.create_slider("Roughness Contrast", 0.5, 3.0, 1.2, 4)
        self.create_slider("AO Strength", 0.5, 3.0, 1.5, 5)
        self.create_slider("Displacement Depth", 0.1, 2.0, 1.0, 6)
        
        # Toggles
        self.chk_seamless = ctk.CTkCheckBox(self.sidebar, text="Make Seamless (Tiling)")
        self.chk_seamless.grid(row=7, column=0, padx=20, pady=20)
        
        # Export
        self.btn_export = ctk.CTkButton(self.sidebar, text="EXPORT ALL MAPS", fg_color="green", command=self.export_maps)
        self.btn_export.grid(row=8, column=0, padx=20, pady=20, sticky="s")
        
        # Right Side (Preview)
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="No Image Loaded")
        self.preview_label.pack(expand=True)
        
        # State
        self.current_image_path = None
        
    def create_slider(self, label, min_val, max_val, default, row):
        lbl = ctk.CTkLabel(self.sidebar, text=label, anchor="w")
        lbl.grid(row=row*2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        slider = ctk.CTkSlider(self.sidebar, from_=min_val, to=max_val, number_of_steps=50)
        slider.set(default)
        slider.grid(row=row*2+1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Store ref if needed later
        setattr(self, f"slider_{label.lower().replace(' ', '_')}", slider)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.tga")])
        if file_path:
            self.current_image_path = file_path
            
            # Show thumbnail
            img = Image.open(file_path)
            img.thumbnail((800, 800))
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
            
            # Auto-generate previews in background?
            # For now, just show loaded state
            print(f"Loaded {file_path}")

    def export_maps(self):
        if not self.current_image_path:
            return
            
        export_dir = filedialog.askdirectory()
        if not export_dir:
            return
            
        # Get Values
        # In a real app, pass these to the engine
        # norm_str = self.slider_normal_strength.get()
        
        # Run in thread to not freeze UI
        threading.Thread(target=self.run_generation, args=(export_dir,)).start()
        
    def run_generation(self, export_dir):
        self.btn_export.configure(text="Generating...", state="disabled")
        try:
            self.engine.process_pipeline(self.current_image_path, export_dir)
            self.btn_export.configure(text="EXPORT ALL MAPS", state="normal")
            print("Export Complete")
        except Exception as e:
            print(f"Error: {e}")
            self.btn_export.configure(text="Error!", fg_color="red")

if __name__ == "__main__":
    app = TextureApp()
    app.mainloop()
