# --- AUTO-UPDATED: 2025-12-03 04:19:50 UTC ---
import tkinter as tk
from tkinter import ttk
import pydivert
import threading
import time
import ctypes
import gc
import os
import sys
import json
from collections import deque
from pynput import mouse, keyboard
import pystray
from PIL import Image, ImageDraw
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

def resource_path(relative_path):
    try:
        return sys._MEIPASS + '/' + relative_path
    except AttributeError:
        return os.path.join(os.path.abspath("."), relative_path)

APP_NAME = "clumsex"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class GlobalState:
    def __init__(self):
        self.target_port = "2050"
        self.duration = 12.0
        self.lock_timer = True
        self.timer_pos = None
        self.hotkey_type = "mouse"
        self.trigger_btn = mouse.Button.middle
        self.trigger_str = "Middle Click"
        self.lag_event = threading.Event()
        self.lock = threading.Lock()
        self.gc_lock = threading.Lock()
        self.buffer_cond = threading.Condition()
        self.current_ip = "---"
        self.last_ip = "---"
        self.lag_start_time = 0.0
        self.last_toggle_time = 0.0
        self.packet_buffer = deque(maxlen=10000)
        self.shaping_rate = 2000
        self.shaping_burst = 50
        self.gc_dirty = False
        self.app_running = True
        self.remap_mode = False
        self.divert = None
        self.game_window_title = "RotMGExalt"
        self.mouse_listener = None
        self.kb_listener = None
        self.load_config()

    def get_clean_trigger_str(self, key_obj, k_type):
        if k_type == "mouse":
            return str(key_obj).replace("Button.", "").capitalize() + " Click"
        try:
            return key_obj.char.upper() if hasattr(key_obj, 'char') else str(key_obj).replace("Key.", "").upper()
        except AttributeError:
            return str(key_obj).replace("Key.", "").upper()

    def save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = {"port": self.target_port, "duration": self.duration, "lock_timer": self.lock_timer,
                "timer_pos": self.timer_pos, "hotkey_type": self.hotkey_type,
                "trigger_val": str(self.trigger_btn).replace("'", "")}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: %s", e)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading config: %s", e)
            return
        self.target_port = data.get("port", "2050")
        self.duration = float(data.get("duration", 12.0))
        self.lock_timer = data.get("lock_timer", True)
        self.timer_pos = data.get("timer_pos", None)
        h_type = data.get("hotkey_type", "mouse")
        t_val = data.get("trigger_val", "Button.middle")
        self.hotkey_type = h_type
        if h_type == "mouse":
            try:
                self.trigger_btn = getattr(mouse.Button, t_val.split('.')[-1], mouse.Button.middle)
            except AttributeError:
                self.trigger_btn = mouse.Button.middle
        else:
            try:
                self.trigger_btn = getattr(keyboard.Key, t_val.split('.')[-1], keyboard.Key.f2) if "Key." in t_val else keyboard.KeyCode(char=t_val)
            except AttributeError:
                self.trigger_btn = keyboard.Key.f2
        self.trigger_str = self.get_clean_trigger_str(self.trigger_btn, self.hotkey_type)

state = GlobalState()

def optimize_system():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        pid = os.getpid()
        handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
        ctypes.windll.kernel32.SetPriorityClass(handle, 0x00000020)
        ctypes.windll.kernel32.CloseHandle(handle)
        ctypes.windll.winmm.timeBeginPeriod(1)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('clumsex.v12.2')
    except Exception as e:
        logging.error(f"Error optimizing system: %s", e)

def restore_system():
    try:
        ctypes.windll.winmm.timeEndPeriod(1)
    except Exception as e:
        logging.error(f"Error restoring system: %s", e)

def restore_gc():
    with state.gc_lock:
        if state.gc_dirty:
            gc.enable()
            state.gc_dirty = False

def watchdog_worker():
    while state.app_running:
        if state.lag_event.wait():
            deadline = state.lag_start_time + state.duration
            while state.lag_event.is_set():
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    deactivate_lag()
                    break
                time.sleep(min(remaining, 0.1))
            if state.gc_dirty:
                restore_gc()

