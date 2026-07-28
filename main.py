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
        print(f"Error sending message: {e}")

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
        driver.implicitly_wait(5)
        
        movies = driver.find_elements(By.CSS_SELECTOR, "article.movie-summary")
        
        for movie in movies:
            try:
                title = movie.find_element(By.CSS_SELECTOR, "h3").text.strip()
                link = movie.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                
                if title and title not in sent_items:
                    save_sent_item(title)
                    sent_items.add(title)
                    msg = (
                        "🎬 <b>New Movie Available at Vox!</b>\n\n"
                        f"📌 <b>Title:</b> {title}\n\n"
                        f"🎟 <a href='{link}'>Click here to book</a>"
                    )
                    send_telegram_message(msg)
                    print(f"Alert sent for movie: {title}")
            except:
                continue
    except Exception as e:
        print(f"Vox Cinemas Error: {e}")

def check_tazkarti(driver, sent_items):
    print("Checking Tazkarti Matches...")
    try:
        driver.get(TAZKARTI_URL)
        driver.implicitly_wait(8)
        
        match_cards = driver.find_elements(By.CSS_SELECTOR, ".match-card, .card")
        
        for card in match_cards:
            try:
                match_info = card.text.strip()
                
                if match_info and len(match_info) > 5:
                    flat_info = match_info.replace('\n', ' - ')
                    
                    if flat_info not in sent_items:
                        save_sent_item(flat_info)
                        sent_items.add(flat_info)
                        msg = (
                            "⚽️ <b>New Match Available on Tazkarti!</b>\n\n"
                            f"🏆 <b>Details:</b>\n{match_info}\n\n"
                            f"🎟 <a href='{TAZKARTI_URL}'>Click here to book</a>"
                        )
                        send_telegram_message(msg)
                        print("Alert sent for a new match.")
            except:
                continue
    except Exception as e:
        print(f"Tazkarti Error: {e}")

if __name__ == "__main__":
    print("Starting Scraper Bot...")
    
    sent_items = load_sent_items()
    driver = setup_browser()
    
    try:
        check_vox_cinemas(driver, sent_items)
        check_tazkarti(driver, sent_items)
    finally:
        driver.quit()
        print("Scraping cycle completed.")