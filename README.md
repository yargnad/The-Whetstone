# The Whetstone

**Act II of The Authentic Rebellion Framework**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

> "Cognitive Strengthening - Learning to think again"

## Overview

The Whetstone is a **physical AI device** that acts as a Socratic interlocutor—challenging assumptions, exposing contradictions, and helping you reason toward clarity about your beliefs and values. Unlike apps or cloud services, The Whetstone is a tangible object that stays in one place, creating intentional space for philosophical dialogue.

**Status:** 🔨 Hardware Ordered (Radxa Rock 5B+ 24GB)

**Core Philosophy:** Privacy-first cognitive strengthening through local AI inference. Your conversations never leave your home. Your thinking process is sovereign.

---

## Why Physical?

- **Presence over portability** - It stays in one place; you go to it intentionally (ritual, not distraction)
- **Privacy by architecture** - Local-first AI; conversations never leave your home or enter the cloud
- **Tactile ritual** - Physical objects create habits (like journaling, but dialectical)
- **Sovereignty** - You own the hardware, the software, and your thoughts. Can't be remotely disabled, paywalled, or censored

---

## Hardware Specifications

### Target Platform: Radxa Rock 5B+ (24GB RAM)

**Why this board?**
- **24GB RAM**: Required for comfortable local inference of Mistral 7B Q4_K_M quantized model (~6-8GB) plus OS overhead and RAG operations
- **Rockchip RK3588**: Octa-core ARM (4x Cortex-A76 @ 2.4GHz + 4x Cortex-A55 @ 1.8GHz)
- **NPU acceleration**: 6 TOPS for potential STT/TTS optimization
- **Power efficiency**: ARM architecture suitable for always-on device
- **Cost**: ~$120-150 (board only)

**Additional Hardware Needed:**
- MicroSD card (32GB+ for OS + model storage)
- Power supply (USB-C PD 5V/3A or higher)
- Heatsink/fan (passive cooling recommended for sustained inference)
- **E-ink display** (low power, readable in any light, philosophical aesthetic)
- **Physical buttons** (persona selection, push-to-talk, navigation)
- **USB microphone + speaker** for voice interface
- Optional: Display + keyboard for initial setup (development only)

---

## Software Architecture

### Core Components

#### 1. **Ollama** (LLM Runtime)
- Manages local Mistral Instruct 7B inference
- Model: `mistral-instruct-7b-v0.3` (Q4_K_M quantized, ~4GB)
- OpenAI-compatible API on `localhost:11434`
- Configured via `Modelfile` for GPU offloading

#### 2. **Persona-Based RAG System**
- **Philosophy Library**: Curated texts (Plato, Nietzsche, Stoics, Absurdism)
- **Keyword Search**: Simple but effective matching for philosophical context
- **Library Filtering**: Each persona restricts search to relevant texts
  - Example: "Plato" persona only searches files prefixed with `plato_`
- **Context Injection**: Top 3 relevant snippets fed into LLM prompt

#### 3. **Philosopher Personas**
- **Benevolent Absurdist**: Empathy + reason + Absurdist philosophy (all texts)
- **Socratic Inquirer**: Rigorous questioning, definitional clarity (Plato texts)
- **Stoic Guide**: Dichotomy of control, virtue ethics, tranquility (all texts)
- **Plato**: Direct dialogue as Plato would speak (Plato texts only)
- **Nietzsche**: Provocative, aphoristic, challenging (Nietzsche texts only)

