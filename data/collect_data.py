import os
import requests
from serpapi import GoogleSearch
from time import sleep

# === KONFIGURASI DASAR ===
API_KEY = "22cc68e17ec26c884f5b93569ac90c704ae87075cdfb066aae6d96db585dcbbd"  # Ganti dengan API key kamu
DATA_DIR = "dataset"
IMAGES_PER_CLASS = 300  # bisa disesuaikan: 300–500 gambar per kelas
SLEEP_TIME = 2  # jeda antar request agar aman dari rate limit

# === LIST BUAH DAN TINGKAT KEMATANGAN ===
fruit_stages = {
    # "banana": ["unripe", "ripe", "overripe"],
    "mango": ["ripe", "overripe"],
    "tomato": ["unripe", "ripe", "overripe"],
}

# === FUNGSI DOWNLOAD GAMBAR ===
def download_images(query, folder, num=200):
    os.makedirs(folder, exist_ok=True)
    print(f"🔍 Mencari gambar: {query}")

    params = {
        "q": query,
        "engine": "google_images",
        "api_key": API_KEY,
        "num": num,
        "safe": "active",  # pastikan hasil aman
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    images = results.get("images_results", [])
    print(f"📸 Ditemukan {len(images)} gambar untuk {query}")

    for i, img in enumerate(images):
        url = img.get("original")
        if not url:
            continue

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                file_path = os.path.join(folder, f"{query.replace(' ', '_')}_{i}.jpg")
                with open(file_path, "wb") as f:
                    f.write(response.content)
        except Exception as e:
            print(f"⚠️ Gagal mengunduh gambar {i} untuk {query}: {e}")

# === MAIN LOOP ===
if __name__ == "__main__":
    for fruit, stages in fruit_stages.items():
        for stage in stages:
            query = f"{stage} {fruit} high quality photo"
            save_folder = os.path.join(DATA_DIR, fruit, stage)
            download_images(query, save_folder, num=IMAGES_PER_CLASS)
            sleep(SLEEP_TIME)  # jeda untuk menghindari rate limit

    print("\n✅ Pengumpulan dataset selesai!")
