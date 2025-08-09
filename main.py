import os

# Environment tweaks
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

from startup import ask_startup, is_in_startup, add_to_startup, remove_from_startup

import psutil
from py3nvml.py3nvml import *  # type: ignore
import tkinter as tk
from tkinter import ttk
import time
from typing import Optional, Dict, Tuple, List

# Pillow for anti-aliased gauges
try:
    from PIL import Image, ImageDraw, ImageTk  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageTk = None  # type: ignore

# ---------------- Theme ---------------- #
PRIMARY_BG = "#121317"
CARD_BG = "#1E1F24"
HEADER_BG = "#1A1C21"
ACCENT = "#4C8BF5"
FG = "#FFFFFF"
MUTED_FG = "#9CA3AF"
TRACK = "#2A2F38"
CPU_COLOR = "#28C76F"
RAM_COLOR = "#FECB2E"
GPU_COLOR = "#7367F0"
VRAM_COLOR = "#00B5FF"
DANGER_COLOR = "#EA5455"
IO_COLOR = "#FF9F43"
NET_COLOR = "#4C8BF5"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SECTION = ("Segoe UI Semibold", 11)
FONT_GAUGE = ("Segoe UI Semibold", 11)
FONT_SMALL = ("Segoe UI", 10)
FONT_TINY = ("Segoe UI", 9)

SMOOTH_ALPHA = 0.30
UPDATE_MS = 1000
RENDER_DELTA_THRESH = 0.4  # percent change required to redraw ring

# NVML persistent handle to reduce init cost
_NVML_INITIALIZED = False
_NVML_HANDLE = None

def safe_nvml_get() -> Tuple[float, Optional[float], Optional[Tuple[int,int]]]:
    """Return (gpu_util%, temperatureC, (vram_used, vram_total)) with persistent NVML handle."""
    global _NVML_INITIALIZED, _NVML_HANDLE
    try:
        if not _NVML_INITIALIZED:
            nvmlInit()
            _NVML_HANDLE = nvmlDeviceGetHandleByIndex(0)
            _NVML_INITIALIZED = True
        handle = _NVML_HANDLE  # type: ignore
        util_obj = nvmlDeviceGetUtilizationRates(handle)
        utilization = float(getattr(util_obj, 'gpu', 0.0) if util_obj else 0.0)
        temperature = float(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
        mem = nvmlDeviceGetMemoryInfo(handle)  # type: ignore[assignment]
        vram_tuple = (int(getattr(mem, 'used', 0)), int(getattr(mem, 'total', 0))) if mem else None  # type: ignore[attr-defined]
        return utilization, temperature, vram_tuple
    except Exception:
        return 0.0, None, None

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def interpolate_color(start: str, mid: str, end: str, fraction: float) -> str:
    fraction = max(0.0, min(1.0, fraction))
    if fraction < 0.5:
        local = fraction / 0.5
        s, e = start, mid
    else:
        local = (fraction - 0.5) / 0.5
        s, e = mid, end
    rs, gs, bs = int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)
    re, ge, be = int(e[1:3], 16), int(e[3:5], 16), int(e[5:7], 16)
    r = int(lerp(rs, re, local))
    g = int(lerp(gs, ge, local))
    b = int(lerp(bs, be, local))
    return f"#{r:02X}{g:02X}{b:02X}"

def format_bytes(n: float) -> str:
    units = ['B','KB','MB','GB','TB']
    i = 0
    while n >= 1024 and i < len(units)-1:
        n /= 1024
        i += 1
    return f"{n:.1f} {units[i]}"

def format_time(sec: float) -> str:
    sec = int(sec)
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

# ---------------- Gauge Widget (Anti-aliased) ---------------- #

