import os
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

# --- CONFIGURATION ---
LOCATIONS = [
    "Bitexco",
    "Nha tho duc ba Saigon",
    "Dinh doc lap"
]
MAX_IMAGES = 5  # Set to 10 to ensure we safely get at least 8
SAVE_DIR = "high_res_places"

def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Keep off to see the scrolling
    options.add_argument("--lang=en") 
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver
def extract_hours(driver, place_dir):
    """
    Finds the operating hours text and saves it to info.txt
    """
    try:
        # Google Maps uses 'data-item-id="oh"' for the Operating Hours section
        # We wait briefly for it to be visible
        hours_element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-item-id="oh"]'))
        )
        
        # The 'aria-label' often contains the cleanest summary (e.g., "Operating hours: Open ⋅ Closes 10 PM")
        raw_text = hours_element.get_attribute("aria-label")
        
        # If aria-label is empty, we grab the visible text on screen
        if not raw_text:
            raw_text = hours_element.text.replace("\n", " ")

        # Clean up the text
        clean_text = raw_text.replace("Operating hours: ", "").strip()

        # Save to file
        with open(os.path.join(place_dir, "info.txt"), "w", encoding="utf-8") as f:
            f.write(f"Hours: {clean_text}")
            
        print(f"   🕒 Hours info saved: {clean_text[:30]}...")
        
    except:
        # If not found (e.g., a park that is always open or a place with no data)
        print("   ⚠️ No hours info found.")
        with open(os.path.join(place_dir, "info.txt"), "w", encoding="utf-8") as f:
            f.write("Hours: Not available")
def get_high_res_url(thumbnail_url):
    if not thumbnail_url: return None
    # Change size param to s0 (original size)
    return re.sub(r'=w\d+-h\d+.*', '=s0', thumbnail_url)

def process_location(driver, location):
    print(f"\n📍 Processing: {location}")
    
    # --- FIX: DEFINE DIRECTORY AT THE START ---
    # We must define and create the folder here so extract_hours can use it
    place_dir = os.path.join(SAVE_DIR, location.replace(" ", "_"))
    if not os.path.exists(place_dir): 
        os.makedirs(place_dir)
    # ------------------------------------------

    # 1. Open Maps
    try:
        driver.get("https://www.google.com/maps?hl=en")
    except WebDriverException:
        raise # Trigger restart in main loop

    # 2. Search
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
        search_box.clear()
        search_box.send_keys(location)
        search_box.send_keys(Keys.ENTER)
        time.sleep(3) 
    except Exception as e:
        print(f"   ⚠️ Search error: {e}")
        return

    # 3. Handle "List of Results"
    try:
        WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
        )
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        if results:
            print("   ℹ️ Clicking first result in list...")
            results[0].click()
            time.sleep(3)
    except:
        pass 
    
    # --- EXTRACT HOURS (Now safe because place_dir exists) ---
    extract_hours(driver, place_dir)
    # ---------------------------------------------------------

    # 4. Click Photos Tab
    try:
        photo_tab = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Photo') or contains(@data-item-id, 'at-work-photos')]"))
        )
        photo_tab.click()
        print("   ✅ Opened Photos tab")
        time.sleep(2)
    except:
        print("   ⚠️ Could not find Photos tab. Skipping.")
        return

    # 5. Scrape & Scroll Loop
    collected_urls = set()
    stuck_counter = 0 
    
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
                        # Download
                        try:
                            r = requests.get(hd_url, timeout=5)
                            if r.status_code == 200:
                                count = len(collected_urls) + 1
                                with open(os.path.join(place_dir, f"img_{count}.jpg"), 'wb') as f:
                                    f.write(r.content)
                                print(f"   ⬇️ Downloaded {count}/{MAX_IMAGES}")
                                collected_urls.add(hd_url)
                                found_new = True
                        except:
                            pass
            except:
                continue

        # Stuck Counter
        if not found_new:
            stuck_counter += 1
            print(f"   ⏳ Scrolling... (No new images found {stuck_counter}/4)")
        else:
            stuck_counter = 0

        if stuck_counter >= 4:
            print("   🛑 Reached end of gallery or stuck. Moving to next.")
            break

        # Scroll Logic
        try:
            if images:
                driver.execute_script("arguments[0].scrollIntoView();", images[-1])
            
            if scrollable_div:
                driver.execute_script("arguments[0].scrollBy(0, 500);", scrollable_div)
                
            time.sleep(2) 
        except:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            time.sleep(2)
# --- EXECUTION ---
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

driver = setup_driver()

for place in LOCATIONS:
    try:
        process_location(driver, place)
    except WebDriverException:
        print("   🚨 Browser connection lost. Restarting...")
        try:
            driver.quit()
        except:
            pass
        driver = setup_driver()
        time.sleep(2)
    except Exception as e:
        print(f"   ❌ Error: {e}")

driver.quit()
print("All Done!")