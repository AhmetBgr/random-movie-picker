import pandas as pd
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json
import os

CONFIG_FILE = 'config.json'
df = pd.DataFrame()
title_types = []
genre_list = []

# --- Load & Save Config ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

config = load_config()
last_csv_path = config.get("csv_path", "")
last_api_key = config.get("api_key", "")

# --- GUI Setup ---

window = tk.Tk()
window.title("🎬 Random Movie Picker")

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

main_width = 450
main_height = 530
main_x = int(((screen_width - main_width) / 2) - (main_width / 2) - 55) 
main_y = int((screen_height - main_height) / 2)

window.geometry(f"{main_width}x{main_height}+{main_x}+{main_y}")
window.configure(bg="#f0f0f0")

# Updated fonts
font_label = ("Sitka Small", 10, "bold")
font_text = ("Sitka Small", 10)

# --- API Key + Load CSV (swapped with vertical separator) ---
top_frame = tk.Frame(window, bg="#f0f0f0")
top_frame.pack(fill="x", padx=10, pady=(10, 5))

def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path and load_csv_from_path(file_path):
        config['csv_path'] = file_path
        save_config(config)

# --- Load Button (Left) ---
load_button = ttk.Button(top_frame, text="📂 Load Movies(.csv)", command=load_csv)
load_button.pack(side="left")

# --- Vertical Separator ---
sep = ttk.Separator(top_frame, orient="vertical")
sep.pack(side="left", fill="y", padx=10, pady=2)

# --- API Entry (Right) ---
api_key_var = tk.StringVar(value=last_api_key)
api_label = tk.Label(top_frame, text="🔑 OMDb API Key:", font=font_text, bg="#f0f0f0", fg="#333")
api_label.pack(side="left", padx=(5, 5))

api_entry = ttk.Entry(top_frame, textvariable=api_key_var, font=font_text, show="*")
api_entry.pack(side="left", fill="x", expand=True)

def update_api_key(*args):
    config['api_key'] = api_key_var.get().strip()
    save_config(config)

api_key_var.trace_add("write", update_api_key)

# --- Separator Line ---
separator = ttk.Separator(window, orient="horizontal")
separator.pack(fill="x", padx=10, pady=(10, 15))

# --- CSV Loader ---
def load_csv_from_path(file_path):
    try:
        global df, title_types, genre_list
        df = pd.read_csv(file_path)
        df.dropna(subset=['Title'], inplace=True)

        title_types = sorted(df['Title Type'].dropna().unique())
        all_genres = set()
        for genres in df['Genres'].dropna():
            for genre in genres.split(','):
                all_genres.add(genre.strip())
        genre_list = sorted(all_genres)

        type_dropdown['values'] = ["Any"] + title_types
        type_dropdown.current(0)
        genre_dropdown['values'] = ["Any"] + genre_list
        genre_dropdown.current(0)

        pick_button.config(state=tk.NORMAL)
        messagebox.showinfo("Success", f"Loaded {len(df)} titles from CSV.")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file:\n{e}")
        return False

# --- Filter: Type ---
tk.Label(window, text="🎞️ Type:", font=font_label, bg="#f0f0f0", fg="#333").pack(pady=(10, 5))
type_var = tk.StringVar()
type_dropdown = ttk.Combobox(window, textvariable=type_var, values=["Any"], font=font_text)
type_dropdown.current(0)
type_dropdown.pack(padx=10)

# --- Filter: Genre ---
tk.Label(window, text="🎭 Genre:", font=font_label, bg="#f0f0f0", fg="#333").pack(pady=(10, 5))
genre_var = tk.StringVar()
genre_dropdown = ttk.Combobox(window, textvariable=genre_var, values=["Any"], font=font_text)
genre_dropdown.current(0)
genre_dropdown.pack(padx=10)

# --- Filter: Keyword ---
tk.Label(window, text="🔍 Keyword (Title / Director):", font=font_label, bg="#f0f0f0", fg="#333").pack(pady=(10, 5))
keyword_var = tk.StringVar()
keyword_entry = ttk.Entry(window, textvariable=keyword_var, font=font_text)
keyword_entry.pack(padx=10)

# --- Year Filters ---
tk.Label(window, text="📅 Year Min:", font=font_label, bg="#f0f0f0", fg="#333").pack(pady=(10, 5))
min_year_var = tk.IntVar(value=1900)
min_year_spin = ttk.Spinbox(window, from_=1900, to_=2025, textvariable=min_year_var, font=font_text)
min_year_spin.pack(padx=10)

tk.Label(window, text="📅 Year Max:", font=font_label, bg="#f0f0f0", fg="#333").pack(pady=(10, 5))
max_year_var = tk.IntVar(value=2025)
max_year_spin = ttk.Spinbox(window, from_=1900, to_=2025, textvariable=max_year_var, font=font_text)
max_year_spin.pack()

