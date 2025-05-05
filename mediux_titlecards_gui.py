import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os
import yaml
import requests
from datetime import datetime
from io import StringIO

TMDB_API_KEY = "INSERT_TMDB_API_KEY"
DEFAULT_FOLDER = r"C:/Default/Destination/TitleCards"

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

        for season_num, season_data in show_data.get("seasons", {}).items():
            season_folder = os.path.join(show_folder, f"Season {season_num}")
            os.makedirs(season_folder, exist_ok=True)

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

# === GUI ===

def start_thread(yaml_input, output_widget, folder_entry, progress_var, progress_max):
    base_folder = folder_entry.get().strip()
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

def main():
    root = tk.Tk()
    root.title("Mediux Title Card Downloader")
    root.geometry("850x720")
    root.configure(padx=20, pady=20)

    ttk.Label(root, text="Download Destination:").pack(anchor=tk.W)
    folder_entry = ttk.Entry(root, width=80)
    folder_entry.insert(0, DEFAULT_FOLDER)
    folder_entry.pack(fill=tk.X, pady=5)
    ttk.Button(root, text="Browse...", command=lambda: browse_folder(folder_entry)).pack(pady=(0, 10))

    ttk.Label(root, text="Paste YAML:").pack(anchor=tk.W)
    yaml_input = scrolledtext.ScrolledText(root, height=15, font=("Consolas", 10), wrap=tk.WORD)
    yaml_input.pack(fill=tk.BOTH, expand=True, pady=5)

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
