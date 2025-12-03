# System Architecture

**Component Status:** 📋 Design Phase  
**Target Platforms:** 1. **Core:** Radxa Dragon Q6A (Qualcomm QCS6490)  
2. **Pro:** Radxa Rock 5B+ (Rockchip RK3588)  

---

## Overview

The Whetstone architecture is bifurcated to serve two distinct roles: the efficient, always-on **Core** and the powerful, flexible **Pro**. While they share a philosophical DNA (Personas, Privacy), their technical stacks differ significantly to optimize for their respective hardware.

---

## Architecture 1: Whetstone Core (Dragon Q6A)

**Design Goal:** Extreme efficiency, instant latency, "Appliance" reliability.
```
┌─────────────────────────────────────────────────────────────────┐ │ WHETSTONE CORE (Q6A) │ │ │ │ ┌──────────────────────┐ ┌───────────────────────────────┐ │ │ │ Whetstone OS │ │ Hexagon NPU │ │ │ │ (Read-Only Root) │ │ │ │ │ │ │ │ ┌─────────────────────────┐ │ │ │ │ [App Service] │────┼─►│ Qwen 3 8B (w4a16) │ │ │ │ │ - Persona Loader │ │ │ [Context Binary .bin] │ │ │ │ │ - Voice VAD │ │ └─────────────────────────┘ │ │ │ │ │ │ │ │ │ └──────────┬───────────┘ │ ┌─────────────────────────┐ │ │ │ │ └─►│ Whisper (Qualcomm Opt) │ │ │ │ ▼ └─────────────────────────┘ │ │ │ ┌──────────────────────┐ │ │ │ │ Security Subsys │ │ │ │ │ │ │ │ │ │ [Dead Man Switch] │◄────── [Maintenance Button] │ │ │ │ - rfkill unblock │ │ │ │ │ - Verify Signature │◄...... [Wi-Fi (No Antenna)] │ │ │ └──────────────────────┘ │ │ └─────────────────────────────────────────────────────────────────┘
```

### Key Components (Core)

#### 1. The Inference Engine (QNN)
* **Model:** **Qwen 3 8B** (Dense).
* **Format:** `.bin` (Qualcomm Neural Network Context Binary).
* **Optimization:** 4-bit Integer (INT4) weights fitting within 8GB RAM.

#### 2. The Voice Stack (Qualcomm)
* **STT:** **Whisper**. Optimized using the Qualcomm AI Stack to run on the Hexagon DSP, ensuring low-power always-on listening.
* **TTS:** **Piper**. Lightweight and fast, running on the CPU/DSP hybrid.

#### 3. Dynamic Persona Injection
* On boot, the system mounts the `philosophy_library` partition (Read-Only).
* It scans filenames (e.g., `nietzsche_Twilight.txt`) to build the RAG index in memory.
* **User Action:** To add a persona, the user boots into Maintenance Mode and copies a `.txt` file to the library partition. The system handles the rest.

---

## Architecture 2: Whetstone Pro (Rock 5B+)

**Design Goal:** Flexibility, deep archival, research.
```
┌─────────────────────────────────────────────────────────────────┐ │ WHETSTONE PRO (Rock 5) │ │ │ │ ┌──────────────────────┐ ┌───────────────────────────────┐ │ │ │ Orchestrator │ │ Ollama Runtime │ │ │ │ (Python) │ │ │ │ │ │ │ │ ┌─────────────────────────┐ │ │ │ │ - Persona Auto-Gen │───►│ Qwen 3 14B / 32B │ │ │ │ │ - RAG Controller │ │ (GGUF Format) │ │ │ │ │ - Web Interface │ │ │ │ │ │ └──────────┬───────────┘ └───────────────────────────────┘ │ │ │ │ │ ▼ │ │ ┌──────────────────────┐ ┌───────────────────────────────┐ │ │ │ Vector DB │ │ Voice Pipeline (NPU) │ │ │ │ (ChromaDB) │ │ │ │ │ │ │ │ [SenseVoiceSmallRKNN] -> STT │ │ │ │ - Journal Entries │ │ [Paroli] -> TTS │ │ │ │ - Philosophy Texts │ │ │ │ │ └──────────────────────┘ └───────────────────────────────┘ │ └─────────────────────────────────────────────────────────────────┘
```

### Key Components (Pro)

#### 1. Dynamic Inference (Ollama)
* Runs **Qwen 3 14B** or **32B** depending on user configuration.
* Leverages 24GB RAM for massive context windows.

#### 2. The Voice Stack (Rockchip NPU)
* **STT:** **SenseVoiceSmallRKNN**. A highly optimized port of SenseVoice that runs on the Rockchip RK3588 NPU, delivering ~20x real-time performance.
* **TTS:** **Paroli**. A port of Piper TTS accelerated for the RK3588 NPU, enabling near-instant speech generation even for long philosophical monologues.

#### 3. The Persona Forge (Dynamic)
* **Watcher Service:** Monitors `philosophy_library/` for changes.
* **Auto-Ingest:** When a new file is detected (e.g., `marcus_Meditations.txt`):
    1.  The text is chunked and embedded into ChromaDB.
    2.  A new entry is added to `personas.json`.
    3.  The Persona becomes immediately selectable via Voice or UI.

---

## The Forge (Build System)

Since the **Core** device cannot compile its own models (requires x86_64 host), we introduce **The Forge**.

* **Hardware:** High-performance PC (e.g., AMD Strix Halo).
* **Pipeline:**
    1.  **Teacher:** Qwen 3 72B generates synthetic philosophical data.
    2.  **Student:** Qwen 3 8B is fine-tuned on this data.
    3.  **Compiler:** Qualcomm QNN SDK converts the fine-tuned model into `qwen_ctx.bin`.
    4.  **Packager:** The binary is wrapped into a signed OTA update file.

---

## Shared Interfaces

### Button Interface
Both devices utilize a similar GPIO button schema for navigation.
* **See:** `BUTTON_INTERFACE.md`