def capture_worker():
    while state.app_running:
        active_port_filter = state.target_port
        current_filter = f"outbound and tcp.DstPort == {active_port_filter} and tcp.PayloadLength > 0"
        try:
            with pydivert.WinDivert(current_filter) as w:
                state.divert = w
                for packet in w:
                    if not state.app_running:
                        break
                    if state.target_port != active_port_filter:
                        with state.buffer_cond:
                            state.buffer_cond.notify()
                        break
                    with state.lock:
                        current_ip = packet.dst_addr
                        if state.current_ip != current_ip:
                            state.last_ip = state.current_ip if state.current_ip != "---" else state.last_ip
                            state.current_ip = current_ip
                    packet_data = packet.raw
                    if state.lag_event.is_set():
                        with state.buffer_cond:
                            state.packet_buffer.append(packet_data)
                    else:
                        w.send(packet)
                        if state.packet_buffer:
                            with state.buffer_cond:
                                state.buffer_cond.notify()
        except OSError as e:
            logging.error(f"WinDivert OSError: %s", e)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Capture died: %s", e)
            time.sleep(1)
        finally:
            state.divert = None

def flush_worker():
    try:
        with pydivert.WinDivert("false") as w_inject:
            perf = time.perf_counter
            queue = state.packet_buffer
            base_rate = state.shaping_rate
            burst = state.shaping_burst
            tokens = burst
            last_check = perf()
            while state.app_running:
                with state.buffer_cond:
                    while (not queue or state.lag_event.is_set()) and state.app_running:
                        last_check = perf() if state.lag_event.is_set() else last_check
                        state.buffer_cond.wait(1)
                    if not state.app_running:
                        break
                    try:
                        packet_data = queue.popleft()
                    except IndexError:
                        continue
                if state.lag_event.is_set():
                    with state.buffer_cond:
                        queue.appendleft(packet_data)
                    continue
                current_rate = base_rate * 3.0 if len(queue) > 5000 else base_rate
                now = perf()
                elapsed = now - last_check
                last_check = now
                tokens = min(burst, tokens + (elapsed * current_rate))
                if tokens < 0:
                    tokens = 0
                if tokens < 1.0:
                    time.sleep((1.0 - tokens) / current_rate)
                    now = perf()
                    elapsed = now - last_check
                    last_check = now
                    tokens = min(burst, tokens + (elapsed * current_rate))
                if state.lag_event.is_set():
                    with state.buffer_cond:
                        queue.appendleft(packet_data)
                    continue
                try:
                    w_inject.send(packet_data)
                    tokens -= 1.0
                except Exception as e:
                    logging.debug(f"Flush Send Err: %s", e)
                if not queue:
                    restore_gc()
                    if current_rate > base_rate:
                        gc.collect()
    except Exception as e:
        logging.error(f"Flush died: %s", e)

def toggle_lag(source="unknown"):
    if state.remap_mode:
        return
    now = time.time()
    if (now - state.last_toggle_time) < 0.2:
        return
    state.last_toggle_time = now
    if not state.lag_event.is_set():
        with state.gc_lock:
            if not state.gc_dirty:
                gc.disable()
                state.gc_dirty = True
        state.lag_start_time = time.perf_counter()
        state.lag_event.set()
    else:
        deactivate_lag()

def deactivate_lag():
    state.lag_event.clear()
    with state.buffer_cond:
        state.buffer_cond.notify()

def on_input_event(key_or_btn, device_type):
    if device_type == "mouse" and (key_or_btn == mouse.Button.left or key_or_btn == mouse.Button.right):
        return
    if device_type == "keyboard":
        invalid_keys = {keyboard.Key.shift, keyboard.Key.shift_r,
                        keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                        keyboard.Key.alt_l, keyboard.Key.alt_gr,
                        keyboard.Key.cmd, keyboard.Key.cmd_r,
                        keyboard.Key.caps_lock}
        if key_or_btn in invalid_keys:
            return
    with state.lock:
        state.hotkey_type = device_type
        state.trigger_btn = key_or_btn
        state.trigger_str = state.get_clean_trigger_str(key_or_btn, device_type)
        state.remap_mode = False
        state.save_config()
    threading.Thread(target=restart_input_listeners, daemon=True).start()
    return False

def restart_input_listeners():
    def safe_stop(listener, listener_name):
        if listener:
            try:
                listener.stop()
                listener.join(0.1)
            except Exception as e:
                logging.error(f"Error stopping {listener_name} listener: %s", e)
    safe_stop(state.mouse_listener, "mouse")
    safe_stop(state.kb_listener, "keyboard")
    time.sleep(0.1)
    state.mouse_listener = mouse.Listener(on_click=on_mouse_click)
    state.mouse_listener.start()
    state.kb_listener = keyboard.Listener(on_press=on_key_press)
    state.kb_listener.start()

