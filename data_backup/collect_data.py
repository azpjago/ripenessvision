import os
import requests
from serpapi import GoogleSearch
from time import sleep
from PIL import Image, ImageStat
from io import BytesIO
import urllib3
import warnings
import colorsys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

# === KONFIGURASI ===
API_KEY = "22cc68e17ec26c884f5b93569ac90c704ae87075cdfb066aae6d96db585dcbbd"
DATA_DIR = "data"
IMAGES_PER_STAGE = 150
SLEEP_TIME = 2

# === BUAH DAN STAGE ===
fruit_stages = {
    "banana": ["unripe", "ripe", "overripe"],
    "mango": ["unripe", "ripe", "overripe"], 
    "tomato": ["unripe", "ripe", "overripe"],
}

# === QUERY YANG SANGAT SPESIFIK UNTUK SEMUA BUAH ===
stage_queries = {
    "unripe": [
        "unripe green {fruit} hard texture not edible",
        "raw {fruit} before ripening solid firm", 
        "young {fruit} harvesting agriculture green color",
        "immature {fruit} on tree not ready",
        "fresh picked unripe {fruit} cooking",
        "{fruit} green stage hard not sweet"
    ],
    
    "ripe": [
        "perfectly ripe {fruit} fresh ready to eat",
        "optimal ripeness {fruit} supermarket quality", 
        "fresh ripe {fruit} perfect sweetness",
        "just ripe {fruit} at peak freshness",
        "ready to eat {fruit} ideal condition",
        "fresh ripe {fruit} nutrition healthy"
    ],
    
    "overripe": [
        "overripe {fruit} brown black spots rotten",
        "spoiled {fruit} decaying fermentation", 
        "rotten {fruit} mold fungus spoiled",
        "over ripened {fruit} mushy texture bad",
        "old {fruit} too ripe waste",
        "decaying {fruit} fermentation"
    ]
}

