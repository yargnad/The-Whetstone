# Persona Ecosystem v2.0 Specification

**Purpose:** Transform the persona system from a local file scanner into a portable, shareable ecosystem supporting "High-Res" imports and User Cloning.

---

## 1. Persona Plugins (The "Cartridge" Model)

Persona Plugins are zip archives containing everything needed to instantiate a persona without requiring on-device generation.

### File Structure (`*.whetstone`)

```text
plato.whetstone (zip)
├── metadata.json       # Version, Author, Source Hash
├── prompt.txt          # The "High-Res" generated system prompt
├── config.json         # Default settings (voice, weirdness, context limits)
├── avatar.png          # (Optional) UI representation
└── library/            # (Optional) Curated best-of texts for RAG
    ├── republic_excerpt.txt
    └── apology_excerpt.txt
```

### Workflow

1. **Generation:** Created offline using massive models (e.g., Qwen 72B, GPT-4) to distill gigabytes of text into the "Perfect Prompt."
2. **Distribution:** Users share `.whetstone` files.
3. **Import:** Web UI upload -> System unzips to `philosophy_library/imported/` -> Updates `personas.json`.

---

## 2. User Cloning ("The Mirror")

**Concept:** After sufficient interaction time, the system can generate a persona based on the USER'S chat logs, allowing them to "see themselves" or share their digital twin.

### Implementation

1. **Data Source:** `chat_history.log` (anonymized/sanitized).
2. **Threshold:** Requires min. 500 interaction turns.
3. **Generation Process:**
    * **Input:** User's sides of the conversations.
    * **Prompt:** "Analyze the following user's speech patterns, beliefs, and rhetorical style. Create a persona definition that mimics them..."
4. **Output:** A new entry in `personas.json` tagged as `type: "clone"`.

---

## 3. Web UI Integration

The Web UI (Phase 3) will be the hub for managing this ecosystem:

* **"The Agora" (Marketplace):** Browse available local personas.
* **"The Forge" (Create):** Upload texts to generate new personas (Standard Mode) or Upload `.whetstone` files (High-Res Mode).
## 4. Management & Interface Consistency

To support the transition from a "Script" to a "Platform", all management interfaces (CLI, TUI, Web) must adopt the **Persona Manager** nomenclature and structure:
* **The Manager:** A dedicated screen for scanning, deleting, and importing personas.
* **Scan Modes:** Standardize "Shallow" (filename only) vs "Deep" (content analysis) scanning options across all UIs.
* **Parity:** What is manageable in the CLI's `Settings -> Update Personas` must be identical in the TUI's `Persona Manager` screen.

