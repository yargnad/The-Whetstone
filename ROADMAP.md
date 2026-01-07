# The Whetstone: Task Tracker

## Phase 1: Cleanup & Linux Porting ✅

- [x] Remove Mistral artifacts, update Modelfile
- [x] Make model configurable (env var)
- [x] Create `requirements.txt`, `install_pro.sh`, systemd service
- [x] Dual-backend (Ollama + llama.cpp)
- [x] Concise response mode for e-ink UX
- [x] Test on Rock 5B+ with Armbian

## Phase 1.5: Architecture Refactoring (The Foundation) ✅

- [x] Implement `PhilosopherCore` (decouple logic from CLI)
- [x] Implement SQLite Database (`whetstone.db`)
- [x] Add Privacy Control (Opt-in Logging Toggle)
- [x] Migrate CLI to use `PhilosopherCore`

## Phase 2: Benchmarking & Portability

- [ ] Standard question suite for inference testing
- [ ] Document platform/model performance matrix

## Phase 2.5: Socratic Scheduler & Automation ✅

- [x] **The Symposium:** AI-to-AI Debate loop
- [x] Scheduler implementation (schedule lib)
- [x] "Interaction Type" config (Rhetorical, Question)
- [x] "Poke" mechanism (Audio/Display trigger)
- [x] **Advanced Config:** Personas/Topics (Symposium Controls)
- [x] **Rich TUI:** Modern CLI with scrollable containers (Textual/Rich)
- [x] Configuration UI (Settings menu)

## Phase 3: Web UI & App Backend

- [ ] Flask/FastAPI server implementation
- [ ] Chat Interface (Web)
- [ ] **Dream Mode:** Background worker for past chat analysis
- [ ] **Commonplace Book:** Insight extraction system
- [ ] Settings & Configuration Page
- [ ] API endpoints for Android Bridge

## Phase 4: Persona Ecosystem (v2.0)

- [ ] **Persona Plugins:** Import/Export logic (Zip/JSON standard)
- [ ] **User Cloning:** Logic to generate persona from chat history
- [ ] "High-Res" Prompt Library management

## Phase 5: RAG Upgrade (ChromaDB)

- [ ] ChromaDB integration
- [ ] Embed philosophy library
- [ ] Hybrid search (semantic + keyword)

## Phase 6: Hardware Acceleration

- [ ] ONNX export pipeline
- [ ] QNN context binary for Hexagon
- [ ] Arduino UNO Q integration

## Phase 7: Android Bridge App

- [ ] Airgap update protocol design
- [ ] Android app scaffold
- [ ] Signed OTA packaging

## Phase 8: Voice (Platform-Specific)

- [ ] Rock 5B+: SenseVoice + Paroli
- [ ] Dragon Q6A: Whisper (QNN) + Piper

## Phase 9: GPIO & E-Ink

- [ ] ButtonManager
- [ ] Waveshare e-ink integration
