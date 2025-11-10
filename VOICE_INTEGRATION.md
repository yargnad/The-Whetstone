# Voice Integration Specification

**Component Status:** 📋 Specification Phase  
**Target Hardware:** Radxa Rock 5B+ with NPU (Rockchip RK3588)  
**Purpose:** Integrate Whisper STT and Piper TTS for voice-based philosophical dialogue

---

## Overview

The Whetstone's voice interface transforms spoken questions into text (Speech-to-Text) and AI responses into spoken audio (Text-to-Speech), enabling hands-free philosophical dialogue.

**Key Challenge:** Maintain low latency and privacy while running entirely on-device.

**Solution:** Leverage Radxa Rock 5B+'s NPU (Neural Processing Unit) for hardware-accelerated inference.

---

## Voice Workflow

```
┌─────────────┐
│ User presses│
│ PTT button  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Record audio│
│ from mic    │ ─── USB microphone
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Whisper STT │
│ (NPU-accel) │ ─── SenseVoice or Whisper.cpp on RK3588 NPU
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Text query  │
│ → Ollama    │ ─── Mistral 7B inference (existing)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AI response │
│ (text)      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Piper TTS   │
│ (NPU-accel) │ ─── Piper with RK3588 optimization
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Play audio  │
│ on speaker  │ ─── USB speaker or 3.5mm audio
└─────────────┘
```

---

## Speech-to-Text (STT)

### Option 1: SenseVoice (Recommended for NPU)

**What is SenseVoice?**
- Open-source multilingual STT model by FunAudioLLM
- Optimized for Rockchip NPU via RKNN2 runtime
- Fast inference (~real-time on RK3588)
- Good accuracy for English

**Model:** `SenseVoiceSmall` (RKNN2-optimized version)

**Installation:**
```bash
# Install RKNN2 runtime for Rockchip NPU
sudo apt-get install rockchip-rknn2

# Clone SenseVoice RKNN2 repo
git clone https://github.com/airockchip/rknn-toolkit2.git
cd rknn-toolkit2/rknn-toolkit2/examples/SenseVoice

# Download pre-converted RKNN model
wget https://example.com/sensevoice_small_rknn2.rknn  # (URL to be confirmed)

# Install Python dependencies
pip3 install rknn-toolkit2-lite
```

**Usage:**
```python
from rknn.api import RKNN

class SenseVoiceSTT:
    def __init__(self, model_path="sensevoice_small.rknn"):
        self.rknn = RKNN()
        self.rknn.load_rknn(model_path)
        self.rknn.init_runtime()
    
    def transcribe(self, audio_file):
        """
        Transcribe audio file to text using NPU acceleration
        audio_file: path to .wav file (16kHz, mono)
        """
        # Load audio
        audio_data = self.load_audio(audio_file)
        
        # Run inference on NPU
        output = self.rknn.inference(inputs=[audio_data])
        
        # Decode output to text
        text = self.decode_output(output)
        return text
    
    def load_audio(self, audio_file):
        # Load and preprocess audio to format expected by model
        # (Implementation details depend on SenseVoice requirements)
        pass
    
    def decode_output(self, output):
        # Convert model output tensor to text
        # (Implementation details depend on SenseVoice output format)
        pass
```

**Pros:**
- NPU-accelerated (very fast)
- Low power consumption
- Good for short-form queries (typical Whetstone use case)

**Cons:**
- Less mature than Whisper (fewer community resources)
- May require manual RKNN conversion if pre-converted model unavailable
- Documentation sparse

---

### Option 2: Whisper.cpp (CPU, Fallback)

**What is Whisper.cpp?**
- OpenAI's Whisper model ported to C++ for efficient CPU inference
- Highly accurate, multilingual STT
- No NPU support (runs on CPU)

**Model:** `whisper.cpp base` or `small` (quantized)

**Installation:**
```bash
# Clone whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp

# Build for ARM64
make

# Download model (base.en for English-only, faster)
bash ./models/download-ggml-model.sh base.en
```

