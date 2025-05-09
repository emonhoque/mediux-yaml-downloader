# 🎞️ Mediux YAML Downloader

A desktop GUI tool (tested on Windows) to download episode title cards, show posters, season posters, and backgrounds based on Mediux YAML configuration files using either:

- **TMDb (The Movie Database)**  
- **TVDb (TheTVDB v4)**

---

## 📦 Features

- Paste YAML from [Mediux](https://mediux.pro) directly
- Choose **TMDb** or **TVDb** version based on your metadata preference
- Automatically fetch show titles and episode names
- Downloads:
  - 🖼️ Missing **episode title cards**
  - 🎭 **Show posters** as `poster.jpg`
  - 🌌 **Backgrounds** as `background.jpg`
  - 📦 **Season posters** as `seasonXX.jpg`, or `specials.jpg` for Season 0
- Folder `Season 0` is renamed to `Specials`
- Skips already downloaded images automatically
- Persistent settings:
  - Remembers your **API key** (TMDb or TVDb)
  - Remembers your last used download folder
- Built-in progress bar and real-time logging
- GUI for folder browsing and API key management
- Easy to convert into a standalone `.exe`

---

## ✅ Requirements

- Python 3.8 or higher
- Install dependencies:

```bash
pip install requests pyyaml
```

---

## 🚀 Which Version Should I Use?

Download or run **one** of the following depending on which service you'd like to use for metadata:

| File | API Used | Requires |
|------|----------|----------|
| `mediux_titlecards_tmdb.py` | TMDb | TMDb API Key (Required) |
| `mediux_titlecards_tvdb.py` | TVDb | TVDb API Key (Required) + PIN (Optional) |

You can find both in this repo.

---

## 🛠️ How to Use

### 1. Run your preferred script

```bash
# For TMDb
python mediux_titlecards_tmdb.py

# For TVDb
python mediux_titlecards_tvdb.py
```

---

### 2. First-time setup

- The app will ask for your **API key** (TMDb or TVDb depending on the version)
- For TVDb, **PIN is optional**
- Choose a destination folder
- Both are saved in `userconfig.json`

---

### 3. Copy YAML from Mediux

Click the `YAML` button on any Mediux set page.

![Copy YAML from Mediux](img/img1.png)

Then paste the YAML block into the app and click **Start Download**:

![Paste YAML and Download](img/img3.png)

Watch the download progress and logs:

![Download in Progress](img/img4.png)

---

## 📂 Folder Structure

Downloaded images are saved to:

```
<Destination Folder>/
  └── Show Title (Year)/
      ├── poster.jpg
      ├── background.jpg
      ├── Specials/
      │   ├── specials.jpg
      │   └── Episode cards...
      └── Season 1/
          ├── season01.jpg
          └── Episode cards...
```

Example:

```
D:/Title Cards/Andor (2022)/Season 1/Andor (2022) - S01E01 - Kassa.jpg
```

---

## 💾 Convert to EXE (Optional)

To build a Windows executable:

```bash
pip install pyinstaller
python -m pyinstaller --noconsole --onefile --icon=mediuxdownload.ico mediux_titlecards_tmdb.py
# Or
python -m pyinstaller --noconsole --onefile --icon=mediuxdownload.ico mediux_titlecards_tvdb.py
```

The `.exe` will be located in the `dist/` folder.

---

## 📘 License

MIT © 2025 Emon Hoque
