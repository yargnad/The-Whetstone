# Button Interface Specification

**Component Status:** 📋 Specification Phase  
**Target Hardware:** Physical buttons connected to Radxa Rock 5B+ GPIO pins  
**Purpose:** Provide tactile control for persona selection, navigation, and voice input (PTT)

---

## Overview

The Whetstone uses physical buttons as its primary input method, creating an intentional, tactile interface that contrasts with touchscreen immediacy. Each button has a specific function designed to make the device usable without a keyboard.

**Design Philosophy:**
- **Tactile feedback** - Physical button presses create mindful interaction
- **Minimal complexity** - 4-6 buttons total, each with clear purpose
- **No visual dependency** - Can navigate by muscle memory after familiarization
- **Interruption-friendly** - PTT button works even during AI response

---

## Hardware Options

### Option 1: Discrete Tactile Buttons (Recommended for Prototyping)

**Components:**
- 4-6 individual tactile push buttons (12mm x 12mm panel-mount)
- Pull-down resistors (10kΩ) or use internal pull-down on GPIO
- Jumper wires to GPIO header

**Advantages:**
- Cheap (~$0.50 per button)
- Easy to prototype (breadboard-friendly)
- Flexible placement in enclosure
- Easy to debug (one wire per button)

**Disadvantages:**
- Requires manual wiring
- Need to design custom panel layout
- No integrated solution

