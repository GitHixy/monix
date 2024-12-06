import psutil
import GPUtil
import tkinter as tk
from tkinter import ttk
import threading
import time


def update_stats_thread():
    prev_net = psutil.net_io_counters()
    while True:
        # CPU and RAM usage
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_percent = psutil.virtual_memory().percent

        # CPU Temperature
        cpu_temp = None
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                cpu_temp = temps["coretemp"][0].current

        # Network usage
        net = psutil.net_io_counters()
        download_speed = (net.bytes_recv - prev_net.bytes_recv) / 1024  
        upload_speed = (net.bytes_sent - prev_net.bytes_sent) / 1024  
        prev_net = net

        # GPU usage and temperature
        gpus = GPUtil.getGPUs()
        gpu_percent = gpus[0].load * 100 if gpus else 0
        gpu_temp = gpus[0].temperature if gpus else None

        # Update the GUI using the `update_gui` function
        root.after(0, update_gui, cpu_percent, ram_percent, cpu_temp, gpu_percent, gpu_temp, download_speed, upload_speed)

        # Pause the thread for 1 second
        time.sleep(1)


def update_gui(cpu, ram, cpu_temp, gpu, gpu_temp, download, upload):
    # Update CPU
    cpu_label.config(text=f"CPU: {cpu}%")
    cpu_bar['value'] = cpu

    # Update RAM
    ram_label.config(text=f"RAM: {ram}%")
    ram_bar['value'] = ram

    # Update CPU Temperature
    if cpu_temp:
        cpu_temp_label.config(text=f"CPU Temp: {cpu_temp:.1f}°C")
        cpu_temp_label.pack(pady=(0, 10))  
    else:
        cpu_temp_label.pack_forget()  

    # Update GPU
    if gpu > 0:
        gpu_label.config(text=f"GPU: {gpu:.2f}%")
        gpu_bar['value'] = gpu
    else:
        gpu_label.config(text="GPU: No GPU")
        gpu_bar['value'] = 0

    # Update GPU Temperature
    if gpu_temp:
        gpu_temp_label.config(text=f"GPU Temp: {gpu_temp:.1f}°C")
        gpu_temp_label.pack(pady=(0, 10)) 
    else:
        gpu_temp_label.pack_forget()  

    # Update Network
    net_label.config(text=f"Net: ↓ {download:.2f} KB/s ↑ {upload:.2f} KB/s")


def close_app():
    root.destroy()


def start_move(event):
    root.x = event.x
    root.y = event.y


def stop_move(event):
    root.x = None
    root.y = None


def do_move(event):
    x = root.winfo_pointerx() - root.x
    y = root.winfo_pointery() - root.y
    root.geometry(f"+{x}+{y}")


# Create the main window
root = tk.Tk()
root.title("Monix - Resource Monitor")
root.geometry("400x450")
root.configure(bg="#2C2F33")  

# Remove window decorations for overlay style
root.overrideredirect(True)
root.wm_attributes('-topmost', True) 
root.wm_attributes('-transparentcolor', '#2C2F33') 

# Font and Style
font_large = ("Segoe UI", 16, "bold")
font_small = ("Segoe UI", 12)

style = ttk.Style()
style.theme_use("clam")
style.configure("TProgressbar", thickness=10, troughcolor="#23272A", background="#7289DA")

# Close Button
close_button = tk.Button(root, text="X", font=("Segoe UI", 12, "bold"), bg="#FF5555", fg="white",
                         borderwidth=0, command=close_app)
close_button.place(x=370, y=10, width=20, height=20)

# Make the overlay draggable
root.bind("<Button-1>", start_move)
root.bind("<ButtonRelease-1>", stop_move)
root.bind("<B1-Motion>", do_move)

# CPU Section
cpu_label = tk.Label(root, text="CPU: Calculating...", font=font_large, bg="#2C2F33", fg="white")
cpu_label.pack(pady=(20, 5))

cpu_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
cpu_bar.pack(pady=(0, 10))

cpu_temp_label = tk.Label(root, text="CPU Temp: Calculating...", font=font_small, bg="#2C2F33", fg="white")
cpu_temp_label.pack(pady=(0, 10))

# RAM Section
ram_label = tk.Label(root, text="RAM: Calculating...", font=font_large, bg="#2C2F33", fg="white")
ram_label.pack(pady=(0, 5))

ram_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
ram_bar.pack(pady=(0, 10))

# GPU Section
gpu_label = tk.Label(root, text="GPU: Calculating...", font=font_large, bg="#2C2F33", fg="white")
gpu_label.pack(pady=(0, 5))

gpu_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
gpu_bar.pack(pady=(0, 10))

gpu_temp_label = tk.Label(root, text="GPU Temp: Calculating...", font=font_small, bg="#2C2F33", fg="white")
gpu_temp_label.pack(pady=(0, 10))

# Network Section
net_label = tk.Label(root, text="Network: Calculating...", font=font_large, bg="#2C2F33", fg="white")
net_label.pack(pady=(0, 10))

# Start the stats update thread
thread = threading.Thread(target=update_stats_thread, daemon=True)
thread.start()

# Run the app
root.mainloop()





