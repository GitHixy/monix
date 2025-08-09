import os
import sys
import winreg as reg
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

# ---------------- Registry Helpers ---------------- #
APP_NAME = "Monix"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_path() -> str:
    """Return the path to the executable intended for startup.

    When packaged (PyInstaller), sys.argv[0] points to the exe. When running from source,
    prefer sys.executable to ensure pythonw/python path is used with the script.
    We wrap the path in quotes in case there are spaces.
    """
    # If running a frozen build (PyInstaller)
    if getattr(sys, "frozen", False):  # type: ignore[attr-defined]
        path = sys.executable
    else:
        # Use the launching interpreter with the main script
        script = os.path.abspath(sys.argv[0])
        path = f"{sys.executable} \"{script}\""
    return f'"{path}"' if not path.startswith('"') else path


def is_in_startup() -> bool:
    """Check if the application already has a startup entry."""
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, reg.KEY_READ) as run_key:
            value, _ = reg.QueryValueEx(run_key, APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def add_to_startup() -> bool:
    """Create or update the Run key entry for the app.

    Returns True on success, False otherwise.
    """
    exe_path = get_executable_path()
    try:
        # Create the key if it does not exist
        with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, reg.KEY_SET_VALUE) as run_key:
            reg.SetValueEx(run_key, APP_NAME, 0, reg.REG_SZ, exe_path)
        print(f"{APP_NAME} successfully added to startup => {exe_path}")
        return True
    except OSError as e:
        print(f"Error adding to startup: {e}")
        return False


def remove_from_startup() -> bool:
    """Remove the app from startup. Returns True if removed or already absent."""
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, reg.KEY_SET_VALUE) as run_key:  # Need write to delete
            reg.DeleteValue(run_key, APP_NAME)
        print(f"{APP_NAME} removed from startup.")
        return True
    except FileNotFoundError:
        return True
    except OSError as e:
        print(f"Error removing from startup: {e}")
        return False


# ---------------- UI ---------------- #

def ask_startup(parent: Optional[tk.Tk] = None, force: bool = False) -> None:
    """Ask the user whether to add the application to Windows startup.

    Parameters
    ----------
    parent : Optional[tk.Tk]
        Existing root window (to avoid creating multiple Tk instances). If None, a temporary hidden root is created.
    force : bool
        If True, show dialog even if already configured.
    """
    if not force and is_in_startup():
        # Already configured; silent return.
        return

    # Ensure a single root context
    owns_root = False
    if parent is None:
        parent = tk.Tk()
        parent.withdraw()  # Hide if we create it
        owns_root = True

    # Modal top-level dialog
    dialog = tk.Toplevel(parent)
    dialog.title("Monix – Startup Settings")
    dialog.configure(bg="#1E1F22")
    dialog.resizable(False, False)
    dialog.attributes('-topmost', True)

    # Center the dialog
    dialog.update_idletasks()
    w, h = 420, 240
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    x = (screen_w // 2) - (w // 2)
    y = (screen_h // 2) - (h // 2)
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    # Style (modern dark)
    style = ttk.Style(dialog)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Monix.TButton",
                    font=("Segoe UI", 11, "bold"),
                    padding=8)
    style.map("Monix.TButton",
              foreground=[('disabled', '#777'), ('!disabled', 'white')])

    # Header
    header = tk.Label(dialog, text="Start Monix with Windows?", font=("Segoe UI", 15, "bold"),
                      bg="#1E1F22", fg="#FFFFFF")
    header.pack(pady=(18, 6))

    # Body text
    body_text = ("Monix can launch automatically to give you instant access "
                 "to system performance metrics after you sign in.")
    body = tk.Label(dialog, text=body_text, font=("Segoe UI", 11), wraplength=380,
                    justify="center", bg="#1E1F22", fg="#C8C9CC")
    body.pack(pady=(0, 16))

    # Status label (for feedback)
    status_var = tk.StringVar(value="")
    status_lbl = tk.Label(dialog, textvariable=status_var, font=("Segoe UI", 10),
                          bg="#1E1F22", fg="#7FBF7F")
    status_lbl.pack(pady=(0, 8))

    btn_frame = tk.Frame(dialog, bg="#1E1F22")
    btn_frame.pack(pady=4)

    def finalize():
        dialog.destroy()
        if owns_root:
            parent.destroy()

    def on_enable():
        if add_to_startup():
            messagebox.showinfo(APP_NAME, f"{APP_NAME} will start with Windows.")
        else:
            messagebox.showerror(APP_NAME, "Failed to add to startup.")
        finalize()

    def on_disable():
        remove_from_startup()  # Attempt removal (idempotent)
        messagebox.showinfo(APP_NAME, f"{APP_NAME} will not start automatically.")
        finalize()

    enable_btn = ttk.Button(btn_frame, text="Enable", style="Monix.TButton", command=on_enable)
    enable_btn.grid(row=0, column=0, padx=10)

    disable_btn = ttk.Button(btn_frame, text="Not Now", style="Monix.TButton", command=on_disable)
    disable_btn.grid(row=0, column=1, padx=10)

    # Optional: checkbox for 'Don't ask again' could be implemented by storing a config file
    # For now we keep it simple.

    dialog.transient(parent)
    dialog.grab_set()
    parent.wait_window(dialog)


# If this module is run directly, show the prompt (useful for quick manual testing)
if __name__ == "__main__":
    ask_startup(force=True)