**Example Part:** Adafruit Tactile Button (product #1119)

---

### Option 2: HAT with Integrated Buttons + Display

**Components:**
- Waveshare 1.3" OLED HAT (128x64 OLED + joystick + 3 buttons)
- Or similar GPIO HAT with integrated controls

**Advantages:**
- Pre-wired solution (plugs directly into GPIO header)
- Includes small OLED for status (bonus secondary display)
- Compact, integrated form factor
- Joystick provides 5 directional inputs + center press

**Disadvantages:**
- More expensive (~$15-20)
- Fixed button layout (less customization)
- Joystick may be overkill for our use case
- Display competes with main e-ink (confusing UX)

**Example Part:** Waveshare 1.3" OLED HAT for Raspberry Pi

---

### Option 3: Keypad Matrix (Future Consideration)

**Components:**
- 3x4 or 4x4 membrane keypad
- GPIO matrix scanning

**Advantages:**
- Numeric input for advanced features (channel selection, etc.)
- Familiar interface (like a phone)
- Scalable (add more functions via menu system)

**Disadvantages:**
- Overcomplicates initial design
- Requires matrix scanning logic (more complex GPIO handling)
- Doesn't align with "minimal tactile" philosophy

**Status:** Not recommended for Phase 1

---

## Button Layout (Recommended Configuration)

### Minimal 4-Button Layout

```
┌─────────────────────────┐
│                         │
│     E-Ink Display       │
│                         │
│                         │
└─────────────────────────┘
         
    [▲]  UP        Scroll up / Navigate menu up
    [▼]  DOWN      Scroll down / Navigate menu down
    [●]  SELECT    Confirm selection / Enter menu
    [◉]  PTT       Push-to-talk (hold to speak)
```

**Rationale:**
- **UP/DOWN:** Navigate personas, scroll conversation history
- **SELECT:** Confirm persona choice, enter/exit menus
- **PTT:** Voice input (hold to record, release to send)

---

### Extended 6-Button Layout (Recommended)

```
┌─────────────────────────┐
│                         │
│     E-Ink Display       │
│                         │
│                         │
└─────────────────────────┘
         
    [◀]  LEFT      Previous persona / Menu back
    [▶]  RIGHT     Next persona / Menu forward
    [▲]  UP        Scroll up / Adjust volume up
    [▼]  DOWN      Scroll down / Adjust volume down
    [●]  SELECT    Confirm selection / Power menu
    [◉]  PTT       Push-to-talk (hold to speak)
```

**Rationale:**
- **LEFT/RIGHT:** Faster persona switching, menu navigation
- **UP/DOWN:** Dual purpose (scroll + volume control in voice mode)
- **SELECT:** Multi-function (confirm, long-press for power/settings)
- **PTT:** Dedicated voice input

---

## GPIO Pin Assignment (Radxa Rock 5B+)

### Recommended GPIO Pins

**Pin Selection Criteria:**
- Use standard GPIO pins (avoid special-function pins like SPI, I2C unless necessary)
- Group pins together for clean wiring
- Leave SPI pins free for e-ink display

**Proposed Mapping:**

| Button | GPIO Pin | Physical Pin | Notes |
|--------|----------|--------------|-------|
| UP | GPIO3_A4 (PIN 11) | Pin 11 | Standard GPIO |
| DOWN | GPIO3_A5 (PIN 13) | Pin 13 | Standard GPIO |
| LEFT | GPIO3_A6 (PIN 15) | Pin 15 | Standard GPIO |
| RIGHT | GPIO3_A7 (PIN 29) | Pin 29 | Standard GPIO |
| SELECT | GPIO3_B0 (PIN 31) | Pin 31 | Standard GPIO |
| PTT | GPIO3_B1 (PIN 33) | Pin 33 | Standard GPIO |
| GND | GND | Pin 9, 14, 20, 25, etc. | Common ground for all buttons |

**Note:** Actual GPIO numbers may vary depending on Radxa's GPIO mapping. Verify with:
```bash
cat /sys/kernel/debug/gpio
```

---

## Button Wiring

### Circuit Design (Per Button)

**Option A: Internal Pull-Down (Recommended)**
```
GPIO Pin ──────┐
               │
            [Button]
               │
              GND
```

- Configure GPIO pin with internal pull-down resistor (software)
- Button press pulls pin HIGH
- No external resistors needed

**Option B: External Pull-Down**
```
         3.3V
          │
       [Button]
          │
GPIO Pin ─┤
          │
        [10kΩ]
          │
         GND
```

- External 10kΩ pull-down resistor holds pin LOW when button not pressed
- Button press pulls pin HIGH
- More reliable if GPIO doesn't have internal pull-down

**Chosen Method:** Internal pull-down (simpler wiring, fewer components)

---

## Button Event Handling

### Event Types

1. **Short Press** - Quick tap (< 0.5 seconds)
   - Example: UP button → scroll up one line

2. **Long Press** - Held down (> 1 second)
   - Example: SELECT button → open power menu

3. **Hold** - Continuous press (for PTT)
   - Example: PTT button → record while held, stop when released

4. **Double Press** - Two quick presses (< 0.3 seconds apart)
   - Example: SELECT double-press → quick action (optional future feature)

---

### Debouncing Strategy

**Problem:** Mechanical buttons "bounce" when pressed (rapid on/off signals)

**Software Debouncing:**
```python
import time

class Button:
    def __init__(self, pin, debounce_time=0.05):
        self.pin = pin
        self.debounce_time = debounce_time  # 50ms
        self.last_press_time = 0
        self.is_pressed = False
    
    def check_press(self):
        """
        Returns True if button is newly pressed (debounced)
        """
        current_state = GPIO.input(self.pin)
        current_time = time.time()
        
        if current_state == GPIO.HIGH:
            if not self.is_pressed:
                # Button just pressed
                if current_time - self.last_press_time > self.debounce_time:
                    self.is_pressed = True
                    self.last_press_time = current_time
                    return True
        else:
            self.is_pressed = False
        
        return False
```

**Hardware Debouncing (Alternative):**
- Add 0.1µF capacitor across button terminals
- Slower but more reliable
- Recommended for noisy environments

---

## Button Function Mapping

### Mode: Persona Selection

| Button | Action | Result |
|--------|--------|--------|
| UP | Short press | Highlight previous persona |
| DOWN | Short press | Highlight next persona |
| LEFT | Short press | Jump to first persona |
| RIGHT | Short press | Jump to last persona |
| SELECT | Short press | Confirm selection, enter conversation mode |
| PTT | N/A | Disabled in this mode |

---

### Mode: Conversation (Text Display)

| Button | Action | Result |
|--------|--------|--------|
| UP | Short press | Scroll conversation up 1 line |
| UP | Long press | Scroll conversation up 5 lines |
| DOWN | Short press | Scroll conversation down 1 line |
| DOWN | Long press | Scroll conversation down 5 lines |
| LEFT | Short press | Return to persona selection |
| RIGHT | Short press | Open settings menu (future) |
| SELECT | Short press | No action (reserved) |
| SELECT | Long press | Open power menu (sleep/shutdown) |
| PTT | Hold | Start voice recording |

---

### Mode: Conversation (Voice Active)

| Button | Action | Result |
|--------|--------|--------|
| UP | Short press | Volume up |
| DOWN | Short press | Volume down |
| LEFT | Short press | Cancel current response |
| RIGHT | Short press | N/A |
| SELECT | Short press | Pause/resume AI response (future) |
| PTT | Hold | Record voice input |
| PTT | Release | Stop recording, send to Whisper STT |

---

### Mode: Power Menu

| Button | Action | Result |
|--------|--------|--------|
| UP | Short press | Highlight "Sleep" |
| DOWN | Short press | Highlight "Shutdown" |
| SELECT | Short press | Confirm selection |
| LEFT | Short press | Cancel, return to conversation |

---

## GPIO Setup (Python Implementation)

### Using `gpiod` Library (Modern Approach)

**Installation:**
```bash
sudo apt-get install python3-libgpiod
pip3 install gpiod
```

**Initialization:**
```python
import gpiod
import time

# GPIO chip (usually 'gpiochip0' on Radxa)
chip = gpiod.Chip('gpiochip0')

# Define button GPIO line numbers (update with actual Radxa mapping)
BUTTON_UP = 68      # GPIO3_A4
BUTTON_DOWN = 69    # GPIO3_A5
BUTTON_LEFT = 70    # GPIO3_A6
BUTTON_RIGHT = 71   # GPIO3_A7
BUTTON_SELECT = 72  # GPIO3_B0
BUTTON_PTT = 73     # GPIO3_B1

# Request GPIO lines for button input
button_lines = chip.get_lines([BUTTON_UP, BUTTON_DOWN, BUTTON_LEFT, BUTTON_RIGHT, BUTTON_SELECT, BUTTON_PTT])
button_lines.request(consumer="whetstone", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN)
```

---

### Button Manager Class

```python
class ButtonManager:
    def __init__(self, chip_name='gpiochip0'):
        self.chip = gpiod.Chip(chip_name)
        
        # Button GPIO line numbers
        self.pins = {
            'up': 68,
            'down': 69,
            'left': 70,
            'right': 71,
            'select': 72,
            'ptt': 73
        }
        
        # Request all button lines
        self.lines = self.chip.get_lines(list(self.pins.values()))
        self.lines.request(consumer="whetstone", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN)
        
        # Button state tracking
        self.button_states = {name: False for name in self.pins.keys()}
        self.press_start_times = {name: 0 for name in self.pins.keys()}
        
        # Callbacks for each button
        self.callbacks = {
            'up': {'short': None, 'long': None},
            'down': {'short': None, 'long': None},
            'left': {'short': None, 'long': None},
            'right': {'short': None, 'long': None},
            'select': {'short': None, 'long': None},
            'ptt': {'hold': None, 'release': None}
        }
    
    def register_callback(self, button_name, event_type, callback):
        """
        Register a callback function for button events
        event_type: 'short', 'long', 'hold', 'release'
        """
        self.callbacks[button_name][event_type] = callback
    
    def poll_buttons(self):
        """
        Call this in main loop to check button states and trigger callbacks
        """
        values = self.lines.get_values()
        
        for i, (name, pin) in enumerate(self.pins.items()):
            current_state = values[i] == 1  # HIGH when pressed
            previous_state = self.button_states[name]
            
            # Button just pressed
            if current_state and not previous_state:
                self.press_start_times[name] = time.time()
                self.button_states[name] = True
                
                # PTT special case: trigger 'hold' callback immediately
                if name == 'ptt' and self.callbacks[name]['hold']:
                    self.callbacks[name]['hold']()
            
            # Button just released
            elif not current_state and previous_state:
                self.button_states[name] = False
                press_duration = time.time() - self.press_start_times[name]
                
                # PTT special case: trigger 'release' callback
                if name == 'ptt':
                    if self.callbacks[name]['release']:
                        self.callbacks[name]['release']()
                else:
                    # Determine short vs long press
                    if press_duration < 1.0:
                        # Short press
                        if self.callbacks[name]['short']:
                            self.callbacks[name]['short']()
                    else:
                        # Long press
                        if self.callbacks[name]['long']:
                            self.callbacks[name]['long']()
    
    def cleanup(self):
        """Release GPIO resources"""
        self.lines.release()
```

---

### Example Usage in Main App

```python
from button_manager import ButtonManager
from display_manager import DisplayManager

display = DisplayManager()
buttons = ButtonManager()

# Define callback functions
def on_up_short():
    print("UP pressed")
    display.scroll_conversation_up()

def on_down_short():
    print("DOWN pressed")
    display.scroll_conversation_down()

def on_select_long():
    print("SELECT long press - opening power menu")
    display.show_power_menu()

def on_ptt_hold():
    print("PTT held - start recording")
    # Start voice recording

def on_ptt_release():
    print("PTT released - stop recording")
    # Stop voice recording, send to Whisper

# Register callbacks
buttons.register_callback('up', 'short', on_up_short)
buttons.register_callback('down', 'short', on_down_short)
buttons.register_callback('select', 'long', on_select_long)
buttons.register_callback('ptt', 'hold', on_ptt_hold)
buttons.register_callback('ptt', 'release', on_ptt_release)

# Main loop
try:
    while True:
        buttons.poll_buttons()
        time.sleep(0.01)  # Poll every 10ms
except KeyboardInterrupt:
    buttons.cleanup()
```

---

## Power Management Integration

### Wake from Sleep on Button Press

**Challenge:** Display may be in sleep mode; button press should wake it.

**Solution:** Use GPIO interrupt (edge-triggered) to wake system.

```python
import gpiod

# Configure PTT button to trigger interrupt on rising edge (button press)
ptt_line = chip.get_line(BUTTON_PTT)
ptt_line.request(consumer="whetstone_wake", type=gpiod.LINE_REQ_EV_RISING_EDGE)

# In main loop or separate thread
events = ptt_line.event_wait(timeout=1.0)  # Wait up to 1 second
if events:
    event = ptt_line.event_read()
    if event.type == gpiod.LineEvent.RISING_EDGE:
        print("Button pressed - waking display")
        display.wake()
```

**Alternative:** Use Linux `evdev` for system-level button handling (more complex, but supports true hardware interrupts)

---

## Button Placement in Enclosure

### Ergonomics Considerations

**Right-Handed Primary Use:**
- PTT button on right side (thumb position)
- Navigation buttons (UP/DOWN/LEFT/RIGHT) on front face
- SELECT button on front or top

**Left-Handed Alternative:**
- PTT button on left side
- Symmetrical button layout ideal

**Button Spacing:**
- Minimum 15mm center-to-center to avoid accidental presses
- Tactile differentiation (PTT button larger or different texture)

**Accessibility:**
- Buttons should be operable with gloves (12mm+ size)
- Raised labels or Braille dots for blind/low-vision users (future enhancement)

---

## Development Roadmap

### Phase 1: GPIO Testing ✅ Target
- [ ] Confirm GPIO pins on Radxa Rock 5B+
- [ ] Wire one test button to GPIO
- [ ] Test button press detection (simple script)
- [ ] Verify internal pull-down configuration

### Phase 2: Button Manager Implementation
- [ ] Implement ButtonManager class
- [ ] Add debouncing logic
- [ ] Test short press, long press, and hold detection
- [ ] Integrate with display manager (scroll test)

### Phase 3: Multi-Button Support
- [ ] Wire all 6 buttons
- [ ] Test simultaneous button presses (should ignore)
- [ ] Verify each button triggers correct callback

### Phase 4: PTT Integration
- [ ] Connect PTT button to voice recording logic
- [ ] Test hold-to-record, release-to-send workflow
- [ ] Add visual feedback on display ("Listening...")

### Phase 5: Power Integration
- [ ] Implement wake-from-sleep on button press
- [ ] Test SELECT long-press → power menu
- [ ] Add shutdown/reboot functionality

---

## Testing Checklist

### Hardware Tests
- [ ] All buttons physically installed and accessible
- [ ] Button presses register in GPIO test script
- [ ] No cross-talk between buttons (only one triggers at a time)
- [ ] Buttons work reliably after 100+ presses

### Functionality Tests
- [ ] UP/DOWN scroll conversation correctly
- [ ] LEFT/RIGHT navigate persona selection
- [ ] SELECT confirms choices
- [ ] PTT triggers voice recording when held
- [ ] Long press detected correctly (> 1 second)

### Edge Cases
- [ ] Multiple buttons pressed simultaneously (should ignore or handle gracefully)
- [ ] Very rapid button presses (debouncing works)
- [ ] Button held for extended period (> 10 seconds) doesn't crash
- [ ] Wake from sleep via button press works reliably

---

## Known Issues & Mitigations

### Issue: GPIO Pin Conflicts with Other HATs
**Symptom:** E-ink display and buttons fighting for same GPIO pins  
**Mitigation:** Carefully map pins to avoid SPI, I2C, and display control pins  
**Status:** Preventable with proper pin planning

### Issue: Mechanical Button Bounce
**Symptom:** Single press registers multiple times  
**Mitigation:** Software debouncing (50ms delay)  
**Status:** Standard solution

### Issue: PTT Button Stuck in Pressed State
**Symptom:** Voice recording doesn't stop  
**Mitigation:** Timeout after 30 seconds, force-stop recording  
**Status:** Safety feature to be implemented

---

## Resources

### Documentation
- [Radxa Rock 5B+ GPIO Pinout](https://wiki.radxa.com/Rock5/hardware/5b)
- [libgpiod Documentation](https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git/about/)
- [Python gpiod Bindings](https://pypi.org/project/gpiod/)

### Hardware Suppliers
- [Adafruit Tactile Buttons](https://www.adafruit.com/category/235)
- [SparkFun Buttons & Switches](https://www.sparkfun.com/categories/145)
- [Waveshare HATs](https://www.waveshare.com/product/raspberry-pi.htm)

---

## Notes for Future Improvement

**After Phase 1:**
- Document actual GPIO pin numbers used (Radxa-specific)
- Add photos of button wiring
- Note any surprises or gotchas

**After Phase 3:**
- Consider adding LED indicators next to buttons for visual feedback
- Explore capacitive touch alternative (no mechanical wear)

**After Phase 5:**
- Measure actual debounce time needed (may be < 50ms)
- Add haptic feedback (vibration motor) for button presses (future)

---

**Last Updated:** November 9, 2025  
**Status:** Specification complete, awaiting hardware arrival  
**Next Steps:** Test GPIO button detection on Radxa Rock 5B+
