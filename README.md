# Monix

![Monix Icon](monix.ico)

**Monix** is a lightweight and modern application for real-time monitoring of system resources. Perfect for a clean and functional overlay of CPU, RAM, GPU, and network usage.

---

## 📋 Features

- **Real-time monitoring**:
  - **CPU**: Usage and temperature.
  - **RAM**: Usage percentage.
  - **GPU**: Load and temperature (NVIDIA GPUs supported).
  - **Network**: Download and upload speeds.
    
- **Minimal interface**: Simple, modern, and clean overlay.
- **Draggable overlay**: Place Monix anywhere on your screen.
- **Ready to use**: No installation required, just run the `exe`.
- **AutoRun**: Enable to let it run at Windows startup (from v1.0.1).

---

## 🔧 Requirements

- **Windows 10/11**
- NVIDIA GPU (for GPU monitoring and temperature)

---

## 🚀 Installation and Usage

1. **Download the latest version of Monix**:  
   👉 **[Download Monix here](https://github.com/GitHixy/monix/blob/main/dist)** 👈
   
2. Run the **Monix.exe** file.


---

**Always run the latest version to get all fixes ad updates**

## 🛡️ Adding Monix to Windows Defender Exclusions

If Windows Defender flags Monix as a potential threat, you can add it to the exclusions list to prevent it from being mistakenly removed.
This is caused because Monix can create a key in your registry that will allow the app to run on Windows Startup and that is a common case of false positive.

### Steps to Add Monix to Windows Defender Exclusions:

1. Open **Windows Security**:
   - Press `Win + S` and search for **Windows Security**.
   - Click on **Virus & Threat Protection**.

2. Scroll down to **Virus & Threat Protection Settings** and click **Manage Settings**.

3. Scroll to the bottom and click **Add or Remove Exclusions** under **Exclusions**.

4. Click **Add an Exclusion** and choose **File**.

5. Browse to the location of the Monix executable:
   - For example: `C:\Path\To\Monix.exe`.

6. Select the file and confirm.

Monix should now run without being flagged or removed by Windows Defender. If you encounter any issues, please let us know!



