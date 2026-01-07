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
