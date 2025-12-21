# The Whetstone

**Act II of The Authentic Rebellion Framework**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

> "Cognitive Strengthening - Learning to think again"

## Overview

The Whetstone is a **physical AI device** that acts as a Socratic interlocutor—challenging assumptions, exposing contradictions, and helping you reason toward clarity about your beliefs and values. Unlike apps or cloud services, The Whetstone is a tangible object that creates intentional space for philosophical dialogue.

**Status:** 🔨 Hardware In-Development (Radxa Dragon Q6A "Core" & Rock 5B+ "Pro")

**Core Philosophy:** Privacy-first cognitive strengthening through local AI inference. Your conversations never leave your home. Your thinking process is sovereign.

---

## The Two Paths: Core & Pro

To democratize cognitive sovereignty, The Whetstone is available in two hardware tiers:

### 1. The Whetstone Core (The Companion)

* **Role:** The "Socratic Alarm Clock." A dedicated, always-on philosophical companion.
* **Hardware:** **Radxa Dragon Q6A** (Qualcomm QCS6490).
* **AI Model:** **Qwen 3 8B** (Quantized w4a16 & NPU-Accelerated).
* **Voice Stack:** **Whisper** (Qualcomm Optimized) + **Piper** (TTS).
* **Key Feature:** Leverages Qwen 3's **"Thinking Mode"** to perform deep logical step-by-step reasoning on complex ethical questions before speaking.
* **Vibe:** "Passive Provocation." It waits for you to engage or subtly signals via LED when it has a thought.

### 2. The Whetstone Pro (The Oracle)

* **Role:** The Archive & Research Station. A heavy-duty private server for deep RAG and journal analysis.
* **Hardware:** **Radxa Rock 5B+** (24GB RAM).
* **AI Model:** **Qwen 3 14B / 32B** (Full Precision).
* **Voice Stack:** **SenseVoiceSmallRKNN** (STT) + **Paroli** (TTS).
    * *Why?* Uses the Rockchip NPU's specific architecture to run voice transcription at 20x real-time speed.
* **Capabilities:** Massive context windows, deep archival search, voice cloning training.

---

## Feature Highlight: Dynamic Personas (Filesystem as UI)

The Whetstone does not rely on hard-coded personalities. **The AI becomes what it reads.**

* **How it works:** The system dynamically scans the `philosophy_library/` folder on boot.
* **How to add a Philosopher:**
    1.  Find a `.txt` file of a book (e.g., `watts_The Way of Zen.txt`).
    2.  Copy it to the device via USB or the Bridge App.
    3.  **Done.** The Whetstone automatically generates an "Alan Watts" persona, indexes the text for RAG, and adopts his rhetorical style.
* **No Code Required:** If you can copy a file, you can expand the AI's mind.

---

## Hardware Specifications

### Core Kit (Radxa Dragon Q6A)

-   **SoC:** Qualcomm QCS6490 (8-core Kryo CPU + **12 TOPS Hexagon NPU**)
-   **RAM:** 8GB LPDDR5 (Required for Qwen 3 8B @ 4-bit)
-   **Storage:** 64GB eMMC or NVMe
-   **Key Feature:** NPU-optimized inference allows for instant wake and low-power "always-on" listening.
-   **Est. Cost:** ~$130 (Board + Case + Mic)

### Pro Kit (Radxa Rock 5B+)

-   **SoC:** Rockchip RK3588 (8-core ARM + 6 TOPS NPU)
-   **RAM:** 24GB LPDDR4x
-   **Storage:** 1TB NVMe SSD (for massive RAG databases)
-   **Key Feature:** Brute-force RAM capacity for running large 14B+ models.
-   **Est. Cost:** ~$280 (Board + Case + Peripherals)

---

## The "Dead Man's Switch" (Security)

The Whetstone Core implements a **Functional Air Gap**:

1.  **Hardware:** The device has **no installed Wi-Fi antennas**. Range is limited to ~10cm.
2.  **Software:** The radio is hard-blocked (`rfkill block all`) at boot.
3.  **The Ritual:** To update the device:
    * Hold the physical **Maintenance Button** for 3 seconds.
    * Place your phone (running the Whetstone Bridge App) directly on top of the device.
    * The device wakes the radio for 5 minutes, handshakes via a cryptographic key, pulls the signed update, and immediately reboots back to silence.

---

## Deployment Guide

### For Whetstone Core (Dragon Q6A)

*We provide a pre-built OS image. No manual software installation required.*

1.  Download the latest `WhetstoneOS_Core_vX.img`.
2.  Flash to SD Card or NVMe using BalenaEtcher.
3.  Boot. The device is immediately active.

### For Whetstone Pro (Rock 5B+)

1.  Install Armbian or Ubuntu 22.04.
2.  Run the setup script:

    ```bash
    curl -fsSL [https://raw.githubusercontent.com/yargnad/The-Whetstone/main/install_pro.sh](https://raw.githubusercontent.com/yargnad/The-Whetstone/main/install_pro.sh) | sh
    ```

3.  Access the web interface at `http://whetstone.local:8080` to configure personas.

---

## License

**GNU General Public License v3.0**

The Whetstone hardware designs and software are GPL v3.0 licensed. This ensures the tool for cognitive sovereignty remains ungovernable and forkable.

---

> **"The Whetstone doesn't give you answers. It sharpens your capacity to find them yourself."**