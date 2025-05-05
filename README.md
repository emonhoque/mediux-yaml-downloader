# 🎞️ Mediux YAML Downloader

A Windows GUI tool to download episode poster images based on Mediux YAML configuration files and The Movie Database (TMDb) metadata.

## 📦 Features

- Paste YAML from [Mediux](https://mediux.pro) directly.
- Automatically fetch show titles and episode names from TMDb.
- Downloads missing episode title cards into the correct folder structure.
- Skips existing images automatically.
- Customizable destination directory.
- Built-in progress bar and logging.
- Easy to convert into a standalone `.exe`.

---

## ✅ Requirements

- Python 3.8 or higher
- Required Python packages:

```bash
pip install requests pyyaml
```

---

## 🛠️ How to Use

### 1. Copy YAML from Mediux

Click the `YAML` button on a Mediux set page to copy the configuration.

![Copy YAML from Mediux](img/img1.png)

Then copy the generated YAML block:

![YAML Config](img/img2.png)

### 2. Clone this repository or [download `mediux_titlecards_gui.py`](./mediux_titlecards_gui.py).

### 3. Insert your TMDb API key

Open `mediux_titlecards_gui.py` and replace:

```python
TMDB_API_KEY = "INSERT_TMDB_API_KEY"
```

with your personal API key from [TMDb Settings](https://www.themoviedb.org/settings/api).

### 4. Set your preferred default download location

Edit the `DEFAULT_FOLDER` variable in the script:

```python
DEFAULT_FOLDER = r"C:/Default/Destination/TitleCards"
```

You can still change this in the app UI.

### 5. Run the script

```bash
python mediux_titlecards_gui.py
```

Paste your copied YAML into the app and click "Start Download":

![Paste YAML and Download](img/img3.png)

You'll see progress and log output:

![Download in Progress](img/img4.png)

---

## 💾 Convert to EXE (Optional)

To turn the script into a standalone executable:

### 1. Install `pyinstaller`:

```bash
pip install pyinstaller
```

### 2. Run the following in the script directory:

```bash
python -m pyinstaller --noconsole --onefile --icon=mediuxdownload.ico mediux_titlecards_gui.py
```

> Ensure `mediuxdownload.ico` is in the same folder.

The `.exe` will be available in the `dist/` folder.

---

## 📂 Folder Structure

Downloaded images are saved to:

```
<Destination Folder>/Show Title (Year)/Season N/<Episode Filename>.jpg
```

Example:

```
D:/Title Cards/Andor (2022)/Season 1/Andor (2022) - S01E01 - Kassa.jpg
```

Example Output:

![Example Output](img/img5.png)

---

## 📜 License

MIT License
