import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

VOX_BASE_URL = 'https://egy.voxcinemas.com/showtimes?c=city-centre-almaza'
TAZKARTI_URL = 'https://www.tazkarti.com/#/matches'
SENT_FILE = 'sent.txt'

EGYPT_TZ = ZoneInfo("Africa/Cairo")

HALL_NAME_DISPLAY = {
    "gold": "GOLD",
    "imax": "IMAX",
    "max": "MAX",
    "4dx": "4DX",
    "standard": "Standard",
    "kids": "Kids",
    "vip": "VIP",
}


def normalize_hall_name(raw_name):
    key = raw_name.strip().lower()
    return HALL_NAME_DISPLAY.get(key, raw_name.strip())


def now_egypt():
    return datetime.now(EGYPT_TZ)


def today_egypt():
    return now_egypt().date()


def date_label(d):
    diff = (d - today_egypt()).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Tomorrow"
    return d.strftime('%a %d %b')


def vox_url_for_date(d):
    if d == today_egypt():
        return VOX_BASE_URL
    return f"{VOX_BASE_URL}&d={d.strftime('%Y%m%d')}"


def parse_showtime_dt(target_date, time_text):
    try:
        t = datetime.strptime(time_text.strip().lower(), "%I:%M%p").time()
    except ValueError:
        return None
    return datetime.combine(target_date, t, tzinfo=EGYPT_TZ)


def load_sent_items():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


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
        resp = requests.post(url, json=payload, timeout=15)
        if not resp.ok:
            print(f"Telegram API error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def new_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver


def save_debug_snapshot(driver, name):
    try:
        driver.save_screenshot(f"debug_{name}.png")
        with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Saved debug snapshot for {name}")
    except Exception as e:
        print(f"Could not save debug snapshot for {name}: {e}")


def load_vox_page(driver, url, timeout=25, retries=2, pause_between=3):
    last_error = None
    for attempt in range(1, retries + 2):
        try:
            driver.get(url)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.movie-compare"))
            )
            return True
        except Exception as e:
            last_error = e
            print(f"     Attempt {attempt} failed for {url}: {e.__class__.__name__}")
            time.sleep(pause_between)
    print(f"     Giving up on {url}. Last error: {last_error}")
    return False


def discover_open_dates(driver):
    dates = [today_egypt()]
    nav_links = driver.find_elements(By.CSS_SELECTOR, "nav.date-filter li a[href]")
    for link in nav_links:
        href = link.get_attribute("href") or ""
        match = re.search(r'[?&]d=(\d{8})', href)
        if match:
            d = datetime.strptime(match.group(1), '%Y%m%d').date()
            dates.append(d)
    return sorted(set(dates))


def extract_movies(driver):
    movies = []
    articles = driver.find_elements(By.CSS_SELECTOR, "article.movie-compare")

    for article in articles:
        try:
            title_el = article.find_elements(By.TAG_NAME, "h2")
            title = title_el[0].text.strip() if title_el else "Unknown Movie"

            rating_el = article.find_elements(By.CSS_SELECTOR, "span.classification")
            rating = rating_el[0].text.strip() if rating_el else ""

            tag_els = article.find_elements(By.CSS_SELECTOR, "span.tag")
            tags = [t.text.strip() for t in tag_els if t.text.strip()]
            language = tags[0] if len(tags) > 0 else ""
            duration = tags[1] if len(tags) > 1 else ""

            info_link_el = article.find_elements(By.CSS_SELECTOR, "a.read-more")
            info_link = info_link_el[0].get_attribute("href") if info_link_el else ""

            halls = []
            hall_groups = article.find_elements(By.CSS_SELECTOR, "div.dates ol.showtimes > li")
            for hall in hall_groups:
                strong_el = hall.find_elements(By.TAG_NAME, "strong")
                raw_hall_name = strong_el[0].text.strip() if strong_el else "Standard"
                hall_name = normalize_hall_name(raw_hall_name)

                showtimes = []
                time_items = hall.find_elements(By.CSS_SELECTOR, "ol > li")
                for item in time_items:
                    booking_id = item.get_attribute("data-id") or ""
                    link_el = item.find_elements(By.CSS_SELECTOR, "a.showtime")
                    if not link_el:
                        continue
                    time_text = link_el[0].text.strip()
                    link = link_el[0].get_attribute("href")
                    if booking_id and time_text and link:
                        showtimes.append({
                            "booking_id": booking_id,
                            "time": time_text,
                            "link": link,
                        })

                if showtimes:
                    halls.append({"name": hall_name, "showtimes": showtimes})

            if halls:
                movies.append({
                    "title": title,
                    "rating": rating,
                    "language": language,
                    "duration": duration,
                    "info_link": info_link,
                    "halls": halls,
                })
        except Exception as e:
            print(f"Error parsing a movie article: {e}")
            continue

    return movies


