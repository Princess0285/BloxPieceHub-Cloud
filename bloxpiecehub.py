# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import requests
import pyperclip
import sys
import logging
import threading
from datetime import datetime
from random import choice
from packaging import version
import webbrowser

# ======================== CONFIGURATION ========================
GITHUB_REPO = "https://raw.githubusercontent.com/Princess0285/BloxPieceHub-Cloud/main"
STATUS_URL = f"{GITHUB_REPO}/status.json"
VERSION_URL = f"{GITHUB_REPO}/version.txt"
SCRIPT_URL = f"{GITHUB_REPO}/bloxpiecehub.py"

COLOR_SCHEME = {
    "background": "#1A1A1A",
    "accent": "#8A2BE2",
    "secondary": "#FF3030",
    "text": "#FFFFFF",
    "online": "#43B581",
    "offline": "#FF3030"
}

EXECUTOR_CONFIG = {
    "Scripts": {
        "AutoFarm": {"discord": "https://discord.gg/script1", "website": "https://script1.com"},
        "Teleport": {"discord": "https://discord.gg/script2", "website": "https://script2.com"}
    },
    "Executors": {
        "Arsenal": {"discord": "https://discord.gg/exec1", "website": "https://exec1.com"},
        "BloxFruits": {"discord": "https://discord.gg/exec2", "website": "https://exec2.com"}
    }
}