# --- Poster + Movie Display ---
def fetch_poster(imdb_id):
    api_key = api_key_var.get().strip()
    if not api_key:
        return None, "No API key provided."
    url = f"http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}"
    try:
        r = requests.get(url)
        data = r.json()
        return data.get('Poster'), data.get('Plot', 'No description.')
    except:
        return None, "Failed to fetch data."

def pick_movie(filtered):
    movie = filtered.sample().iloc[0]
    poster_url, plot = fetch_poster(movie['Const'])

    top = tk.Toplevel()
    top.title(movie['Title'])
    top.configure(bg="#ffffff")

    detail_width = 725
    detail_height = 530
    detail_x = int(((screen_width - detail_width) / 2) + (detail_width / 2) - 45) 
    detail_y = int((screen_height - detail_height) / 2)

    top.geometry(f"{detail_width}x{detail_height}+{detail_x}+{detail_y}")

    # --- Title ---
    tk.Label(top, text=movie['Title'], font=("Sitka Small", 16, "bold"), bg="#ffffff").pack(pady=(10, 5))

    # --- Main Frame (horizontal layout) ---
    main_frame = tk.Frame(top, bg="#ffffff")
    main_frame.pack(padx=10, pady=5, fill="both", expand=True)

    # --- Poster on Left ---
    if poster_url and poster_url != 'N/A':
        try:
            img_data = requests.get(poster_url).content
            img = Image.open(BytesIO(img_data)).resize((300, 450))
            img_tk = ImageTk.PhotoImage(img)
            poster_label = tk.Label(main_frame, image=img_tk, bg="#ffffff")
            poster_label.image = img_tk
            poster_label.pack(side="left", padx=(0, 15), pady=10)
        except:
            pass



    # --- Right Info Panel ---
    info_panel = tk.Frame(main_frame, bg="#ffffff")
    info_panel.pack(side="left", fill="both", expand=True)

    # --- Vertical Separator ---
    sep = ttk.Separator(info_panel, orient="vertical")
    sep.pack(side="left", fill="y", padx=10, pady=2)

    def info_row(label, value):
        tk.Label(info_panel, text=label, font=("Sitka Small", 10, "bold"), bg="#ffffff", anchor="w").pack(fill="x", padx=5)
        tk.Label(info_panel, text=value or "N/A", font=("Sitka Small", 10), bg="#ffffff", anchor="w", wraplength=350).pack(fill="x", padx=5, pady=(0, 5))

    info_row("⭐ IMDb Rating:", movie.get('IMDb Rating'))
    info_row("📅 Year:", str(movie.get('Year')))
    info_row("🎞️ Genres:", movie.get('Genres'))
    info_row("🎬 Directors:", movie.get('Directors'))
    info_row("📝 Plot:", plot)

    # --- Next Movie Button ---
    next_button = tk.Button(info_panel, text="🎬 Next Movie", font=("Sitka Small", 12, "bold"),
                            bg="#337ab7", fg="white", activebackground="#286090", relief="raised",
                            command=lambda: [top.destroy(), pick_movie(filtered)])
    next_button.pack(pady=10)

def filter_movies():
    if df.empty:
        messagebox.showerror("No Data", "Please load a CSV file first.")
        return

    filtered = df.copy()

    selected_type = type_var.get()
    selected_genre = genre_var.get()
    min_year = min_year_var.get()
    max_year = max_year_var.get()
    keyword = keyword_var.get().strip().lower()

    if selected_type != "Any":
        filtered = filtered[filtered['Title Type'] == selected_type]

    if selected_genre != "Any":
        filtered = filtered[filtered['Genres'].str.contains(selected_genre, na=False)]

    filtered = filtered[(filtered['Year'] >= min_year) & (filtered['Year'] <= max_year)]

    if keyword:
        filtered = filtered[
            filtered['Title'].str.lower().str.contains(keyword, na=False) |
            filtered['Genres'].str.lower().str.contains(keyword, na=False) |
            filtered['Directors'].str.lower().str.contains(keyword, na=False)
        ]

    if filtered.empty:
        messagebox.showinfo("No Match", "No movies match the selected filters.")
        return

    pick_movie(filtered)

# --- Pick Button ---
pick_button = tk.Button(window, text="🎲 Pick a Movie", font=("Sitka Small", 14, "bold"), bg="#28a745", fg="white",
                        activebackground="#218838", relief="raised", command=filter_movies, state=tk.DISABLED)
pick_button.pack(pady=20)

# --- Auto-load Last CSV ---
if last_csv_path and os.path.exists(last_csv_path):
    load_csv_from_path(last_csv_path)

#api_entry.focus_set()
window.focus_force()
window.mainloop()
