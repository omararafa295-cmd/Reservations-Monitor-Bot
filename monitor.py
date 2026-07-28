import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

TELEGRAM_TOKEN = '7632916042:AAEYh_kUluMXb2oNQ-mpQPiZQJDU7FZ8x-I'
CHAT_ID = '1238932334'

VOX_URL = 'https://egy.voxcinemas.com/showtimes?c=city-centre-almaza'
TAZKARTI_URL = 'https://www.tazkarti.com/#/matches'
SENT_FILE = 'sent.txt'

def load_sent_items():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_sent_item(item):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{item}\n")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def check_vox_cinemas(driver, sent_items):
    print("Checking Vox Cinemas Almaza...")
    try:
        driver.get(VOX_URL)
        driver.implicitly_wait(6)
        
        elements = driver.find_elements(By.TAG_NAME, "a")
        count = 0
        
        for el in elements:
            try:
                text = el.text.strip()
                link = el.get_attribute("href")
                
                if link and ("book" in link or "movies" in link) and len(text) > 3:
                    if text not in sent_items:
                        save_sent_item(text)
                        sent_items.add(text)
                        msg = f"🎬 <b>Vox Cinemas Update!</b>\n\n{text}\n\n🎟 <a href='{link}'>Book Here</a>"
                        send_telegram_message(msg)
                        count += 1
            except:
                continue
        print(f"Found and processed {count} new items in Vox.")
    except Exception as e:
        print(f"Vox Error: {e}")

def check_tazkarti(driver, sent_items):
    print("Checking Tazkarti...")
    try:
        driver.get(TAZKARTI_URL)
        driver.implicitly_wait(8)
        
        cards = driver.find_elements(By.TAG_NAME, "mat-card")
        if not cards:
            cards = driver.find_elements(By.TAG_NAME, "div")
            
        count = 0
        for card in cards:
            try:
                info = card.text.strip()
                if info and len(info) > 10 and ("vs" in info.lower() or "استاد" in info):
                    flat_info = info.replace('\n', ' - ')
                    if flat_info not in sent_items:
                        save_sent_item(flat_info)
                        sent_items.add(flat_info)
                        msg = f"⚽️ <b>Tazkarti Match Update!</b>\n\n{flat_info}\n\n🎟 <a href='{TAZKARTI_URL}'>Book Here</a>"
                        send_telegram_message(msg)
                        count += 1
            except:
                continue
        print(f"Found and processed {count} new items in Tazkarti.")
    except Exception as e:
        print(f"Tazkarti Error: {e}")

if __name__ == "__main__":
    print("Starting Bot...")
    sent_items = load_sent_items()
    driver = setup_browser()
    
    try:
        check_vox_cinemas(driver, sent_items)
        check_tazkarti(driver, sent_items)
    finally:
        driver.quit()
        print("Done.")