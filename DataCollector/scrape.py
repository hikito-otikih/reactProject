import os
import time
import re
import json
import random
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'result', 'places.db')
CACHE_FILE = os.path.join(SCRIPT_DIR, 'result', 'scraped_images.json') # New JSON cache
MAX_IMAGES = 3  # Increased to 3 as requested
SAVE_DIR = "high_res_places"
BATCH_SIZE = 25  # Restart browser every 25 locations to free memory
DELAY_BETWEEN_LOCATIONS = (0.5, 1)  # Minimal delay, still safe

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Re-enable headless for speed
    options.add_argument("--lang=en")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Memory optimization flags (but keep images enabled!)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # DON'T disable images - we need them to extract URLs from style attributes
    
    # Rotate user agents to look more human
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_high_res_url(thumbnail_url):
    if not thumbnail_url: return None
    # Change size param to s0 (original size)
    return re.sub(r'=w\d+-h\d+.*', '=s0', thumbnail_url)

def load_cache():
    """Load scraped images from JSON cache"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_to_cache(name, urls):
    """Append new result to JSON cache"""
    cache = load_cache()
    cache[name] = urls
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def sync_cache_to_db():
    """Batch update database from JSON cache"""
    cache = load_cache()
    if not cache: return
    
    print(f"\n💾 Syncing {len(cache)} records from JSON cache to Database...")
    
    data_to_update = []
    for name, urls in cache.items():
        urls_json = json.dumps(urls)
        data_to_update.append((urls_json, name))
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            UPDATE places 
            SET Image_URLs = ?
            WHERE Name = ?
        """, data_to_update)
        conn.commit()
        print(f"✅ Database updated successfully! ({cursor.rowcount} rows modified)")

def get_locations_from_db(limit=100):
    """Get locations from database that don't have image URLs yet"""
    cache = load_cache()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Add Image_URLs column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE places ADD COLUMN Image_URLs TEXT")
            conn.commit()
            print("✅ Added Image_URLs column to database")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        cursor.execute("""
            SELECT Name, Address 
            FROM places 
            WHERE Image_URLs IS NULL OR Image_URLs = ''
        """)
        all_rows = cursor.fetchall()
        
        # Filter out locations that are already in the cache
        filtered_rows = [row for row in all_rows if row[0] not in cache]
        
        return filtered_rows[:limit]

# Removed old save_images_to_db function as we use cache now

