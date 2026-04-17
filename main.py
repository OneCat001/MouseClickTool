import tkinter as tk
import threading
import time
import ctypes
import keyboard
import winreg
import json
import os
from tkinter import messagebox

# ========== 配置保存到【用户文件夹】 ==========
USER_HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(USER_HOME, "clicker_config.json")

user32 = ctypes.WinDLL("user32", use_last_error=True)
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def click():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def is_dark_mode():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        val = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
        return val == 0
    except:
        return False

# 左右键正确显示
def format_key(name):
    key_map = {
        "space": "空格",
        "shift": "左Shift",
        "ctrl": "左Ctrl",
        "alt": "左Alt",
        "left shift": "左Shift",
        "right shift": "右Shift",
        "left ctrl": "左Ctrl",
        "right ctrl": "右Ctrl",
        "left alt": "左Alt",
        "right alt": "右Alt",
        "left windows": "左Win",
        "right windows": "右Win",
        "enter": "回车",
        "tab": "Tab",
        "backspace": "Backspace",
        "caps lock": "CapsLock",
        "esc": "Esc",
        "right":"右箭头",
        "left":"左箭头",
        "up":"上箭头",
        "down":"下箭头"
    }
    if name in key_map:
        return key_map[name]
    if name.startswith("f") and name[1:].isdigit():
        return name.upper()
    if len(name) == 1 and name.isalpha():
        return name.upper()
    return name

# ========== 保存/加载 ==========
def save_config(cps, hotkey_raw, hotkey_show):
    data = {
        "cps": cps,
        "hotkey_raw": hotkey_raw,
        "hotkey_show": hotkey_show
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(e)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return 700, "`", "`"
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (
            data.get("cps", 700),
            data.get("hotkey_raw", "`"),
            data.get("hotkey_show", "`")
        )
    except:
        return 700, "`", "`"

class ClickerFinal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("连点器")
        self.root.geometry("360x360")
        self.root.resizable(False, False)

        # 从用户目录加载配置
        self.target_cps, self.hotkey_raw, self.hotkey_show = load_config()

        self.clicking = False
        self.recording = False
        self.current_dark = is_dark_mode()

        self.bg = "#202124" if self.current_dark else "#ffffff"
        self.fg = "#e0e0e0" if self.current_dark else "#000000"
        self.btn_bg = "#3d3d3d" if self.current_dark else "#f0f0f0"
        self.entry_bg = "#2a2a2a" if self.current_dark else "#ffffff"
        self.entry_fg = "#e0e0e0" if self.current_dark else "#000000"

        self.root.config(bg=self.bg)

        tk.Label(self.root, text="目标 CPS", bg=self.bg, fg=self.fg, font=("微软雅黑", 12)).pack(pady=10)
        self.cps_entry = tk.Entry(self.root, font=("Arial",14), justify="center",
                                  bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.fg)
        self.cps_entry.insert(0, str(self.target_cps))
        self.cps_entry.pack(pady=5)

        self.confirm_btn = tk.Button(
            self.root, text="确认", font=("微软雅黑",12),
            bg=self.btn_bg, fg=self.fg, command=self.confirm_cps
        )
        self.confirm_btn.pack(pady=5)

        tk.Label(self.root, text="启动/暂停热键", bg=self.bg, fg=self.fg, font=("微软雅黑",12)).pack(pady=10)
        self.hk_btn = tk.Button(self.root, text=self.hotkey_show, font=("Arial",12), width=10,
                                bg=self.btn_bg, fg=self.fg, command=self.start_record)
        self.hk_btn.pack()

        self.status = tk.Label(self.root, text="✅ 已停止", fg="red", bg=self.bg, font=("黑体",14,"bold"))
        self.status.pack(pady=15)

        threading.Thread(target=self.theme_monitor, daemon=True).start()
        threading.Thread(target=self.click_worker, daemon=True).start()
        threading.Thread(target=self.hotkey_monitor, daemon=True).start()

        self.root.mainloop()

    def confirm_cps(self):
        content = self.cps_entry.get().strip()
        if not content.isdigit():
            messagebox.showerror("输入错误", "请输入纯整数！")
            return
        cps = int(content)
        if not (0 <= cps <= 800):
            messagebox.showerror("范围错误", "CPS 必须在 0 ~ 800 之间！")
            return
        self.target_cps = cps
        save_config(self.target_cps, self.hotkey_raw, self.hotkey_show)
        messagebox.showinfo("成功", f"CPS 已设置为：{cps}（已保存）")

    def update_theme(self, dark):
        self.bg = "#202124" if dark else "#ffffff"
        self.fg = "#e0e0e0" if dark else "#000000"
        self.btn_bg = "#3d3d3d" if dark else "#f0f0f0"
        self.entry_bg = "#2a2a2a" if dark else "#ffffff"
        self.entry_fg = "#e0e0e0" if dark else "#000000"

        self.root.config(bg=self.bg)
        for w in self.root.winfo_children():
            try:
                w.config(bg=self.bg, fg=self.fg)
            except:
                pass
        self.cps_entry.config(bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.fg)
        self.hk_btn.config(bg=self.btn_bg, fg=self.fg)
        self.confirm_btn.config(bg=self.btn_bg, fg=self.fg)

    def theme_monitor(self):
        while True:
            new_dark = is_dark_mode()
            if new_dark != self.current_dark:
                self.current_dark = new_dark
                self.root.after(0, self.update_theme, new_dark)
            time.sleep(1)

    def start_record(self):
        if self.recording:
            return
        self.recording = True
        self.hk_btn.config(text=f"<{self.hotkey_show}>")

        def record():
            key_name = keyboard.read_key()
            while keyboard.is_pressed(key_name):
                time.sleep(0.01)
            self.hotkey_raw = key_name
            self.hotkey_show = format_key(key_name)
            self.hk_btn.config(text=self.hotkey_show)
            # 改完热键立即保存
            save_config(self.target_cps, self.hotkey_raw, self.hotkey_show)
            time.sleep(0.3)
            self.recording = False

        threading.Thread(target=record, daemon=True).start()

    def hotkey_monitor(self):
        while True:
            if self.recording:
                time.sleep(0.01)
                continue
            try:
                if keyboard.is_pressed(self.hotkey_raw):
                    self.clicking = not self.clicking
                    self.status.config(
                        text="▶ 运行中" if self.clicking else "✅ 已停止",
                        fg="green" if self.clicking else "red"
                    )
                    while keyboard.is_pressed(self.hotkey_raw):
                        time.sleep(0.01)
            except:
                pass
            time.sleep(0.001)

    def click_worker(self):
        while True:
            if not self.clicking:
                time.sleep(0.001)
                continue

            cps = self.target_cps
            if cps <= 0:
                time.sleep(0.05)
                continue

            clicks = []
            while self.clicking:
                now = time.time()
                while clicks and now - clicks[0] > 1.0:
                    clicks.pop(0)
                if len(clicks) < cps:
                    click()
                    clicks.append(now)
                else:
                    time.sleep(0.0001)
            time.sleep(0.001)

if __name__ == "__main__":
    ClickerFinal()