def format_vox_message(movie, day_label, new_showtimes_by_hall):
    meta_parts = [p for p in [movie["rating"], movie["language"], movie["duration"]] if p]
    meta_line = " | ".join(meta_parts)

    lines = [f"🎬 <b>{movie['title']}</b>"]
    if meta_line:
        lines.append(f"🏷 {meta_line}")
    lines.append(f"📅 <b>{day_label}</b>")
    lines.append("")

    for hall_name, showtimes in new_showtimes_by_hall.items():
        time_links = " | ".join(f"<a href='{s['link']}'>{s['time']}</a>" for s in showtimes)
        lines.append(f"🍿 <b>{hall_name}:</b> {time_links}")

    if movie["info_link"]:
        lines.append("")
        lines.append(f"ℹ️ <a href='{movie['info_link']}'>Movie Info</a>")

    return "\n".join(lines)


def process_movies_for_date(movies, target_date, sent_items):
    day_label = date_label(target_date)
    today = today_egypt()
    current_time = now_egypt()
    total_new = 0

    for movie in movies:
        new_by_hall = {}
        for hall in movie["halls"]:
            new_showtimes = []
            for s in hall["showtimes"]:
                if target_date == today:
                    showtime_dt = parse_showtime_dt(target_date, s["time"])
                    if showtime_dt and showtime_dt < current_time:
                        continue

                dedupe_key = f"vox:{target_date.isoformat()}:{s['booking_id']}"
                if dedupe_key not in sent_items:
                    save_sent_item(dedupe_key)
                    sent_items.add(dedupe_key)
                    new_showtimes.append(s)
            if new_showtimes:
                new_by_hall[hall["name"]] = new_showtimes

        if new_by_hall:
            msg = format_vox_message(movie, day_label, new_by_hall)
            send_telegram_message(msg)
            total_new += sum(len(v) for v in new_by_hall.values())

    return total_new


def check_vox_cinemas(sent_items):
    print("Checking Vox Cinemas Almaza...")
    total_new = 0

    driver = new_browser()
    try:
        ok = load_vox_page(driver, VOX_BASE_URL)
        if not ok:
            save_debug_snapshot(driver, "vox_today")
            return
        dates_to_check = discover_open_dates(driver)
        print(f"  Dates currently open for booking: {[d.isoformat() for d in dates_to_check]}")

        today = today_egypt()
        movies_today = extract_movies(driver)
        total_new += process_movies_for_date(movies_today, today, sent_items)
    finally:
        driver.quit()

    for target_date in dates_to_check:
        if target_date == today:
            continue

        url = vox_url_for_date(target_date)
        print(f"  -> Checking {date_label(target_date)} ({url})")

        driver = new_browser()
        try:
            ok = load_vox_page(driver, url)
            if not ok:
                save_debug_snapshot(driver, f"vox_{target_date.isoformat()}")
                continue
            movies = extract_movies(driver)
            total_new += process_movies_for_date(movies, target_date, sent_items)
        finally:
            driver.quit()

        time.sleep(2)

    print(f"Found and processed {total_new} new showtimes in Vox.")


def check_tazkarti(sent_items):
    print("Checking Tazkarti...")
    driver = new_browser()
    try:
        driver.get(TAZKARTI_URL)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "mat-card"))
            )
        except Exception:
            print("Timed out waiting for Tazkarti 'mat-card' elements; falling back to div scan.")

        cards = driver.find_elements(By.TAG_NAME, "mat-card")
        if not cards:
            cards = driver.find_elements(By.TAG_NAME, "div")

        count = 0
        for card in cards:
            try:
                info = card.text.strip()
                if info and len(info) > 10 and ("vs" in info.lower() or "استاد" in info):
                    flat_info = info.replace('\n', ' - ')
                    dedupe_key = f"tazkarti:{flat_info}"
                    if dedupe_key not in sent_items:
                        save_sent_item(dedupe_key)
                        sent_items.add(dedupe_key)
                        msg = f"⚽️ <b>Tazkarti Match Update!</b>\n\n{flat_info}\n\n🎟 <a href='{TAZKARTI_URL}'>Book Here</a>"
                        send_telegram_message(msg)
                        count += 1
            except Exception:
                continue

        print(f"Found and processed {count} new items in Tazkarti.")
        if count == 0:
            save_debug_snapshot(driver, "tazkarti")
    except Exception as e:
        print(f"Tazkarti Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    print("Starting Bot...")
    sent_items = load_sent_items()

    check_vox_cinemas(sent_items)
    check_tazkarti(sent_items)

    print("Done.")