# === FILTER WARNA LENGKAP UNTUK SEMUA BUAH ===
def should_keep_image_advanced(image, stage, fruit):
    """
    Filter ketat berdasarkan analisis warna untuk semua buah
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Analisis warna
        image_small = image.resize((100, 100))
        stat = ImageStat.Stat(image_small)
        r, g, b = stat.mean
        
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # === RULES UNTUK BANANA ===
        if fruit == "banana":
            if stage == "unripe":
                # HARUS: Green dominant, bright
                keep = (g > r + 20 and g > b + 20 and  # Green dominant
                       v > 0.4 and s > 0.3 and        # Not too dark
                       h > 0.2 and h < 0.4)           # Green hue range
                if not keep:
                    print(f"    🚫 REJECTED: Unripe banana color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "ripe":
                # HARUS: Yellow (high R and G), bright
                keep = (r > 120 and g > 120 and b < 100 and  # Yellow tones
                       v > 0.5 and s > 0.4 and              # Bright and saturated
                       abs(r - g) < 50)                     # Balanced R and G
                if not keep:
                    print(f"    🚫 REJECTED: Ripe banana color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "overripe":
                # HARUS: Dark, brown, low brightness
                keep = (v < 0.6 or                          # Dark overall
                       (r > 140 and g > 90 and b < 70) or   # Brown tones
                       (r < 80 and g < 80 and b < 80))      # Very dark
                if not keep:
                    print(f"    🚫 REJECTED: Overripe banana too bright - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
        
        # === RULES UNTUK MANGA (MANGO) ===
        elif fruit == "mango":
            if stage == "unripe":
                # HARUS: Green dominant, bisa ada sedikit yellow tapi masih dominan green
                keep = (g > r + 10 and g > b + 10 and  # Green dominant
                       v > 0.4 and s > 0.3 and        # Not too dark
                       h > 0.2 and h < 0.4)           # Green hue range
                if not keep:
                    print(f"    🚫 REJECTED: Unripe mango color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "ripe":
                # HARUS: Yellow, orange, atau red dominant
                keep = ((r > g and r > b and r > 120) or    # Red/orange dominant
                       (r > 100 and g > 100 and b < 80))    # Yellow tones
                if not keep:
                    print(f"    🚫 REJECTED: Ripe mango color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "overripe":
                # HARUS: Dark, brown, black spots, low brightness
                keep = (v < 0.5 or                          # Very dark
                       (r > 150 and g < 100 and b < 80) or  # Dark red/brown
                       (r < 100 and g < 100 and b < 100))   # Dark overall
                if not keep:
                    print(f"    🚫 REJECTED: Overripe mango too bright - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
        
        # === RULES UNTUK TOMAT (TOMATO) ===
        elif fruit == "tomato":
            if stage == "unripe":
                # HARUS: Green dominant, bisa ada sedikit yellow
                keep = (g > r + 15 and g > b + 15 and  # Green clearly dominant
                       v > 0.4 and s > 0.3 and        # Not too dark
                       h > 0.2 and h < 0.4)           # Green hue range
                if not keep:
                    print(f"    🚫 REJECTED: Unripe tomato color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "ripe":
                # HARUS: Red dominant, bright red
                keep = (r > g + 40 and r > b + 40 and  # Red clearly dominant
                       r > 120 and v > 0.5 and         # Bright red
                       s > 0.5)                        # Highly saturated
                if not keep:
                    print(f"    🚫 REJECTED: Ripe tomato color wrong - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
                
            elif stage == "overripe":
                # HARUS: Dark red, brown, wrinkled, soft
                keep = ((v < 0.5 and r > 100) or        # Dark red
                       (r > 140 and g < 80 and b < 60) or  # Brownish red
                       (r < 80 and g < 80 and b < 80))     # Very dark
                if not keep:
                    print(f"    🚫 REJECTED: Overripe tomato too bright - R:{r:.0f},G:{g:.0f},B:{b:.0f}")
                return keep
        
        # Default untuk fruit lain (jika ada)
        return True
        
    except Exception as e:
        print(f"    ⚠️  Color analysis error: {e}")
        return False

# === QUERY SPESIFIK UNTUK SETIAP BUAH ===
def get_fruit_specific_queries(fruit, stage):
    """Query yang lebih spesifik berdasarkan buah"""
    base_queries = stage_queries[stage]
    
    # Tambahkan query spesifik berdasarkan buah
    if fruit == "mango":
        if stage == "unripe":
            additional = [
                "green mango hard sour",
                "unripe mango for pickles",
                "raw mango cooking ingredient"
            ]
        elif stage == "ripe":
            additional = [
                "yellow mango sweet juicy", 
                "ripe mango orange flesh",
                "sweet mango ready to eat"
            ]
        elif stage == "overripe":
            additional = [
                "brown mango fermented",
                "overripe mango alcohol wine",
                "rotten mango black spots"
            ]
    
    elif fruit == "tomato":
        if stage == "unripe":
            additional = [
                "green tomato firm hard",
                "unripe tomato for frying", 
                "raw tomato green color"
            ]
        elif stage == "ripe":
            additional = [
                "red tomato fresh salad",
                "ripe tomato juicy red", 
                "fresh tomato vibrant red"
            ]
        elif stage == "overripe":
            additional = [
                "overripe tomato wrinkled",
                "rotten tomato mold fungus", 
                "spoiled tomato mushy"
            ]
    
    else:  # banana
        additional = []
    
    return base_queries + additional

# === FUNGSI DOWNLOAD UTAMA ===
def download_with_anti_contamination(fruit, stage, folder, target_count=IMAGES_PER_STAGE):
    """
    Download dengan protection untuk semua buah
    """
    os.makedirs(folder, exist_ok=True)
    
    downloaded_count = 0
    queries = get_fruit_specific_queries(fruit, stage)
    
    print(f"\n🔍 DOWNLOADING: {fruit.upper()} - {stage.upper()}")
    print(f"   Target: {target_count} clean images")
    print(f"   Using {len(queries)} specialized queries")
    
    for query_idx, query_template in enumerate(queries):
        if downloaded_count >= target_count:
            break
            
        actual_query = query_template.format(fruit=fruit)
        print(f"\n   📝 Query {query_idx+1}: {actual_query}")
        
        try:
            params = {
                "q": actual_query,
                "engine": "google_images", 
                "api_key": API_KEY,
                "num": 100,
                "safe": "active",
                "tbs": "itp:photo,isz:m"
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            images = results.get("images_results", [])
            
            print(f"   📸 Found {len(images)} potential images")
            
            successful_in_query = 0
            rejected_count = 0
            
            for i, img in enumerate(images):
                if downloaded_count >= target_count:
                    break
                    
                url = img.get("original") or img.get("thumbnail")
                if not url:
                    continue

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(url, timeout=20, verify=False, stream=True, headers=headers)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if not content_type.startswith('image/'):
                            rejected_count += 1
                            continue

                        # Process image
                        img_data = BytesIO(response.content)
                        
                        with Image.open(img_data) as img_pil:
                            if img_pil.mode != 'RGB':
                                img_pil = img_pil.convert('RGB')
                            
                            # Filter ukuran
                            if img_pil.size[0] < 400 or img_pil.size[1] < 400:
                                rejected_count += 1
                                continue
                            
                            # Filter warna ketat
                            if not should_keep_image_advanced(img_pil, stage, fruit):
                                rejected_count += 1
                                continue
                            
                            # Filter aspect ratio
                            aspect_ratio = img_pil.size[0] / img_pil.size[1]
                            if aspect_ratio > 3 or aspect_ratio < 0.3:
                                rejected_count += 1
                                continue
                            
                            # Save image
                            file_path = os.path.join(folder, f"{fruit}_{stage}_{downloaded_count:03d}.jpg")
                            img_pil.save(file_path, "JPEG", quality=90, optimize=True)
                            
                            if os.path.getsize(file_path) > 15360:
                                downloaded_count += 1
                                successful_in_query += 1
                                if downloaded_count % 10 == 0:
                                    print(f"   📥 Progress: {downloaded_count}/{target_count}")
                            else:
                                os.remove(file_path)
                                rejected_count += 1
                                
                except Exception as e:
                    rejected_count += 1
                    continue
                    
                sleep(1)
            
            print(f"   ✅ Query result: +{successful_in_query} accepted, {rejected_count} rejected")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            continue
            
        sleep(SLEEP_TIME)
    
    print(f"   🎯 FINAL: {downloaded_count}/{target_count} clean images for {fruit} {stage}")
    return downloaded_count

# === VALIDATION OTOMATIS ===
def auto_validate_folder(fruit, stage):
    """Validasi otomatis folder setelah download"""
    folder = os.path.join(DATA_DIR, fruit, stage)
    if not os.path.exists(folder):
        return 0, 0
    
    valid_count = 0
    invalid_count = 0
    
    for file in os.listdir(folder):
        if file.endswith('.jpg'):
            file_path = os.path.join(folder, file)
            try:
                with Image.open(file_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    if should_keep_image_advanced(img, stage, fruit):
                        valid_count += 1
                    else:
                        invalid_count += 1
                        os.remove(file_path)
            except:
                invalid_count += 1
                try:
                    os.remove(file_path)
                except:
                    pass
    
    if invalid_count > 0:
        print(f"   🧹 Cleaned {invalid_count} inconsistent images")
    
    return valid_count, invalid_count

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("🚀 STARTING COMPLETE ANTI-CONTAMINATION DOWNLOAD")
    print("🍌 Including: Banana, Mango, Tomato")
    
    total_downloaded = 0
    stage_stats = {}
    
    for fruit, stages in fruit_stages.items():
        stage_stats[fruit] = {}
        print(f"\n" + "="*50)
        print(f"🍎 PROCESSING: {fruit.upper()}")
        print("="*50)
        
        for stage in stages:
            save_folder = os.path.join(DATA_DIR, fruit, stage)
            
            # Download dengan protection
            downloaded = download_with_anti_contamination(fruit, stage, save_folder, IMAGES_PER_STAGE)
            
            # Auto-validation
            sleep(1)
            valid, invalid = auto_validate_folder(fruit, stage)
            
            stage_stats[fruit][stage] = {
                'downloaded': downloaded,
                'valid': valid,
                'invalid': invalid
            }
            total_downloaded += valid
            
            print(f"   💤 Cooling down...")
            sleep(SLEEP_TIME * 2)
    
    # FINAL REPORT DETAILED
    print(f"\n" + "="*60)
    print("📊 COMPLETE DOWNLOAD REPORT - ALL FRUITS")
    print("="*60)
    
    for fruit, stages in stage_stats.items():
        print(f"\n{fruit.upper()}:")
        fruit_total = 0
        for stage, stats in stages.items():
            success_rate = (stats['valid'] / stats['downloaded']) * 100 if stats['downloaded'] > 0 else 0
            print(f"  {stage:8}: {stats['valid']:3d} valid ({success_rate:5.1f}% success)")
            fruit_total += stats['valid']
        print(f"  {'TOTAL':8}: {fruit_total:3d} images")
    
    total_valid = sum(stats['valid'] for fruit_stats in stage_stats.values() for stats in fruit_stats.values())
    print(f"\n🎉 GRAND TOTAL CLEAN IMAGES: {total_valid}")
    
    # Folder structure
    print(f"\n📁 FINAL DATASET STRUCTURE:")
    for fruit in fruit_stages.keys():
        for stage in fruit_stages[fruit]:
            folder = os.path.join(DATA_DIR, fruit, stage)
            if os.path.exists(folder):
                count = len([f for f in os.listdir(folder) if f.endswith('.jpg')])
                print(f"  📂 {fruit}/{stage}: {count} images")