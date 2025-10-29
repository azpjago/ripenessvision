import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import requests
from serpapi import GoogleSearch
from time import sleep
from PIL import Image, ImageStat
from io import BytesIO
import urllib3
import warnings
import colorsys
from datetime import datetime

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Training Data Downloader")
        self.root.geometry("900x700")  # Ukuran lebih kecil
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.is_downloading = False
        self.download_thread = None
        
        self.setup_gui()
    
    def setup_gui(self):
        # Create main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title - lebih kecil
        title_label = ttk.Label(scrollable_frame, text="🚀 AI Training Data Downloader", 
                               font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # === CONFIGURATION SECTION ===
        config_frame = ttk.LabelFrame(scrollable_frame, text="📋 Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # API Key - lebih compact
        ttk.Label(config_frame, text="SerpAPI Key:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.api_key = tk.StringVar()
        api_entry = ttk.Entry(config_frame, textvariable=self.api_key, width=40, font=('Arial', 9))
        api_entry.grid(row=0, column=1, pady=3, padx=(5, 0), sticky=(tk.W, tk.E))
        ttk.Button(config_frame, text="Get Key", command=self.open_serpapi_website, width=8).grid(row=0, column=2, padx=(5, 0))
        
        # Output Directory
        ttk.Label(config_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.output_dir = tk.StringVar(value="training_data")
        ttk.Entry(config_frame, textvariable=self.output_dir, width=30, font=('Arial', 9)).grid(row=1, column=1, pady=3, padx=(5, 0), sticky=(tk.W, tk.E))
        ttk.Button(config_frame, text="Browse", command=self.browse_folder, width=8).grid(row=1, column=2, padx=(5, 0))
        
        config_frame.columnconfigure(1, weight=1)
        
        # === SEARCH PARAMETERS SECTION ===
        search_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Search Parameters", padding="10")
        search_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Object Type - satu baris
        ttk.Label(search_frame, text="Object:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.object_type = tk.StringVar(value="banana")
        object_combo = ttk.Combobox(search_frame, textvariable=self.object_type, 
                                   values=["banana", "mango", "tomato", "apple", "orange", "custom"],
                                   state="readonly", width=12, font=('Arial', 9))
        object_combo.grid(row=0, column=1, pady=3, padx=(5, 0), sticky=tk.W)
        object_combo.bind('<<ComboboxSelected>>', self.on_object_change)
        
        # Custom Object Type
        ttk.Label(search_frame, text="Custom:").grid(row=0, column=2, sticky=tk.W, pady=3, padx=(10, 0))
        self.custom_object = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.custom_object, width=15, font=('Arial', 9)).grid(row=0, column=3, pady=3, padx=(5, 0))
        
        # Categories/Stages - lebih compact
        ttk.Label(search_frame, text="Categories:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.categories_frame = ttk.Frame(search_frame)
        self.categories_frame.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=3, padx=(5, 0))
        
        self.category_vars = {}
        default_categories = ["unripe", "ripe", "overripe", "fresh", "rotten"]
        for i, cat in enumerate(default_categories):
            var = tk.BooleanVar(value=(cat in ["unripe", "ripe", "overripe"]))
            self.category_vars[cat] = var
            ttk.Checkbutton(self.categories_frame, text=cat, variable=var).grid(row=0, column=i, padx=(0, 8))
        
        # Custom Category
        ttk.Label(search_frame, text="Custom Cats:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.custom_categories = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.custom_categories, width=25, font=('Arial', 9)).grid(row=2, column=1, columnspan=2, pady=3, padx=(5, 0), sticky=(tk.W, tk.E))
        ttk.Label(search_frame, text="(use commas)").grid(row=2, column=3, sticky=tk.W, pady=3, padx=(5, 0))
        
        # Images per Category
        ttk.Label(search_frame, text="Images/Cat:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.images_per_category = tk.IntVar(value=50)
        ttk.Spinbox(search_frame, from_=10, to=500, textvariable=self.images_per_category, width=8).grid(row=3, column=1, pady=3, padx=(5, 0))
        
        search_frame.columnconfigure(1, weight=1)
        
        # === FILTER OPTIONS SECTION ===
        filter_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Filter Options", padding="10")
        filter_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Baris 1 - Size dan Filter
        ttk.Label(filter_frame, text="Min Size:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.min_size = tk.StringVar(value="400x400")
        size_combo = ttk.Combobox(filter_frame, textvariable=self.min_size,
                                 values=["200x200", "400x400", "600x600", "800x800"],
                                 state="readonly", width=8)
        size_combo.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        self.use_color_filter = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Color Filter", variable=self.use_color_filter).grid(row=0, column=2, pady=2, padx=(10, 0))
        
        self.safe_search = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Safe Search", variable=self.safe_search).grid(row=0, column=3, pady=2, padx=(10, 0))
        
        # Baris 2 - Type dan Delay
        ttk.Label(filter_frame, text="Image Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.image_type = tk.StringVar(value="photo")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.image_type,
                                 values=["photo", "clipart", "lineart", "face"],
                                 state="readonly", width=8)
        type_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(filter_frame, text="Delay:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.download_delay = tk.DoubleVar(value=0.5)
        ttk.Spinbox(filter_frame, from_=0.1, to=5.0, increment=0.1, 
                   textvariable=self.download_delay, width=6).grid(row=1, column=3, pady=2, padx=(5, 0))
        
        # === TOMBOL CONTROL ===
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Tombol START yang jelas
        self.start_button = ttk.Button(
            button_frame, 
            text="🚀 START DOWNLOAD", 
            command=self.start_download,
            width=20
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹️ STOP", 
            command=self.stop_download, 
            state='disabled',
            width=10
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame, 
            text="🧹 Clear Log", 
            command=self.clear_log,
            width=10
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame, 
            text="📂 Open Folder", 
            command=self.open_output_folder,
            width=10
        ).grid(row=0, column=3, padx=5)
        
        # === PROGRESS SECTION ===
        progress_frame = ttk.LabelFrame(scrollable_frame, text="📊 Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress bars compact
        ttk.Label(progress_frame, text="Overall:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.overall_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.overall_progress.grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(progress_frame, text="Current:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.current_progress.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        # Status labels compact
        self.overall_status = ttk.Label(progress_frame, text="Ready to start...", font=('Arial', 9))
        self.overall_status.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=3)
        
        self.current_status = ttk.Label(progress_frame, text="", font=('Arial', 8))
        self.current_status.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=1)
        
        self.stats_label = ttk.Label(progress_frame, text="", font=('Arial', 8, 'bold'))
        self.stats_label.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=1)
        
        # Log area - lebih kecil
        ttk.Label(progress_frame, text="Log:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(8, 2))
        
        log_frame = ttk.Frame(progress_frame)
        log_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)
        
        self.log_text = tk.Text(log_frame, height=6, width=70, font=('Consolas', 8))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Configure grid weights untuk responsive layout
        scrollable_frame.columnconfigure(0, weight=1)
        progress_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Initialize
        self.log("🌟 AI Training Data Downloader Ready!")
        self.log("➡️ Configure parameters and click START DOWNLOAD")
        self.log("➡️ Get API key from: https://serpapi.com")
    
    def on_object_change(self, event):
        if self.object_type.get() == "custom":
            self.custom_object.set("")
            self.custom_object.focus()
        else:
            self.custom_object.set("")
    
    def open_serpapi_website(self):
        import webbrowser
        webbrowser.open("https://serpapi.com")
        self.log("🌐 Opening SerpAPI website...")
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)
            self.log(f"📁 Output folder: {folder}")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared - Ready for new download")
    
    def open_output_folder(self):
        output_path = self.output_dir.get()
        if os.path.exists(output_path):
            try:
                os.startfile(output_path)
                self.log(f"📂 Opened: {output_path}")
            except:
                self.log("❌ Could not open folder")
        else:
            messagebox.showwarning("Warning", "Output folder doesn't exist yet!")
    
    def start_download(self):
        # Validasi input
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter your SerpAPI key!\nGet free key from: https://serpapi.com")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select output directory!")
            return
        
        # Get selected categories
        categories = []
        for cat, var in self.category_vars.items():
            if var.get():
                categories.append(cat)
        
        # Add custom categories
        custom_cats = [cat.strip() for cat in self.custom_categories.get().split(',') if cat.strip()]
        categories.extend(custom_cats)
        
        if not categories:
            messagebox.showerror("Error", "Please select at least one category!")
            return
        
        # Get object type
        obj_type = self.custom_object.get() if self.object_type.get() == "custom" else self.object_type.get()
        if not obj_type:
            messagebox.showerror("Error", "Please specify object type!")
            return
        
        # Konfirmasi
        total_images = len(categories) * self.images_per_category.get()
        confirm = messagebox.askyesno(
            "Confirm Download", 
            f"Start downloading?\n\nObject: {obj_type}\nCategories: {', '.join(categories)}\nImages: {self.images_per_category.get()} per category\nTotal: {total_images} images"
        )
        
        if not confirm:
            return
        
        # Setup download
        self.is_downloading = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Reset progress
        self.overall_progress['value'] = 0
        self.current_progress['value'] = 0
        
        # Start download thread
        self.download_thread = threading.Thread(
            target=self.download_images_thread,
            args=(obj_type, categories, self.images_per_category.get())
        )
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def stop_download(self):
        self.is_downloading = False
        self.log("🛑 Stopping download...")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def download_images_thread(self, obj_type, categories, images_per_category):
        try:
            total_categories = len(categories)
            total_target = total_categories * images_per_category
            total_downloaded = 0
            
            self.log(f"🎯 STARTING DOWNLOAD")
            self.log(f"📦 Object: {obj_type}")
            self.log(f"🏷️ Categories: {', '.join(categories)}")
            self.log(f"📊 Target: {total_target} images")
            
            # Setup progress
            self.overall_progress['maximum'] = total_target
            self.current_progress['maximum'] = images_per_category
            
            for i, category in enumerate(categories):
                if not self.is_downloading:
                    break
                
                self.current_status.config(text=f"Downloading: {category}")
                self.current_progress['value'] = 0
                
                self.log(f"📁 {obj_type} - {category}")
                
                # Download category
                downloaded = self.download_category_images(obj_type, category, images_per_category)
                total_downloaded += downloaded
                
                # Update progress
                self.overall_progress['value'] = (i + 1) * images_per_category
                progress_percent = ((i + 1) / total_categories) * 100
                self.overall_status.config(text=f"Progress: {i+1}/{total_categories} categories ({progress_percent:.1f}%)")
                
                self.log(f"✅ {category}: {downloaded}/{images_per_category} images")
                
                # Jeda antar kategori
                if self.is_downloading and i < len(categories) - 1:
                    sleep(1)
            
            # Final report
            if self.is_downloading:
                success_rate = (total_downloaded / total_target) * 100
                self.log(f"🎉 COMPLETED: {total_downloaded}/{total_target} images ({success_rate:.1f}%)")
                self.current_status.config(text=f"Completed! {total_downloaded} images")
                self.stats_label.config(text=f"SUCCESS: {total_downloaded} images", foreground="green")
                
                messagebox.showinfo("Completed", f"Download finished!\n{total_downloaded}/{total_target} images")
            else:
                self.log(f"⏹️ STOPPED: {total_downloaded} images")
                self.stats_label.config(text=f"STOPPED: {total_downloaded} images", foreground="orange")
            
        except Exception as e:
            error_msg = f"❌ ERROR: {str(e)}"
            self.log(error_msg)
            self.stats_label.config(text=error_msg, foreground="red")
            messagebox.showerror("Error", f"Download failed:\n{str(e)}")
        finally:
            self.is_downloading = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
    
    def download_category_images(self, obj_type, category, target_count):
        """Download images for a category"""
        folder = os.path.join(self.output_dir.get(), obj_type, category)
        os.makedirs(folder, exist_ok=True)
        
        downloaded_count = 0
        queries = self.generate_queries(obj_type, category)
        
        for query in queries:
            if not self.is_downloading or downloaded_count >= target_count:
                break
            
            try:
                params = {
                    "q": query,
                    "engine": "google_images", 
                    "api_key": self.api_key.get(),
                    "num": 100,
                    "safe": "active" if self.safe_search.get() else "off",
                    "tbs": f"itp:{self.image_type.get()},isz:l"
                }
                
                search = GoogleSearch(params)
                results = search.get_dict()
                images = results.get("images_results", [])
                
                for img in images:
                    if not self.is_downloading or downloaded_count >= target_count:
                        break
                    
                    url = img.get("original") or img.get("thumbnail")
                    if not url:
                        continue
                    
                    try:
                        response = requests.get(url, timeout=15, verify=False)
                        if response.status_code == 200:
                            img_data = BytesIO(response.content)
                            
                            with Image.open(img_data) as img_pil:
                                if img_pil.mode != 'RGB':
                                    img_pil = img_pil.convert('RGB')
                                
                                # Size filter
                                min_size = int(self.min_size.get().split('x')[0])
                                if img_pil.size[0] < min_size or img_pil.size[1] < min_size:
                                    continue
                                
                                # Color filter
                                if self.use_color_filter.get() and not self.color_filter(img_pil, obj_type, category):
                                    continue
                                
                                # Save
                                filename = f"{obj_type}_{category}_{downloaded_count:04d}.jpg"
                                file_path = os.path.join(folder, filename)
                                img_pil.save(file_path, "JPEG", quality=85)
                                
                                if os.path.getsize(file_path) > 10240:
                                    downloaded_count += 1
                                    self.current_progress['value'] = downloaded_count
                                    self.stats_label.config(text=f"Downloaded: {downloaded_count}/{target_count}")
                            
                    except:
                        continue
                    
                    sleep(self.download_delay.get())
                
            except Exception as e:
                continue
            
            sleep(0.5)
        
        return downloaded_count
    
    def generate_queries(self, obj_type, category):
        """Generate search queries"""
        base_queries = [
            f"{category} {obj_type}",
            f"{obj_type} {category}",
            f"{category} {obj_type} photo",
            f"{obj_type} {category} high quality"
        ]
        
        category_queries = {
            "unripe": [f"green {obj_type} unripe", f"raw {obj_type}"],
            "ripe": [f"fresh ripe {obj_type}", f"perfect {obj_type}"],
            "overripe": [f"rotten {obj_type}", f"spoiled {obj_type}"],
        }
        
        additional = category_queries.get(category, [])
        return base_queries + additional
    
    def color_filter(self, image, obj_type, category):
        """Simple color filter"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image_small = image.resize((50, 50))
            stat = ImageStat.Stat(image_small)
            r, g, b = stat.mean
            
            if "unripe" in category:
                return g > r and g > b
            elif "ripe" in category:
                return r > 80 or g > 80
            elif "overripe" in category:
                return (r + g + b) / 3 < 180
            
            return True
        except:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDownloaderApp(root)
    root.mainloop()