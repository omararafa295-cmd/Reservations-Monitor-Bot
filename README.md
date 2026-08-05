# 🎬 Vox Cinemas Almaza — Showtime Monitor Bot

An automated bot that watches **Vox Cinemas, City Centre Almaza** for new showtimes across all currently open booking dates, and sends a real-time alert to Telegram the moment a new time slot becomes available for booking.

Runs on a schedule via **GitHub Actions** — no server required.

---

## 🚀 Want to use this yourself?

This bot doesn't message you directly — you run your own copy, connected to your own Telegram bot. That takes about 5 minutes:

1. **Fork** this repository.
2. Message [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot`, and save the token it gives you.
3. Add that token (and your chat ID — see [Setup](#️-setup) below) as **GitHub Secrets** in your fork.
4. Enable **Read and write permissions** for the workflow (see [Setup](#️-setup)).
5. Go to the **Actions** tab and run the workflow manually once to confirm it works — after that, it runs on its own schedule.

Full step-by-step details are in the [Setup](#️-setup) section below.

---

## ✨ Features

- **Auto-discovers open dates** — reads the date tabs directly from the site, so it automatically covers every day currently open for booking (no hardcoded dates to maintain).
- **Rich, structured alerts** — each message includes the movie title, age rating, language, duration, cinema hall (GOLD / IMAX / MAX / 4DX / Standard...), and a direct booking link per showtime.
- **Smart deduplication** — every showtime is tracked individually, so you're only notified once per new slot, never spammed with repeats.
- **Past-showtime filtering** — times that have already passed today are automatically ignored, since they can never become bookable again.
- **Resilient scraping** — uses a fresh browser session per date to avoid known headless-Chrome networking issues, with automatic retries on slow loads.

---

## 🖼 Example Alert

```
🎬 The Odyssey
🏷 16+ | English | 175 min
📅 Today

🍿 GOLD: 11:30am | 2:00pm | 4:30pm
🍿 Standard: 12:30pm | 3:15pm

ℹ️ Movie Info
```

---

## 🛠 Tech Stack

| Component | Purpose |
|---|---|
| Python 3.11 | Core scripting |
| Selenium | Headless browser automation |
| Telegram Bot API | Delivering alerts |
| GitHub Actions | Scheduled, serverless execution |

---

## 📁 Project Structure

```
.
├── monitor.py               # Main bot script
├── requirements.txt         # Python dependencies
├── sent.txt                 # Persisted record of already-notified showtimes
└── .github/
    └── workflows/
        └── main.yml          # Scheduled GitHub Actions workflow
```

---

## ⚙️ Setup

### 1. Create a Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram and run `/newbot`.
2. Save the token it gives you.
3. Message your new bot once (e.g. `/start`) so it can message you back.
4. Get your chat ID by visiting:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

### 2. Configure Repository Secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TELEGRAM_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

> ⚠️ Never commit tokens directly into the code. This project reads both values exclusively from environment variables / GitHub Secrets.

### 3. Enable Workflow Permissions
In **Settings → Actions → General → Workflow permissions**, make sure **Read and write permissions** is selected — the bot commits `sent.txt` back to the repo after each run to persist what's already been sent.

### 4. Run It
The workflow runs automatically on the schedule defined in `.github/workflows/main.yml`. You can also trigger it manually from the **Actions** tab via **Run workflow**.

---

## 🔁 Changing the Schedule

Edit the `cron` expression in `.github/workflows/main.yml`:

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'   # every 15 minutes
  workflow_dispatch:          # allows manual runs from the Actions tab
```

---

## 🐛 Debugging

If a run fails to find showtimes, it automatically saves a screenshot and the page's HTML as workflow artifacts (`debug-snapshots`) so you can inspect exactly what the bot saw. Download them from the run's summary page under **Artifacts**.

---

## 📄 License

For personal use. Not affiliated with or endorsed by Vox Cinemas.