#### 4. **Voice Interface** (Roadmap)
- **STT**: Whisper (OpenAI's speech-to-text, local inference)
- **TTS**: Piper (fast, lightweight, privacy-preserving text-to-speech)
- **Workflow**: Voice → Whisper → Text → LLM → Text → Piper → Voice

---

## Current Implementation

### What's Working (Laptop Prototype)

The `philosopher_app.py` script demonstrates:

1. ✅ **Multi-persona system** with library filtering
2. ✅ **Local Ollama integration** (Mistral 7B via OpenAI-compatible API)
3. ✅ **Philosophy library RAG** (13 texts: Plato, Nietzsche, Stoics, Absurdism)
4. ✅ **Streaming responses** for real-time dialogue feel
5. ✅ **Context-aware prompting** with persona-specific system prompts

### Philosophy Library Contents

```
philosophy_library/
├── plato_Euthyphro.txt
├── plato_The Apology.txt
├── nietzsche_Beyond Good and Evil.txt
├── nietzsche_The Antichrist.txt
├── nietzsche_The Birth of Tragedy.txt
├── nietzsche_The Genealogy of Morals.txt
├── nietzsche_The Twilight of the Idols.txt
├── nietzsche_zarathustra.txt
├── Meditations by Marcus Aurelius.txt
├── A Guide to Stoicism by St. George William Joseph Stock.txt
├── Roman Stoicism by Edward Vernon Arnold.txt
├── The Golden Sayings of Epictetus.txt
└── absurdism_notes.txt
```

---

## The Philosophical Immune System

Built-in ethical guardrails that challenge reasoning:

1. **Epistemic Humility** - Identify your uncertainties before answering
2. **Bias Detection** - Check for hidden assumptions about superiority/inferiority
3. **Consequentialist Gate** - Who benefits? Who is harmed?
4. **Deontological Gate** - Is this universalizable? (Kantian categorical imperative)
5. **Virtue Ethics Gate** - Does this cultivate excellence or vice?
6. **Dialectical Mode** - Steel-man opposing views before critiquing

These aren't hardcoded censorship—they're prompts that ask the user to examine their own thinking from multiple ethical frameworks.

---

## Deployment Guide

### Prerequisites

1. **Radxa Rock 5B+ (24GB)** with Armbian or Ubuntu 22.04 ARM64
2. **Ollama installed** ([ollama.com](https://ollama.com))
3. **Python 3.10+** with `openai` library
4. **Philosophy library texts** in `philosophy_library/` directory

### Installation Steps

#### 1. Install Ollama on Radxa

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### 2. Create Custom Model

```bash
# Create Modelfile (already included in repo)
# Modelfile contents:
# FROM mistral
# PARAMETER num_gpu 99

ollama create whetstone-philosopher -f Modelfile
```

#### 3. Clone Repository

```bash
git clone https://github.com/yargnad/The-Whetstone.git
cd The-Whetstone
```

#### 4. Install Python Dependencies

```bash
pip install openai
```

#### 5. Run The Whetstone

```bash
python philosopher_app.py
```

#### 6. Select Persona and Start Dialogue

```
Please select a persona for this session:
  1: Benevolent Absurdist (All Texts)
  2: Socratic Inquirer
  3: Stoic Guide
  4: Plato
  5: Nietzsche
Enter the number of your choice: 2

--- Session starting with Socratic Inquirer persona ---
AI is ready. Type your question and press Enter. Type 'quit' to exit.

You: What is justice?
Socratic Inquirer: [begins rigorous questioning process...]
```

---

## Roadmap

### Phase 1: E-ink Display + Button Interface (Next)
- [ ] Select e-ink display (Waveshare, Good Display, or similar)
- [ ] Design button layout (persona selection, PTT, navigation, power)
- [ ] Build UI framework for e-ink (low refresh rate, high readability)
- [ ] Implement persona selection via buttons (no keyboard needed)
- [ ] Display conversation history on screen (text-based dialogue)
- [ ] Power management (sleep mode when inactive, wake on button press)

### Phase 2: Voice Interface
- [ ] Integrate Whisper for local STT
- [ ] Integrate Piper for local TTS
- [ ] Test latency on Radxa Rock 5B+ with NPU acceleration
- [ ] Implement push-to-talk button functionality
- [ ] Display voice transcription on e-ink screen
- [ ] Add visual feedback for "listening" and "thinking" states

### Phase 3: Hardware Enclosure
- [ ] Design 3D-printable case with e-ink display mount
- [ ] Integrate speaker and microphone into enclosure
- [ ] Button placement ergonomics (one-handed operation)
- [ ] Ventilation for sustained inference heat dissipation

### Phase 3: Enhanced RAG
- [ ] Vector database for semantic search (ChromaDB or similar)
- [ ] Personal context tracking (previous dialogues)
- [ ] Expandable library (user-added texts)

### Phase 4: Multi-User Support
- [ ] Profile switching (different users, different conversation histories)
- [ ] Optional anonymization (conversations stored without identifiers)

### Phase 5: Open-Source Hardware Kit
- [ ] Bill of materials (BOM)
- [ ] Assembly guide
- [ ] Software image for one-click deployment
- [ ] Documentation for adding new personas

---

## Design Philosophy

### Local-First

**No cloud dependencies.** The Whetstone operates entirely offline. Your philosophical explorations are private by default. No telemetry, no tracking, no data mining.

### Forkable by Design

This project is **GPL v3.0** licensed. Anyone can:
- Fork the code and modify it
- Add new personas
- Create custom philosophy libraries
- Build alternative hardware enclosures
- Share improvements back to the community

### Empowerment, Not Replacement

The Whetstone doesn't think *for* you—it helps you think *better*. It's a dialectical partner, not an answer machine. The goal is **cognitive sovereignty**: developing the capacity to reason independently.

---

## Why Mistral 7B?

**Privacy commitment:** Mistral AI has a strong stance on user privacy and open-source models.

**Performance:** The 7B parameter count strikes the right balance between capability and resource requirements. The Q4_K_M quantization makes it runnable on consumer hardware while maintaining reasoning quality.

**Philosophy-appropriate:** Mistral's instruction-following and reasoning capabilities are well-suited for Socratic dialogue, not just factual Q&A.

---

## Cost Analysis

### DIY Build (~$200-280)

| Component | Cost (USD) |
|-----------|------------|
| Radxa Rock 5B+ (24GB) | $120-145 |
| MicroSD Card (64GB) | $10-15 |
| Power Supply | $10-15 |
| Heatsink/Fan | $5-10 |
| **E-ink Display (4.2"-7.5")** | **$30-60** |
| **Physical Buttons (4-6 tactile switches)** | **$5-10** |
| USB Microphone | $15-25 |
| USB Speaker | $15-25 |
| **Total** | **$210-305** |

**Why expensive?** The 24GB RAM requirement. Mistral 7B quantized needs ~6-8GB for inference, plus OS overhead. Cheaper boards (8GB/16GB) would struggle with sustained dialogue.

**Is it worth it?** If you value:
- Privacy (conversations never leave your home)
- Sovereignty (you own the hardware and software)
- Longevity (device works forever, no subscriptions)
- Cognitive empowerment (developing independent thinking)

Then yes. This is a **tool for life**, not a monthly SaaS fee.

---

## FAQ

### Q: Why not just use ChatGPT?

**A:** ChatGPT is cloud-based (your conversations are stored on OpenAI servers), requires internet, can be paywalled or censored, and optimizes for engagement rather than philosophical rigor. The Whetstone is local-first, private, offline-capable, and designed specifically for Socratic dialogue.

### Q: Can I run this on a Raspberry Pi?

**A:** Not recommended. Even the Raspberry Pi 5 (8GB) lacks sufficient RAM for comfortable Mistral 7B inference. The Radxa Rock 5B+ (24GB) is the minimum viable platform for this use case.

### Q: Can I add my own philosophy texts?

**A:** Yes! Simply add `.txt` files to the `philosophy_library/` directory. You can also create custom personas with library filters in `philosopher_app.py`.

### Q: Will this work on other ARM boards?

**A:** Potentially. Any ARM64 board with 24GB+ RAM and Ollama support should work. The Radxa Rock 5B+ is recommended due to its NPU (useful for future Whisper/Piper optimization).

### Q: What about privacy of voice data?

**A:** Whisper and Piper both run **locally**. Voice data never leaves the device. No cloud transcription services.

---

## Contributing

We welcome contributions:

- **Personas**: Design new philosophical personas (e.g., Kant, Aristotle, Buddha, Simone de Beauvoir)
- **Philosophy Texts**: Curate and add public domain philosophical works
- **Hardware Guides**: Document builds on alternative ARM platforms
- **Voice Interface**: Help integrate Whisper + Piper with NPU acceleration
- **Enclosure Designs**: Create 3D-printable cases or laser-cut designs

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon).

---

## Part of The Authentic Rebellion Framework

The Whetstone is **Act II** of a four-act movement for building ethical AI infrastructure:

- **Act I: Sensus** ([GitHub](https://github.com/yargnad/Sensus)) — Anonymous emotional exchange to escape the Performance Prison
- **Act II: The Whetstone** (this project) — Physical AI device for Socratic cognitive strengthening
- ***The Interlude: The Crystalizer*** ([GitHub](https://github.com/yargnad/The-Crystalizer)) — Chrome extension for preserving AI conversations when platforms fail you
- **Act III: Kintsugi** ([GitHub](https://github.com/yargnad/Kintsugi)) — Public gallery for transformation stories
- **Act IV: The Lyceum Network** ([GitHub](https://github.com/yargnad/The-Lyceum)) — Decentralized mesh network for sovereign infrastructure

**[📖 Read the full Framework documentation](https://rebellion.musubiaccord.org)**

---

## License

**GNU General Public License v3.0**

The Whetstone hardware designs and software are GPL v3.0 licensed. This ensures the tool for cognitive sovereignty remains ungovernable and forkable. You own your device, you own your thoughts, you own the code.

See [LICENSE](LICENSE) for full text.

---

## Links

- **The Authentic Rebellion Framework**: [rebellion.musubiaccord.org](https://rebellion.musubiaccord.org)
- **The Musubi Accord (Steward Organization)**: [musubiaccord.org](https://musubiaccord.org)
- **Ollama**: [ollama.com](https://ollama.com)
- **Radxa Rock 5B+**: [radxa.com](https://radxa.com/products/rock5/5bplus/)
- **Whisper**: [github.com/openai/whisper](https://github.com/openai/whisper)
- **Piper TTS**: [github.com/rhasspy/piper](https://github.com/rhasspy/piper)

---

## Acknowledgments

This project builds on the work of:
- **Mistral AI** for privacy-respecting open-source models
- **Ollama team** for making local LLM inference accessible
- **Project Gutenberg** for public domain philosophical texts
- **Radxa** for affordable ARM64 SBC platforms
- **OpenAI** for Whisper (ironically, their best contribution to open-source)
- **Rhasspy community** for Piper TTS

---

> **"The Whetstone doesn't give you answers. It sharpens your capacity to find them yourself."**

---

*This is Act II of The Authentic Rebellion Framework. Use it, fork it, improve it. That's praxis.*

*Last updated: November 9, 2025*
