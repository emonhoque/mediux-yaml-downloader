# mediux_titlecards_tvdb.py

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, simpledialog, messagebox
import threading
import os
import yaml
import requests
from datetime import datetime
from io import StringIO
import json
import sys

VERSION = "1.3"
CONFIG_FILE = "userconfig.json"
DEFAULT_FOLDER = r"C:/Default/Destination/TitleCards"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

config = load_config()
download_path = config.get("download_path", DEFAULT_FOLDER)

TVDB_API_KEY = config.get("TVDB_API_KEY", "")
TVDB_PIN = config.get("TVDB_PIN", "")
TOKEN = None

def prompt_for_tvdb_api_key():
    global TVDB_API_KEY, TVDB_PIN

    root = tk.Tk()
    root.withdraw()

    if not TVDB_API_KEY:
        TVDB_API_KEY = simpledialog.askstring("TVDB API Key", "Enter your TVDB API Key:", parent=root)
        if not TVDB_API_KEY:
            messagebox.showerror("Missing Key", "TVDB API Key is required.", parent=root)
            sys.exit(1)
        config["TVDB_API_KEY"] = TVDB_API_KEY

    if not TVDB_PIN:
        TVDB_PIN = simpledialog.askstring("TVDB PIN (Optional)", "Enter your TVDB PIN (press Cancel to skip):", parent=root) or ""
        config["TVDB_PIN"] = TVDB_PIN

    save_config(config)
    root.destroy()

def authenticate_tvdb():
    global TOKEN
    payload = {"apikey": TVDB_API_KEY}
    if TVDB_PIN:
        payload["pin"] = TVDB_PIN
    resp = requests.post("https://api4.thetvdb.com/v4/login", json=payload)
    if resp.ok:
        TOKEN = resp.json()["data"]["token"]
    else:
        raise Exception("TVDB Authentication failed.")

def get_headers():
    global TOKEN
    if not TOKEN:
        authenticate_tvdb()
    return {"Authorization": f"Bearer {TOKEN}"}

def get_show_info(tvdb_id):
    resp = requests.get(f"https://api4.thetvdb.com/v4/series/{tvdb_id}", headers=get_headers())
    if resp.ok:
        data = resp.json()["data"]
        title = data.get("name", "Unknown Title").replace(":", " -")
        year = data.get("firstAired", "0000")[:4]
        return title, year
    return None, None

def get_episode_titles(tvdb_id, season_number):
    result = {}
    page = 0
    while True:
        resp = requests.get(
            f"https://api4.thetvdb.com/v4/series/{tvdb_id}/episodes/default",
            headers=get_headers(),
            params={"page": page}
        )
        if not resp.ok:
            break
        data = resp.json()
        episodes = data.get("data", {}).get("episodes", []) if isinstance(data.get("data"), dict) else data.get("data", [])
        for ep in episodes:
            if ep.get("seasonNumber") == season_number:
                ep_num = str(ep.get("number"))
                ep_title = ep.get("name", "").strip()
                if ep_num and ep_title:
                    result[ep_num] = ep_title
        if not data.get("links", {}).get("next"):
            break
        page += 1
    return result

def download_image(url, dest_path):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
    except Exception:
        pass

def log(message, output_widget):
    timestamped = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    output_widget.insert(tk.END, timestamped + '\n')
    output_widget.see(tk.END)

