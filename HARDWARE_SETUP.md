# The Whetstone - Hardware Setup Guide

**Complete assembly and configuration documentation**

---

## Table of Contents

1. [Bill of Materials](#bill-of-materials)
2. [E-Ink Display Connection](#e-ink-display-connection)
3. [GPIO Button Wiring](#gpio-button-wiring)
4. [Audio Hardware Integration](#audio-hardware-integration)
5. [System Assembly](#system-assembly)
6. [Software Configuration](#software-configuration)
7. [Testing & Validation](#testing--validation)

---

## Bill of Materials

### Core Components

| Component | Specification | Quantity | Notes |
|-----------|---------------|----------|-------|
| **Main Board** | Radxa ROCK 5B+ (24GB LPDDR5) | 1 | Primary compute platform |
| **Storage** | NVMe M.2 2280 SSD | 1 | OS and model storage |
| **Wireless** | Intel AX210 M.2 E-Key | 1 | Wi-Fi 6 + Bluetooth 5.x |
| **Display** | Waveshare 2.9" e-Paper Module (296×128) | 1 | SPI interface, Rev 2.1 |
| **Cooling** | Radxa 4012 Heatsink/Fan | 1 | Mandatory for sustained AI workload |
| **Microphone** | USB Conference Microphone (omnidirectional) | 1 | Voice input |
| **Speaker** | Adafruit 4W USB Speaker | 1 | Audio output (to be disassembled) |
| **Buttons** | LED-illuminated tactile momentary switches | 3 | Page Up, Page Down, Listen |
| **Power Supply** | USB-C PD (5V/5A minimum) | 1 | 25W recommended |

### Additional Hardware

| Component | Specification | Quantity | Notes |
|-----------|---------------|----------|-------|
| MicroSD Card | 32GB+ (for Armbian installation) | 1 | Temporary, OS moves to NVMe |
| Jumper Wires | Female-to-Female, 20cm | 20+ | GPIO connections |
| Breadboard | Half-size or full-size | 1 | Testing phase only |
| Resistors | 220Ω (for button LEDs) | 3 | Current limiting |
| Resistors | 10kΩ pull-up/pull-down | 3 | Button debouncing |
| 3D Printed Case | Custom vertical cylinder design | 1 | OpenSCAD file (TBD) |

---

## E-Ink Display Connection

### Display Specifications

**Waveshare 2.9inch e-Paper Module**
- **Resolution:** 296×128 pixels (landscape orientation)
- **Interface:** SPI (3-line or 4-line mode selectable)
- **Operating Voltage:** 3.3V/5V compatible
- **Refresh Time:** ~2 seconds (full), <1 second (partial)
- **Power Consumption:** <5mA active, <0.1mA standby
- **Viewing Angle:** 170° (paper-like)

### SPI Pin Functions

| Pin Name | Function | Signal Type |
|----------|----------|-------------|
| **VCC** | Power supply | 3.3V or 5V |
| **GND** | Ground | Ground |
| **DIN** | SPI data input (MOSI) | SPI |
| **CLK** | SPI clock | SPI |
| **CS** | Chip select | Active low |
| **DC** | Data/Command selection | GPIO |
| **RST** | Reset | Active low |
| **BUSY** | Busy status output | Active low |

### Radxa ROCK 5B+ GPIO Mapping

**Using SPI3 Bus (40-pin GPIO Header)**

| E-Ink Pin | Radxa GPIO | Physical Pin | Function |
|-----------|------------|--------------|----------|
| VCC | 3.3V Power | Pin 1 | Power supply (3.3V recommended) |
| GND | Ground | Pin 6 | Ground reference |
| DIN | GPIO4_A6 (SPI3_MOSI) | Pin 19 | SPI Master Out, Slave In |
| CLK | GPIO4_A7 (SPI3_CLK) | Pin 23 | SPI Clock |
| CS | GPIO4_B1 (SPI3_CS0) | Pin 24 | SPI Chip Select 0 |
| DC | GPIO3_C4 | Pin 18 | Data/Command select (any GPIO) |
| RST | GPIO3_C5 | Pin 22 | Reset control (any GPIO) |
| BUSY | GPIO3_C6 | Pin 16 | Busy status input (any GPIO) |

### Wiring Diagram (Text Representation)

```
Radxa ROCK 5B+ (40-pin GPIO Header)
┌─────────────────────────────────┐
│ Pin 1  (3.3V)     ──────────────┼──> VCC   │
│ Pin 6  (GND)      ──────────────┼──> GND   │
│ Pin 19 (SPI3_MOSI)──────────────┼──> DIN   │  Waveshare
│ Pin 23 (SPI3_CLK) ──────────────┼──> CLK   │  2.9" e-Paper
│ Pin 24 (SPI3_CS0) ──────────────┼──> CS    │  Module
│ Pin 18 (GPIO3_C4) ──────────────┼──> DC    │
│ Pin 22 (GPIO3_C5) ──────────────┼──> RST   │
│ Pin 16 (GPIO3_C6) ──────────────┼──> BUSY  │
└─────────────────────────────────┘
```

### Important Notes

1. **Voltage Level:** Use 3.3V power for the display (safer, lower power consumption)
2. **SPI Mode:** Configure display for 4-line SPI mode (default)
3. **Cable Length:** Keep wires short (<20cm) to minimize signal interference
4. **Shared SPI Bus:** If using other SPI devices, ensure unique CS pins
5. **BUSY Pin:** Always check BUSY status before sending new commands to prevent corruption

---

## GPIO Button Wiring

### Button Functions

| Button # | Function | LED Color | Purpose |
|----------|----------|-----------|---------|
| **Button 1** | Page Up | Blue | Scroll conversation history upward |
| **Button 2** | Page Down | Blue | Scroll conversation history downward |
| **Button 3** | Listen (PTT) | Red | Push-to-talk voice input trigger |

### Button Hardware Schematic

Each button requires:
- **1x LED-illuminated tactile switch** (normally open)
- **1x 220Ω resistor** (LED current limiting)
- **1x 10kΩ resistor** (pull-down for button input)

```
                    3.3V
                     │
                     │
                   ┌─┴─┐
                   │220Ω│  (LED current limit)
                   └─┬─┘
                     │
                    LED (in switch housing)
                     │
   GPIO_LED ─────────┤
                     │
                    GND

   
                    3.3V
                     │
                  ┌──┴──┐
                  │  SW  │  (Tactile switch)
                  └──┬──┘
                     │
   GPIO_BTN ─────────┼──────┬──> To Radxa GPIO input
                     │      │
                   ┌─┴─┐  ┌─┴─┐
                   │10kΩ│  │   │  (Pull-down)
                   └─┬─┘  │   │
                     │    │   │
                    GND   └───┘
```

### GPIO Pin Assignments

| Button | Button GPIO | LED GPIO | Physical Pin (Button) | Physical Pin (LED) |
|--------|-------------|----------|----------------------|-------------------|
| **Page Up** | GPIO3_D0 | GPIO3_D1 | Pin 11 | Pin 13 |
| **Page Down** | GPIO3_D2 | GPIO3_D3 | Pin 15 | Pin 29 |
| **Listen (PTT)** | GPIO3_D4 | GPIO3_D5 | Pin 31 | Pin 33 |

### Button State Logic

**Button Input (Pull-down configuration):**
- **LOW (0V):** Button not pressed (default state)
- **HIGH (3.3V):** Button pressed

**LED Output:**
- **LOW (0V):** LED off
- **HIGH (3.3V):** LED on (current-limited to ~15mA)

### Software Debouncing

Implement 50ms debounce delay in software to prevent false triggers:

```python
import time

def read_button_with_debounce(gpio_pin, debounce_time=0.05):
    """
    Read button state with software debouncing.
    Returns True if button is pressed and held for debounce_time.
    """
    if gpio_pin.value:  # Initial press detected
        time.sleep(debounce_time)  # Wait for bounce to settle
        if gpio_pin.value:  # Still pressed after debounce
            return True
    return False
```

---

## Audio Hardware Integration

### Microphone

**Type:** USB conference microphone (omnidirectional)

**Connection:**
- Plug directly into Radxa USB 3.0 port
- No GPIO wiring required
- Will appear as `/dev/audio` device in Armbian

**Specifications:**
- **Polar Pattern:** Omnidirectional (360° pickup)
- **Frequency Response:** 100Hz - 16kHz (voice optimized)
- **Sample Rate:** 48kHz (Whisper compatible)
- **Interface:** USB Audio Class 1.0/2.0 (plug-and-play)

**Testing:**
```bash
# List audio input devices
arecord -l

# Test recording (5 seconds)
arecord -D hw:1,0 -f cd -d 5 test.wav

# Playback test
aplay test.wav
```

### Speaker

**Type:** Adafruit 4W USB Speaker (to be disassembled)

**Integration Plan:**
1. Disassemble USB speaker housing
2. Mount speaker driver and amp board inside Whetstone case
3. Retain USB connection to Radxa
4. Position speaker driver for optimal acoustic projection

**Specifications:**
- **Power:** 4W RMS
- **Impedance:** 4Ω
- **Frequency Response:** 250Hz - 18kHz
- **Interface:** USB Audio (plug-and-play)

**Testing:**
```bash
# List audio output devices
aplay -l

# Test playback
speaker-test -c 2 -t wav

# Set as default output
sudo nano /etc/asound.conf
# Add: pcm.!default { type hw; card 1; }
```

---

## System Assembly

### Step 1: Prepare the Radxa Board

1. **Install heatsink/fan:**
   - Apply thermal paste to RK3588 SoC
   - Mount Radxa 4012 heatsink with provided screws
   - Connect 4-pin fan header to PWM fan connector

2. **Install NVMe SSD:**
   - Remove M.2 M-Key slot cover
   - Insert NVMe drive at 30° angle
   - Press down and secure with screw

3. **Install Intel AX210 Wi-Fi card:**
   - Remove M.2 E-Key slot cover
   - Insert AX210 card at 30° angle
   - Connect antenna cables (black = AUX, white = MAIN)
   - Press down and secure with screw

### Step 2: Install Armbian to NVMe

1. **Download Armbian:**
   - Get Armbian Desktop (XFCE) for ROCK 5B+
   - URL: [armbian.com/rock-5b-plus](https://www.armbian.com/rock-5b-plus/)

2. **Flash to MicroSD:**
   ```bash
   # Windows (use Rufus or Win32DiskImager)
   # Linux/Mac:
   sudo dd if=Armbian_*.img of=/dev/sdX bs=4M status=progress
   ```

3. **First Boot (from SD):**
   - Insert SD card
   - Connect HDMI, keyboard, mouse
   - Power on Radxa
   - Follow Armbian setup wizard (create user, set timezone)

4. **Transfer OS to NVMe:**
   ```bash
   # Run Armbian config utility
   sudo armbian-config
   
   # Navigate to: System → Install → Install to NVMe
   # Select filesystem: ext4
   # Wait for transfer (~10 minutes)
   # Reboot and remove SD card
   ```

### Step 3: Configure Wi-Fi and Bluetooth

```bash
# Enable Wi-Fi
nmcli device wifi list
nmcli device wifi connect "SSID" password "PASSWORD"

# Enable Bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
bluetoothctl
# > power on
# > agent on
# > scan on
```

### Step 4: Wire E-Ink Display

Follow the [E-Ink Display Connection](#e-ink-display-connection) section above.

**Verification:**
```bash
# Check if SPI3 is available
ls /dev/spidev*
# Should show: /dev/spidev3.0

# If not present, enable SPI3 overlay
sudo armbian-config
# Navigate to: System → Hardware → spi-spidev3 → Enable
# Reboot
```

### Step 5: Wire GPIO Buttons

Follow the [GPIO Button Wiring](#gpio-button-wiring) section above.

**Verification:**
```bash
# Install GPIO utilities
sudo apt install gpiod

# List available GPIO chips
gpiodetect

# Monitor button GPIO (example: GPIO3_D0)
gpioget gpiochip3 120  # Read pin state (0 = not pressed, 1 = pressed)
```

### Step 6: Connect Audio

1. Plug USB microphone into USB 3.0 port
2. Plug USB speaker into another USB 3.0 port
3. Verify devices recognized (see Audio Hardware Integration section)

---

## Software Configuration

### Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install SPI and GPIO libraries
sudo apt install python3-spidev python3-rpi.gpio -y

# Install audio libraries
sudo apt install portaudio19-dev python3-pyaudio -y

# Install Pillow for image rendering
sudo apt install python3-pil -y
```

### Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Pull Mistral 7B Instruct model
ollama pull mistral

# Create custom Whetstone model
cd ~/The_Whetstone
ollama create whetstone-philosopher -f Modelfile
```

### Install Waveshare E-Ink Library

```bash
# Clone Waveshare e-Paper library
cd ~
git clone https://github.com/waveshare/e-Paper.git

# Install Python dependencies
cd e-Paper/RaspberryPi_JetsonNano/python
sudo python3 setup.py install

# Test display (if wired correctly)
cd examples
python3 epd_2in9_V2_test.py
```

### Install Python Dependencies for The Whetstone

```bash
cd ~/The_Whetstone

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install openai  # For Ollama API client
pip install spidev  # SPI communication
pip install RPi.GPIO  # GPIO control (or gpiod for newer approach)
pip install Pillow  # Image manipulation for e-ink
pip install pyaudio  # Audio I/O (for future Whisper/Piper)
```

### Enable Auto-Start (Optional)

```bash
# Create systemd service
sudo nano /etc/systemd/system/whetstone.service
```

**Service file contents:**
```ini
[Unit]
Description=The Whetstone Philosopher
After=network.target ollama.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/The_Whetstone
ExecStart=/home/your_username/The_Whetstone/venv/bin/python philosopher_app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable whetstone.service
sudo systemctl start whetstone.service

# Check status
sudo systemctl status whetstone.service
```

---

## Testing & Validation

### Hardware Tests

#### 1. E-Ink Display Test

```bash
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples
python3 epd_2in9_V2_test.py
```

**Expected Result:**
- Display should show Waveshare logo
- Screen should update with test patterns
- No flickering or artifacts

#### 2. GPIO Button Test

```python
#!/usr/bin/env python3
# button_test.py

import RPi.GPIO as GPIO
import time

# Button GPIO pins (BCM numbering)
BUTTON_PINS = {
    'page_up': 120,    # GPIO3_D0
    'page_down': 122,  # GPIO3_D2
    'listen': 124      # GPIO3_D4
}

GPIO.setmode(GPIO.BCM)

for name, pin in BUTTON_PINS.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("Press buttons (Ctrl+C to exit)...")

try:
    while True:
        for name, pin in BUTTON_PINS.items():
            if GPIO.input(pin):
                print(f"{name.upper()} button pressed!")
                time.sleep(0.2)  # Debounce
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nTest complete.")
```

#### 3. Audio Test

```bash
# Record 5 seconds of audio
arecord -D hw:1,0 -f cd -d 5 mic_test.wav

# Play back recording
aplay mic_test.wav

# Verify quality (should be clear, no distortion)
```

#### 4. Ollama Inference Test

```bash
# Test basic Ollama response
ollama run whetstone-philosopher "What is the meaning of life?"

# Expected: Philosophical response from Mistral 7B model
```

### Integration Test

Run the complete Whetstone system:

```bash
cd ~/The_Whetstone
source venv/bin/activate
python philosopher_app.py
```

**Test Checklist:**
- [ ] Persona selection menu displays on e-ink
- [ ] Buttons navigate persona selection
- [ ] Selected persona activates (visual confirmation)
- [ ] Text input accepted via keyboard (temporary, before voice)
- [ ] RAG searches library correctly
- [ ] Ollama generates response
- [ ] Response displays on e-ink screen (scrollable)
- [ ] Page Up/Down buttons scroll conversation history
- [ ] No memory leaks after 30+ minute session

---

## Troubleshooting

### Issue: E-Ink Display Not Detected

**Symptoms:** `/dev/spidev3.0` does not exist

**Solution:**
```bash
sudo armbian-config
# System → Hardware → spi-spidev3 → Enable
sudo reboot
```

### Issue: Buttons Not Responding

**Symptoms:** `gpioget` shows no state change when pressing buttons

**Solution:**
- Check wiring (ensure pull-down resistors are connected)
- Verify GPIO pin numbers match physical pins
- Test with multimeter (should read 3.3V when pressed)

### Issue: Audio Devices Not Recognized

**Symptoms:** `arecord -l` or `aplay -l` shows no devices

**Solution:**
```bash
# Reload USB audio drivers
sudo modprobe snd-usb-audio

# Check USB device recognition
lsusb | grep -i audio

# If still not working, try different USB port
```

### Issue: Ollama Model Loading Slowly

**Symptoms:** First inference takes >30 seconds

**Solution:**
- This is normal on first run (model loading into RAM)
- Subsequent requests should be <3 seconds
- Ensure `num_gpu 99` in Modelfile (offloads to GPU)
- Monitor RAM usage: `htop` (should have 10-15GB free after model loads)

### Issue: E-Ink Display Shows Artifacts

**Symptoms:** Ghosting, incomplete refreshes, or garbled text

**Solution:**
- Perform full refresh (not partial) periodically
- Check BUSY pin status before sending new commands
- Reduce SPI clock speed if artifacts persist
- Ensure power supply provides stable 3.3V (measure with multimeter)

---

## Next Steps

After hardware validation:

1. **Develop E-Ink UI Module** (`display_manager.py`)
   - Text rendering for 296×128 resolution
   - Conversation history pagination
   - Persona selection menu
   - Status indicators (listening, thinking, idle)

2. **Integrate Voice Interface**
   - Whisper STT (local inference)
   - Piper TTS (local synthesis)
   - Push-to-talk button handling
   - Audio pipeline optimization

3. **Build Enclosure**
   - OpenSCAD design for vertical cylinder case
   - Component mounting positions
   - Acoustic design for speaker
   - Ventilation for continuous operation

4. **Develop Phase 2 Companion App**
   - Bluetooth communication protocol
   - Project Gutenberg library sync
   - Automated Persona Forge

---

## Safety Notes

⚠️ **Electrical Safety:**
- Never connect/disconnect components while board is powered
- Use ESD wrist strap when handling components
- Double-check voltage levels before connecting (3.3V vs 5V)

⚠️ **Thermal Management:**
- Radxa 4012 heatsink/fan is **mandatory** for sustained AI workload
- Monitor temperatures: `watch -n 1 sensors` (install: `sudo apt install lm-sensors`)
- Safe operating range: 40-70°C (SoC temp under load)
- Thermal throttling begins at 85°C

⚠️ **Power Supply:**
- Use 5V/5A (25W) or higher USB-C PD power supply
- Insufficient power causes random crashes during inference
- Recommended: Official Radxa 30W USB-C adapter

---

*This hardware setup guide will be updated as we build and test The Whetstone prototype.*

*Last updated: November 9, 2025*
