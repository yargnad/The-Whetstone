# Web UI Architecture

**Purpose:** Provide a visual interface for Chat, Configuration, and Management, serving as the backend for the Android Bridge App.

---

## 1. Technology Stack

* **Backend:** Flask (Python) - lightweight, integrates easily with existing `philosopher_app.py`.
* **Frontend:** HTML5 / TailwindCSS (minimal interactions) or Jinja2 templates.
* **Communication:** REST API + Server-Sent Events (SSE) for streaming chat tokens.

## 2. Core Components

### A. The Dashboard (Home)

* **Status:** System health, current model (8B/14B), temperature.
* **Quick Toggles:** Deep Mode, Scheduler ON/OFF.

### B. Chat Interface

* **Visuals:** Modern chat bubble UI.
* **Features:**
  * Persona Selector (Dropdown with avatars).
  * Streaming responses.
  * Input history.
  * `/deep` toggle button.

### C. "The Library" (Persona Manager)

* **Persona Manager:** 
  * List, Delete, Import (`.whetstone` upload).
  * Manual "Scan Library" button (matches TUI/CLI logic).
* **Socratic Scheduler:** Visual calendar/list of active schedules.

## 3. UI Parity Principles

To ensure a seamless experience across all interfaces (CLI, TUI, Web), the following structural rules apply:
1. **Naming Consistency:** If a feature is "Persona Manager" in the TUI, it must be "Persona Manager" in the Web UI.
2. **Screen Logic:** High-level managers (Scheduler, Personas, Symposium) should be distinct screens/menus rather than flat buttons in the sidebar where possible.
3. **Global Toggles:** System-wide settings (Deep Mode, Privacy) should be easily accessible but not dominate the primary content space.

### D. Settings

* **Model Config:** Switch backends (Ollama/llama.cpp), change models.
* **System:** Wi-Fi hotspot config (Ad-hoc mode), Updates.

## 3. API Endpoints (Android Bridge Ready)

* `GET /api/status`
* `GET /api/personas`
* `POST /api/chat` (Payload: `{query, persona_id, deep_mode}`) -> Stream
* `POST /api/personas/import` (File upload)
* `GET /api/scheduler`

## 4. Security

Since this is an airgapped/local device:

* **Auth:** Basic Token or PIN matching the "dead man's switch."
* **Bind:** 0.0.0.0 (Allow LAN connections for Ad-hoc mode).
