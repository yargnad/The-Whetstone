# E-Ink Display Manager

**Component Status:** 📋 Specification Phase  
**Target Hardware:** E-ink display (4.2"-7.5") connected to Radxa Rock 5B+ via SPI  
**Purpose:** Manage display rendering, refresh strategies, and text layout for The Whetstone UI

---

## Overview

The E-ink Display Manager is responsible for rendering the text-based UI on The Whetstone's e-ink screen. Unlike traditional displays, e-ink has unique constraints and advantages that must be carefully managed:

**Advantages:**
- Readable in any lighting condition (including direct sunlight)
- Zero power consumption when static
- Philosophical aesthetic (like reading a book)
- Eye-friendly for extended sessions

**Constraints:**
- Slow refresh rate (~1-2 seconds for full refresh)
- Ghosting artifacts if not properly managed
- Limited to grayscale (typically 2-bit or 4-bit)
- Partial refresh capabilities vary by model

---

## Hardware Selection

### Recommended E-Ink Displays

| Model | Size | Resolution | Interface | Partial Refresh | Cost | Notes |
|-------|------|------------|-----------|-----------------|------|-------|
| **Waveshare 4.2" (Recommended)** | 4.2" | 400x300 | SPI | Yes | $30-40 | Good balance of size/cost |
| **Waveshare 5.65"** | 5.65" | 600x448 | SPI | Yes | $40-50 | 7-color option available |
| **Waveshare 7.5"** | 7.5" | 800x480 | SPI | Yes | $50-60 | More readable, larger form factor |
| **Good Display 4.2"** | 4.2" | 400x300 | SPI | Yes | $35-45 | Alternative to Waveshare |

**Selection Criteria:**
- Must support partial refresh (critical for responsive UI)
- SPI interface for compatibility with Radxa Rock 5B+
- Grayscale support (4-bit ideal for readability)
- Open documentation and Python library availability

**Chosen for this build:** Waveshare 4.2" (update after hardware selection)

---

## Display Manager Architecture

### Core Components

```
┌─────────────────────────────────────────┐
│         Display Manager Service         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Refresh Strategy Controller     │ │
│  │  - Full Refresh Scheduler         │ │
│  │  - Partial Refresh Handler        │ │
│  │  - Ghosting Prevention            │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Text Rendering Engine           │ │
│  │  - Font Management                │ │
│  │  - Word Wrapping                  │ │
│  │  - Scroll Buffer                  │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   UI State Manager                │ │
│  │  - Screen Layouts                 │ │
│  │  - Active Region Tracking         │ │
│  │  - Menu Navigation                │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Hardware Interface (SPI Driver) │ │
│  │  - E-ink Controller Communication │ │
│  │  - Power Management               │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## Refresh Strategies

### Full Refresh vs Partial Refresh

**Full Refresh:**
- **When:** Every 10-20 partial refreshes, or when returning from sleep
- **Duration:** 1-2 seconds (visible flashing)
- **Purpose:** Clear all ghosting artifacts
- **Use cases:** 
  - Screen mode changes (persona selection → conversation)
  - Clearing conversation history
  - Initial boot

**Partial Refresh:**
- **When:** Updating conversation text, button feedback, status indicators
- **Duration:** 200-500ms
- **Purpose:** Quick updates without full screen flash
- **Limitation:** Can cause ghosting over time (requires periodic full refresh)

**Ghosting Prevention Strategy:**
- Track number of partial refreshes since last full refresh
- Force full refresh every 15 partial refreshes
- Store "dirty regions" and prioritize cleaning high-traffic areas

---

## Screen Layouts

### 1. Persona Selection Screen

```
┌────────────────────────────────────┐
│  THE WHETSTONE                     │
│  Select Persona:                   │
│                                    │
│  [1] Benevolent Absurdist          │
│  [2] Socratic Inquirer       ◄     │
│  [3] Stoic Guide                   │
│  [4] Plato                         │
│  [5] Nietzsche                     │
│                                    │
│  Press button to select            │
└────────────────────────────────────┘
```

**Rendering Requirements:**
- Static title (rarely updates)
- Highlight bar for selected persona (partial refresh)
- Button hint text at bottom

---

### 2. Conversation Screen

```
┌────────────────────────────────────┐
│  Socratic Inquirer                 │
│────────────────────────────────────│
│ You: What is justice?              │
│                                    │
│ AI: Before we explore justice,     │
│ let us first clarify what you      │
│ mean. When you say "justice,"      │
│ do you refer to a quality within   │
│ an individual, or to the proper    │
│ ordering of a society?             │
│                                    │
│ [Listening...]                     │
└────────────────────────────────────┘
```

**Rendering Requirements:**
- **Header:** Persona name (static)
- **Conversation area:** Scrolling text buffer (partial refresh)
- **Status bar:** "Listening...", "Thinking...", "Speaking..." (partial refresh)

**Text Flow:**
- New AI responses stream in at bottom
- Older text scrolls up (partial refresh for each line)
- User can scroll back through history with buttons

---

### 3. Thinking/Processing Screen

```
┌────────────────────────────────────┐
│  Socratic Inquirer                 │
│────────────────────────────────────│
│ You: What is justice?              │
│                                    │
│                                    │
│         ┌─────────────┐            │
│         │  THINKING   │            │
│         │   •••••     │            │
│         └─────────────┘            │
│                                    │
│                                    │
└────────────────────────────────────┘
```

**Rendering Requirements:**
- Minimal animation (dot progression or static)
- Clear visual feedback that processing is happening
- No rapid partial refreshes (wait for full response)

---

## Text Rendering Engine

### Font Management

**Requirements:**
- Monospace font for consistent layout
- Multiple sizes:
  - **Title:** 16pt (persona name, headers)
  - **Body:** 12pt (conversation text)
  - **Status:** 10pt (status indicators)
- Support for basic Latin characters + common punctuation

**Recommended Fonts:**
- **DejaVu Sans Mono** (clean, readable, open-source)
- **Ubuntu Mono** (slightly more modern aesthetic)
- **Liberation Mono** (fallback, widely available)

**Implementation:**
```python
from PIL import Image, ImageDraw, ImageFont

