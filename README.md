# Monix

![Monix Icon](monix.ico)

**Monix** is a lightweight, modern always‑on‑top desktop overlay for real‑time monitoring of key system resources.

---

## 📦 Latest Release

Current version: **v1.0.3**  
Download: **[Monix v1.0.3 (EXE)](https://github.com/GitHixy/monix/blob/main/Dist/Monix%20v1.0.3.exe)**

(Older builds remain in `dist/` for reference.)

---

## ✨ What's New in v1.0.3
- Redesigned compact overlay UI (dark modern theme).
- Always-on-top frameless window, now draggable from header.
- Smooth ring gauges for CPU, RAM, GPU, VRAM (anti‑aliased via Pillow).
- GPU + VRAM metrics (persistent NVML handle for reduced overhead).
- Disk card: all drives listed with usage bar, percent, and size on separate lines.
- Network card: download & upload shown separately (Mb/s, smoothed).
- System card: CPU temp, GPU temp, uptime, process/thread summary, battery status.
- Smoother updates with EMA filtering; minimized redraw to reduce stutter.
- Footer height & layout adjustments to prevent text cutoff.
- Gear (⚙) settings button.
- Shorter process/thread summary text to avoid truncation.

---

## 📋 Feature Overview

- CPU, RAM, GPU load, VRAM usage
- Disk usage (all mounted disks)
- Network throughput (↓ / ↑ Mb/s)
- Temperatures (CPU / GPU when available)
- Processes & thread counts (summary)
- Optional Windows startup integration

---

## 🔧 Requirements
- Windows 10 / 11
- NVIDIA GPU (for GPU + VRAM metrics & temperature)
- (Optional) Battery & sensors support for related info

---

## 🚀 Usage
1. Download the latest EXE from the link above.
2. Run `Monix v1.0.3.exe` (no installation required).
3. Drag by the header to position. Use ⚙ for options (startup toggle / quit).
4. Press `Esc` to quit quickly.

Place the EXE somewhere stable if enabling startup.

---

## 🔄 Auto Run at Startup
Use the in‑app settings (⚙ -> Toggle Startup). This adds/removes a registry entry in `HKCU:Software\Microsoft\Windows\CurrentVersion\Run`.

---

## 🛡️ Windows Defender False Positives
Because Monix can register itself for startup, some AV engines may flag it. If needed, add the EXE to Windows Security exclusions:
1. Windows Security → Virus & Threat Protection
2. Manage Settings → Exclusions → Add or Remove
3. Add an Exclusion → File → select the Monix EXE.

---

## ❓ FAQ
Q: Why is GPU data blank?  
A: Ensure you have an NVIDIA GPU + latest drivers. NVML is required.

Q: Does it support per‑core CPU?  
A: Removed intentionally for a cleaner, lighter UI.

Q: Can I resize the window?  
A: Not in this version; size is optimized for readability & compactness.

---

## 🗺️ Roadmap Ideas
- Optional minimal mode
- Custom refresh interval
- Theme customization

---

## 📜 License
MIT (see repository for details).

---

**Always run the latest version to get fixes and improvements.**



