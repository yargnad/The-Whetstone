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
* **Runtime:** On boot, the system mounts the `curated_library` partition (Read-Only exploded cache).
* **Ingestion:** To add a persona, the user copies a `.codex` (or raw text) file to the `ingest_tray/`.
* **Process:** The system validates, updates the CODEX store, and "explodes" the clean data to the `curated_library` for the runtime to see.

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

* **Dual Watcher:**
    1.  `codex_library/`: For portable archives (Interchange).
    2.  `raw/`: For loose text files (Quick Drop).
* **The "Auto-Packer" Loop**:
    -   **Event**: New file in `raw/` (e.g., `zen.txt`).
    -   **Action**: System wraps `zen.txt` into `Zen.codex`.
    -   **Side Effect**: This change to `codex_library/` triggers the **Auto-Explosion**.
* **Auto-Explosion**:
    1.  The CODEX is unpaxed to `curated_library/`.
    2.  The RAG indexer (ChromaDB) consumes the *curated* files only.
    3.  The Persona becomes immediately selectable.

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