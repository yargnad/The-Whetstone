# System Architecture

**Component Status:** 📋 Specification Phase  
**Target Platform:** Radxa Rock 5B+ (24GB RAM, Rockchip RK3588)  
**Purpose:** Overall system design showing how all Whetstone components integrate

---

## Overview

The Whetstone is a physical AI device composed of multiple interconnected subsystems. This document provides the high-level architecture showing how components communicate and where each piece of code lives.

**Design Goals:**
- **Modularity** - Each component can be developed and tested independently
- **Clarity** - Clear interfaces between subsystems
- **Maintainability** - Easy to debug and extend
- **Performance** - Minimize latency in critical paths (voice → AI → speech)

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        RADXA ROCK 5B+                           │
│                     (Rockchip RK3588)                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Main Application Loop                      │   │
│  │          (philosopher_whetstone.py)                     │   │
│  │                                                         │   │
│  │  - State management (persona select / conversation)     │   │
│  │  - Coordinate component interactions                    │   │
│  │  - Event handling                                       │   │
│  └────┬─────────────┬──────────────┬─────────────┬────────┘   │
│       │             │              │             │             │
│       ▼             ▼              ▼             ▼             │
│  ┌────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐       │
│  │Display │   │ Button  │   │  Voice   │   │Philosopher│      │
│  │Manager │   │Manager  │   │Interface │   │  Engine  │       │
│  └────┬───┘   └────┬────┘   └─────┬────┘   └────┬────┘       │
│       │            │               │             │             │
│       │            │               │             │             │
│  ┌────▼───────┐ ┌─▼──────────┐ ┌──▼─────────┐ ┌─▼────────┐   │
│  │  E-Ink     │ │   GPIO     │ │   Audio    │ │  Ollama  │   │
│  │  Display   │ │  (gpiod)   │ │  (pyaudio) │ │  Server  │   │
│  │  (SPI)     │ │            │ │  Whisper   │ │ (Mistral)│   │
│  │            │ │  Buttons   │ │  Piper     │ │          │   │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘   │
│                                                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
    ┌────▼────┐              ┌──────▼──────┐
    │  USB    │              │   USB       │
    │  Mic    │              │  Speaker    │
    └─────────┘              └─────────────┘
```

---

## Component Breakdown

### 1. Main Application Loop

**File:** `philosopher_whetstone.py`

**Responsibilities:**
- Initialize all subsystems (display, buttons, voice, AI)
- Manage application state (persona selection, conversation mode, power menu)
- Route button events to appropriate handlers
- Coordinate voice workflow (record → transcribe → AI → speak)
- Handle errors and recovery

**Key Functions:**
```python
def main():
    # Initialize subsystems
    display = DisplayManager()
    buttons = ButtonManager()
    voice = VoiceInterface()
    philosopher = PhilosopherEngine()
    
    # Set up event handlers
    buttons.register_callback('up', 'short', on_scroll_up)
    buttons.register_callback('ptt', 'hold', on_ptt_hold)
    # ... etc
    
    # Main loop
    state = AppState.PERSONA_SELECT
    while True:
        buttons.poll_buttons()
        
        if state == AppState.PERSONA_SELECT:
            # Handle persona selection
            pass
        elif state == AppState.CONVERSATION:
            # Handle conversation
            pass
        
        time.sleep(0.01)  # Poll at 100Hz
```

---

### 2. Display Manager

**File:** `display_manager.py`

**Responsibilities:**
- Render UI layouts (persona selection, conversation, overlays)
- Manage e-ink refresh strategy (full vs partial)
- Handle text wrapping and scrolling
- Power management (sleep/wake)

**Key Interfaces:**
```python
class DisplayManager:
    def initialize(self):
        """Initialize e-ink display"""
        
    def show_persona_selection(self, selected_index):
        """Render persona selection screen"""
        
    def add_message(self, role, text):
        """Add message to conversation buffer and render"""
        
    def show_status(self, status_text):
        """Update status bar (e.g., 'Listening...')"""
        
    def scroll_up(self, lines=1):
        """Scroll conversation view up"""
        
    def scroll_down(self, lines=1):
        """Scroll conversation view down"""
        
    def show_overlay(self, overlay_type):
        """Show overlay (LISTENING, THINKING, etc.)"""
        
    def sleep(self):
        """Put display in low-power mode"""
        
    def wake(self):
        """Wake display from sleep"""
