import os
import shutil
import subprocess
import threading
import re
import json
import urllib.request
import urllib.parse
import zipfile
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from pathlib import Path

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(key, value):
    config = load_config()
    config[key] = value
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def crear_acceso_directo_escritorio(nombre_juego, ruta_juego):
    try:
        exe_principal = None
        for root_dir, dirs, files in os.walk(ruta_juego):
            for file in files:
                if file.lower().endswith(".exe") and not any(x in file.lower() for x in ["crash", "redist", "setup", "unins", "unity", "dotnet"]):
                    exe_principal = os.path.join(root_dir, file)
                    break
            if exe_principal:
                break

        if not exe_principal:
            return False

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, f"{nombre_juego}.lnk")
        
        vbs_script = f"""
        Set WshShell = WScript.CreateObject("WScript.Shell")
        Set shortcut = WshShell.CreateShortcut("{shortcut_path}")
        shortcut.TargetPath = "{exe_principal}"
        shortcut.WorkingDirectory = "{os.path.dirname(exe_principal)}"
        shortcut.WindowStyle = 1
        shortcut.Save
        """
        vbs_path = os.path.join(os.environ.get("TEMP", "."), "create_shortcut.vbs")
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_script)

        subprocess.run(["cscript", "//Nologo", vbs_path], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if os.path.exists(vbs_path):
            os.remove(vbs_path)
        return True
    except:
        return False

class SteamUnboundApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SteamUnbound")
        self.root.geometry("650x720")
        self.root.minsize(600, 650)

        try:
            icon_path = os.path.join("assets", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        self.config_data = load_config()
        self.selected_appid = None
        self.selected_game_name = None
        self.search_after_id = None
        self.avatar_temp = self.config_data.get("avatar_path", "")

        self.bg_black = "#0a0710"      
        self.panel_dark = "#140e1f"    
        self.accent_violet = "#4a154b" 
        self.accent_hover = "#632065"  
        self.text_light = "#e0d6eb"    
        self.text_muted = "#a399b2"    

        self.root.configure(bg=self.bg_black)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.bg_black, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.panel_dark, foreground=self.text_muted, padding=[12, 6], font=('Tahoma', 9, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.accent_violet)], foreground=[('selected', '#ffffff')])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        self.tab_download = tk.Frame(self.notebook, bg=self.bg_black)
        self.tab_settings = tk.Frame(self.notebook, bg=self.bg_black)

        self.notebook.add(self.tab_download, text=" Download ")
        self.notebook.add(self.tab_settings, text=" Settings ")

        self.build_download_tab()
        self.build_settings_tab()

    def build_download_tab(self):
        search_frame = tk.Frame(self.tab_download, bg=self.bg_black)
        search_frame.pack(fill="x", padx=12, pady=(10, 5))

        lbl_search = tk.Label(search_frame, text="Game Search:", fg=self.text_light, bg=self.bg_black, font=("Tahoma", 9, "bold"))
        lbl_search.pack(side="top", anchor="w", pady=(0, 2))

        self.e_search = tk.Entry(search_frame, font=("Tahoma", 10), bg=self.panel_dark, fg=self.text_light, insertbackground="white", relief="solid", bd=1)
        self.e_search.pack(side="top", fill="x", pady=(0, 2), ipady=3)
        self.e_search.bind("<KeyRelease>", self.on_search_key_release)

        self.listbox_sugerencias = tk.Listbox(self.tab_download, height=3, font=("Tahoma", 9), bg=self.panel_dark, fg=self.text_light, selectbackground=self.accent_violet, bd=1, relief="solid")
        self.listbox_sugerencias.bind("<ButtonRelease-1>", self.seleccionar_sugerencia)

        details_frame = tk.LabelFrame(self.tab_download, text=" Game Details ", bg=self.bg_black, fg=self.text_light, font=("Tahoma", 9, "bold"), bd=1, relief="solid")
        details_frame.pack(fill="both", expand=True, padx=12, pady=5)

        self.lbl_game_title = tk.Label(details_frame, text="No game selected", fg="#d1a3ff", bg=self.bg_black, font=("Tahoma", 10, "bold"))
        self.lbl_game_title.pack(anchor="w", padx=10, pady=2)

        lang_frame = tk.Frame(details_frame, bg=self.bg_black)
        lang_frame.pack(fill="x", padx=10, pady=2)
        tk.Label(lang_frame, text="Language:", fg=self.text_light, bg=self.bg_black, font=("Tahoma", 9)).pack(side="left", padx=(0, 5))
        
        self.language_var = tk.StringVar(value="english")
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, values=["english", "spanish", "french", "german", "italian", "brazilian"], state="readonly", width=15)
        self.lang_combo.pack(side="left")

        self.text_meta = tk.Text(details_frame, height=4, bg=self.panel_dark, fg=self.text_light, font=("Tahoma", 9), relief="solid", bd=1, insertbackground="white")
        self.text_meta.pack(fill="both", expand=True, padx=10, pady=3)
        self.text_meta.insert("1.0", "Type in the search bar above to look up a game from Steam.")
        self.text_meta.config(state="disabled")

        self.btn_download = tk.Button(details_frame, text="Install Game", bg=self.accent_violet, fg="#ffffff", font=("Tahoma", 9, "bold"), relief="flat", activebackground=self.accent_hover, activeforeground="white", state="disabled", command=self.iniciar_proceso_instalacion, cursor="hand2")
        self.btn_download.pack(fill="x", padx=10, pady=5, ipady=2)

        log_frame = tk.LabelFrame(self.tab_download, text=" Activity Log & Progress ", bg=self.bg_black, fg=self.text_light, font=("Tahoma", 9, "bold"), bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(5, 10))

        self.text_log = tk.Text(log_frame, height=5, bg=self.panel_dark, fg=self.text_light, font=("Tahoma", 8), relief="solid", bd=1, state="disabled")
        self.text_log.pack(fill="both", expand=True, padx=8, pady=5)

        self.progress = ttk.Progressbar(log_frame, orient="horizontal", mode="determinate", length=400)
        self.progress.pack(fill="x", padx=8, pady=(0, 5))

    def log_message(self, message):
        def _update():
            self.text_log.config(state="normal")
            self.text_log.insert(tk.END, message + "\n")
            self.text_log.see(tk.END)
            self.text_log.config(state="disabled")
        self.root.after(0, _update)

    def build_settings_tab(self):
        f = tk.Frame(self.tab_settings, bg=self.bg_black)
        f.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(f, text="Hubcap / Morrenus API Key:", fg=self.text_light, bg=self.bg_black, font=("Tahoma", 9, "bold")).pack(anchor="w", pady=(5, 2))
        self.e_key = tk.Entry(f, width=50, font=("Tahoma", 9), show="*", bg=self.panel_dark, fg=self.text_light, insertbackground="white", relief="solid", bd=1)
        self.e_key.pack(anchor="w", pady=(0, 10), ipady=3)
        saved_key = self.config_data.get("api_key", "")
        if saved_key:
            self.e_key.insert(0, saved_key)

        tk.Label(f, text="Player Nickname (Goldberg Emulator):", fg=self.text_light, bg=self.bg_black, font=("Tahoma", 9, "bold")).pack(anchor="w", pady=(5, 2))
        self.e_nick = tk.Entry(f, width=30, font=("Tahoma", 9), bg=self.panel_dark, fg=self.text_light, insertbackground="white", relief="solid", bd=1)
        self.e_nick.pack(anchor="w", pady=(0, 10), ipady=3)
        
        saved_nick = self.config_data.get("nickname", "SteamUnbound")
        self.e_nick.insert(0, saved_nick)

        tk.Label(f, text="Profile Avatar Image (Optional):", fg=self.text_light, bg=self.bg_black, font=("Tahoma", 9, "bold")).pack(anchor="w", pady=(5, 2))
        avatar_frame = tk.Frame(f, bg=self.bg_black)
        avatar_frame.pack(anchor="w", pady=(0, 15), fill="x")

        self.e_avatar = tk.Entry(avatar_frame, width=35, font=("Tahoma", 9), bg=self.panel_dark, fg=self.text_light, insertbackground="white", relief="solid", bd=1)
        self.e_avatar.pack(side="left", padx=(0, 5), ipady=3)
        if self.avatar_temp and os.path.exists(self.avatar_temp):
            self.e_avatar.insert(0, self.avatar_temp)

        btn_avatar = tk.Button(avatar_frame, text="Browse...", bg=self.accent_violet, fg="#ffffff", font=("Tahoma", 8, "bold"), relief="flat", activebackground=self.accent_hover, activeforeground="white", command=self.buscar_avatar, cursor="hand2")
        btn_avatar.pack(side="left", ipadx=6, ipady=3)

        btn_save = tk.Button(f, text="Apply Settings", bg=self.accent_violet, fg="#ffffff", font=("Tahoma", 9, "bold"), relief="flat", activebackground=self.accent_hover, activeforeground="white", command=self.guardar_config, cursor="hand2")
        btn_save.pack(anchor="w", pady=5, ipadx=10, ipady=4)

    def buscar_avatar(self):
        filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if filename:
            self.avatar_temp = filename
            self.e_avatar.delete(0, tk.END)
            self.e_avatar.insert(0, filename)

    def guardar_config(self):
        save_config("api_key", self.e_key.get().strip())
        save_config("nickname", self.e_nick.get().strip() or "SteamUnbound")
        save_config("avatar_path", self.avatar_temp)
        messagebox.showinfo("SteamUnbound", "Settings saved successfully.")

    def on_search_key_release(self, event):
        if event.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab'):
            return
        query = self.e_search.get().strip()
        if len(query) < 2:
            self.listbox_sugerencias.pack_forget()
            return
        if self.search_after_id:
            self.root.after_cancel(self.search_after_id)
        self.search_after_id = self.root.after(350, lambda: self.ejecutar_busqueda_steam(query))

    def ejecutar_busqueda_steam(self, query):
        def tarea():
            try:
                url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(query)}&l=english&cc=US"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    items = data.get('items', [])
                    self.root.after(0, lambda: self.mostrar_sugerencias(items))
            except:
                pass
        threading.Thread(target=tarea, daemon=True).start()

    def mostrar_sugerencias(self, items):
        self.listbox_sugerencias.delete(0, tk.END)
        self.search_results_cache = items
        if items:
            self.listbox_sugerencias.pack(after=self.e_search, fill="x", pady=(0, 5))
            for item in items:
                self.listbox_sugerencias.insert(tk.END, f"{item['name']} (AppID: {item['id']})")
        else:
            self.listbox_sugerencias.pack_forget()

    def seleccionar_sugerencia(self, event):
        idx = self.listbox_sugerencias.curselection()
        if not idx:
            return
        item = self.search_results_cache[idx[0]]
        self.selected_appid = str(item['id'])
        self.selected_game_name = item['name']
        self.e_search.delete(0, tk.END)
        self.e_search.insert(0, item['name'])
        self.listbox_sugerencias.pack_forget()
        self.lbl_game_title.configure(text=item['name'])

        threading.Thread(target=self.cargar_metadatos, args=(self.selected_appid,), daemon=True).start()

    def cargar_metadatos(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get(appid, {}).get("success"):
                    details = data[appid]["data"]
                    desc = details.get("short_description", "No description.")
                    released = details.get("release_date", {}).get("date", "N/A")
                    devs = ", ".join(details.get("developers", ["N/A"]))
                    text = f"Release Date: {released}\nDeveloper: {devs}\n\nDescription:\n{desc}"
                    self.root.after(0, lambda: self.actualizar_texto_meta(text))
        except:
            pass

    def actualizar_texto_meta(self, text):
        self.text_meta.config(state="normal")
        self.text_meta.delete("1.0", tk.END)
        self.text_meta.insert("1.0", text)
        self.text_meta.config(state="disabled")
        self.btn_download.config(state="normal")

    def iniciar_proceso_instalacion(self):
        if not self.selected_appid or not self.selected_game_name:
            return
        api_key = load_config().get("api_key", "")
        if not api_key:
            messagebox.showerror("Error", "API Key missing. Configure it in Settings.")
            self.notebook.select(self.tab_settings)
            return

        ruta_padre = filedialog.askdirectory(title="Select Parent Destination Folder")
        if not ruta_padre:
            return

        safe_name = re.sub(r'[<>:"/\\|?*]', '', self.selected_game_name).strip()
        ruta_juego = os.path.join(ruta_padre, safe_name)
        os.makedirs(ruta_juego, exist_ok=True)

        lang = self.language_var.get()
        
        self.text_log.config(state="normal")
        self.text_log.delete("1.0", tk.END)
        self.text_log.config(state="disabled")
        
        self.progress['value'] = 0
        threading.Thread(target=self.proceso_descarga_real, args=(self.selected_appid, api_key, ruta_juego, lang), daemon=True).start()

    def proceso_descarga_real(self, app_id, api_key, ruta_juego, language):
        api_base_url = "https://hubcapmanifest.com/api/v1"
        temp_dir = Path("temp_depot_data")
        keys_file = "keys.txt"
        mod_exe = os.path.join("DepotDownloaderMod", "DepotDownloaderMod.exe")
        steamless_exe = os.path.join("Steamless", "Steamless.CLI.exe")

        if not os.path.exists(mod_exe):
            self.log_message("Missing DepotDownloaderMod.exe")
            messagebox.showerror("Error", "Missing DepotDownloaderMod.exe")
            return

        self.log_message(f"Connecting to Hubcap API for AppID {app_id}...")
        self.root.after(0, lambda: self.progress.configure(value=10))

        url = f"{api_base_url}/manifest/{app_id}"
        headers = {"User-Agent": "SteamUnbound/1.0", "Authorization": f"Bearer {api_key}"}

        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            r = requests.get(url, headers=headers, stream=True, timeout=30)
            if r.status_code in (401, 403):
                self.log_message("Invalid or expired API Key.")
                messagebox.showerror("Error", "Invalid API Key.")
                return
            r.raise_for_status()

            zip_path = temp_dir / "data.zip"
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
        except Exception as e:
            self.log_message(f"Download error: {e}")
            messagebox.showerror("Error", f"Download error: {e}")
            return

        self.log_message("Scanning depots, manifests and keys...")
        self.root.after(0, lambda: self.progress.configure(value=25))

        inventory = {}
        for lua_file in temp_dir.glob("*.lua"):
            try:
                with open(lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(r'addappid\((\d+),\s*\d+,\s*"([A-Za-z0-9]+)"\)', content)
                    if not matches:
                        matches = re.findall(r'\[(\d+)\]\s*=\s*"([A-Za-z0-9]+)"', content)
                    for depot_id, key in matches:
                        if depot_id not in inventory:
                            inventory[depot_id] = {"key": None, "manifest_file": None}
                        inventory[depot_id]["key"] = key
            except:
                pass

        for m in temp_dir.glob("*.manifest"):
            match = re.match(r"^(\d+)_(\d+)\.manifest$", m.name)
            if match:
                depot_id = match.group(1)
                if depot_id not in inventory:
                    inventory[depot_id] = {"key": None, "manifest_file": None}
                inventory[depot_id]["manifest_file"] = m

        selected_depots = [did for did, info in inventory.items() if info["key"] and info["manifest_file"]]
        if not selected_depots:
            selected_depots = list(inventory.keys())

        keys_to_write = {did: inventory[did]["key"] for did in selected_depots if inventory[did].get("key")}
        with open(keys_file, "w", encoding="utf-8") as f:
            for did, k in keys_to_write.items():
                f.write(f"{did};{k}\n")

        manifest_filenames = []
        for did in selected_depots:
            info = inventory.get(did)
            if info and info["manifest_file"]:
                target = Path(info["manifest_file"].name)
                shutil.copy(str(info["manifest_file"]), str(target))
                manifest_filenames.append(target.name)

        total_manifests = len(manifest_filenames) if manifest_filenames else 1
        step_progress = 40.0 / total_manifests 

        self.log_message(f"Starting file downloads (Game + DLCs / Depots: {total_manifests})...")
        try:
            for i, manifest_file in enumerate(manifest_filenames):
                match = re.match(r"^(\d+)_(\d+)\.manifest$", manifest_file)
                if not match: continue
                depot_id, manifest_id = match.group(1), match.group(2)

                self.log_message(f"Downloading Depot ID: {depot_id} (Manifest: {manifest_id})")

                cmd = [
                    mod_exe, "-app", str(app_id), "-depot", str(depot_id),
                    "-manifest", str(manifest_id), "-manifestfile", manifest_file,
                    "-depotkeys", keys_file, "-dir", ruta_juego, "-max-downloads", "16", "-language", language
                ]

                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                for line in process.stdout:
                    l = line.strip()
                    if l and ("%" in l or "Downloaded" in l or "Error" in l):
                        self.log_message(f"   {l}")
                process.wait()

                current_prog = 25 + (i + 1) * step_progress
                self.root.after(0, lambda p=current_prog: self.progress.configure(value=p))

        except Exception as e:
            self.log_message(f"Download execution error: {e}")
            messagebox.showerror("Error", f"Download execution error: {e}")
            return

        if os.path.exists(keys_file): os.remove(keys_file)

        self.log_message("Unpacking executables with Steamless...")
        self.root.after(0, lambda: self.progress.configure(value=75))

        if os.path.exists(steamless_exe) and os.path.exists(ruta_juego):
            for root_dir, dirs, files in os.walk(ruta_juego):
                for file in files:
                    if file.lower().endswith(".exe") and "unpacked" not in file.lower():
                        exe_path = os.path.join(root_dir, file)
                        try:
                            self.log_message(f"Unpacking: {file}")
                            subprocess.run([steamless_exe, exe_path], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                            unpacked_1 = exe_path + ".unpacked.exe"
                            unpacked_2 = os.path.join(root_dir, file[:-4] + ".unpacked.exe")
                            target_unpacked = unpacked_1 if os.path.exists(unpacked_1) else (unpacked_2 if os.path.exists(unpacked_2) else None)
                            if target_unpacked:
                                os.remove(exe_path)
                                os.rename(target_unpacked, exe_path)
                        except:
                            pass

        self.log_message("Applying Goldberg Emulator patch...")
        self.root.after(0, lambda: self.progress.configure(value=90))

        es_64bits = False
        for root_dir, dirs, files in os.walk(ruta_juego):
            if "steam_api64.dll" in files:
                es_64bits = True
                break
            elif "steam_api.dll" in files:
                es_64bits = False
                break

        steam_settings = os.path.join(ruta_juego, "steam_settings")
        os.makedirs(steam_settings, exist_ok=True)
        with open(os.path.join(steam_settings, "steam_appid.txt"), "w") as f: f.write(str(app_id))
        
        nick = load_config().get("nickname", "SteamUnbound")
        with open(os.path.join(steam_settings, "force_account_name.txt"), "w", encoding="utf-8") as f: f.write(nick)
        with open(os.path.join(steam_settings, "offline.txt"), "w", encoding="utf-8") as f: f.write("1")

        avatar_path = load_config().get("avatar_path", "")
        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize((184, 184))
                img.save(os.path.join(steam_settings, "avatar.png"), "PNG")
            except:
                pass

        src_dll = os.path.join("assets", "bge_64" if es_64bits else "bge_32", "steam_api64.dll" if es_64bits else "steam_api.dll")
        dst_dll = os.path.join(ruta_juego, "steam_api64.dll" if es_64bits else "steam_api.dll")
        if os.path.exists(src_dll): shutil.copy(src_dll, dst_dll)

        for m_name in manifest_filenames:
            if os.path.exists(m_name): os.remove(m_name)
        if temp_dir.exists(): shutil.rmtree(temp_dir, ignore_errors=True)

        self.log_message("All files downloaded, unpacked and patched successfully!")
        self.root.after(0, lambda: self.progress.configure(value=100))

        def prompt_acceso_directo():
            res = messagebox.askyesno("SteamUnbound", f"{self.selected_game_name} is ready to play!\n\nDo you want to create a desktop shortcut?")
            if res:
                creado = crear_acceso_directo_escritorio(self.selected_game_name, ruta_juego)
                if creado:
                    messagebox.showinfo("SteamUnbound", "Desktop shortcut created successfully!")
                else:
                    messagebox.showwarning("SteamUnbound", "Could not automatically locate the main executable to create shortcut.")

        self.root.after(0, prompt_acceso_directo)

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamUnboundApp(root)
    root.mainloop()