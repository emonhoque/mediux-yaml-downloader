# mediux_titlecards_gui.py

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os
import yaml
import requests
from datetime import datetime
from io import StringIO
import sys
import json
from tkinter import simpledialog, messagebox

VERSION = "1.0"
CONFIG_FILE = "userconfig.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

config = load_config()
TMDB_API_KEY = config.get("TMDB_API_KEY", "")
DEFAULT_FOLDER = config.get("download_path", r"C:/Default/Destination/TitleCards")

if not TMDB_API_KEY:
    temp_root = tk.Tk()
    temp_root.withdraw()
    TMDB_API_KEY = simpledialog.askstring("TMDB API Key", "Enter your TMDB API Key:", parent=temp_root)
    if TMDB_API_KEY:
        config["TMDB_API_KEY"] = TMDB_API_KEY
        save_config(config)
    else:
        messagebox.showerror("Error", "TMDB API Key is required.", parent=temp_root)
        sys.exit(1)
    temp_root.destroy()

def change_api_key(root):
    global TMDB_API_KEY
    new_key = simpledialog.askstring("Update TMDB API Key", "Enter new TMDB API Key:", parent=root)
    if new_key:
        TMDB_API_KEY = new_key
        config["TMDB_API_KEY"] = new_key
        save_config(config)
        messagebox.showinfo("Success", "TMDB API Key updated successfully.", parent=root)

def show_version_info(root):
    messagebox.showinfo("About", f"Mediux YAML Downloader\nVersion {VERSION}", parent=root)

def log(message, output_widget):
    timestamped = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    output_widget.insert(tk.END, timestamped + '\n')
    output_widget.see(tk.END)

def get_tmdb_id(tvdb_id):
    url = f"https://api.themoviedb.org/3/find/{tvdb_id}?api_key={TMDB_API_KEY}&external_source=tvdb_id"
    resp = requests.get(url)
    if resp.ok:
        results = resp.json().get("tv_results", [])
        return results[0]["id"] if results else None
    return None

def get_show_info(tmdb_id):
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_API_KEY}"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        title = data["name"].replace(":", " -")
        year = data["first_air_date"][:4]
        return title, year
    return None, None

def get_episode_titles(tmdb_id, season_number):
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?api_key={TMDB_API_KEY}"
    resp = requests.get(url)
    if resp.ok:
        episodes = resp.json().get("episodes", [])
        return {str(ep["episode_number"]): ep["name"] for ep in episodes}
    return {}

def download_image(url, dest_path):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
    except Exception:
        pass

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
        tmdb_id = get_tmdb_id(tvdb_id)
        if not tmdb_id:
            log(f"TMDb ID not found for TVDB ID {tvdb_id}", output_widget)
            continue

        title, year = get_show_info(tmdb_id)
        if not title or not year:
            log(f"Could not get title/year for {tvdb_id}", output_widget)
            continue

        show_folder = os.path.join(base_folder, f"{title} ({year})")
        os.makedirs(show_folder, exist_ok=True)

        show_poster_url = show_data.get("url_poster")
        show_background_url = show_data.get("url_background")
        if show_poster_url:
            ext = os.path.splitext(show_poster_url)[1] or ".jpg"
            dest = os.path.join(show_folder, f"poster{ext}")
            if not os.path.isfile(dest):
                download_image(show_poster_url, dest)
                log(f"Downloaded show poster: {dest}", output_widget)
        if show_background_url:
            ext = os.path.splitext(show_background_url)[1] or ".jpg"
            dest = os.path.join(show_folder, f"background{ext}")
            if not os.path.isfile(dest):
                download_image(show_background_url, dest)
                log(f"Downloaded background: {dest}", output_widget)

        for season_num, season_data in show_data.get("seasons", {}).items():
            season_name = "Specials" if str(season_num) == "0" else f"Season {int(season_num):02}"
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

            episode_titles = get_episode_titles(tmdb_id, season_num)
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

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)

def main():
    root = tk.Tk()
    root.title("Mediux YAML Downloader")
    root.geometry("850x720")
    root.configure(padx=20, pady=20)

    menubar = tk.Menu(root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Change TMDB API Key", command=lambda: change_api_key(root))
    settings_menu.add_separator()
    settings_menu.add_command(label="About / Version", command=lambda: show_version_info(root))
    menubar.add_cascade(label="Settings", menu=settings_menu)
    root.config(menu=menubar)

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