```

**Dependencies:**
- E-ink display HAT (via SPI)
- PIL (Python Imaging Library) for text rendering
- Waveshare EPD library (or similar)

**See:** [EINK_DISPLAY_MANAGER.md](EINK_DISPLAY_MANAGER.md)

---

### 3. Button Manager

**File:** `button_manager.py`

**Responsibilities:**
- Poll GPIO pins for button state changes
- Debounce button presses
- Detect short press, long press, and hold events
- Trigger registered callbacks

**Key Interfaces:**
```python
class ButtonManager:
    def __init__(self):
        """Initialize GPIO pins for buttons"""
        
    def register_callback(self, button_name, event_type, callback):
        """Register callback for button event"""
        
    def poll_buttons(self):
        """Check button states and trigger callbacks"""
        
    def cleanup(self):
        """Release GPIO resources"""
```

**Dependencies:**
- `gpiod` library (modern GPIO access)
- Physical buttons wired to GPIO pins

**See:** [BUTTON_INTERFACE.md](BUTTON_INTERFACE.md)

---

### 4. Voice Interface

**File:** `voice_interface.py`

**Responsibilities:**
- Record audio from microphone
- Transcribe speech to text (STT)
- Synthesize text to speech (TTS)
- Play audio through speaker

**Key Interfaces:**
```python
class VoiceInterface:
    def __init__(self, stt_model="whisper.cpp", tts_model="piper"):
        """Initialize STT and TTS engines"""
        
    def start_recording(self):
        """Start capturing audio from mic"""
        
    def stop_and_transcribe(self):
        """Stop recording and return transcribed text"""
        
    def speak(self, text):
        """Convert text to speech and play audio"""
        
    def set_volume(self, level):
        """Adjust playback volume (0.0 to 1.0)"""
        
    def cancel_playback(self):
        """Stop current TTS playback"""
```

**Dependencies:**
- `pyaudio` (audio capture/playback)
- Whisper.cpp or SenseVoice (STT)
- Piper TTS
- USB microphone and speaker

**See:** [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md)

---

### 5. Philosopher Engine

**File:** `philosopher_engine.py`

**Responsibilities:**
- Load persona configurations (system prompts, library filters)
- Interface with Ollama API
- Manage RAG (Retrieval-Augmented Generation) with philosophy library
- Stream AI responses

**Key Interfaces:**
```python
class PhilosopherEngine:
    def __init__(self, persona="Benevolent Absurdist"):
        """Initialize with selected persona"""
        
    def set_persona(self, persona_name):
        """Switch to a different persona"""
        
    def query(self, user_input):
        """Send query to AI and return response"""
        
    def query_stream(self, user_input, callback):
        """Stream AI response token-by-token to callback"""
        
    def search_library(self, query):
        """Search philosophy library for relevant context"""
```

**Dependencies:**
- Ollama server (running locally on `localhost:11434`)
- Mistral 7B model
- Philosophy library (text files)
- OpenAI Python client (for Ollama compatibility)

**See:** Existing `philosopher_app.py` (to be refactored into this class)

---

## Data Flow Examples

### Example 1: Persona Selection

```
1. User presses DOWN button
   └─► ButtonManager detects press
       └─► Triggers `on_down_short()` callback
           └─► Main app increments selected_index
               └─► DisplayManager.show_persona_selection(selected_index)
                   └─► E-ink display partial refresh (highlight moves down)

2. User presses SELECT button
   └─► ButtonManager detects press
       └─► Triggers `on_select_short()` callback
           └─► Main app changes state to CONVERSATION
               └─► PhilosopherEngine.set_persona(selected_persona)
               └─► DisplayManager.show_conversation_screen()
                   └─► E-ink display full refresh (new screen)
```

---

### Example 2: Voice Query

```
1. User holds PTT button
   └─► ButtonManager detects hold
       └─► Triggers `on_ptt_hold()` callback
           └─► VoiceInterface.start_recording()
               ├─► Mic starts capturing audio
               └─► DisplayManager.show_overlay("LISTENING")
                   └─► E-ink partial refresh

