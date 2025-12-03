# The Whetstone - Hardware Setup Guide

**Assembly and configuration for Core and Pro editions.**

---

## 1. Select Your Edition

| Feature | **Core Edition** | **Pro Edition** |
| :--- | :--- | :--- |
| **Primary Use** | Daily Companion, "Socratic Alarm Clock" | Private Archive, Research Server |
| **Complexity** | Low (Pre-built Image) | Medium (Linux Setup) |
| **Cost** | ~$130 | ~$280 |
| **AI Model** | **Qwen 3 8B** (Static Context Binary) | **Qwen 3 14B / 32B** (Dynamic) |

---

## 2. Bill of Materials (Core Edition)

### Essential Components
| Component | Specification | Notes |
|-----------|---------------|-------|
| **SBC** | **Radxa Dragon Q6A** (8GB RAM) | **Critical:** 8GB is the minimum to run Qwen 3 8B (Q4). |
| **Storage** | 64GB+ NVMe SSD (M.2 2230) | Faster than eMMC, required for fast wake & NPU paging. |
| **Power** | USB-C PD Adapter (30W+) | Official Radxa supply recommended. |
| **Microphone** | USB Omnidirectional Mic | Compact, driverless. |
| **Speaker** | USB or 3.5mm Speaker | Small 3W driver. |
| **Button** | 1x Momentary Push Button | For "Maintenance Mode" (Dead Man Switch). |

### The "Antenna Hack" (Security)
* **Instruction:** Do **NOT** install the external IPEX Wi-Fi antennas included with the Dragon Q6A.
* **Result:** This limits Wi-Fi range to ~5-10cm, creating a physical security layer for the update process.

---

## 3. Bill of Materials (Pro Edition)

### Essential Components
| Component | Specification | Notes |
|-----------|---------------|-------|
| **SBC** | **Radxa Rock 5B+** (24GB RAM) | 24GB required for Qwen 3 14B/32B + Vector DB. |
| **Storage** | 1TB NVMe SSD (M.2 2280) | Capacity for long-term journal storage. |
| **Cooling** | Active Fan/Heatsink | Mandatory for continuous 14B+ model inference. |
| **Display** | E-Ink Display (Waveshare) | For "Passive Provocation" messages. |
| **Audio** | USB Mic + Speaker | Same as Core. |

---

## 4. Assembly & Setup

### Core Edition (Firmware Flash)
1.  Download the **WhetstoneOS Core** image (built via The Forge).
2.  Flash to NVMe SSD using a USB-to-NVMe adapter and BalenaEtcher.
3.  Install SSD into Dragon Q6A.
4.  Connect Button to GPIO Pins (See `BUTTON_INTERFACE.md`).
5.  Power on. The Green LED should pulse, indicating the NPU has loaded the Qwen 3 context binary.

### Pro Edition (Manual Setup)
1.  Install **Armbian 24.04** (CLI version) to NVMe.
2.  Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
3.  Pull the model: `ollama pull qwen3:14b`
4.  **Install Voice Stack:**
    * `git clone https://github.com/marty1885/paroli` (Paroli TTS)
    * Clone `SenseVoiceSmallRKNN` repository.
5.  Clone the Whetstone repo and run the installer script.

---

## 5. Adding Personas (Dynamic)

**The Filesystem is the UI.** You do not need to code to add new philosophers.

1.  Obtain a plain text file (`.txt`) of the philosopher's work (e.g., from Project Gutenberg).
2.  Rename it using the format: `Author_Title.txt` (e.g., `MarcusAurelius_Meditations.txt`).
3.  **Transfer:**
    * **Core:** Connect via USB in Maintenance Mode and drop file into `philosophy_library`.
    * **Pro:** `scp` the file to `~/The-Whetstone/philosophy_library/`.
4.  **Restart/Reload:** The system will automatically parse the file, generate the Persona definition, and index the text for RAG.