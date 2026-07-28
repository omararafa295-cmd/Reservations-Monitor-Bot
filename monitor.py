import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= إعدادات تليجرام =================
TELEGRAM_TOKEN = '7632916042:AAEYh_kUluMXb2oNQ-mpQPiZQJDU7FZ8x-I'
CHAT_ID = '1238932334'


VOX_URL = 'https://egy.voxcinemas.com/showtimes?c=city-centre-almaza'
TAZKARTI_URL = 'https://www.tazkarti.com/#/matches'

sent_movies = set()
sent_matches = set()

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
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    return webdriver.Chrome(options=chrome_options)

def check_vox_cinemas(driver):
    print("جاري فحص سينما فوكس ألماظة...")
    try:
        driver.get(VOX_URL)
        time.sleep(5) 
      
        movies = driver.find_elements(By.CSS_SELECTOR, "article.movie-summary")
        
        for movie in movies:
            try:
                title = movie.find_element(By.CSS_SELECTOR, "h3").text
                link = movie.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                
                if title and title not in sent_movies:
                    sent_movies.add(title)
                    msg = f"🎬 <b>فيلم متاح في فوكس ألماظة!</b>\n\n<b>الفيلم:</b> {title}\n🔗 <a href='{link}'>رابط الحجز</a>"
                    send_telegram_message(msg)
                    print(f"تم تنبيه فيلم: {title}")
            except:
                continue
    except Exception as e:
        print(f"خطأ في فوكس: {e}")

def check_tazkarti(driver):
    print("جاري فحص تذكرتي للمباريات...")
    try:
        driver.get(TAZKARTI_URL)
    
        time.sleep(8) 
        
        match_cards = driver.find_elements(By.CSS_SELECTOR, ".match-card, .card") 
        
        for card in match_cards:
            try:
                match_info = card.text
                if match_info and len(match_info) > 5 and match_info not in sent_matches:
                    sent_matches.add(match_info)
                    msg = f"⚽️ <b>مباراة جديدة متاحة على تذكرتي!</b>\n\n{match_info}\n🔗 <a href='{TAZKARTI_URL}'>ادخل احجز هنا</a>"
                    send_telegram_message(msg)
                    print("تم تنبيه مباراة جديدة")
            except:
                continue
    except Exception as e:
        print(f"خطأ في تذكرتي: {e}")

if __name__ == "__main__":
    print("🚀 جاري تشغيل البوت... اضغط Ctrl+C للإيقاف")
    driver = setup_browser()
    
    try:
        while True:
            check_vox_cinemas(driver)
            check_tazkarti(driver)
            
            print("⏳ انتظار 5 دقائق للفحص القادم...")
            time.sleep(300) # يفحص كل 5 دقائق
            
    except KeyboardInterrupt:
        print("تم إيقاف البوت.")
    finally:
        driver.quit()