def on_mouse_click(x, y, button, pressed):
    if pressed:
        if state.remap_mode:
            on_input_event(button, "mouse")
        elif state.hotkey_type == "mouse" and button == state.trigger_btn:
            toggle_lag()

def on_key_press(key):
    if state.remap_mode:
        on_input_event(key, "keyboard")
    elif state.hotkey_type == "keyboard" and key == state.trigger_btn:
        toggle_lag()

class OverlayTimer(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "black")
        self.configure(bg="black")
        self.lbl_time = tk.Label(self, text="READY", font=("Segoe UI", 16, "bold"), bg="black", fg="#00FF00")
        self.lbl_time.pack(expand=True)
        self.width = 150
        self.height = 50
        self._offsetx = 0
        self._offsety = 0
        self._last_visible = False
        self._last_text = ""
        self._last_color = ""
        self.track_counter = 0
        self.bind('<Button-1>', self.click_win)
        self.bind('<B1-Motion>', self.drag_win)
        self.bind('<ButtonRelease-1>', self.release_win)
        self.update_click_through()
        x, y = state.timer_pos if state.timer_pos else (-1000, -1000)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def click_win(self, event):
        if state.lock_timer:
            return
        self._offsetx = event.x
        self._offsety = event.y

    def drag_win(self, event):
        if state.lock_timer:
            return
        x = self.winfo_x() + (event.x - self._offsetx)
        y = self.winfo_y() + (event.y - self._offsety)
        self.geometry(f"+{x}+{y}")

    def release_win(self, event):
        if state.lock_timer:
            return
        state.timer_pos = (self.winfo_x(), self.winfo_y())
        state.save_config()

    def update_click_through(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            style = (style | 0x80000 | 0x20) if state.lock_timer else (style & ~0x20 | 0x80000)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            self.lbl_time.config(cursor="arrow" if state.lock_timer else "fleur")
        except Exception as e:
            logging.debug(f"Error updating click through: %s", e)

    def update_view(self):
        hwnd_target = ctypes.windll.user32.FindWindowW(None, state.game_window_title)
        should_be_visible_logic = (not state.lock_timer) or state.lag_event.is_set()
        is_visible = should_be_visible_logic and bool(hwnd_target)
        if is_visible != self._last_visible:
            getattr(self, "deiconify" if is_visible else "withdraw")()
            if is_visible:
                self.attributes("-topmost", True)
            self._last_visible = is_visible
        if not is_visible:
            return
        text, color = "", ""
        if not state.lag_event.is_set():
            text, color = ("DRAG ME", "#FFFFFF") if not state.lock_timer else ("READY", "#00FF00")
        else:
            remaining = max(0, state.duration - (time.perf_counter() - state.lag_start_time))
            color = "#00FF00" if remaining > 6.0 else "#FFFF00" if remaining > 3.0 else "#FF0000"
            text = f"{remaining:.1f}s"
        if text != self._last_text or color != self._last_color:
            self.lbl_time.config(text=text, fg=color)
            self._last_text, self._last_color = text, color
        if state.lock_timer:
            self.track_counter += 1
            if self.track_counter >= 8:
                self.track_counter = 0
                try:
                    if hwnd_target:
                        rect = RECT()
                        ctypes.windll.user32.GetWindowRect(hwnd_target, ctypes.byref(rect))
                        win_w = rect.right - rect.left
                        new_x = rect.left + (win_w // 2) - (self.width // 2)
                        new_y = rect.top + 20
                        if abs(self.winfo_x() - new_x) > 2 or abs(self.winfo_y() - new_y) > 2:
                            self.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
                except Exception as e:
                    logging.debug(f"Error tracking window: %s", e)

class ClumsexGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("clumsex")
        self.geometry("240x390")
        self.resizable(False, False)
        try:
            self.iconbitmap(resource_path("clumsex.ico"))
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self.on_close_x)
        self.bind("<Map>", self.on_window_state_change)
        self.tray_icon = None
        self._last_lag_state = None
        self._last_ip_text = ""
        self._last_prev_ip_text = ""
        self._last_btn_text = ""
        bg_color = "#f2f2f2"
        self.configure(bg=bg_color)
        style = ttk.Style()
        style.theme_use('clam')
        for element, config in [
            ("TFrame", {"background": bg_color}),
            ("TLabelframe", {"background": bg_color, "relief": "flat"}),
            ("TLabelframe.Label", {"background": bg_color, "font": ("Segoe UI", 10, "bold"), "foreground": "#333"}),
            ("TLabel", {"background": bg_color, "font": ("Segoe UI", 9), "foreground": "#444"}),
            ("TCheckbutton", {"background": bg_color, "font": ("Segoe UI", 9)}),
            ("Flat.TButton", {"font": ("Segoe UI", 9, "bold"), "relief": "flat", "background": "#e0e0e0"})
        ]:
            style.configure(element, **config)
        style.map("Flat.TButton", background=[('active', '#d0d0d0')])
        self.var_port = tk.StringVar(value=state.target_port)
        self.var_duration = tk.StringVar(value=str(int(state.duration)))
        self.var_ip = tk.StringVar(value="---")
        self.var_last_ip = tk.StringVar(value="---")
        self.var_btn_text = tk.StringVar(value=f"{state.trigger_str}")
        self.var_lock = tk.BooleanVar(value=state.lock_timer)
        self.overlay = OverlayTimer(self)
        self.create_widgets()
        self.after(1000, self.delayed_startup)
        self.update_loop()
        self.check_minimize_loop()

    def delayed_startup(self):
        optimize_system()
        restart_input_listeners()
        threading.Thread(target=capture_worker, daemon=True).start()
        threading.Thread(target=flush_worker, daemon=True).start()
        threading.Thread(target=watchdog_worker, daemon=True).start()

    def create_widgets(self):
        self.canvas_ind = tk.Canvas(self, height=45, bg="#cccccc", highlightthickness=0, cursor="hand2")
        self.canvas_ind.pack(side="bottom", fill="x")
        self.ind_rect = self.canvas_ind.create_rectangle(0, 0, 300, 50, fill="#cc0000", outline="")
        self.ind_text = self.canvas_ind.create_text(120, 22, text="OFF", fill="white", font=("Segoe UI", 16, "bold"))
        self.canvas_ind.bind("<Button-1>", lambda e: toggle_lag("gui"))
        content = ttk.Frame(self)
        content.pack(side="top", fill="both", expand=True, padx=15, pady=10)
        f_ip = ttk.LabelFrame(content, text="IP History")
        f_ip.pack(fill="x", pady=(0, 10), ipady=3)
        f_ip.columnconfigure(1, weight=1)
        ttk.Label(f_ip, text="Previous:", font=("Segoe UI", 9, "bold"), foreground="#888").grid(row=0, column=0, padx=(10, 5), pady=2, sticky="w")
        ttk.Label(f_ip, textvariable=self.var_last_ip, foreground="#888", font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        tk.Button(f_ip, text="❐", font=("Segoe UI", 8), command=self.copy_last_ip, bd=0, bg="#f0f0f0", cursor="hand2").grid(row=0, column=2, padx=10)
        ttk.Label(f_ip, text="Current:", font=("Segoe UI", 9, "bold"), foreground="#444").grid(row=1, column=0, padx=(10, 5), pady=2, sticky="w")
        ttk.Label(f_ip, textvariable=self.var_ip, font=("Segoe UI", 9, "bold"), foreground="#000").grid(row=1, column=1, pady=2, sticky="w")
        tk.Button(f_ip, text="❐", font=("Segoe UI", 8), command=self.copy_ip, bd=0, bg="#f0f0f0", cursor="hand2").grid(row=1, column=2, padx=10)
        f_cfg = ttk.LabelFrame(content, text="Configuration")
        f_cfg.pack(fill="x", pady=(0, 10), ipady=2)
        f_port = ttk.Frame(f_cfg)
        f_port.pack(fill="x", padx=10, pady=3)
        ttk.Label(f_port, text="Target Port:").pack(side="left")
        e_port = ttk.Entry(f_port, textvariable=self.var_port, width=8, justify="center", font=("Segoe UI", 9))
        e_port.pack(side="right")
        e_port.bind("<FocusOut>", self.update_config)
        f_dur = ttk.Frame(f_cfg)
        f_dur.pack(fill="x", padx=10, pady=(0, 5))
        ttk.Label(f_dur, text="Max Duration (s):").pack(side="left")
        e_dur = ttk.Entry(f_dur, textvariable=self.var_duration, width=8, justify="center", font=("Segoe UI", 9))
        e_dur.pack(side="right")
        e_dur.bind("<FocusOut>", self.update_config)
        f_lock = ttk.Frame(f_cfg)
        f_lock.pack(fill="x", padx=10, pady=(5, 5))
        chk_lock = ttk.Checkbutton(f_lock, text="Lock Timer Position", variable=self.var_lock, command=self.toggle_lock)
        chk_lock.pack(side="left")
        f_trig = ttk.LabelFrame(content, text="Trigger")
        f_trig.pack(fill="x", pady=(0, 0), ipady=2)
        lbl_trig = ttk.Label(f_trig, textvariable=self.var_btn_text, font=("Segoe UI", 9, "bold"), anchor="center")
        lbl_trig.pack(fill="x", pady=(5, 3))
        btn_remap = ttk.Button(f_trig, text="Remap Key / Button", command=lambda: setattr(state, 'remap_mode', True), style="Flat.TButton")
        btn_remap.pack(fill="x", padx=10, pady=(0, 6))

    def toggle_lock(self):
        state.lock_timer = self.var_lock.get()
        self.overlay.update_click_through()
        state.save_config()

    def update_loop(self):
        active_now = state.lag_event.is_set()
        self.overlay.update_view()
        if active_now != self._last_lag_state:
            color = "#00cc00" if active_now else "#cc0000"
            status_text = "ON" if active_now else "OFF"
            self.canvas_ind.itemconfig(self.ind_rect, fill=color)
            self.canvas_ind.itemconfig(self.ind_text, text=status_text)
            if self.tray_icon:
                self.tray_icon.icon = self.create_tray_image(color)
            self._last_lag_state = active_now
        width = self.canvas_ind.winfo_width()
        self.canvas_ind.coords(self.ind_rect, 0, 0, width, 50)
        self.canvas_ind.coords(self.ind_text, width/2, 23)
        if state.current_ip != self._last_ip_text:
            self.var_ip.set(state.current_ip)
            self._last_ip_text = state.current_ip
        if state.last_ip != self._last_prev_ip_text:
            self.var_last_ip.set(state.last_ip)
            self._last_prev_ip_text = state.last_ip
        display_text = "Press Key..." if state.remap_mode else state.trigger_str
        if display_text != self._last_btn_text:
            self.var_btn_text.set(display_text)
            self._last_btn_text = display_text
        self.after(66, self.update_loop)

    def check_minimize_loop(self):
        if self.state() == 'iconic':
            self.withdraw()
            self.show_tray()
        self.after(200, self.check_minimize_loop)

    def update_config(self, event=None):
        try:
            state.target_port = self.var_port.get()
            state.duration = float(self.var_duration.get())
            state.save_config()
        except ValueError:
            logging.error("Invalid port or duration value.")
        except Exception as e:
            logging.error(f"Error updating config: %s", e)

    def copy_ip(self):
        self.clipboard_clear()
        self.clipboard_append(state.current_ip)

    def copy_last_ip(self):
        self.clipboard_clear()
        self.clipboard_append(state.last_ip)

    def on_window_state_change(self, event):
        pass

    def on_close_x(self):
        state.app_running = False
        def safe_stop(listener, name):
            if listener:
                try:
                    listener.stop()
                except Exception as e:
                    logging.error(f"Error stopping {name}: %s", e)
        safe_stop(state.mouse_listener, "mouse")
        safe_stop(state.kb_listener, "keyboard")
        if state.divert:
            try:
                state.divert.close()
            except Exception as e:
                logging.error(f"Error closing divert: %s", e)
        if self.tray_icon:
            self.tray_icon.stop()
        with state.buffer_cond:
            state.buffer_cond.notify_all()
        restore_system()
        self.destroy()
        time.sleep(0.1)
        os._exit(0)

    def create_tray_image(self, color_str):
        image_file = resource_path("icon_on.png") if color_str == "#00cc00" else resource_path("icon_off.png")
        try:
            return Image.open(image_file)
        except FileNotFoundError:
            logging.error(f"Tray icon file not found: {image_file}")
        except Exception as e:
            logging.error(f"Error loading tray icon: %s", e)
        image = Image.new('RGB', (64, 64), (0, 0, 0))
        d = ImageDraw.Draw(image)
        d.rectangle([10, 10, 54, 54], fill=color_str)
        return image

    def show_tray(self):
        if self.tray_icon:
            return
        def on_tray_exit(icon, item):
            self.after(0, self.on_close_x)
        def on_tray_show(icon, item):
            self.after(0, self.deiconify)
        menu = pystray.Menu(
            pystray.MenuItem("Show", on_tray_show),
            pystray.MenuItem("Exit", on_tray_exit)
        )
        self.tray_icon = pystray.Icon("clumsex", icon=self.create_tray_image("#cc0000"), title="clumsex", menu=menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

if __name__ == "__main__":
    app = ClumsexGUI()
    app.mainloop()