**Usage:**
```python
import subprocess

class WhisperSTT:
    def __init__(self, model_path="models/ggml-base.en.bin"):
        self.model_path = model_path
        self.whisper_bin = "./whisper.cpp/main"
    
    def transcribe(self, audio_file):
        """
        Transcribe audio file using whisper.cpp
        audio_file: path to .wav file (16kHz, mono)
        """
        result = subprocess.run(
            [self.whisper_bin, "-m", self.model_path, "-f", audio_file, "-nt"],
            capture_output=True,
            text=True
        )
        
        # Parse output (whisper.cpp prints transcription to stdout)
        transcription = result.stdout.strip()
        return transcription
```

**Pros:**
- Proven accuracy (OpenAI Whisper)
- Well-documented
- Actively maintained

**Cons:**
- CPU-only (slower than NPU, higher power)
- Latency: ~2-5 seconds for 5-second audio on RK3588
- Not ideal for real-time use

---

### STT Performance Comparison

| Model | Hardware | Latency (5s audio) | Accuracy | Power |
|-------|----------|-------------------|----------|-------|
| **SenseVoice (RKNN2)** | NPU | ~1-2s | Good | Low |
| **Whisper.cpp (base)** | CPU | ~3-5s | Excellent | Medium |
| **Whisper.cpp (tiny)** | CPU | ~1-2s | Good | Low |

**Recommendation:** Start with Whisper.cpp (base.en) for development (easier setup), migrate to SenseVoice RKNN2 for production (better performance).

---

## Audio Capture

### Hardware: USB Microphone

**Recommended Models:**
- **Blue Snowball iCE** (~$50, USB, excellent quality)
- **Fifine K669B** (~$25, budget-friendly)
- **Any USB mic with 16kHz+ sample rate**

**Alternative:** 3.5mm mic + USB sound card adapter (~$10)

---

### Audio Recording (Python)

**Library:** `pyaudio` or `sounddevice`

**Installation:**
```bash
sudo apt-get install portaudio19-dev
pip3 install pyaudio
```

**Record Audio on PTT Press:**
```python
import pyaudio
import wave

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
    
    def start_recording(self):
        """Start capturing audio from microphone"""
        self.frames = []
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        print("Recording started...")
    
    def stop_recording(self, output_file="temp_recording.wav"):
        """Stop recording and save to WAV file"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            print("Recording stopped.")
        
        # Save to WAV
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
        
        return output_file
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback to store audio frames"""
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def cleanup(self):
        """Release audio resources"""
        self.audio.terminate()
```

**Integration with PTT Button:**
```python
# In button_interface.py
recorder = AudioRecorder()

def on_ptt_hold():
    """PTT button pressed - start recording"""
    display.show_status("Listening...")
    recorder.start_recording()

def on_ptt_release():
    """PTT button released - stop recording, transcribe"""
    audio_file = recorder.stop_recording()
    display.show_status("Transcribing...")
    
    # Send to STT
    text = stt.transcribe(audio_file)
    print(f"Transcribed: {text}")
    
    # Display user input
    display.add_message(role="user", text=text)
    
    # Send to AI
    # ... (existing Ollama integration)
```

---

## Text-to-Speech (TTS)

### Option 1: Piper (Recommended)

**What is Piper?**
- Fast, local TTS by Rhasspy project
- Generates high-quality speech (WAV format)
- Supports multiple voices
- Can be optimized for NPU (ONNX → RKNN conversion)

**Installation:**
```bash
# Download Piper binary for ARM64
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz
cd piper

# Download a voice model (e.g., en_US-lessac-medium)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

**Usage:**
```python
import subprocess