def process_yaml(yaml_text, output_widget, base_folder, progress_var, progress_max):
    try:
        parsed = yaml.safe_load(StringIO(yaml_text))
    except Exception as e:
        log(f"Failed to parse YAML: {e}", output_widget)
        return

    total = sum(
        len(season.get("episodes", {}))
        for show in parsed.values()
        for season in show.get("seasons", {}).values()
    )
    progress_max.set(total)
    current = 0

    for tvdb_id, show_data in parsed.items():
        title, year = get_show_info(tvdb_id)
        if not title or not year:
            log(f"Could not get title/year for {tvdb_id}", output_widget)
            continue

        expected_prefix = f"{title} ({year})"
        show_folder = os.path.join(base_folder, expected_prefix)
        for entry in os.listdir(base_folder):
            full_path = os.path.join(base_folder, entry)
            if os.path.isdir(full_path) and entry.startswith(expected_prefix):
                show_folder = full_path
                break
        else:
            os.makedirs(show_folder, exist_ok=True)

        for season_num, season_data in show_data.get("seasons", {}).items():
            season_name = "Specials" if str(season_num) == "0" else f"Season {int(season_num)}"
            season_folder = os.path.join(show_folder, season_name)
            os.makedirs(season_folder, exist_ok=True)

            season_poster_url = season_data.get("url_poster")
            if season_poster_url:
                ext = os.path.splitext(season_poster_url)[1] or ".jpg"
                season_poster_name = f"specials{ext}" if str(season_num) == "0" else f"season{int(season_num):02}{ext}"
                dest = os.path.join(season_folder, season_poster_name)
                if not os.path.isfile(dest):
                    download_image(season_poster_url, dest)
                    log(f"Downloaded season poster: {dest}", output_widget)

            episode_titles = get_episode_titles(tvdb_id, int(season_num))
            for episode_num, ep_data in season_data.get("episodes", {}).items():
                ep_title = episode_titles.get(str(episode_num))
                ep_url = ep_data.get("url_poster")
                if not ep_url or not ep_title:
                    current += 1
                    progress_var.set(current)
                    continue

                filename = f"{title} ({year}) - S{int(season_num):02}E{int(episode_num):02} - {ep_title}.jpg"
                dest_path = os.path.join(season_folder, filename)
                if os.path.isfile(dest_path):
                    current += 1
                    progress_var.set(current)
                    continue

                download_image(ep_url, dest_path)
                log(f"Downloaded: {filename}", output_widget)
                current += 1
                progress_var.set(current)

        log(f"Finished processing {title} ({year})", output_widget)

    log("All done.", output_widget)

def start_thread(yaml_input, output_widget, folder_entry, progress_var, progress_max):
    base_folder = folder_entry.get().strip()
    config["download_path"] = base_folder
    save_config(config)
    threading.Thread(target=process_yaml, args=(
        yaml_input.get("1.0", tk.END),
        output_widget,
        base_folder,
        progress_var,
        progress_max
    )).start()

def browse_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)
        config["download_path"] = folder
        save_config(config)

def enable_right_click_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))

def main():
    prompt_for_tvdb_api_key()

    root = tk.Tk()
    root.title("Mediux YAML Downloader [TVDB]")
    root.geometry("850x720")
    root.configure(padx=20, pady=20)

    ttk.Label(root, text="Download Destination:").pack(anchor=tk.W)
    folder_entry = ttk.Entry(root, width=80)
    folder_entry.insert(0, config.get("download_path", DEFAULT_FOLDER))
    folder_entry.pack(fill=tk.X, pady=5)
    ttk.Button(root, text="Browse...", command=lambda: browse_folder(folder_entry)).pack(pady=(0, 10))

    ttk.Label(root, text="Paste YAML:").pack(anchor=tk.W)
    yaml_input = scrolledtext.ScrolledText(root, height=15, font=("Consolas", 10), wrap=tk.WORD)
    yaml_input.pack(fill=tk.BOTH, expand=True, pady=5)
    enable_right_click_menu(yaml_input)

    progress_var = tk.IntVar()
    progress_max = tk.IntVar()
    ttk.Label(root, text="Progress:").pack(anchor=tk.W, pady=(10, 0))
    progress = ttk.Progressbar(root, variable=progress_var, maximum=1)
    progress.pack(fill=tk.X, pady=5)
    progress_max.trace_add("write", lambda *_: progress.config(maximum=progress_max.get()))

    ttk.Button(root, text="Start Download", command=lambda: start_thread(yaml_input, output, folder_entry, progress_var, progress_max)).pack(pady=10)

    ttk.Label(root, text="Log Output:").pack(anchor=tk.W)
    output = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 10), wrap=tk.WORD)
    output.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