def is_already_processed(name):
    """Check if location already has image URLs in database OR cache"""
    # Check cache first
    cache = load_cache()
    if name in cache: return True

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Image_URLs 
            FROM places 
            WHERE Name = ?
        """, (name,))
        result = cursor.fetchone()
        return result and result[0] and result[0] != ''

def process_location(driver, db_name, search_query):
    print(f"\n📍 Processing: {db_name} (Search: {search_query})")
    
    # 1. Open Maps
    try:
        driver.get("https://www.google.com/maps?hl=en")
    except WebDriverException:
        raise # Trigger restart in main loop

    # 2. Search
    try:
        search_box = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(1.5)  # Reduced from 2
    except Exception as e:
        print(f"   ⚠️ Search error: {e}")
        return

    # 3. Handle "List of Results"
    try:
        WebDriverWait(driver, 2).until(  # Reduced from 3
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
        )
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        if results:
            print("   ℹ️ Clicking first result in list...")
            results[0].click()
            time.sleep(1.5)  # Reduced from 2
    except:
        pass

    # 4. Click Photos Tab
    try:
        photo_tab = WebDriverWait(driver, 5).until(  # Reduced from 6
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Photo') or contains(@data-item-id, 'at-work-photos')]"))
        )
        photo_tab.click()
        print("   ✅ Opened Photos tab")
        time.sleep(1)  # Reduced from 1.5
    except:
        print("   ⚠️ Could not find Photos tab. Skipping.")
        return

    # 5. Scrape & Scroll Loop
    collected_urls = []
    stuck_counter = 0 
    max_stuck = 1  # Exit immediately when stuck (was 2) 
    
    # Identify the scrollable container
    scrollable_div = None
    try:
        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="listbox"]')
    except:
        pass

    while len(collected_urls) < MAX_IMAGES:
        # Get all currently loaded images
        images = driver.find_elements(By.CSS_SELECTOR, 'div[role="img"]')
        found_new = False

        for img in images:
            if len(collected_urls) >= MAX_IMAGES: break
            try:
                style = img.get_attribute("style")
                match = re.search(r'url\("(.*?)"\)', style)
                if match:
                    raw_url = match.group(1)
                    if "googleapis" in raw_url or "static" in raw_url: continue 
                    
                    hd_url = get_high_res_url(raw_url)
                    if hd_url and hd_url not in collected_urls:
                        # Save URL instead of downloading
                        collected_urls.append(hd_url)
                        print(f"   ✅ Collected URL {len(collected_urls)}/{MAX_IMAGES}")
                        found_new = True
            except:
                continue

        # Stuck Counter
        if not found_new:
            stuck_counter += 1
            print(f"   ⏳ Scrolling... (No new images found {stuck_counter}/{max_stuck})")
        else:
            stuck_counter = 0

        if stuck_counter >= max_stuck:
            print("   🛑 Reached end of gallery or stuck. Moving to next.")
            break

        # Scroll Logic
        try:
            if images:
                driver.execute_script("arguments[0].scrollIntoView();", images[-1])
            
            if scrollable_div:
                driver.execute_script("arguments[0].scrollBy(0, 500);", scrollable_div)
                
            time.sleep(random.uniform(0.5, 1))  # Faster scrolling (was 0.8-1.5)
        except:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            time.sleep(random.uniform(0.5, 1))
    
    # Save URLs to cache
    if collected_urls:
        save_to_cache(db_name, collected_urls)
        print(f"   💾 Saved {len(collected_urls)} image URLs to JSON cache")
    
    return len(collected_urls) > 0

# --- EXECUTION ---
start_time = time.time()

# Get locations from database
print("📊 Loading locations from database...")
locations = get_locations_from_db(limit=100)
print(f"Found {len(locations)} locations without images\n")

if not locations:
    print("✅ All locations already have images!")
    exit()

driver = setup_driver()
processed = 0
skipped = 0

for i, (name, address) in enumerate(locations):
    # Use address for search (more reliable than name)
    search_query = address if address else name
    
    # Skip already processed locations
    if is_already_processed(name):
        print(f"\n⏭️ Skipping {name} (already processed)")
        skipped += 1
        continue
    
    try:
        process_location(driver, name, search_query)
        processed += 1
        
        # Human-like delay between locations
        if i < len(locations) - 1:  # Don't wait after last one
            delay = random.uniform(*DELAY_BETWEEN_LOCATIONS)
            print(f"   ⏸️ Waiting {delay:.1f}s before next location...")
            time.sleep(delay)
        
        # Take a break every BATCH_SIZE locations
        if (processed % BATCH_SIZE) == 0 and processed > 0:
            print(f"\n🔄 Processed {processed} locations. Syncing DB & Restarting browser...")
            sync_cache_to_db()  # Sync periodically
            driver.quit()
            time.sleep(3)  # Short break
            driver = setup_driver()
            
    except WebDriverException:
        print("   🚨 Browser connection lost. Restarting...")
        try:
            driver.quit()
        except:
            pass
        time.sleep(random.uniform(5, 15))  # Random restart delay
        driver = setup_driver()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        time.sleep(2)

# Sync at the end
sync_cache_to_db()

driver.quit()

end_time = time.time()
duration = end_time - start_time
minutes = int(duration // 60)
seconds = int(duration % 60)

print(f"\n✅ All Done! Processed: {processed}, Skipped: {skipped}, Total: {len(locations)}")
print(f"⏱️ Total execution time: {minutes}m {seconds}s")