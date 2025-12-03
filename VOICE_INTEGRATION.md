# Voice Integration Specification

**Component Status:** 📋 Specification Phase  
**Target Platforms:** 1. **Core:** Radxa Dragon Q6A (Qualcomm QCS6490)  
2. **Pro:** Radxa Rock 5B+ (Rockchip RK3588)  

**Purpose:** Low-latency, privacy-first voice interaction optimized for specific NPU architectures.

---

## Overview

The Whetstone's voice interface is not a generic "Linux audio" setup. To achieve acceptable latency (<2s) on embedded hardware, we utilize distinct NPU (Neural Processing Unit) acceleration stacks for each device tier.

### The Two Stacks

| Feature | **Core Stack** (Dragon Q6A) | **Pro Stack** (Rock 5B+) |
| :--- | :--- | :--- |
| **NPU Arch** | **Qualcomm Hexagon DSP** (12 TOPS) | **Rockchip RKNN** (6 TOPS) |
| **STT Model** | **Whisper** (Qualcomm Optimized) | **SenseVoiceSmall** (RKNN Port) |
| **TTS Model** | **Piper** (QNN / ONNX Runtime) | **Paroli** (Piper for RK3588) |
| **Latency** | Extremely Low (DSP-native) | Low (NPU-accelerated) |
| **Wake Word** | "Always-on" capable (Low Power) | Push-to-Talk (Primary) |

---

## Architecture 1: The Core Stack (Dragon Q6A)

**Hardware:** Qualcomm QCS6490  
**Focus:** Efficiency, low-power state, "Always-on" readiness.

### 1. STT: Whisper (Qualcomm AI Engine)
Instead of running Whisper.cpp on the CPU, we utilize the **Qualcomm AI Hub** optimization of OpenAI's Whisper. This runs the encoder directly on the **Hexagon DSP**, freeing up the CPU for the main application logic.

* **Model:** `whisper-tiny-en` or `whisper-base-en` (Quantized to INT8).
* **Optimization:** The model is compiled using the **QNN SDK** into a context binary (`.bin`) that loads instantly into the shared memory heap.
* **VAD (Voice Activity Detection):** Utilizes the dedicated **Low Power Audio Subsystem (LPASS)** on the Snapdragon chip to wake the main cores only when human speech is detected.

### 2. TTS: Piper (Hexagon Optimized)
Piper is chosen for its lightweight VITS architecture.
* **Execution Provider:** We run Piper via **ONNX Runtime** with the **QNN Execution Provider** enabled.
* **Voices:** Custom "Philosopher" voices (e.g., deep, resonant, slow-paced) trained and quantized to INT8.

---

## Architecture 2: The Pro Stack (Rock 5B+)

**Hardware:** Rockchip RK3588  
**Focus:** High throughput, "Vision-like" processing speed.

### 1. STT: SenseVoiceSmallRKNN
The Rockchip NPU is architecturally similar to a vision processor. **SenseVoice** (by FunAudioLLM) treats audio spectrograms almost like images, making it significantly faster on this specific NPU than Whisper.

* **Repository:** `SenseVoiceSmallRKNN` (Community Port).
* **Performance:** Can transcribe 10 seconds of audio in <0.2 seconds (50x real-time).
* **Implementation:**
    ```python
    from rknn.api import RKNN
    # Loads the .rknn compiled model directly to the NPU
    rknn.load_rknn('sensevoice_small_int8.rknn')
    ```

### 2. TTS: Paroli (Piper for Rockchip)
**Paroli** is a specialized fork of Piper designed to utilize the RK3588's NPU for the heavy matrix multiplications involved in speech synthesis.

* **Repository:** `marty1885/paroli`
* **Key Advantage:** While standard Piper runs well on CPU, Paroli offloads the generation to the NPU, preventing audio "stuttering" if the CPU is busy processing a massive Qwen 3 32B thought chain.

---

## Shared Workflow (The "Loop")

Despite the different engines, the Python application loop remains consistent for both devices:

```python
def voice_loop():
    # 1. Wait for Trigger (GPIO Button or LPASS Wake)
    wait_for_trigger()
    
    # 2. Record (PyAudio)
    audio_frames = record_audio_buffer()
    
    # 3. Transcribe (Hardware Specific)
    if HW_TYPE == "CORE":
        text = qnn_whisper.transcribe(audio_frames)
    elif HW_TYPE == "PRO":
        text = rknn_sensevoice.transcribe(audio_frames)
        
    # 4. Thinking (LLM)
    llm_response = philosopher_engine.query(text)
    
    # 5. Synthesis (Hardware Specific)
    if HW_TYPE == "CORE":
        audio_out = qnn_piper.synthesize(llm_response)
    elif HW_TYPE == "PRO":
        audio_out = paroli.synthesize(llm_response)
        
    # 6. Playback
    play_audio(audio_out)
```

---

## Audio Hardware Setup

### Microphone

**Recommended:** USB Omnidirectional Conference Mic (e.g., Anker PowerConf S330 or generic alternative).

**Why:** We need 360-degree pickup since the Whetstone sits in the center of a table.

**Sample Rate:** All models are standardized to 16kHz Mono.

### Speaker

**Interface:** USB or 3.5mm Aux.

**Requirement:** Must be shielded to prevent GSM buzz (crucial for the Core device which relies on close-proximity "antenna-less" updates).

---

## UX Patterns & Feedback

Since the Core device has no screen, audio cues are critical.

| State | Audio Cue | LED State (Core) |
|-------|-----------|------------------|
| Listening | Soft "Click" (Analog feel) | Solid Amber |
| Thinking | Silence | Pulsing White |
| Speaking | Voice Output | Solid Green |
| Error | Low-tone "Thud" | Flash Red |

---

## Latency Targets

| Metric | Core Target (Q6A) | Pro Target (Rock 5B) |
|--------|-------------------|----------------------|
| Wake to Listen | < 100ms | < 300ms |
| STT Processing | < 1s (Whisper Tiny) | < 0.5s (SenseVoice) |
| TTS Generation | Real-time (Streaming) | Real-time (Streaming) |

---

## Development Roadmap

### Phase 1: Pro Stack Verification

- [ ] Build paroli on Rock 5B+ Armbian.
- [ ] Benchmark SenseVoiceSmallRKNN against standard Whisper.cpp (CPU).

### Phase 2: Core Stack Pipeline

- [ ] Setup "The Forge" (Host PC) to compile QNN context binaries for Whisper.
- [ ] Implement VAD using the QCS6490 LPASS hardware (requires specific kernel drivers).

### Phase 3: Voice Training

- [ ] Train a custom "Socratic" voice for Piper/Paroli (Goal: Calming, authoritative, non-robotic).
- [ ] Dataset: Public domain philosophy audiobooks (LibriVox).
