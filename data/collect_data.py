import os
import requests
from serpapi import GoogleSearch
from time import sleep
from PIL import Image
from io import BytesIO
import urllib3
import warnings

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

# === KONFIGURASI DASAR ===
API_KEY = "22cc68e17ec26c884f5b93569ac90c704ae87075cdfb066aae6d96db585dcbbd"
DATA_DIR = "data"
IMAGES_PER_CLASS = 100  # Mencari 100 gambar per class
SLEEP_TIME = 3  # Tambah jeda

# === LIST BUAH DAN TINGKAT KEMATANGAN ===
fruit_stages = {
    "banana": ["unripe", "ripe", "overripe"],
    "mango": ["unripe", "ripe", "overripe"],
    "tomato": ["unripe", "ripe", "overripe"],
}

# === FUNGSI DOWNLOAD GAMBAR YANG DIPERBAIKI ===
def download_images(query, folder, num=100):
    os.makedirs(folder, exist_ok=True)
    print(f"🔍 Mencari gambar: {query}")

    params = {
        "q": query,
        "engine": "google_images",
        "api_key": API_KEY,
        "num": num,
        "safe": "active",
        "ijn": "0"  # Page number
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        images = results.get("images_results", [])
        print(f"📸 Ditemukan {len(images)} gambar untuk {query}")

        downloaded_count = 0
        for i, img in enumerate(images):
            if downloaded_count >= 50:  # Batasi per class untuk testing
                break
                
            url = img.get("original") or img.get("thumbnail")
            if not url:
                continue

            try:
                # HEAD request dulu untuk cek content type
                head_response = requests.head(url, timeout=10, verify=False)
                content_type = head_response.headers.get('content-type', '')
                
                if 'image' not in content_type:
                    print(f"⚠️  Bukan gambar: {url}")
                    continue

                # Download gambar
                response = requests.get(url, timeout=15, verify=False, stream=True)
                if response.status_code == 200:
                    # Validasi gambar dengan PIL sebelum save
                    try:
                        img_data = BytesIO(response.content)
                        with Image.open(img_data) as img_pil:
                            img_pil.verify()  # Verify image integrity
                            
                            # Cek ukuran minimal
                            if img_pil.size[0] < 100 or img_pil.size[1] < 100:
                                print(f"⚠️  Gambar terlalu kecil: {img_pil.size}")
                                continue
                            
                            # Convert ke RGB jika perlu
                            img_pil = img_pil.convert('RGB')
                            
                            # Save gambar
                            file_path = os.path.join(folder, f"{query.replace(' ', '_')}_{downloaded_count}.jpg")
                            img_pil.save(file_path, "JPEG", quality=85)
                            downloaded_count += 1
                            print(f"✅ Berhasil download: {file_path}")
                            
                    except Exception as img_error:
                        print(f"❌ Gambar corrupt: {url} - {img_error}")
                        continue
                        
            except Exception as e:
                print(f"⚠️  Gagal mengunduh gambar {i}: {e}")
                continue

        print(f"📊 Berhasil download {downloaded_count} gambar untuk {query}")
        return downloaded_count

    except Exception as e:
        print(f"❌ Error saat search: {e}")
        return 0

# === FUNGSI VALIDASI DATASET ===
def validate_dataset():
    """Validasi dataset yang sudah didownload"""
    print("\n🔍 VALIDASI DATASET...")
    total_valid = 0
    total_invalid = 0
    
    for fruit in fruit_stages.keys():
        for stage in fruit_stages[fruit]:
            folder = os.path.join(DATA_DIR, fruit, stage)
            if os.path.exists(folder):
                valid_in_class = 0
                invalid_in_class = 0
                
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    try:
                        with Image.open(file_path) as img:
                            img.verify()
                        # Cek file size
                        if os.path.getsize(file_path) > 1024:  # Minimal 1KB
                            valid_in_class += 1
                        else:
                            invalid_in_class += 1
                            os.remove(file_path)
                    except:
                        invalid_in_class += 1
                        os.remove(file_path)
                
                print(f"   {fruit}/{stage}: {valid_in_class} valid, {invalid_in_class} invalid")
                total_valid += valid_in_class
                total_invalid += invalid_in_class
    
    print(f"\n📊 TOTAL: {total_valid} valid, {total_invalid} invalid")
    return total_valid

# === MAIN LOOP YANG DIPERBAIKI ===
if __name__ == "__main__":
    print("🚀 MEMULAI DOWNLOAD DATASET YANG DIPERBAIKI...")
    
    total_downloaded = 0
    for fruit, stages in fruit_stages.items():
        for stage in stages:
            query = f"{stage} {fruit} high quality photo"
            save_folder = os.path.join(DATA_DIR, fruit, stage)
            
            print(f"\n🎯 Processing: {fruit} - {stage}")
            downloaded = download_images(query, save_folder, num=IMAGES_PER_CLASS)
            total_downloaded += downloaded
            
            sleep(SLEEP_TIME)  # Jeda antar request

    print(f"\n✅ Download selesai! Total gambar: {total_downloaded}")
    
    # Validasi dataset
    valid_count = validate_dataset()
    
    if valid_count > 0:
        print(f"\n🎉 SUKSES! Dataset memiliki {valid_count} gambar valid!")
        print("📁 Struktur dataset:")
        for fruit in fruit_stages.keys():
            for stage in fruit_stages[fruit]:
                folder = os.path.join(DATA_DIR, fruit, stage)
                if os.path.exists(folder):
                    count = len([f for f in os.listdir(folder) if f.endswith(('.jpg', '.jpeg', '.png'))])
                    print(f"   📂 {fruit}/{stage}: {count} gambar")
    else:
        print("\n❌ GAGAL! Tidak ada gambar valid yang terdownload.")
        print("💡 Coba solusi alternatif...")