# Load fonts at startup
font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
font_status = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
```

---

### Word Wrapping Algorithm

**Challenge:** E-ink displays have fixed pixel dimensions; text must wrap at word boundaries to maintain readability.

**Requirements:**
- Calculate max characters per line based on display width and font size
- Break lines at word boundaries (not mid-word)
- Handle long words gracefully (hyphenation or forced break)

**Pseudocode:**
```python
def wrap_text(text, max_width, font):
    """
    Wrap text to fit within max_width pixels using given font.
    Returns list of wrapped lines.
    """
    lines = []
    words = text.split(' ')
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        width, _ = font.getsize(test_line)
        
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines
```

---

### Scroll Buffer Management

**Challenge:** Conversations can exceed display height; must maintain scrollable history.

**Design:**
- Maintain in-memory buffer of conversation (list of messages)
- Track current "viewport" position (which lines are visible)
- User can scroll up/down with buttons
- Render only visible portion to minimize partial refreshes

**Data Structure:**
```python
class ConversationBuffer:
    def __init__(self, display_height_lines):
        self.messages = []  # List of (role, text) tuples
        self.viewport_start = 0  # Index of topmost visible line
        self.display_height = display_height_lines
    
    def add_message(self, role, text):
        """Add new message and auto-scroll to bottom"""
        self.messages.append((role, text))
        self.scroll_to_bottom()
    
    def scroll_up(self, lines=1):
        """Scroll viewport up"""
        self.viewport_start = max(0, self.viewport_start - lines)
    
    def scroll_down(self, lines=1):
        """Scroll viewport down"""
        max_start = max(0, len(self.messages) - self.display_height)
        self.viewport_start = min(max_start, self.viewport_start + lines)
    
    def get_visible_lines(self):
        """Return lines currently in viewport"""
        return self.messages[self.viewport_start:self.viewport_start + self.display_height]
```

---

## Hardware Interface (SPI Driver)

### Python Library Selection

**Option 1: Waveshare Official Library (Recommended)**
- Provides pre-built drivers for Waveshare displays
- Handles SPI communication and refresh logic
- Example: `waveshare-epd` Python package

**Option 2: IT8951 Generic Driver**
- For displays using IT8951 controller
- More flexible but requires more configuration

**Installation:**
```bash
# Enable SPI on Radxa Rock 5B+
sudo apt-get install python3-spidev python3-pil

# Install Waveshare library (if using Waveshare display)
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
sudo python3 setup.py install
```

---

### SPI Configuration

**Radxa Rock 5B+ SPI Pins:**
- SPI0 CS0: Pin 24
- MOSI: Pin 19
- MISO: Pin 21
- SCLK: Pin 23
- Additional GPIOs for Reset, DC, Busy signals

**Enable SPI in Device Tree:**
```bash
# Check if SPI is enabled
ls /dev/spidev*