class RingGauge(tk.Frame):
    def __init__(self, master, diameter: int = 110, thickness: int = 12, label: str = "", base_color: str = ACCENT):
        super().__init__(master, bg=CARD_BG)
        self.diameter = diameter
        self.thickness = thickness
        self.label_text = label
        self.base_color = base_color
        self.image_label = tk.Label(self, bg=CARD_BG)
        self.image_label.pack(padx=2, pady=(4,0))
        self.text_var = tk.StringVar(value="0%")
        self.label_var = tk.StringVar(value=label)
        tk.Label(self, textvariable=self.text_var, font=FONT_GAUGE, fg=FG, bg=CARD_BG).pack(pady=(0,0))
        tk.Label(self, textvariable=self.label_var, font=FONT_TINY, fg=MUTED_FG, bg=CARD_BG).pack(pady=(0,6))
        self._cache_img = None
        self._last_drawn_value = -1.0
        self._last_color = None

    def set_value(self, value: float, color: Optional[str] = None, show_percent: bool = True):
        value = max(0.0, min(100.0, value))
        self.text_var.set(f"{value:.0f}%" if show_percent else f"{value:.1f}")
        col = color or self.base_color
        # Skip redraw if change is tiny & color unchanged
        if abs(value - self._last_drawn_value) < RENDER_DELTA_THRESH and col == self._last_color:
            return
        if Image is None:  # Fallback: text only
            self.image_label.configure(text=f"{value:.0f}%")
            self._last_drawn_value = value
            self._last_color = col
            return
        d = self.diameter
        upscale = 4
        size = d * upscale
        img = Image.new('RGBA', (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(img)  # type: ignore[assignment]
        track_w = self.thickness * upscale
        pad = track_w//2 + 3*upscale
        # Track
        draw.arc((pad, pad, size-pad, size-pad), start=0, end=359, fill=TRACK, width=track_w)
        # Value arc
        extent = 360 * (value / 100.0)
        start_angle = -90
        end_angle = start_angle + extent
        draw.arc((pad, pad, size-pad, size-pad), start=start_angle, end=end_angle, fill=col, width=track_w)
        img_small = img.resize((d, d), Image.LANCZOS)  # type: ignore[attr-defined]
        self._cache_img = ImageTk.PhotoImage(img_small)  # type: ignore[attr-defined]
        self.image_label.configure(image=self._cache_img)
        self._last_drawn_value = value
        self._last_color = col

# ---------------- Main Application ---------------- #

class ResourceMonitorApp:
    def __init__(self):
        ask_startup()
        self.root = tk.Tk()
        self.root.title("Monix – Resource Monitor")
        self.root.configure(bg=PRIMARY_BG)
        # Increased size further for footer + card content
        self.root.geometry("840x460")
        self.root.minsize(840, 460)
        self.root.overrideredirect(True)
        # Always on top (no pin toggle now)
        self.root.wm_attributes('-topmost', True)
        self.drag_origin = (0,0)

        # Styles
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Dark.Horizontal.TProgressbar', background=ACCENT, troughcolor=TRACK, bordercolor=TRACK, lightcolor=ACCENT, darkcolor=ACCENT)

        self._build_ui()

        # State
        self.prev_net = psutil.net_io_counters()
        self.prev_disk_io = psutil.disk_io_counters(perdisk=True)
        self.prev_time = time.time()
        psutil.cpu_percent(interval=None)
        self.state_ema: Dict[str, float] = {}
        self.update_fail_count = 0
        self.update_counter = 0
        self.root.after(200, self.update_stats)

    # ---------- UI Construction ---------- #
    def _build_ui(self):
        header = tk.Frame(self.root, bg=HEADER_BG, height=40)
        header.pack(fill='x', side='top')
        header.bind('<Button-1>', self._start_drag)
        header.bind('<B1-Motion>', self._do_drag)
        title = tk.Label(header, text="Monix", fg=FG, bg=HEADER_BG, font=FONT_TITLE)
        title.pack(side='left', padx=14)
        title.bind('<Button-1>', self._start_drag)
        title.bind('<B1-Motion>', self._do_drag)

        def btn(text, cmd, bg=HEADER_BG, fg=FG, active="#2A2D33"):
            b = tk.Label(header, text=text, fg=fg, bg=bg, cursor='hand2', font=("Segoe UI", 11))
            b.pack(side='right', padx=4, pady=4)
            b.bind('<Enter>', lambda e: b.configure(bg=active))
            b.bind('<Leave>', lambda e: b.configure(bg=bg))
            b.bind('<Button-1>', lambda e: cmd())
            return b

        # Options (gear) button
        self.settings_button = btn('⚙', self._open_menu, bg='#3A3F44')
        btn('✕', self.quit, bg='#D9534F')
        btn('—', self.minimize, bg='#3A3F44')
        # No pin button, no right-click menu usage

        # Content (no scrolling; compact grid)
        content = tk.Frame(self.root, bg=PRIMARY_BG)
        content.pack(fill='both', expand=True, padx=6, pady=(2,4))

        # Gauges row
        gauges_row = tk.Frame(content, bg=PRIMARY_BG)
        gauges_row.pack(pady=(0,0))  # reduced vertical padding to free space
        # Smaller diameter to save space
        self.gauge_cpu = RingGauge(gauges_row, label='CPU', base_color=CPU_COLOR, diameter=100)
        self.gauge_ram = RingGauge(gauges_row, label='RAM', base_color=RAM_COLOR, diameter=100)
        self.gauge_gpu = RingGauge(gauges_row, label='GPU', base_color=GPU_COLOR, diameter=100)
        self.gauge_vram = RingGauge(gauges_row, label='VRAM', base_color=VRAM_COLOR, diameter=100)
        for g in [self.gauge_cpu, self.gauge_ram, self.gauge_gpu, self.gauge_vram]:
            g.pack(side='left', padx=10)

        # Lower cards container
        lower = tk.Frame(content, bg=PRIMARY_BG)
        lower.pack(fill='both', expand=True)

        # Memory & GPU
        mem_gpu_card = self._card(lower, 'Memory / GPU')
        self.mem_detail_var = tk.StringVar(value='—')
        self.gpu_detail_var = tk.StringVar(value='—')
        tk.Label(mem_gpu_card, textvariable=self.mem_detail_var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL, justify='left').pack(anchor='w', padx=12, pady=(0,4))
        tk.Label(mem_gpu_card, textvariable=self.gpu_detail_var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL, justify='left').pack(anchor='w', padx=12, pady=(0,6))

        # Disk / IO
        disk_card = self._card(lower, 'Disk / IO')
        self.disk_usage_frame = tk.Frame(disk_card, bg=CARD_BG)
        self.disk_usage_frame.pack(fill='x', padx=12, pady=(0,4))
        self.disk_io_var = tk.StringVar(value='IO: –')
        tk.Label(disk_card, textvariable=self.disk_io_var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL).pack(anchor='w', padx=12, pady=(0,6))
        self.disk_usage_rows: Dict[str, Tuple[ttk.Progressbar, tk.Label, tk.Label]] = {}

        # Network
        net_card = self._card(lower, 'Network')
        self.net_down_var = tk.StringVar(value='Down: – Mb/s')
        self.net_up_var = tk.StringVar(value='Up: – Mb/s')
        tk.Label(net_card, textvariable=self.net_down_var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL).pack(anchor='w', padx=12, pady=(0,0))
        tk.Label(net_card, textvariable=self.net_up_var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL).pack(anchor='w', padx=12, pady=(0,6))

        # System
        sys_card = self._card(lower, 'System')
        self.cpu_temp_var = tk.StringVar(value='CPU Temp: –')
        self.gpu_temp_var = tk.StringVar(value='GPU Temp: –')
        self.uptime_var = tk.StringVar(value='Uptime: –')
        self.proc_summary_var = tk.StringVar(value='Processes: –')
        self.battery_var = tk.StringVar(value='Battery: –')
        for var in [self.cpu_temp_var, self.gpu_temp_var, self.uptime_var, self.proc_summary_var, self.battery_var]:
            tk.Label(sys_card, textvariable=var, bg=CARD_BG, fg=MUTED_FG, font=FONT_SMALL).pack(anchor='w', padx=12)
        # Removed right-click hint label

        # Arrange lower cards horizontally
        mem_gpu_card.pack(side='left', fill='both', expand=True, padx=4)
        disk_card.pack(side='left', fill='both', expand=True, padx=4)
        net_card.pack(side='left', fill='both', expand=True, padx=4)
        sys_card.pack(side='left', fill='both', expand=True, padx=4)

        # Footer (taller to prevent cutoff)
        footer = tk.Frame(self.root, bg=HEADER_BG, height=38)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        self.status_var = tk.StringVar(value='Initializing…')
        tk.Label(footer, textvariable=self.status_var, bg=HEADER_BG, fg=MUTED_FG, font=FONT_TINY).pack(side='left', padx=8)
        self.last_update_var = tk.StringVar(value='—')
        tk.Label(footer, textvariable=self.last_update_var, bg=HEADER_BG, fg=MUTED_FG, font=FONT_TINY).pack(side='right', padx=8)

        # Menu now opened via gear button only
        self.menu = tk.Menu(self.root, tearoff=0, bg=CARD_BG, fg=FG, activebackground=ACCENT, activeforeground=FG)
        self.menu.add_command(label="Toggle Startup", command=self._toggle_startup)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.quit)
        # Removed right-click binding
        self.root.bind('<Escape>', lambda e: self.quit())

    def _card(self, master, title: str):
        frame = tk.Frame(master, bg=CARD_BG, bd=0, highlightthickness=0)
        lbl = tk.Label(frame, text=title, font=FONT_SECTION, fg=FG, bg=CARD_BG, anchor='w')
        lbl.pack(fill='x', padx=12, pady=(8,2))
        # Optional subtle separator line (draw using a thin frame)
        sep = tk.Frame(frame, bg=TRACK, height=1)
        sep.pack(fill='x', padx=12, pady=(0,4))
        return frame

    # New helper to open menu below gear button
    def _open_menu(self):
        try:
            x = self.settings_button.winfo_rootx()
            y = self.settings_button.winfo_rooty() + self.settings_button.winfo_height()
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    # ---------- Event Handlers ---------- #
    def _start_drag(self, event):
        self.drag_origin = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _do_drag(self, event):
        x = event.x_root - self.drag_origin[0]
        y = event.y_root - self.drag_origin[1]
        self.root.geometry(f"+{x}+{y}")

    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _toggle_startup(self):
        if is_in_startup():
            if remove_from_startup():
                self.status_var.set('Startup disabled')
        else:
            if add_to_startup():
                self.status_var.set('Startup enabled')

    def minimize(self):
        self.root.update_idletasks()
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(50, lambda: self.root.overrideredirect(True))

    def quit(self):
        try:
            if _NVML_INITIALIZED:
                nvmlShutdown()
        except Exception:
            pass
        self.root.destroy()

    # ---------- Stats Update ---------- #
    def ema(self, key: str, new: float, alpha: float = SMOOTH_ALPHA) -> float:
        if key not in self.state_ema:
            self.state_ema[key] = new
        else:
            self.state_ema[key] = alpha * new + (1 - alpha) * self.state_ema[key]
        return self.state_ema[key]

    def update_stats(self):
        try:
            self.update_counter += 1
            # CPU & Memory
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            # GPU
            gpu_percent, gpu_temp_val, vram_tuple = safe_nvml_get()
            vram_pct = 0.0
            if vram_tuple:
                used_v, total_v = vram_tuple
                vram_pct = (used_v/total_v)*100 if total_v else 0
            # Temps
            cpu_temp_val = None
            temps_func = getattr(psutil, 'sensors_temperatures', None)
            if callable(temps_func):
                try:
                    temps_raw = temps_func()
                    if isinstance(temps_raw, dict):
                        # Find first with any reading
                        for sensor_list in temps_raw.values():
                            if sensor_list:
                                cand = getattr(sensor_list[0], 'current', None)
                                if cand is not None:
                                    cpu_temp_val = cand
                                    break
                except Exception:
                    cpu_temp_val = None
            # Network
            net_now = psutil.net_io_counters()
            now = time.time()
            dt = max(0.001, now - self.prev_time)
            down_rate_bytes = (net_now.bytes_recv - self.prev_net.bytes_recv)/dt
            up_rate_bytes = (net_now.bytes_sent - self.prev_net.bytes_sent)/dt
            self.prev_net = net_now
            # Disk IO
            disk_io_now = psutil.disk_io_counters(perdisk=True)
            reads = writes = 0.0
            for name, stats in disk_io_now.items():
                prev = self.prev_disk_io.get(name)
                if prev:
                    reads += max(0, stats.read_bytes - prev.read_bytes)
                    writes += max(0, stats.write_bytes - prev.write_bytes)
            reads_rate = reads/dt
            writes_rate = writes/dt
            self.prev_disk_io = disk_io_now
            self.prev_time = now
            # All disks (no limit)
            self._update_disk_usage()
            self.disk_io_var.set(f"IO: R {format_bytes(self.ema('read_rate', reads_rate))}/s  W {format_bytes(self.ema('write_rate', writes_rate))}/s")
            # Smoothing main gauges
            cpu_s = self.ema('cpu', cpu)
            ram_s = self.ema('ram', mem.percent)
            gpu_s = self.ema('gpu', gpu_percent)
            vram_s = self.ema('vram', vram_pct)
            # Colors
            cpu_col = interpolate_color(CPU_COLOR, RAM_COLOR, DANGER_COLOR, cpu_s/100)
            ram_col = interpolate_color(CPU_COLOR, RAM_COLOR, DANGER_COLOR, ram_s/100)
            gpu_col = interpolate_color(CPU_COLOR, RAM_COLOR, DANGER_COLOR, gpu_s/100)
            vram_col = interpolate_color(VRAM_COLOR, RAM_COLOR, DANGER_COLOR, vram_s/100)
            self.gauge_cpu.set_value(cpu_s, color=cpu_col)
            self.gauge_ram.set_value(ram_s, color=ram_col)
            self.gauge_gpu.set_value(gpu_s, color=gpu_col)
            self.gauge_vram.set_value(vram_s, color=vram_col)
            # Detail texts
            self.mem_detail_var.set(
                f"RAM: {format_bytes(mem.used)} / {format_bytes(mem.total)} (Avail {format_bytes(mem.available)})\n" +
                (f"Swap: {swap.percent:.0f}% ({format_bytes(swap.used)}/{format_bytes(swap.total)})" if swap.total else "Swap: –")
            )
            if vram_tuple:
                used, total = vram_tuple
                self.gpu_detail_var.set(f"VRAM: {format_bytes(used)} / {format_bytes(total)}\nUtil: {gpu_percent:.0f}%")
            else:
                self.gpu_detail_var.set("No GPU data")
            self.cpu_temp_var.set(f"CPU Temp: {cpu_temp_val:.0f}°C" if cpu_temp_val is not None else 'CPU Temp: –')
            self.gpu_temp_var.set(f"GPU Temp: {gpu_temp_val:.0f}°C" if gpu_temp_val is not None else 'GPU Temp: –')
            # Network Mbps (decimal megabits)
            down_mbps = self.ema('down', down_rate_bytes) * 8 / 1_000_000
            up_mbps = self.ema('up', up_rate_bytes) * 8 / 1_000_000
            self.net_down_var.set(f"↓ {down_mbps:.2f} Mb/s")
            self.net_up_var.set(f"↑ {up_mbps:.2f} Mb/s")
            self.uptime_var.set(f"Uptime: {format_time(time.time() - psutil.boot_time())}")
            # Processes summary updated every 5 cycles
            if self.update_counter % 5 == 0:
                try:
                    proc_count = len(psutil.pids())
                    thread_total = 0
                    for p in psutil.process_iter(['num_threads']):
                        try:
                            thread_total += p.info.get('num_threads', 0)
                        except Exception:
                            pass
                    # Shorter text to avoid truncation
                    self.proc_summary_var.set(f"Proc: {proc_count} Thr: {thread_total}")
                except Exception:
                    pass
            # Battery
            try:
                bat = getattr(psutil, 'sensors_battery', lambda: None)()
                if bat:
                    plug = '⚡' if getattr(bat, 'power_plugged', False) else ''
                    secs = getattr(bat, 'secsleft', None)
                    left = ''
                    if secs and secs > 0 and not getattr(bat, 'power_plugged', False):
                        left = f" ({format_time(secs)})"
                    self.battery_var.set(f"Battery: {bat.percent:.0f}%{plug}{left}")
                else:
                    self.battery_var.set("Battery: –")
            except Exception:
                self.battery_var.set("Battery: –")
            now_str = time.strftime('%H:%M:%S')
            self.last_update_var.set(f"Updated {now_str}")
            self.status_var.set('Monitoring')
            self.update_fail_count = 0
        except Exception as e:
            self.update_fail_count += 1
            self.status_var.set(f"Error ({self.update_fail_count}): {e}")
            if self.update_fail_count > 3:
                self.last_update_var.set('Stalled')
        finally:
            self.root.after(UPDATE_MS, self.update_stats)

    def _update_disk_usage(self):
        existing = set(self.disk_usage_rows.keys())
        parts = [p for p in psutil.disk_partitions(all=False) if p.fstype and ('cdrom' not in p.opts.lower())]
        seen = set()
        for p in parts:
            letter = (p.device or p.mountpoint)
            if os.name == 'nt' and len(letter) >= 2 and letter[1] == ':':
                display = letter[:2]
            else:
                display = p.mountpoint
            try:
                usage = psutil.disk_usage(p.mountpoint)
            except Exception:
                continue
            seen.add(display)
            if display not in self.disk_usage_rows:
                row = tk.Frame(self.disk_usage_frame, bg=CARD_BG)
                row.pack(fill='x', pady=2)
                lbl = tk.Label(row, text=display, width=4, anchor='w', fg=MUTED_FG, bg=CARD_BG, font=FONT_TINY)
                lbl.pack(side='left')
                bar = ttk.Progressbar(row, orient='horizontal', mode='determinate', length=120, style='Dark.Horizontal.TProgressbar', maximum=100.0)
                bar.pack(side='left', fill='x', expand=True, padx=4)
                right = tk.Frame(row, bg=CARD_BG)
                right.pack(side='right')
                pct_lbl = tk.Label(right, text='', fg=FG, bg=CARD_BG, font=FONT_TINY, anchor='e')
                pct_lbl.pack(anchor='e')
                size_lbl = tk.Label(right, text='', fg=MUTED_FG, bg=CARD_BG, font=FONT_TINY, anchor='e')
                size_lbl.pack(anchor='e')
                self.disk_usage_rows[display] = (bar, pct_lbl, size_lbl)
            bar, pct_lbl, size_lbl = self.disk_usage_rows[display]  # type: ignore[index]
            bar['value'] = usage.percent
            pct_lbl.configure(text=f"{usage.percent:.0f}%")
            size_lbl.configure(text=f"{format_bytes(usage.used)}/{format_bytes(usage.total)}")
        for k in list(existing - seen):
            widgets = self.disk_usage_rows.pop(k, None)
            if widgets:
                widgets[0].master.destroy()  # type: ignore[index]

    # ---------- Run ---------- #
    def run(self):
        self.root.mainloop()


def main():
    app = ResourceMonitorApp()
    app.run()


if __name__ == '__main__':
    main()





