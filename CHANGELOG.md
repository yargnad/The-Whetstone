# Changelog

All notable changes to the Whetstone project will be documented in this file.

## [2026-01-06] - TUI Stability & Refactor Phase

### Fixed
- **TUI Invisible Text**: Resolved a critical bug where AI responses were invisible in `ChatBubble` and `SymposiumBubble`. The issue was a naming conflict between our custom `loading` attribute and Textual's built-in `Widget.loading` property, which triggered an opaque overlay. Renamed to `is_generating`.
- **Scheduler Crashes**: Fixed `InvalidButtonVariant` crash in `SchedulerScreen` caused by using "accent" variant (not supported by Textual Buttons).
- **Label Argument Error**: Fixed `TypeError` in `SchedulerScreen` where `Label()` was passed an unsupported `style` keyword argument.
- **Backend Syntax Error**: Fixed a logical comparison bug in `backends.py` (`===` vs `is None`).
- **Ollama Debugging**: Added enhanced logging to `OllamaBackend` to track raw stream chunks for easier debugging.

### Changed
- **Settings Refactor**: Moved "Deep Mode" and "Privacy" toggles from the sidebar buttons to the global **Command Palette** (Ctrl+P). 
    - New Shortcuts: `d` for Deep Mode, `p` for Privacy.
- **Markdown Rendering**: Replaced `Label` with `Markdown` widgets for AI message bubbles in the TUI to support rich text formatting (bold, lists, etc.) and better word-wrapping.

### Added
- **Global Actions**: Implemented `action_toggle_deep` and `action_toggle_privacy` at the `App` level for consistent behavior across all screens.

## [2026-01-07] - Phase 3: Web UI Implementation & Persona Manager

### Added
- **Web API Server** (`web_api.py`): FastAPI backend with REST API and SSE streaming.
- **Enhanced Persona Manager**:
    - **Per-Persona Configuration**: Edit custom preambles and instructions for each persona.
    - **Backend Persistence**: Custom configurations are saved to the SQLite `settings` table.
    - **Scan Modes**: Support for "Deep" vs. "Shallow" persona directory scanning.
    - **Scan Integration**: GUI trigger for re-scanning the `philosophy_library/`.
    - **Background Scanning**: Moved the persona library scan to an asynchronous background task with a status tracking endpoint (`/api/personas/scan/status`) to prevent gateway timeouts.
    - **Navigation Refinement**: Consolidated "Scheduler" and "Persona Manager" into a responsive hamburger menu for a cleaner UI.
- **Chat Interface**: Modern dark-themed web UI with real-time streaming responses.
- **Model Selector**: Switch between Ollama models at runtime from the UI.
- **Chat History**: Persists conversations across page refreshes (when logging enabled).
- **Markdown Rendering**: Full markdown support in chat bubbles.
- **TTS Prep**: `strip_stage_directions()` function for future voice integration.

### Changed
- **Default Model**: Updated default Ollama model to `cogito:8b`.

### Technical Decisions
- **SSE over WebSockets**: Chose Server-Sent Events for streaming (better browser compatibility).
- **Persistence Strategy**: Used SQLite-backed key-value store in the `settings` table for per-persona metadata, ensuring configurations survive sessions without modifying the core `personas.json` library.