# If not present, enable in device tree overlay
# (Radxa-specific instructions to be added after hardware testing)
```

---

### Display Initialization

**Initialization Sequence:**
```python
from waveshare_epd import epd4in2  # Example for 4.2" display

class DisplayManager:
    def __init__(self):
        self.epd = epd4in2.EPD()
        self.width = self.epd.width
        self.height = self.epd.height
        
    def initialize(self):
        """Initialize e-ink display"""
        print("Initializing e-ink display...")
        self.epd.init()
        self.epd.Clear()  # Full refresh to white
        print(f"Display ready: {self.width}x{self.height}px")
    
    def render_full(self, image):
        """Full refresh (use sparingly)"""
        self.epd.display(self.epd.getbuffer(image))
    
    def render_partial(self, image):
        """Partial refresh (faster, but can ghost)"""
        self.epd.displayPartial(self.epd.getbuffer(image))
    
    def sleep(self):
        """Put display in low-power sleep mode"""
        self.epd.sleep()
    
    def shutdown(self):
        """Properly shutdown display"""
        self.epd.Dev_exit()
```

---

## Power Management

### Sleep Strategy

**Goal:** Minimize power consumption when idle while maintaining quick wake.

**States:**
1. **Active:** Display awake, can refresh immediately
2. **Idle:** Display content static, controller in low-power mode (can wake in ~100ms)
3. **Deep Sleep:** Display fully powered down (wake takes ~1s, requires re-init)

**Transition Logic:**
- **Active → Idle:** After 30 seconds of no user interaction
- **Idle → Deep Sleep:** After 5 minutes of no interaction
- **Sleep → Active:** On button press or incoming voice input

**Implementation:**
```python
import time
from enum import Enum

class DisplayState(Enum):
    ACTIVE = 1
    IDLE = 2
    DEEP_SLEEP = 3

class PowerManager:
    def __init__(self, display):
        self.display = display
        self.state = DisplayState.ACTIVE
        self.last_activity = time.time()
    
    def update_activity(self):
        """Call this on any user interaction"""
        self.last_activity = time.time()
        if self.state != DisplayState.ACTIVE:
            self.wake()
    
    def check_sleep_transitions(self):
        """Call this periodically (e.g., every second)"""
        idle_time = time.time() - self.last_activity
        
        if self.state == DisplayState.ACTIVE and idle_time > 30:
            self.enter_idle()
        elif self.state == DisplayState.IDLE and idle_time > 300:
            self.enter_deep_sleep()
    
    def enter_idle(self):
        print("Display entering idle mode")
        self.display.sleep()
        self.state = DisplayState.IDLE
    
    def enter_deep_sleep(self):
        print("Display entering deep sleep")
        self.display.shutdown()
        self.state = DisplayState.DEEP_SLEEP
    
    def wake(self):
        if self.state == DisplayState.DEEP_SLEEP:
            print("Waking from deep sleep (re-initializing)")
            self.display.initialize()
        elif self.state == DisplayState.IDLE:
            print("Waking from idle")
            self.display.init()  # Quick wake
        
        self.state = DisplayState.ACTIVE
        self.last_activity = time.time()
```

---

## Integration Points

### 1. Philosopher App Interface

The display manager receives rendering requests from the main philosopher app:

```python
# In philosopher_app.py
from display_manager import DisplayManager

display = DisplayManager()

# Render persona selection screen
display.show_persona_selection(selected_index=1)

# Render conversation message
display.add_message(role="user", text="What is justice?")
display.add_message(role="ai", text="Before we explore justice...")

# Show status
display.show_status("Listening...")
```

---

### 2. Button Interface

The display manager responds to button events:

```python
# In button_interface.py
def on_scroll_up():
    display.scroll_conversation_up()

def on_scroll_down():
    display.scroll_conversation_down()
```

See [BUTTON_INTERFACE.md](BUTTON_INTERFACE.md) for details.

---

### 3. Voice Interface

Display updates based on voice activity:

```python
# When user presses PTT
display.show_status("Listening...")

# When transcription complete
display.add_message(role="user", text=transcribed_text)
display.show_status("Thinking...")