2. User releases PTT button
   └─► ButtonManager detects release
       └─► Triggers `on_ptt_release()` callback
           └─► VoiceInterface.stop_and_transcribe()
               ├─► Stop mic capture
               ├─► Save audio to WAV file
               ├─► Whisper.cpp transcribes → text
               └─► Return transcribed text
           └─► DisplayManager.add_message("user", text)
               └─► E-ink partial refresh (show user message)
           └─► DisplayManager.show_overlay("THINKING")
               └─► E-ink partial refresh

3. Send query to AI
   └─► PhilosopherEngine.query(text)
       ├─► Search philosophy library for context
       ├─► Send to Ollama (Mistral 7B)
       ├─► Receive AI response
       └─► Return response text
   └─► DisplayManager.add_message("ai", response)
       └─► E-ink partial refresh (show AI message)
   └─► DisplayManager.show_status("Speaking...")
       └─► E-ink partial refresh

4. Speak AI response
   └─► VoiceInterface.speak(response)
       ├─► Piper TTS converts to WAV
       ├─► Play audio through speaker
       └─► Wait for playback to finish
   └─► DisplayManager.show_status("")
       └─► E-ink partial refresh (clear status)
```

---

## File Structure

```
The_Whetstone/
├── philosopher_whetstone.py        # Main application loop
├── display_manager.py              # E-ink display control
├── button_manager.py               # GPIO button handling
├── voice_interface.py              # STT + TTS integration
├── philosopher_engine.py           # AI query logic (refactored from philosopher_app.py)
├── config.py                       # Configuration (GPIO pins, model paths, etc.)
├── README.md                       # User-facing documentation
├── HARDWARE_SETUP.md               # Hardware assembly guide
├── EINK_DISPLAY_MANAGER.md         # Display implementation spec
├── BUTTON_INTERFACE.md             # Button implementation spec
├── UI_FRAMEWORK.md                 # UI design spec
├── VOICE_INTEGRATION.md            # Voice implementation spec
├── SYSTEM_ARCHITECTURE.md          # This file
├── philosophy_library/             # Text files for RAG
│   ├── plato_Euthyphro.txt
│   ├── nietzsche_Beyond Good and Evil.txt
│   └── ...
├── models/                         # AI model files
│   ├── Mistral-7B-Instruct-v0_3_Q4_K_M.gguf
│   ├── sensevoice_small.rknn       # (NPU-optimized STT)
│   └── en_US-lessac-medium.onnx    # (Piper TTS)
└── assets/                         # Fonts, icons (if needed)
    └── DejaVuSansMono.ttf
```

---

## Configuration Management

**File:** `config.py`

**Purpose:** Centralize all hardware-specific settings and model paths.

**Example:**
```python
# Hardware Configuration
GPIO_CHIP = 'gpiochip0'
GPIO_BUTTON_UP = 68
GPIO_BUTTON_DOWN = 69
GPIO_BUTTON_LEFT = 70
GPIO_BUTTON_RIGHT = 71
GPIO_BUTTON_SELECT = 72
GPIO_BUTTON_PTT = 73

DISPLAY_SPI_BUS = 0
DISPLAY_SPI_DEVICE = 0

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
MIC_DEVICE_INDEX = 0  # Default mic
SPEAKER_DEVICE_INDEX = 0  # Default speaker

# AI Configuration
OLLAMA_API_URL = "http://localhost:11434/v1"
MODEL_NAME = "whetstone-philosopher"
PHILOSOPHY_LIBRARY_PATH = "./philosophy_library"

# Voice Configuration
STT_MODEL_PATH = "./models/whisper.cpp/base.en"  # or sensevoice RKNN
TTS_MODEL_PATH = "./models/piper/en_US-lessac-medium.onnx"

# Display Configuration
DISPLAY_WIDTH = 400
DISPLAY_HEIGHT = 300
FONT_TITLE_SIZE = 14
FONT_BODY_SIZE = 11
FONT_FOOTER_SIZE = 9

# UI Behavior
SCROLL_LINES_PER_PRESS = 1
LONG_PRESS_THRESHOLD = 1.0  # seconds
DEBOUNCE_TIME = 0.05  # 50ms

