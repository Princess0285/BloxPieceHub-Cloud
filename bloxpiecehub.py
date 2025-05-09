import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import pyperclip
import threading
from datetime import datetime
from packaging import version

# ======================== 🔗 CUSTOMIZATION POINTS ========================
GITHUB_STATUS_URL = "https://github.com/Princess0285/BloxPieceHub-Cloud/blob/main/status.json"
GITHUB_VERSION_URL = "https://github.com/Princess0285/BloxPieceHub-Cloud/blob/main/version.txt"
DISCORD_INVITE = "https://discord.gg/YOURINVITE"
EXECUTOR_LINKS = {
    "RedzHub": "https://yourarsenallink.com",
    "Velocity": "https://bloxfruitslink.com",
    # Add more executors here
}
# ========================================================================

class BloxPieceHub:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.keys_file = "blox_keys.json"
        self.keys = self.load_keys()
        self.create_widgets()
        self.configure_styles()
        self.setup_cloud_features()
        
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
        self.style.configure('TLabel', background=bg, foreground="#ffffff", font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10), padding=8)
        self.style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground="#7289da")
        self.style.map('Rounded.TButton',
                      foreground=[('active', 'white'), ('!active', 'white')],
                      background=[('active', '#43b581'), ('!active', '#43b581')],
                      relief=[('pressed', 'sunken'), ('!pressed', 'ridge')])

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Header
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="BLOXPIECEHUB", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Discord button
        ttk.Button(header, text="Join Discord", command=lambda: self.open_link(DISCORD_INVITE),
                  style='Rounded.TButton').pack(side=tk.RIGHT)
        
        # Key Vault Section
        key_frame = ttk.LabelFrame(main_frame, text="🔑 Key Vault", padding=20)
        key_frame.pack(fill=tk.X, pady=15)
        
        self.key_display = ttk.Label(key_frame, text="No key generated", font=('Consolas', 14),
                                   background="#36364a", foreground="#ff7e67", anchor='center')
        self.key_display.pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(key_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Generate Key", command=self.get_key, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Copy Key", command=self.copy_key, style='Rounded.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add Keys", command=self.add_keys, style='Rounded.TButton').pack(side=tk.RIGHT)
        
        # Status Panel
        status_frame = ttk.LabelFrame(main_frame, text="🛡️ Executor Status", padding=20)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_canvas = tk.Canvas(status_frame, bg="#36364a", highlightthickness=0, borderwidth=0)
        self.status_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw status indicators
        self.executor_widgets = {}
        y_pos = 30
        for executor in EXECUTOR_LINKS.keys():
            # Status dot
            self.status_canvas.create_oval(30, y_pos-5, 40, y_pos+5, fill="#72757e", tags=f"dot_{executor}")
            # Executor name
            self.status_canvas.create_text(50, y_pos, text=executor, anchor='w', fill="white", font=('Segoe UI', 11))
            # Website button
            btn = ttk.Button(self.status_canvas, text="Website", style='Rounded.TButton',
                           command=lambda e=executor: self.open_link(EXECUTOR_LINKS[e]))
            self.status_canvas.create_window(250, y_pos-2, window=btn, anchor='w')
            y_pos += 40

    def setup_cloud_features(self):
        # Check for updates every 6 hours
        self.root.after(21600000, self.check_updates)
        # Initial status check
        self.update_status()
        
    def update_status(self):
        try:
            response = requests.get(GITHUB_STATUS_URL, timeout=5)
            status_data = response.json()
            for executor, state in status_data.items():
                color = "#43b581" if state == "online" else "#f04747"
                self.status_canvas.itemconfig(f"dot_{executor}", fill=color)
        except Exception as e:
            print(f"Status update failed: {str(e)}")

    def check_updates(self):
        try:
            current_ver = "1.0.0"  # Match your version.txt
            response = requests.get(GITHUB_VERSION_URL, timeout=5)
            latest_ver = response.text.strip()
            
            if version.parse(latest_ver) > version.parse(current_ver):
                if messagebox.askyesno("Update Available", "New version found! Download now?"):
                    self.open_link(f"https://github.com/YOURNAME/BloxPieceHub-Cloud/releases/tag/v{latest_ver}")
        except Exception as e:
            print(f"Update check failed: {str(e)}")

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    # ... [Add your existing key management methods here] ...

if __name__ == "__main__":
    root = tk.Tk()
    app = BloxPieceHub(root)
    root.mainloop()
