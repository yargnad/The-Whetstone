# Architecture: The Whetstone ↔ codepax

## Overview

The Whetstone and codepax are **separate but complementary** systems with distinct responsibilities.

## The Whetstone (This Project)

**Purpose**: Philosophy-focused AI assistant with persona-based interactions

**Responsibilities**:
- Persona generation from Project Gutenberg texts
- PG-specific text curation (boundaries, metadata)
- Philosophy library management
- Web/TUI/CLI interfaces
- Privacy & persistence features

**Key Files**:
- `generate_personas.py` - Creates personas from library texts
- `auto_curator.py` - PG-specific filtering logic
- `philosophy_library/` - Source texts with boundary markers
- `core.py`, `web_api.py`, `tui_app.py` - Application logic

---

## codepax (External Tool)

**Purpose**: Generic CODEX format tooling (format-agnostic)

**Responsibilities**:
- CODEX file packing/unpacking
- Format validation (any CODEX type, not just personas)
- Generic import/export mechanics
- Recipe management (content-agnostic)

**NOT responsible for**:
- Project Gutenberg specifics
- Philosophy domain knowledge
- Persona prompt generation
- Source text curation

---

## Workflow Integration

### Creating Personas (Whetstone-native)

```bash
# Manual process - PG texts → personas
python generate_personas.py --deep

# Output: philosophy_library/personas.json
```

### Exporting to CODEX (Hybrid)

```bash
# Whetstone provides content + metadata
# codepax handles CODEX format

# Use existing CODEX if present
codepax export nietzsche

# Force regeneration from source
codepax export nietzsche --regenerate
```

**Division of Labor**:
1. **Whetstone** supplies:
   - Curated text (via `auto_curator.py`)
   - Persona metadata (from `personas.json`)
   - Library filters (PG-specific)

2. **codepax** handles:
   - CODEX v2.0 structure
   - JSON serialization
   - File compression
   - Format validation

### Importing CODEX (Hybrid)

```bash
# codepax unpacks format
# Whetstone integrates into library

codepax import philosopher.codex --target philosophy_library/
```

---

## Why This Split?

### Whetstone = Domain-Specific
- Understands **philosophy** and **Project Gutenberg**
- Knows how to generate **persona prompts** from author texts
- Manages the **philosophy library** structure

### codepax = Generic Tool
- Usable for **any CODEX type** (not just personas)
- Could pack game assets, config files, datasets
- Reusable across **multiple projects**

---

## Example: Other Projects Using codepax

**Hypothetical Use Cases**:
```bash
# Game mod distribution
codepax pack my-skyrim-mod/ --output elderscrolls.codex

# Machine learning datasets
codepax export mnist-curated --format codex/dataset

# Configuration bundles
codepax pack dotfiles/ --recipe .codexrc
```

None of these need The Whetstone's philosophy logic, but they all benefit from codepax's generic packing/validation.

---

## Current State (After Refactor)

✅ **Whetstone** owns:
- `generate_personas.py` (moved back from codepax)
- `auto_curator.py` (PG filtering)
- `philosophy_library/` (source texts)

✅ **codepax** owns:
- Generic CODEX format tooling
- Extensible for non-philosophy use cases

🔄 **Next Steps**:
- Implement export that checks for existing CODEX
- Add `--regenerate` flag to force recreation
- Define clean API between Whetstone and codepax
