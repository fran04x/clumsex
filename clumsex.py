# --- AUTO-UPDATED: 2025-12-02 18:48:20 UTC ---
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

# --- ESTRUCTURAS WINDOWS ---
class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), 
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except AttributeError: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

APP_NAME = "clumsex"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# --- ESTADO GLOBAL ---
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
        
        # Sincronización eficiente entre Capture y Flush
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
        self.game_window_title = "RotMG Exalt"
        
        self.mouse_listener = None
        self.kb_listener = None
        
        self.load_config()

    def get_clean_trigger_str(self, key_obj, k_type):
        if k_type == "mouse":
            return str(key_obj).replace("Button.", "").capitalize() + " Click"
        else:
            try: return key_obj.char.upper()
            except AttributeError: return str(key_obj).replace("Key.", "").upper()
            except: return str(key_obj).replace("Key.", "").upper()

    def save_config(self):
        if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
        trigger_val = str(self.trigger_btn).replace("'", "")
        data = {
            "port": self.target_port,
            "duration": self.duration,
            "lock_timer": self.lock_timer,
            "timer_pos": self.timer_pos,
            "hotkey_type": self.hotkey_type,
            "trigger_val": trigger_val
        }
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)
        except Exception: pass

    def load_config(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.target_port = data.get("port", "2050")
                self.duration = float(data.get("duration", 12.0))
                self.lock_timer = data.get("lock_timer", True)
                self.timer_pos = data.get("timer_pos", None)
                h_type = data.get("hotkey_type", "mouse")
                t_val = data.get("trigger_val", "Button.middle")
                self.hotkey_type = h_type
                if h_type == "mouse":
                    btn_name = t_val.split('.')[-1]
                    self.trigger_btn = getattr(mouse.Button, btn_name, mouse.Button.middle)
                else:
                    if "Key." in t_val:
                        key_name = t_val.split('.')[-1]
                        self.trigger_btn = getattr(keyboard.Key, key_name, keyboard.Key.f2)
                    else:
                        self.trigger_btn = keyboard.KeyCode(char=t_val)
                self.trigger_str = self.get_clean_trigger_str(self.trigger_btn, self.hotkey_type)
        except Exception: pass

state = GlobalState()

# --- UTILS SISTEMA ---
def optimize_system():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        pid = os.getpid()
        handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
        # Prioridad NORMAL para evitar starvation en CPUs débiles
        ctypes.windll.kernel32.SetPriorityClass(handle, 0x00000020)
            
        ctypes.windll.kernel32.CloseHandle(handle)
        ctypes.windll.winmm.timeBeginPeriod(1)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('clumsex.v12.2')
    except Exception: pass

def restore_system():
    try: ctypes.windll.winmm.timeEndPeriod(1)
    except Exception: pass

def restore_gc():
    with state.gc_lock:
        if state.gc_dirty:
            gc.enable()
            state.gc_dirty = False

# --- WATCHDOG DEDICADO ---
def watchdog_worker():
    """Hilo de bajo costo que solo despierta para apagar el lag."""
    while state.app_running:
        # Espera pasiva eficiente (0% CPU)
        if state.lag_event.wait():
            deadline = state.lag_start_time + state.duration
            
            while state.lag_event.is_set():
                now = time.perf_counter()
                remaining = deadline - now
                
                if remaining <= 0:
                    deactivate_lag()
                    break
                
                # Dormir inteligentemente
                time.sleep(min(remaining, 0.1))
                
            # Limpieza GC al salir
            if state.gc_dirty:
                restore_gc()

# --- CAPTURE WORKER ---
def capture_worker():
    active_port_filter = state.target_port
    
    while state.app_running:
        current_filter = f"outbound and tcp.DstPort == {active_port_filter} and tcp.PayloadLength > 0"
        
        try:
            with pydivert.WinDivert(current_filter) as w:
                state.divert = w
                
                # Bucle bloqueante (0% CPU idle)
                for packet in w:
                    if not state.app_running: break
                    
                    if state.target_port != active_port_filter:
                        # Forzar flush y despertar worker
                        with state.buffer_cond:
                            state.buffer_cond.notify()
                        active_port_filter = state.target_port
                        break 

                    with state.lock:
                        if state.current_ip != packet.dst_addr:
                            if state.current_ip != "---": state.last_ip = state.current_ip
                            state.current_ip = packet.dst_addr

                    if state.lag_event.is_set():
                        # Lag ON: Encolar bajo lock del condition
                        with state.buffer_cond:
                            state.packet_buffer.append((packet.raw, packet.interface, packet.direction))
                    else:
                        # Lag OFF: Passthrough
                        w.send(packet)
                        
                        # [Fix #3] Notificar SOLO si hay buffer remanente
                        if state.packet_buffer:
                            with state.buffer_cond:
                                state.buffer_cond.notify()

        except OSError: 
            pass
        except Exception:
            time.sleep(1)
        finally:
            state.divert = None

# --- FLUSH WORKER (EVENT DRIVEN) ---
def flush_worker():
    try:
        with pydivert.WinDivert("false") as w_inject:
            PacketCls = pydivert.Packet
            send_func = w_inject.send
            perf = time.perf_counter
            
            queue = state.packet_buffer
            base_rate = state.shaping_rate
            
            tokens = state.shaping_burst
            last_check = perf()

            while state.app_running:
                packet_data = None
                
                # 1. ESPERA EFICIENTE
                with state.buffer_cond:
                    # Dormir si no hay datos O hay lag activo
                    while (not queue or state.lag_event.is_set()) and state.app_running:
                        if state.lag_event.is_set():
                            last_check = perf()
                        state.buffer_cond.wait() # 0% CPU Sleep
                    
                    if not state.app_running: break
                    packet_data = queue.popleft()

                # 2. PROCESAMIENTO
                if state.lag_event.is_set():
                    with state.buffer_cond:
                        queue.appendleft(packet_data)
                    continue

                current_rate = base_rate * 3.0 if len(queue) > 5000 else base_rate
                
                now = perf()
                elapsed = now - last_check
                last_check = now
                tokens = min(state.shaping_burst, tokens + (elapsed * current_rate))
                if tokens < 0: tokens = 0

                # Token Wait Matemático (No spinlock)
                if tokens < 1.0:
                    needed = 1.0 - tokens
                    wait_time = needed / current_rate
                    if wait_time > 0: time.sleep(wait_time)
                    
                    now = perf()
                    elapsed = now - last_check
                    last_check = now
                    tokens = min(state.shaping_burst, tokens + (elapsed * current_rate))

                if state.lag_event.is_set():
                    with state.buffer_cond:
                        queue.appendleft(packet_data)
                    continue

                try:
                    raw, iface, direction = packet_data
                    if raw is None: continue 
                    pkt = PacketCls.__new__(PacketCls)
                    pkt.raw = raw
                    pkt.interface = iface
                    pkt.direction = direction
                    send_func(pkt)
                    tokens -= 1.0
                except Exception: pass
                
                if not queue:
                    restore_gc()
                    if current_rate > base_rate: gc.collect()

    except Exception as e:
        print(f"Flush died: {e}")

# --- CONTROL ---
def toggle_lag(source="unknown"):
    if state.remap_mode: return
    
    now = time.time()
    if (now - state.last_toggle_time) < 0.2: return
    state.last_toggle_time = now

    if not state.lag_event.is_set():
        # ACTIVATE
        with state.gc_lock:
            if not state.gc_dirty:
                gc.disable()
                state.gc_dirty = True
        state.lag_start_time = time.perf_counter()
        state.lag_event.set()
        # No notificamos al flush, dejamos que se duerma naturalmente
    else:
        # DEACTIVATE
        state.lag_event.clear()
        # [Fix #5] Notificar explícitamente para despertar al flush worker
        with state.buffer_cond:
            state.buffer_cond.notify()

def deactivate_lag():
    state.lag_event.clear()
    with state.buffer_cond:
        state.buffer_cond.notify()

# --- INPUT SYSTEM ---
def on_input_event(key_or_btn, device_type):
    if device_type == "mouse":
        if key_or_btn == mouse.Button.left or key_or_btn == mouse.Button.right: return 
    
    if device_type == "keyboard":
        invalid_keys = [keyboard.Key.shift, keyboard.Key.shift_r, 
                        keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                        keyboard.Key.alt_l, keyboard.Key.alt_gr,
                        keyboard.Key.cmd, keyboard.Key.cmd_r,
                        keyboard.Key.caps_lock]
        if key_or_btn in invalid_keys: return 
    
    with state.lock:
        state.hotkey_type = device_type
        state.trigger_btn = key_or_btn
        state.trigger_str = state.get_clean_trigger_str(key_or_btn, device_type)
        state.remap_mode = False
        state.save_config()
    
    threading.Thread(target=restart_input_listeners, daemon=True).start()
    return False

def restart_input_listeners():
    if state.mouse_listener:
        try: state.mouse_listener.stop(); state.mouse_listener.join(0.1) 
        except Exception: pass
    if state.kb_listener:
        try: state.kb_listener.stop(); state.kb_listener.join(0.1)
        except Exception: pass
    time.sleep(0.1)
    state.mouse_listener = mouse.Listener(on_click=on_mouse_click)
    state.mouse_listener.start()
    state.kb_listener = keyboard.Listener(on_press=on_key_press)
    state.kb_listener.start()

def on_mouse_click(x, y, button, pressed):
    if not pressed: return
    if state.remap_mode: on_input_event(button, "mouse")
    elif state.hotkey_type == "mouse" and button == state.trigger_btn: toggle_lag()

def on_key_press(key):
    if state.remap_mode: on_input_event(key, "keyboard")
    elif state.hotkey_type == "keyboard" and key == state.trigger_btn: toggle_lag()

# --- OVERLAY ---
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
        
        # [Fix #6] Contador para Throttling de Tracking
        self.track_counter = 0 
        
        self.bind('<Button-1>', self.click_win)
        self.bind('<B1-Motion>', self.drag_win)
        self.bind('<ButtonRelease-1>', self.release_win)
        self.update_click_through()
        
        if state.timer_pos:
            self.geometry(f"{self.width}x{self.height}+{state.timer_pos[0]}+{state.timer_pos[1]}")
        else:
            self.geometry(f"{self.width}x{self.height}+-1000+-1000")

    def click_win(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def drag_win(self, event):
        x = self.winfo_x() + (event.x - self._offsetx)
        y = self.winfo_y() + (event.y - self._offsety)
        self.geometry(f"+{x}+{y}")

    def release_win(self, event):
        state.timer_pos = (self.winfo_x(), self.winfo_y())
        state.save_config()

    def update_click_through(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            if state.lock_timer:
                style = style | 0x80000 | 0x20 
                self.lbl_time.config(cursor="arrow")
            else:
                style = style & ~0x20 | 0x80000
                self.lbl_time.config(cursor="fleur")
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
        except Exception: pass

    def update_view(self):
        is_visible = (not state.lock_timer) or state.lag_event.is_set()
        
        if is_visible != self._last_visible:
            if not is_visible: self.withdraw()
            else:
                self.deiconify()
                self.attributes("-topmost", True)
            self._last_visible = is_visible
            
        if not is_visible: return

        text, color = "", ""
        if not state.lag_event.is_set():
            if not state.lock_timer: text, color = "DRAG ME", "#FFFFFF"
            else: text, color = "READY", "#00FF00"
        else:
            elapsed = time.perf_counter() - state.lag_start_time
            remaining = state.duration - elapsed
            if remaining < 0: remaining = 0
            if remaining > 6.0: color = "#00FF00"
            elif remaining > 3.0: color = "#FFFF00"
            else: color = "#FF0000"
            text = f"{remaining:.1f}s"
            
        if text != self._last_text or color != self._last_color:
            self.lbl_time.config(text=text, fg=color)
            self._last_text, self._last_color = text, color

        # [Fix #6] Tracking Throttled (1 de cada 8 frames ~ 500ms)
        if state.lock_timer:
            self.track_counter += 1
            if self.track_counter >= 8:
                self.track_counter = 0
                try:
                    hwnd_target = ctypes.windll.user32.FindWindowW(None, state.game_window_title)
                    if hwnd_target:
                        rect = RECT()
                        ctypes.windll.user32.GetWindowRect(hwnd_target, ctypes.byref(rect))
                        win_w = rect.right - rect.left
                        new_x = rect.left + (win_w // 2) - (self.width // 2)
                        new_y = rect.top + 20 
                        
                        curr_geo = self.geometry().split('+')
                        if len(curr_geo) > 1:
                            cx, cy = int(curr_geo[1]), int(curr_geo[2])
                            if abs(cx - new_x) > 2 or abs(cy - new_y) > 2:
                                self.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
                except Exception: pass

# --- GUI PRINCIPAL ---
class ClumsexGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("clumsex")
        self.geometry("240x390") 
        self.resizable(False, False)
        try: self.iconbitmap(resource_path("clumsex.ico"))
        except Exception: pass
        
        self.protocol("WM_DELETE_WINDOW", self.on_close_x)
        self.bind("<Map>", self.on_window_state_change)
        
        self.tray_icon = None
        self.last_icon_color = "red"
        self._last_lag_state = None
        self._last_ip_text = ""
        self._last_prev_ip_text = ""
        self._last_btn_text = ""
        
        self.bg_color = "#f2f2f2"
        self.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabelframe", background=self.bg_color, relief="flat")
        style.configure("TLabelframe.Label", background=self.bg_color, font=("Segoe UI", 10, "bold"), foreground="#333")
        style.configure("TLabel", background=self.bg_color, font=("Segoe UI", 9), foreground="#444")
        style.configure("TCheckbutton", background=self.bg_color, font=("Segoe UI", 9))
        style.configure("Flat.TButton", font=("Segoe UI", 9, "bold"), relief="flat", background="#e0e0e0")
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
        self.t_net = threading.Thread(target=capture_worker, daemon=True)
        self.t_net.start()
        self.t_flush = threading.Thread(target=flush_worker, daemon=True)
        self.t_flush.start()
        self.t_watch = threading.Thread(target=watchdog_worker, daemon=True)
        self.t_watch.start()

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
        with state.lock:
            active_now = state.lag_event.is_set()
            
        self.overlay.update_view()
        
        if active_now != self._last_lag_state:
            target_color = "#00cc00" if active_now else "#cc0000"
            status_text = "ON" if active_now else "OFF"
            self.canvas_ind.itemconfig(self.ind_rect, fill=target_color)
            self.canvas_ind.itemconfig(self.ind_text, text=status_text)
            if self.tray_icon:
                self.tray_icon.icon = self.create_tray_image(target_color)
            self._last_lag_state = active_now
            
        w = self.canvas_ind.winfo_width()
        self.canvas_ind.coords(self.ind_rect, 0, 0, w, 50)
        self.canvas_ind.coords(self.ind_text, w/2, 23)
        
        with state.lock:
            if state.current_ip != self._last_ip_text:
                self.var_ip.set(state.current_ip)
                self._last_ip_text = state.current_ip
            if state.last_ip != self._last_prev_ip_text:
                self.var_last_ip.set(state.last_ip)
                self._last_prev_ip_text = state.last_ip
            
        if state.remap_mode: txt = "Press Key..."
        else: txt = f"{state.trigger_str}"
        if txt != self._last_btn_text:
            self.var_btn_text.set(txt)
            self._last_btn_text = txt
            
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
        except Exception: pass

    def copy_ip(self):
        self.clipboard_clear()
        self.clipboard_append(state.current_ip)

    def copy_last_ip(self):
        self.clipboard_clear()
        self.clipboard_append(state.last_ip)

    def on_window_state_change(self, event): pass

    def on_close_x(self):
        state.app_running = False
        if state.mouse_listener:
            try: state.mouse_listener.stop()
            except Exception: pass
        if state.kb_listener:
            try: state.kb_listener.stop()
            except Exception: pass
        if state.divert:
            try: state.divert.close()
            except Exception: pass
        if self.tray_icon: self.tray_icon.stop()
        
        # Wake up workers to exit loops
        with state.buffer_cond:
            state.buffer_cond.notify_all()
            
        restore_system()
        self.destroy()
        time.sleep(0.1)
        os._exit(0)

    def create_tray_image(self, color_str):
        image_file = resource_path("icon_on.png") if color_str == "#00cc00" else resource_path("icon_off.png")
        try: return Image.open(image_file)
        except Exception:
            image = Image.new('RGB', (64, 64), (0, 0, 0))
            d = ImageDraw.Draw(image)
            d.rectangle([10, 10, 54, 54], fill=color_str)
            return image

    def show_tray(self):
        if self.tray_icon: return 
        initial_color = "#00cc00" if state.lag_event.is_set() else "#cc0000"
        self.last_icon_color = initial_color
        def restore_window(icon, item):
            icon.stop()
            self.tray_icon = None
            self.after(0, self.deiconify)
        def quit_app(icon, item):
            icon.stop()
            self.on_close_x()
        menu = pystray.Menu(
            pystray.MenuItem('Restaurar', restore_window, default=True),
            pystray.MenuItem('Salir', quit_app)
        )
        self.tray_icon = pystray.Icon("clumsex", self.create_tray_image(initial_color), "clumsex", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

if __name__ == "__main__":
    app = ClumsexGUI()
    app.mainloop()