# Power Management
IDLE_TIMEOUT = 30  # seconds before entering idle mode
DEEP_SLEEP_TIMEOUT = 300  # seconds before deep sleep
```

**Usage in Components:**
```python
import config

# In display_manager.py
self.width = config.DISPLAY_WIDTH
self.font_size = config.FONT_BODY_SIZE

# In button_manager.py
self.pins = {
    'up': config.GPIO_BUTTON_UP,
    'down': config.GPIO_BUTTON_DOWN,
    # ...
}
```

---

## Threading and Concurrency

### Challenge: Blocking Operations

Some operations block the main loop:
- **TTS playback:** `pygame.mixer.music.play()` blocks until audio finishes
- **AI inference:** Ollama API call can take 2-10 seconds
- **Audio recording:** Continuous capture during PTT hold

### Solution: Use Threads for Blocking Operations

**Voice Playback (TTS):**
```python
import threading

def speak_in_thread(text):
    def _speak():
        tts.synthesize(text)
        player.play("output.wav")
    
    thread = threading.Thread(target=_speak)
    thread.start()
    return thread  # Caller can join() if needed
```

**AI Inference (Optional):**
```python
def query_in_thread(user_input, callback):
    def _query():
        response = philosopher.query(user_input)
        callback(response)
    
    thread = threading.Thread(target=_query)
    thread.start()
```

**Note:** Be careful with thread safety. Display updates should only happen from main thread.

---

## Error Handling Strategy

### Graceful Degradation

**Principle:** Device should never crash. If a component fails, fallback to degraded mode.

**Examples:**

| Component Failure | Fallback Behavior |
|-------------------|-------------------|
| E-ink display fails | Log to console, continue running (blind mode for debugging) |
| Whisper STT crashes | Display error overlay, prompt user to retry |
| Ollama server down | Display "AI unavailable" message, allow persona change |
| TTS fails | Display AI response as text only (silent mode) |
| Button GPIO error | Fallback to keyboard input (development mode) |

**Implementation:**
```python
try:
    display.initialize()
except Exception as e:
    print(f"Display initialization failed: {e}")
    display = None  # Fallback to console-only mode

# Later, check before using
if display:
    display.show_status("Listening...")
else:
    print("[Status] Listening...")
```

---

## Logging and Debugging

### Log Levels

1. **DEBUG:** Verbose info (button presses, GPIO states, API calls)
2. **INFO:** Normal operation (persona selected, message sent)
3. **WARNING:** Recoverable errors (STT timeout, retrying)
4. **ERROR:** Component failure (display crash, Ollama unreachable)

**Setup:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('whetstone.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)
logger.info("The Whetstone started")
logger.debug(f"Persona selected: {persona_name}")
logger.error(f"Display initialization failed: {e}")
```

**Log File:** `/home/user/whetstone.log` (rotates daily to prevent filling disk)

---

## Performance Monitoring

### Key Metrics to Track

1. **Voice latency:** Time from PTT release to TTS playback start
2. **AI inference time:** Ollama query duration
3. **Display refresh rate:** Partial refresh frequency
4. **Memory usage:** Ensure no leaks during long sessions

**Instrumentation:**
```python
import time

def measure_latency(func):
    """Decorator to measure function execution time"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

# Usage
@measure_latency
def query(self, user_input):
    # ... AI inference
    pass
```

---

## Development and Testing

### Unit Testing

**Goal:** Test each component in isolation.

**Example:**
```python
# test_button_manager.py
import unittest
from button_manager import ButtonManager

class TestButtonManager(unittest.TestCase):
    def setUp(self):
        self.buttons = ButtonManager()
    
    def test_button_press(self):
        # Mock GPIO input
        # Trigger callback
        # Assert callback was called
        pass
    
    def tearDown(self):
        self.buttons.cleanup()
```

**Run Tests:**
```bash
python3 -m unittest discover -s tests/
```

---

### Integration Testing

**Goal:** Test component interactions.