# When AI response arrives
display.show_status("Speaking...")
display.add_message(role="ai", text=ai_response)
```

See [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md) for details.

---

## Development Roadmap

### Phase 1: Basic Display Control ✅ Target
- [ ] Install and configure SPI on Radxa Rock 5B+
- [ ] Test e-ink display with manufacturer examples
- [ ] Implement basic text rendering (static screen)
- [ ] Verify full refresh and partial refresh work

### Phase 2: UI Layouts
- [ ] Implement persona selection screen
- [ ] Implement conversation screen layout
- [ ] Implement status/thinking screen
- [ ] Test transitions between screens

### Phase 3: Text Management
- [ ] Implement word wrapping algorithm
- [ ] Create scrollable conversation buffer
- [ ] Add scroll up/down functionality
- [ ] Test with long conversations (stress test)

### Phase 4: Refresh Optimization
- [ ] Implement ghosting prevention (periodic full refresh)
- [ ] Optimize partial refresh regions (update only changed areas)
- [ ] Measure and minimize refresh latency

### Phase 5: Power Management
- [ ] Implement idle/sleep states
- [ ] Test wake-from-sleep latency
- [ ] Integrate with button interface (wake on press)
- [ ] Measure power consumption in each state

---

## Testing Checklist

### Hardware Tests
- [ ] E-ink display properly connected via SPI
- [ ] `/dev/spidev0.0` device exists
- [ ] Manufacturer test scripts run successfully
- [ ] Full refresh produces clean white screen
- [ ] Partial refresh updates without full flash

### Functionality Tests
- [ ] Persona selection screen renders correctly
- [ ] Conversation text wraps at word boundaries
- [ ] Long messages scroll properly
- [ ] Status indicators update via partial refresh
- [ ] Full refresh clears ghosting after 15 partial refreshes

### Performance Tests
- [ ] Full refresh completes in < 2 seconds
- [ ] Partial refresh completes in < 500ms
- [ ] Text rendering doesn't block main thread
- [ ] Display remains responsive during AI inference

### Power Tests
- [ ] Display enters idle mode after 30s
- [ ] Display enters deep sleep after 5min
- [ ] Wake from idle takes < 200ms
- [ ] Wake from deep sleep takes < 1s

---

## Known Issues & Mitigations

### Issue: Ghosting After Multiple Partial Refreshes
**Symptom:** Faint "ghost" images remain after many partial refreshes  
**Mitigation:** Force full refresh every 15 partial refreshes  
**Status:** To be tested

### Issue: Slow Refresh Interrupting Dialogue Flow
**Symptom:** User frustrated by 1-2 second delays during conversation  
**Mitigation:** 
- Use partial refresh for incremental text (faster)
- Display "Thinking..." status before AI responds (manages expectations)
- Consider buffering AI responses and displaying all at once  
**Status:** Design decision pending real-world testing

### Issue: SPI Communication Errors on Long Sessions
**Symptom:** Occasional SPI timeout errors after hours of operation  
**Mitigation:** 
- Implement retry logic in SPI communication
- Periodically reset display connection (every 24 hours)  
**Status:** To be monitored

---

## Resources

### Documentation
- [Waveshare E-Paper Documentation](https://www.waveshare.com/wiki/Main_Page#E-Paper)
- [Radxa Rock 5B+ GPIO Pinout](https://wiki.radxa.com/Rock5/hardware/5b)
- [Python Pillow (PIL) Documentation](https://pillow.readthedocs.io/)

### Example Code
- [Waveshare Python Examples](https://github.com/waveshare/e-Paper/tree/master/RaspberryPi_JetsonNano/python)
- [IT8951 Driver (Generic)](https://github.com/GregDMeyer/IT8951)

### Community Resources
- Reddit: r/eink, r/Radxa
- Waveshare Forum (product-specific support)

---

## Notes for Future Improvement

**After Phase 1 (Hardware Testing):**
- Document actual SPI pins used on Radxa Rock 5B+
- Update initialization code with real device model
- Add photos of hardware setup
- Document any jumper/configuration requirements

**After Phase 3 (Text Management):**
- Consider adding text highlighting for key philosophical terms
- Explore multi-column layout for larger displays
- Add support for basic formatting (bold for speaker names)

**After Phase 5 (Power Management):**
- Measure and document actual power consumption in each state
- Optimize wake latency if > 200ms
- Consider using display's built-in partial refresh buffer (if available)

---

**Last Updated:** November 9, 2025  
**Status:** Specification complete, awaiting hardware arrival  
**Next Steps:** Order e-ink display, test SPI communication on Radxa Rock 5B+