class BloxPieceHub:
    def __init__(self, root):
        self.root = root
        self.setup_core()
        self.setup_ui()
        self.setup_services()

    def setup_core(self):
        self.keys_file = "key_banks.json"
        self.key_banks = self.load_key_banks()
        self.current_bank = tk.StringVar(value=list(self.key_banks.keys())[0])

        self.root.title("BloxPieceHub v2.0")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLOR_SCHEME["background"])

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        logging.basicConfig(filename='hub_errors.log', level=logging.ERROR)

    def configure_styles(self):
        style_config = {
            'TFrame': {'background': COLOR_SCHEME["background"]},
            'TLabel': {
                'background': COLOR_SCHEME["background"],
                'foreground': COLOR_SCHEME["text"],
                'font': ('Helvetica', 10)
            },
            'TButton': {
                'font': ('Helvetica', 10, 'bold'),
                'padding': 8
            },
            'Status.TFrame': {'background': '#2A2A2A'},
            'Bank.TCombobox': {'fieldbackground': COLOR_SCHEME["accent"]}
        }

        for style, config in style_config.items():
            self.style.configure(style, **config)

        self.style.map('Accent.TButton',
            foreground=[('active', 'white'), ('!active', 'white')],
            background=[('active', COLOR_SCHEME["secondary"]), ('!active', COLOR_SCHEME["accent"])]
        )

    def setup_ui(self):
        key_frame = ttk.Frame(self.root)
        key_frame.pack(fill=tk.X, padx=20, pady=10)

        self.setup_bank_controls(key_frame)
        self.setup_key_controls(key_frame)

        self.notebook = ttk.Notebook(self.root)
        self.setup_status_tab("Scripts")
        self.setup_status_tab("Executors")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def setup_bank_controls(self, parent):
        bank_frame = ttk.Frame(parent)
        bank_frame.pack(fill=tk.X)

        ttk.Label(bank_frame, text="Active Key Bank:").pack(side=tk.LEFT)
        self.bank_dropdown = ttk.Combobox(
            bank_frame,
            textvariable=self.current_bank,
            values=list(self.key_banks.keys()),
            state="readonly"
        )
        self.bank_dropdown.pack(side=tk.LEFT, padx=10)

        ttk.Button(bank_frame, text="+ New Bank", command=self.create_bank).pack(side=tk.LEFT)
        ttk.Button(bank_frame, text="✕ Delete Bank", command=self.delete_bank).pack(side=tk.RIGHT)

    def setup_key_controls(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=10)

        actions = [
            ("🔑 Use Key", self.use_key),
            ("📋 Copy Key", self.copy_key),
            ("➕ Add Keys", self.add_keys)
        ]

        for text, cmd in actions:
            ttk.Button(control_frame, text=text, command=cmd, style='Accent.TButton').pack(side=tk.LEFT, padx=5)

    def setup_status_tab(self, tab_name):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)

        canvas = tk.Canvas(tab, bg=COLOR_SCHEME["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0
        self.status_indicators = self.status_indicators if hasattr(self, "status_indicators") else {}

        for name, data in EXECUTOR_CONFIG[tab_name].items():
            frame = ttk.Frame(scroll_frame, style='Status.TFrame')
            frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

            status_canvas = tk.Canvas(frame, width=24, height=24, bg=COLOR_SCHEME["background"], highlightthickness=0)
            dot = status_canvas.create_oval(4, 4, 20, 20, fill="gray")
            self.status_indicators[name] = (status_canvas, dot)
            status_canvas.grid(row=0, column=0, padx=10)

            ttk.Label(frame, text=name, font=('Helvetica', 11, 'bold')).grid(row=0, column=1, sticky="w")
            ttk.Button(frame, text="Discord", command=lambda u=data["discord"]: self.open_link(u)).grid(row=0, column=2, padx=5)
            ttk.Button(frame, text="Website", command=lambda u=data["website"]: self.open_link(u)).grid(row=0, column=3, padx=5)

            row += 1

        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def setup_services(self):
        self.update_status()
        self.check_for_updates()
        self.root.after(120000, self.update_status)

    def load_key_banks(self):
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"Main Bank": []}
        except Exception as e:
            logging.error(f"Key load error: {str(e)}")
            return {"Main Bank": []}

    def save_key_banks(self):
        try:
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(self.key_banks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Key save error: {str(e)}")

    def create_bank(self):
        bank_name = simpledialog.askstring("New Bank", "Enter bank name:")
        if bank_name and bank_name not in self.key_banks:
            self.key_banks[bank_name] = []
            self.bank_dropdown["values"] = list(self.key_banks.keys())
            self.current_bank.set(bank_name)
            self.save_key_banks()

    def delete_bank(self):
        current = self.current_bank.get()
        if len(self.key_banks) > 1:
            del self.key_banks[current]
            new_bank = list(self.key_banks.keys())[0]
            self.current_bank.set(new_bank)
            self.bank_dropdown["values"] = list(self.key_banks.keys())
            self.save_key_banks()

    def use_key(self):
        current_bank = self.current_bank.get()
        if not self.key_banks[current_bank]:
            messagebox.showwarning("Empty Bank", "This key bank has no keys!")
            return
        key = choice(self.key_banks[current_bank])
        self.key_banks[current_bank].remove(key)
        self.save_key_banks()
        messagebox.showinfo("Key Used", f"Used key: {key}")

    def copy_key(self):
        current_bank = self.current_bank.get()
        if self.key_banks[current_bank]:
            key = choice(self.key_banks[current_bank])
            pyperclip.copy(key)
            messagebox.showinfo("Copied", "Key copied to clipboard!")
        else:
            messagebox.showwarning("Empty Bank", "No keys to copy!")

    def add_keys(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Keys")
        text_area = tk.Text(add_window, height=15, width=50)
        text_area.pack(padx=20, pady=10)
        
        def save_keys():
            new_keys = [k.strip() for k in text_area.get("1.0", tk.END).split('\n') if k.strip()]
            if new_keys:
                current_bank = self.current_bank.get()
                self.key_banks[current_bank].extend(new_keys)
                self.save_key_banks()
                messagebox.showinfo("Success", f"Added {len(new_keys)} keys!")
                add_window.destroy()
        
        ttk.Button(add_window, text="Save Keys", command=save_keys).pack(pady=10)

    def update_status(self):
        try:
            response = requests.get(STATUS_URL, timeout=5)
            status_data = response.json()
            for name, (canvas, oval_id) in self.status_indicators.items():
                color = COLOR_SCHEME["online"] if status_data.get(name) == "online" else COLOR_SCHEME["offline"]
                canvas.itemconfig(oval_id, fill=color)
            self.root.after(120000, self.update_status)
        except Exception as e:
            logging.error(f"Failed to update status: {str(e)}")

    def open_link(self, url):
        webbrowser.open(url)

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            current_version = version.parse("2.0.2")  # Assuming the current version is 2.0
            latest_version = version.parse(response.text.strip())
            if latest_version > current_version:
                self.update_script()
        except Exception as e:
            logging.error(f"Failed to check for updates: {str(e)}")

    def update_script(self):
        try:
            updater_bat = "bph_updater.bat"
            script_path = os.path.abspath("bloxpiecehub.py")
            temp_url = SCRIPT_URL
            bat_commands = f"""@echo off
timeout /t 2 >nul
del "{script_path}" >nul 2>&1
curl -L "{temp_url}" -o "{script_path}"
del "{updater_bat}" >nul 2>&1
start "" python "{script_path}"
exit
"""
            with open(updater_bat, "w", encoding="utf-8") as bat_file:
                bat_file.write(bat_commands)

            os.startfile(updater_bat)
            sys.exit()
        except Exception as e:
            logging.error(f"Failed to update script: {str(e)}")
            messagebox.showerror("Error", "Failed to update the script.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BloxPieceHub(root)
    root.mainloop()