**Example:**
```python
# test_voice_workflow.py
def test_voice_query_to_response():
    # Simulate PTT press
    voice.start_recording()
    
    # Play test audio file into mic (via virtual audio device)
    # ...
    
    # Stop recording
    text = voice.stop_and_transcribe()
    
    # Assert text matches expected transcription
    assert "what is justice" in text.lower()
    
    # Send to AI
    response = philosopher.query(text)
    
    # Assert response is non-empty
    assert len(response) > 0
    
    # Speak response
    voice.speak(response)
    # (Audio playback can't be easily asserted, but shouldn't crash)
```

---

### Hardware-in-the-Loop Testing

**Goal:** Test on actual Radxa hardware.

**Setup:**
1. SSH into Radxa Rock 5B+
2. Run test scripts remotely
3. Observe e-ink display and listen to audio output

**Commands:**
```bash
# SSH into Radxa
ssh user@radxa.local

# Run main app
cd The_Whetstone
python3 philosopher_whetstone.py

# Monitor logs in separate terminal
tail -f whetstone.log
```

---

## Deployment

### Installation Script

**File:** `install.sh`

**Purpose:** Automate setup on fresh Radxa system.

```bash
#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
    python3-pip \
    python3-spidev \
    python3-pil \
    python3-gpiod \
    portaudio19-dev \
    git

# Install Python packages
pip3 install \
    pyaudio \
    pygame \
    openai \
    gpiod

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Mistral model
ollama pull mistral

# Install Whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make
bash ./models/download-ggml-model.sh base.en
cd ..

# Install Piper TTS
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz

echo "Installation complete!"
```

**Run:**
```bash
chmod +x install.sh
./install.sh
```

---

### Systemd Service (Auto-Start on Boot)

**File:** `/etc/systemd/system/whetstone.service`

```ini
[Unit]
Description=The Whetstone Philosophical AI
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/The_Whetstone
ExecStart=/usr/bin/python3 philosopher_whetstone.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Enable Service:**
```bash
sudo systemctl enable whetstone.service
sudo systemctl start whetstone.service
```

**Check Status:**
```bash
sudo systemctl status whetstone.service
```

---

## Security Considerations

### Privacy

**Goal:** Ensure all data stays on-device.

**Implementation:**
- Ollama runs locally (no cloud API calls)
- Whisper.cpp and Piper run locally
- No telemetry or analytics
- Conversation history stored in RAM only (ephemeral)

**Optional:** Allow user to export conversation history to encrypted file.

---

### Physical Security

**Goal:** Protect device from tampering.

**Considerations:**
- Enclosure should be opaque (hide internal components)
- SD card slot covered (prevent data extraction)
- No accessible UART/serial ports on enclosure exterior

---

## Future Enhancements

### Phase 2 Features (After Core Functionality)

1. **Multi-User Profiles**
   - Store separate conversation histories per user
   - Voice recognition to auto-detect speaker (advanced)

2. **Conversation Export**
   - Button to save current session to PDF or Markdown
   - Transfer via USB or web interface

3. **Persona Customization**
   - Web UI to create custom personas
   - Upload custom philosophy texts

4. **Battery Power**
   - LiPo battery + charging circuit
   - Battery level indicator on display
   - Low-power sleep modes

5. **Mesh Networking (The Lyceum)**
   - LoRa HAT for peer-to-peer communication
   - Share conversations with nearby Whetstone devices
   - Federated AI (Pneuma integration)

---

## Resources

### Documentation
- [Radxa Rock 5B+ Wiki](https://wiki.radxa.com/Rock5/hardware/5b)
- [Python Threading](https://docs.python.org/3/library/threading.html)
- [Systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

### Related Projects
- [Remarkable 2 Tablet](https://remarkable.com/) - E-ink device design inspiration
- [PiKVM](https://pikvm.org/) - Raspberry Pi embedded system reference
- [MyCroft AI](https://mycroft.ai/) - Open-source voice assistant architecture

---

## Notes for Future Improvement

**After First Build:**
- Document actual component wiring with photos
- Measure real-world performance (latency, battery life if applicable)
- Identify bottlenecks (likely AI inference or TTS)

**After Field Testing:**
- Collect user feedback on UI/UX
- Identify most common errors (add better handling)
- Optimize most-used workflows (e.g., faster persona switching)

---

**Last Updated:** November 9, 2025  
**Status:** Specification complete, ready for implementation  
**Next Steps:** Begin implementing `philosopher_whetstone.py` main loop and component integration
