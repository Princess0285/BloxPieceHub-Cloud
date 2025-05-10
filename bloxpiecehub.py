import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import pyperclip
import threading
import logging
from datetime import datetime
from random import choice
from packaging import version

# ======================== CONFIGURATION ========================
GITHUB_STATUS_URL = "https://raw.githubusercontent.com/Princess0285/BloxPieceHub-Cloud/main/status.json"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/Princess0285/BloxPieceHub-Cloud/main/version.txt"
DISCORD_INVITE = "https://discord.gg/YOUR_INVITE_LINK"
EXECUTOR_LINKS = {
    "Arsenal": "https://example.com/arsenal",
    "BloxFruits": "https://example.com/bloxfruits"
}

# ======================== MAIN APPLICATION ========================
class BloxPieceHub:
    def __init__(self, root):
        self.root = root
        self.setup_logging()
        self.setup_window()
        self.keys_file = "blox_keys.json"
        self.keys = self.load_keys()
        self.create_widgets()
        self.configure_styles()
        self.setup_cloud_features()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='bloxpiecehub_errors.log',
            level=logging.ERROR,
            format='%(asctime)s - %(message)s'
        )

    def setup_window(self):
        self.root.title("BloxPieceHub v1.0")
        self.root.geometry("1000x750")
        self.root.configure(bg="#2a2a3a")
        self.root.resizable(False, False)

    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        bg = "#2a2a3a"
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground="white", font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=8)
        self.style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground="#7289da")

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="BLOXPIECEHUB", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Join Discord", command=lambda: self.open_link(DISCORD_INVITE)).pack(side=tk.RIGHT)

        # Key Vault Section
        key_frame = ttk.LabelFrame(main_frame, text="🔑 Key Vault", padding=15)
        key_frame.pack(fill=tk.X, pady=10)
        
        self.key_display = ttk.Label(key_frame, text="No key generated", font=('Consolas', 14),
                                   background="#36364a", foreground="#ff7e67", anchor='center')
        self.key_display.pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(key_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Generate Key", command=self.get_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Copy Key", command=self.copy_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add Keys", command=self.add_keys).pack(side=tk.RIGHT)

        # Status Panel
        status_frame = ttk.LabelFrame(main_frame, text="🛡️ Executor Status", padding=15)
        status_frame.pack(fill=tk.BOTH, expand=True)

        self.status_canvas = tk.Canvas(status_frame, bg="#36364a", highlightthickness=0)
        self.status_canvas.pack(fill=tk.BOTH, expand=True)

        # Initialize status indicators
        self.executor_widgets = {}
        y_pos = 30
        for executor in EXECUTOR_LINKS.keys():
            self.status_canvas.create_oval(30, y_pos-5, 40, y_pos+5, fill="gray", tags=f"dot_{executor}")
            self.status_canvas.create_text(50, y_pos, text=executor, anchor='w', fill="white", font=('Segoe UI', 11))
            ttk.Button(self.status_canvas, text="Website", command=lambda e=executor: self.open_link(EXECUTOR_LINKS[e])).place(x=250, y=y_pos-10)
            y_pos += 40

    # ======================== KEY MANAGEMENT ========================
    def load_keys(self):
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load keys:\n{str(e)}")
            return []

    def save_keys(self):
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save keys:\n{str(e)}")

    def get_key(self):
        if not self.keys:
            messagebox.showwarning("No Keys", "Key database is empty!")
            return
        
        key = choice(self.keys)
        self.keys.remove(key)
        self.save_keys()
        self.key_display.config(text=key)
        self.update_status()

    def add_keys(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Keys")
        add_window.geometry("400x300")
        
        text_area = tk.Text(add_window, height=10, width=40)
        text_area.pack(pady=10)
        
        def save_keys():
            new_keys = [k.strip() for k in text_area.get("1.0", tk.END).split('\n') if k.strip()]
            if new_keys:
                self.keys.extend(new_keys)
                self.save_keys()
                messagebox.showinfo("Success", f"Added {len(new_keys)} keys!")
                add_window.destroy()
        
        ttk.Button(add_window, text="Save Keys", command=save_keys).pack()

    def copy_key(self):
        current_key = self.key_display.cget("text")
        if current_key != "No key generated":
            try:
                pyperclip.copy(current_key)
                messagebox.showinfo("Copied", "Key copied to clipboard!")
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy key:\n{str(e)}")

    # ======================== CLOUD FEATURES ========================
    def setup_cloud_features(self):
        self.root.after(300000, self.update_status)  # Update every 5 mins
        threading.Thread(target=self.check_updates, daemon=True).start()

    def update_status(self):
        try:
            response = requests.get(GITHUB_STATUS_URL, timeout=5)
            status_data = response.json()
            for executor, state in status_data.items():
                color = "#43b581" if state.lower() == "online" else "#f04747"
                self.status_canvas.itemconfig(f"dot_{executor}", fill=color)
        except Exception as e:
            logging.error(f"Status update failed: {str(e)}")

    def check_updates(self):
        try:
            current_ver = "1.0.0"
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            latest_ver = response.text.strip()
            
            if version.parse(latest_ver) > version.parse(current_ver):
                if messagebox.askyesno("Update Available", "New version available!\nDownload now?"):
                    self.open_link(f"https://github.com/Princess0285/BloxPieceHub-Cloud/releases/latest")
        except Exception as e:
            logging.error(f"Update check failed: {str(e)}")

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

if __name__ == "__main__":
    root = tk.Tk()
    app = BloxPieceHub(root)
    root.mainloop()
