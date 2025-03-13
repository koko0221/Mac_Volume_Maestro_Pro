import tkinter as tk
from tkinter import ttk
import subprocess
import os
import json

# 設定應用名稱與配置檔路徑
app_name = "VolumeMaestro"
config_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
os.makedirs(config_dir, exist_ok=True)  # 確保目錄存在
config_file = os.path.join(config_dir, "volume_profiles.json")

# 初始化配置檔
profiles = {}

# 讀取本地配置檔
def load_profiles_from_file():
    global profiles
    try:
        with open(config_file, "r") as file:
            profiles = json.load(file)
            config_combobox['values'] = list(profiles.keys())  # 更新下拉選單
    except FileNotFoundError:
        profiles = {}  # 檔案不存在時初始化為空
    except json.JSONDecodeError:
        print("配置檔損壞，無法讀取")

# 儲存配置檔至本地檔案
def save_profiles_to_file():
    try:
        with open(config_file, "w") as file:
            json.dump(profiles, file)
        print(f"配置檔已儲存到 {config_file}")
    except Exception as e:
        print(f"無法儲存配置檔：{e}")

# 初始化配置檔案
def initialize_config_file():
    if not os.path.exists(config_file):
        with open(config_file, "w") as file:
            json.dump({}, file)

# 獲取當前音量
def get_current_volume():
    try:
        volume = subprocess.check_output(["osascript", "-e", "output volume of (get volume settings)"]).decode().strip()
        return float(volume) / 100
    except Exception:
        return 0  # 無法取得音量時返回 0

# 設置音量
def set_volume(value):
    global current_volume
    volume_level = max(0, min(round(float(value) * 100), 100))
    if round(current_volume * 100) != volume_level:
        subprocess.run(["osascript", "-e", f"set volume output volume {volume_level}"])
        current_volume = value
        volume_slider.set(current_volume)
        update_label(volume_level)

# 更新音量輸入框
def update_label(volume_level):
    if not is_editing:
        volume_entry.delete(0, tk.END)
        volume_entry.insert(0, str(volume_level))

# 手動設置音量
def manual_set_volume(event=None):
    global is_editing
    try:
        value = float(volume_entry.get()) / 100
        set_volume(value)
        volume_slider.set(value)
    except ValueError:
        update_label(round(current_volume * 100))
        volume_slider.set(current_volume)
    is_editing = False
    root.focus()

# 開始編輯（停止同步更新）
def start_editing(event):
    global is_editing
    is_editing = True

# 偵測視窗背景點擊
def handle_click(event):
    widget = event.widget
    if widget not in [config_combobox, volume_entry]:
        manual_set_volume()

# 靜音功能
def mute_unmute():
    global is_muted, previous_volume
    if is_muted:
        set_volume(previous_volume)
        mute_button.config(text="靜音")
        is_muted = False
    else:
        previous_volume = current_volume
        set_volume(0)
        mute_button.config(text="取消靜音")
        is_muted = True

# 調整音量按鈕功能
def change_volume(change):
    global current_volume
    new_volume = min(max(current_volume + change, 0), 1)
    set_volume(new_volume)
    current_volume = new_volume
    volume_slider.set(new_volume)

# 更新滑桿與輸入框
def refresh_volume():
    global current_volume
    if not is_editing:
        new_volume = get_current_volume()
        if round(current_volume * 100) != round(new_volume * 100):
            current_volume = new_volume
            volume_slider.set(current_volume)
            update_label(round(current_volume * 100))
    root.after(1000, refresh_volume)

# 配置檔功能
def load_profile(profile_name):
    if profile_name in profiles:
        set_volume(profiles[profile_name])
        volume_slider.set(profiles[profile_name])
        update_label(round(profiles[profile_name] * 100))

def save_profile(profile_name):
    profile_name = profile_name.strip()
    if profile_name:
        profiles[profile_name] = current_volume
        config_combobox['values'] = list(profiles.keys())
        save_profiles_to_file()

def delete_profile(profile_name):
    if profile_name in profiles:
        del profiles[profile_name]
        config_combobox['values'] = list(profiles.keys())
        save_profiles_to_file()

# 初始化 GUI
root = tk.Tk()
root.title("Mac音量調整器")
root.geometry("650x185")
root.resizable(False, False)

# 添加背景 Canvas
background = tk.Canvas(root, width=650, height=180, highlightthickness=0)
background.place(x=0, y=0)
background.bind("<Button-1>", lambda event: manual_set_volume())

# 上層框架
top_frame = ttk.Frame(root)
top_frame.pack(pady=10, fill="x")

# 音量輸入框
ttk.Label(top_frame, text="音量：", font=("Arial", 12)).grid(row=0, column=0, padx=10, sticky="w")
volume_entry = ttk.Entry(top_frame, font=("Arial", 12), width=5, justify="center")
volume_entry.grid(row=0, column=1, padx=5, sticky="w")
volume_entry.bind("<Return>", manual_set_volume)
volume_entry.bind("<FocusIn>", start_editing)
volume_entry.bind("<FocusOut>", manual_set_volume)
ttk.Label(top_frame, text="%", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky="w")

# 配置檔下拉選單與按鈕
ttk.Label(top_frame, text="配置檔：", font=("Arial", 12)).grid(row=0, column=3, padx=15, sticky="e")
config_combobox = ttk.Combobox(top_frame, font=("Arial", 12), width=12, state="normal")
config_combobox['values'] = []
config_combobox.grid(row=0, column=4, padx=5, sticky="e")

# 當選取選項時，移除焦點
config_combobox.bind("<<ComboboxSelected>>", lambda event: root.focus())

btn_frame = ttk.Frame(top_frame)
btn_frame.grid(row=0, column=5, padx=10, sticky="e")

ttk.Button(btn_frame, text="讀取", command=lambda: load_profile(config_combobox.get())).grid(row=0, column=0, padx=2)
ttk.Button(btn_frame, text="儲存", command=lambda: save_profile(config_combobox.get())).grid(row=0, column=1, padx=2)
ttk.Button(btn_frame, text="刪除", command=lambda: delete_profile(config_combobox.get())).grid(row=0, column=2, padx=2)

# 控制按鈕與滑桿
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

ttk.Button(control_frame, text="-0.1", command=lambda: change_volume(-0.1)).grid(row=1, column=0, padx=5)
ttk.Button(control_frame, text="-0.01", command=lambda: change_volume(-0.01)).grid(row=1, column=1, padx=5)

volume_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient="horizontal", length=200, command=lambda val: set_volume(float(val)))
volume_slider.grid(row=1, column=2, padx=10)

ttk.Button(control_frame, text="+0.01", command=lambda: change_volume(0.01)).grid(row=1, column=3, padx=5)
ttk.Button(control_frame, text="+0.1", command=lambda: change_volume(0.1)).grid(row=1, column=4, padx=5)

# 靜音與重置音量按鈕
action_frame = ttk.Frame(root)
action_frame.pack(pady=10, anchor="e")

action_box = ttk.Label(action_frame)
action_box.grid(row=0, column=0, padx=5)

mute_button = ttk.Button(action_frame, text="靜音", command=mute_unmute)
mute_button.grid(row=1, column=0, padx=10)
zero_button = ttk.Button(action_frame, text="將音量設為0", command=lambda: set_volume(0))
zero_button.grid(row=1, column=1, padx=10)

# 初始化音量
is_editing = False
is_muted = False
current_volume = get_current_volume()
previous_volume = current_volume
volume_slider.set(current_volume)
update_label(round(current_volume * 100))

# 啟動
initialize_config_file()
load_profiles_from_file()
refresh_volume()
root.mainloop()