class PiperTTS:
    def __init__(self, piper_bin="./piper/piper", model_path="./piper/en_US-lessac-medium.onnx"):
        self.piper_bin = piper_bin
        self.model_path = model_path
    
    def synthesize(self, text, output_file="output.wav"):
        """
        Convert text to speech WAV file
        """
        result = subprocess.run(
            [self.piper_bin, "--model", self.model_path, "--output_file", output_file],
            input=text,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            print(f"TTS generated: {output_file}")
            return output_file
        else:
            print(f"TTS error: {result.stderr}")
            return None
```

**Voice Options:**
- **en_US-lessac-medium** - Clear, neutral American English (recommended)
- **en_GB-alan-medium** - British English
- **en_US-libritts-high** - High quality, slower generation

**Performance:**
- **Latency:** ~500ms for 1 sentence on RK3588 CPU
- **With NPU optimization:** Could reduce to ~200-300ms (requires ONNX → RKNN conversion)

---

### Option 2: eSpeak-NG (Lightweight Fallback)

**What is eSpeak-NG?**
- Simple, rule-based TTS
- Very fast (near real-time)
- Robotic voice quality (acceptable for prototyping)

**Installation:**
```bash
sudo apt-get install espeak-ng
```

**Usage:**
```python
import subprocess

class ESpeakTTS:
    def synthesize(self, text, output_file="output.wav"):
        """Generate speech with eSpeak-NG"""
        subprocess.run(
            ["espeak-ng", "-w", output_file, text]
        )
        return output_file
```

**Pros:**
- Extremely fast
- Minimal resource usage
- No model files needed

**Cons:**
- Robotic, less natural voice
- Not suitable for long-form dialogue (fatiguing to listen to)

---

### TTS Performance Comparison

| TTS Engine | Quality | Latency (1 sentence) | NPU Support |
|------------|---------|---------------------|-------------|
| **Piper (medium)** | Excellent | ~500ms | Possible (ONNX→RKNN) |
| **Piper (low)** | Good | ~200ms | Possible |
| **eSpeak-NG** | Robotic | ~50ms | N/A (rule-based) |

**Recommendation:** Piper (medium quality) for production. eSpeak-NG for early testing.

---

## Audio Playback

### Hardware: Speaker

**Options:**
1. **USB Speaker** (plug-and-play, e.g., Logitech Z50 ~$20)
2. **3.5mm Speaker** (via headphone jack, e.g., any powered speaker)
3. **Bluetooth Speaker** (wireless, but adds latency - not recommended for real-time TTS)

---

### Playback (Python)

**Library:** `pygame` or `pyaudio`

**Installation:**
```bash
pip3 install pygame
```

**Play WAV File:**
```python
import pygame

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
    
    def play(self, wav_file):
        """Play WAV file through speaker"""
        pygame.mixer.music.load(wav_file)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    
    def stop(self):
        """Stop playback"""
        pygame.mixer.music.stop()
    
    def set_volume(self, level):
        """Set volume (0.0 to 1.0)"""
        pygame.mixer.music.set_volume(level)
```

**Integration with Conversation Flow:**
```python
# After AI generates response
ai_response_text = "Before we can explore justice, we must first clarify..."

# Display text on screen
display.add_message(role="ai", text=ai_response_text)

# Convert to speech
display.show_status("Speaking...")
audio_file = tts.synthesize(ai_response_text)

# Play audio
player.play(audio_file)
display.show_status("")  # Clear status after playback
```

---

## NPU Acceleration Strategy

### Why NPU?

The Radxa Rock 5B+'s Rockchip RK3588 includes a **6 TOPS NPU** (Neural Processing Unit). This hardware accelerator can run AI models **10x faster** than CPU while using **5x less power**.

**Target Models for NPU:**
1. **SenseVoice (STT)** - Already has RKNN2 support
2. **Piper (TTS)** - Requires ONNX → RKNN conversion

---

### Converting Piper ONNX to RKNN

**Tools:**
- RKNN-Toolkit2 (Rockchip's conversion tool)

**Process:**
```bash
# Install RKNN-Toolkit2 (on x86 Linux host, NOT on Radxa)
pip install rknn-toolkit2

# Convert ONNX to RKNN
python3 convert_piper_to_rknn.py
```

**Conversion Script (`convert_piper_to_rknn.py`):**
```python
from rknn.api import RKNN

# Create RKNN object
rknn = RKNN()

# Load ONNX model
print("Loading Piper ONNX model...")
ret = rknn.load_onnx(model='en_US-lessac-medium.onnx')
if ret != 0:
    print("Load model failed!")
    exit(ret)

# Build for RK3588 NPU
print("Building RKNN model...")
ret = rknn.build(do_quantization=True, dataset='./dataset.txt')  # Quantize for speed
if ret != 0:
    print("Build failed!")
    exit(ret)

# Export RKNN model
print("Exporting RKNN model...")
ret = rknn.export_rknn('en_US-lessac-medium.rknn')
if ret != 0:
    print("Export failed!")
    exit(ret)

print("Conversion complete: en_US-lessac-medium.rknn")
```

**Note:** Actual conversion may require debugging. Piper's architecture (VITS-based) should be compatible with RKNN, but may need modifications to input/output layers.

---

## Voice Latency Optimization

### Goal: < 2 seconds from voice input to AI speech response

**Latency Breakdown (Current Estimate):**

| Step | Hardware | Latency |
|------|----------|---------|
| 1. Audio recording | Mic | ~0.5s (user speaks) |
| 2. STT (Whisper.cpp base) | CPU | ~3-5s |
| 3. AI inference (Mistral 7B) | CPU/GPU | ~2-5s |
| 4. TTS (Piper medium) | CPU | ~0.5-1s |
| 5. Audio playback | Speaker | ~0.1s |
| **Total** | | **~6.6-11.6s** |

**Optimized Latency (with NPU):**

| Step | Hardware | Latency |
|------|----------|---------|
| 1. Audio recording | Mic | ~0.5s |
| 2. STT (SenseVoice RKNN2) | NPU | ~1-2s |
| 3. AI inference (Mistral 7B) | CPU/GPU | ~2-5s |
| 4. TTS (Piper RKNN2) | NPU | ~0.2-0.3s |
| 5. Audio playback | Speaker | ~0.1s |
| **Total** | | **~3.8-7.9s** |

**Further Optimization:**
- **Parallel TTS:** Start TTS on first sentence while AI still generating remaining text (streaming)
- **Smaller Whisper model:** Use `whisper.cpp tiny` (~1s latency, acceptable accuracy)
- **Quantized Mistral:** Use Q4_K_M quantization (already doing this)

---

## Voice Interface UX Patterns

### Pattern 1: Hold-to-Talk (Recommended)

**User Action:** Hold PTT button while speaking, release when done.

**Pros:**
- Clear start/stop (no accidental triggers)
- User controls recording length
- Familiar (like walkie-talkie)

**Cons:**
- Requires holding button (can't multitask)

---

### Pattern 2: Tap-to-Start, Auto-Stop (Future)

**User Action:** Tap PTT once to start recording, system auto-detects silence and stops.

**Pros:**
- Hands-free after initial tap
- More natural for long questions

**Cons:**
- Requires Voice Activity Detection (VAD)
- Risk of cutting off user mid-sentence

**Implementation:** Use `webrtcvad` library for silence detection.

---

## Integration with Existing Philosopher App

### Modified Dialogue Flow

**Current (Text-Only):**
```python
# User types question
user_query = input("You: ")

# AI responds
ai_response = philosopher.query(user_query)
print(f"AI: {ai_response}")
```

**Enhanced (Voice + Text):**
```python
from voice_interface import VoiceInterface

voice = VoiceInterface(stt_model="whisper.cpp", tts_model="piper")

# PTT button held
def on_ptt_hold():
    voice.start_recording()

# PTT button released
def on_ptt_release():
    # Transcribe
    user_query = voice.stop_and_transcribe()
    display.add_message(role="user", text=user_query)
    
    # AI inference
    display.show_status("Thinking...")
    ai_response = philosopher.query(user_query)
    display.add_message(role="ai", text=ai_response)
    
    # Speak response
    display.show_status("Speaking...")
    voice.speak(ai_response)
    display.show_status("")
```

---

## Development Roadmap

### Phase 1: Audio Capture & Playback ✅ Target
- [ ] Connect USB microphone to Radxa Rock 5B+
- [ ] Test audio recording with `pyaudio` (save to WAV)
- [ ] Connect speaker and test playback with `pygame`
- [ ] Verify 16kHz sample rate works

### Phase 2: STT Integration
- [ ] Install `whisper.cpp` on Radxa
- [ ] Test transcription with pre-recorded audio samples
- [ ] Integrate with PTT button (record → transcribe → display)
- [ ] Measure latency

### Phase 3: TTS Integration
- [ ] Install Piper on Radxa
- [ ] Test TTS with sample sentences
- [ ] Integrate with AI response (text → speech → play)
- [ ] Test volume control with UP/DOWN buttons

### Phase 4: NPU Optimization (Advanced)
- [ ] Convert SenseVoice to RKNN2 (or obtain pre-converted model)
- [ ] Test SenseVoice STT latency vs Whisper.cpp
- [ ] Attempt Piper ONNX → RKNN conversion
- [ ] Benchmark performance gains

### Phase 5: Voice UX Polish
- [ ] Add "beep" sound on PTT press (audio feedback)
- [ ] Implement cancel mid-response (LEFT button stops TTS)
- [ ] Add retry logic (if STT fails, prompt user to repeat)

---

## Testing Checklist

### Audio Hardware Tests
- [ ] Microphone detected (`arecord -l` shows device)
- [ ] Speaker detected (`aplay -l` shows device)
- [ ] Record test audio, verify playback (no distortion)
- [ ] Test at different volumes (quiet room vs noisy environment)

### STT Tests
- [ ] Whisper.cpp transcribes clear speech accurately (> 95%)
- [ ] Handles background noise gracefully (doesn't hallucinate)
- [ ] Works with various accents (test with different speakers)
- [ ] Latency acceptable (< 5s for 5s audio)

### TTS Tests
- [ ] Piper voice is intelligible and pleasant
- [ ] No robotic artifacts or glitches
- [ ] Proper pronunciation of philosophical terms (e.g., "Nietzsche" = "NEE-chuh")
- [ ] Playback doesn't stutter or lag

### Integration Tests
- [ ] PTT hold → record → release → transcribe → display works smoothly
- [ ] AI response → TTS → playback completes without errors
- [ ] Display updates correctly during voice workflow (Listening → Thinking → Speaking)
- [ ] Can interrupt TTS with button press (cancel playback)

---

## Known Issues & Mitigations

### Issue: STT Hallucinations (Whisper)
**Symptom:** Whisper sometimes "hallucinates" text when audio is silent or unintelligible  
**Mitigation:** Check audio level before transcribing. If RMS volume below threshold, display "No audio detected, please speak louder"  
**Status:** Common Whisper issue, requires workaround

### Issue: Piper Voice Pronunciation Errors
**Symptom:** Piper mispronounces philosophical names (e.g., "Camus" as "KAM-us" instead of "kah-MOO")  
**Mitigation:** Use Piper's phonetic override feature in TTS call  
**Status:** Can be fixed per-term basis

### Issue: Audio Playback Blocking UI
**Symptom:** UI freezes during TTS playback  
**Mitigation:** Run TTS playback in separate thread  
**Status:** Standard fix

---

## Resources

### Documentation
- [Whisper.cpp GitHub](https://github.com/ggerganov/whisper.cpp)
- [Piper TTS Documentation](https://github.com/rhasspy/piper)
- [RKNN-Toolkit2 Guide](https://github.com/rockchip-linux/rknn-toolkit2)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)

### Pre-trained Models
- [Whisper Models](https://huggingface.co/ggerganov/whisper.cpp)
- [Piper Voices](https://huggingface.co/rhasspy/piper-voices/tree/main)
- [SenseVoice (Hugging Face)](https://huggingface.co/FunAudioLLM/SenseVoiceSmall)

### Community Resources
- Reddit: r/LocalLLaMA (voice AI discussions)
- Radxa Forum (RK3588 NPU optimization)
- Rhasspy Community (Piper TTS support)

---

## Notes for Future Improvement

**After Phase 1:**
- Document actual USB audio device names (`/dev/snd/...`)
- Test with various microphones (cheap vs quality, test which works best)
- Measure background noise rejection

**After Phase 3:**
- Experiment with Piper voice models (try different voices for different personas?)
- Add "thinking music" during AI inference (subtle ambient sound)

**After Phase 4:**
- Document actual NPU performance gains (before/after benchmarks)
- Share RKNN-converted Piper model with community (if successful)

---

**Last Updated:** November 9, 2025  
**Status:** Specification complete, awaiting hardware arrival  
**Next Steps:** Install Whisper.cpp and Piper on Radxa Rock 5B+ for latency testing
