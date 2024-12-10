import os
import sys
import winreg as reg
import tkinter as tk
from tkinter import messagebox

def add_to_startup():
    """
    Adds Monix to the Windows startup programs by creating a registry entry.
    """
    exe_path = os.path.abspath(sys.argv[0])  # Path of the .exe or script
    if exe_path.endswith(".py"):
        exe_path = exe_path.replace(".py", ".exe")  # Ensure it's the .exe version

    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "Monix"

    try:
        # Open the registry key for editing
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        # Set the registry value for startup
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, exe_path)
        reg.CloseKey(reg_key)
        print(f"{app_name} successfully added to startup.")
    except Exception as e:
        print(f"Error adding to startup: {e}")



def ask_startup():
    """
    Asks the user if they want Monix to start automatically with Windows.
    """
    def on_yes():
        add_to_startup()
        messagebox.showinfo("Monix", "Monix has been added to startup.")
        root.destroy()

    def on_no():
        messagebox.showinfo("Monix", "Monix will not start automatically.")
        root.destroy()

    # Create a simple dialog
    root = tk.Tk()
    root.title("Monix - Startup Settings")
    root.geometry("400x250")
    root.configure(bg="#2C2F33")
    root.resizable(False, False)

    # Message
    label = tk.Label(root, text="Start Monix automatically at Windows startup?", 
                     font=("Segoe UI", 12), bg="#2C2F33", fg="white")
    label.pack(pady=(20, 10))

    # Buttons
    yes_button = tk.Button(root, text="Yes", font=("Segoe UI", 10, "bold"), bg="#4CAF50", fg="white",
                           command=on_yes, width=10)
    yes_button.pack(side="left", padx=(40, 10), pady=(20, 10))

    no_button = tk.Button(root, text="No", font=("Segoe UI", 10, "bold"), bg="#FF5555", fg="white",
                          command=on_no, width=10)
    no_button.pack(side="right", padx=(10, 40), pady=(20, 10))

    root.mainloop()

