# CODEX Lifecycle & Ecosystem: Architecture and Workflows

This document outlines the detailed workflows for the CODEX ecosystem, separating the responsibilities of **The Whetstone** (domain logic, philosophy) and **codepax** (format, distribution). It also establishes the vision for future forks like *Eidolon Triptych* (fiction).

## 1. The Ecosystem Model

The CODEX format (`.codex`) is the universal container. **codepax** is the package manager. **The Whetstone** (and future apps) are the "Editors" or "Runtimes".

- **The Whetstone**: Philosophy-centric. Uses `auto_curator` to process Project Gutenberg texts into philosoper personas.
- **Eidolon Triptych**: Fiction-centric. Uses similar logic to create character personas from fiction texts.
- **codepax**: The "Jack of All Trades" Builder. A universal tool to build, pack, and validate CODEX files without knowing what's inside.
- **The Whetstone**: The Interface. It uses `codepax` to package its specific domain knowledge (philosophy, curated text) into the standard format.

> **Note on Philosophy**: The concepts below (Ingredients, Recipes, Workflows) are design principles for the CODEX specifications. They ensure the format is self-describing and ubiquitous. However, **The Whetstone's core local loop remains unchanged**: it will still watch the library folder and process raw text files directly. CODEX is the *Interchange Layer* for portability.

---

## 2. Unpaxing (Import Workflow)

The import process is designed to be "unpaxing" rather than "loading". It treats the CODEX file as a self-contained archive that explodes into the system seamlessly.

### Workflow: `codepax pull file.codex`

1.  **Validation**: `codepax` validates the file integrity and schema.
2.  **Extraction (Unpaxing)**:
    - **Ingredients (Source Texts)**: Extracted directly to the active library directory (e.g., `philosophy_library/`). This ensures the raw data is available for RAG and future processing.
    - **Metadata & Definitions**: Extracted and injected into the system's central registry (e.g., `personas.json` or a SQLite DB).
3.  **Hydration**:
    - The persona is now "live". The system references the extracted source files and the injected metadata.
    - No further processing is required; the CODEX file contained everything needed.

### Key Concept: "Self-Healing" Import
If source files are missing or corrupted, the CODEX file (which serves as the source of truth) can re-extract them.

---

## 3. Hydration (Export Workflow)

Exporting is the process of gathering a scattered entity (source files, prompts, metadata) and bundling it into a immutable CODEX artifact.

### Workflow: `codepax export [persona_id]`

1.  **Collection**:
    - Identify all **Ingredients** (source text files) associated with the persona.
    - Retrieve the **"Recipe"** (curation filters) used to prepare those ingredients.
    - Retrieve the Persona Definition (system prompt, parameters).
    - Retrieve Metadata (Author, created_by, timestamps).
2.  **Noise Elimination (The Curator)**:
    - *If receipts don't exist:* The system triggers **The Curator** (using Qwen3 8B or similar local LLM) to analyze the source files.
    - **Logic**: The Curator scans the beginning and end of files to identify non-authorial text (Project Gutenberg headers, transcriber notes, etc.).
    - **Output**: A "Recipe" (regex/line-range filters) is generated and stored. It does *not* destructively edit the source files; it stores the *instructions* on how to read them cleanly.
3.  **Packing**:
    - The gathered artifacts (Ingredients + Recipes + Metadata + Prompts) are bundled into the `.codex` container.
4.  **Result**: A fully hydrated (Dense), portable file that can be sent to another device and "unpaxed" to perfectly replicate the persona.

### CODEX Variants: Dense vs. Sparse
- **Dense Imports (Hydrated)**: The CODEX file actually contains the `ingredients` (source files). It is offline-ready and immutable.
- **Sparse Imports (Lite)**: The CODEX file only contains the `recipes` and *pointers* (URIs) to the ingredients. The system must fetch the ingredients upon import.
- **Mixed**: A hybrid approach where critical or rare ingredients are included, but common ones (like public domain books) are referenced by URI.

---

## 4. The Curator Logic (Noise Elimination)
The "Curator" is the intelligent filter that ensures high-quality input for the AI.

- **Model**: Small, fast local model (e.g., Qwen3 8B).
- **Task**: "Identify the boundary lines where the actual content begins and ends. Ignore headers, footers, and license text."
- **Sampling Strategy**: To avoid processing gigabytes of text, the Curator samples the first 5% and last 5% of a file to find boundaries.
- **Adaptability**: *The Whetstone* looks for PG headers. *Eidolon Triptych* might look for publisher pages or fanfic disclaimers. The logic is pluggable.

## 5. The Core Loop vs. The Interchange
It is important to distinguish between the **Device Workflow** and the **portability Workflow**.

### Device Workflow (The Whetstone)
- **Watcher**: The system watches `philosophy_library/` for *any* new text file.
- **Auto-Curation**: When a text file drops, `generate_personas.py` kicks in, runs the noise elimination, generates a prompt, and creates a persona entry.
- **No CODEX needed**: The device works perfectly fine with just raw text files.

### Interchange Workflow (CODEX)
- **Export**: "Pack up this working persona so I can send it to my friend or use it in Gemini Studio."
- **Import**: "Unpack this box of ingredients and recipes into my library so my local watcher can ingest them (or ingest them directly)."


---

## 5. Future Vision: Self-Executing Workflows
CODEX files will evolve beyond static data into **Agentic Workflows**.

- **Structure**: A CODEX file could contain a `workflow.yaml` defining a sequence of actions.
- **Self-Description**: Opening the file tells the AI agent exactly what to do (e.g., "This contains a Python script and a dataset; run the script on the data and summarize the output").
- **IDE Assistant**: A "project" could be a CODEX file. The AI opens it, understands the context, and becomes a specialized assistant for that specific domain immediately.
- **Plugins**: `codepax` plugins will allow third-party tools to define their own execution logic for these workflow files.

## 6. Semantic Portability (The "Drop & Play" Vision)
To achieve true interoperability with advanced AI models (Gemini, Claude, ChatGPT), the CODEX structure uses self-descriptive semantic keys.

- **Ingredients**: Clearly labeled as `source_ingredients` or `context_materials`.
- **Recipes**: Labeled as `preparation_rules` or `processing_instructions`.
- **Inference**: A sufficiently intelligent AI parsing a CODEX file should instantly understand: "Here are the ingredients (context), and here is the recipe (prompt instructions) for how to be this persona."
- **Goal**: Drag-and-drop a `.codex` file into Gemini AI Studio, and the model immediately adopts the persona and context without further configuration.

## 7. The Grand Vision: The "JSON" of AI Workflows
The ultimate goal is for CODEX to become a ubiquitous standard for AI context and workflows, similar to how JSON became the standard for data exchange.

- **Extensibility is Key**: Just as XML/JSON support any schema, CODEX supports any domain (Philosophy, Fiction, Code, Science).
- **Eidolon Triptych Example**: A fiction-focused fork would use the *same* CODEX format but different "fragmentation" logic to assemble characters from novels.
- **Universal Utility**: A CODEX file is a "box of folders and files" that any qualified assistant (The Whetstone, ChatGPT, Claude) can open and understand immediately using the self-descriptive instructions inside.

## 8. Semantic Schema Specification (v2.0)
To maximize interpretability by AI agents, key names are verbose and self-descriptive.

### `codex_manifest.json` Structure
```json
{
  "codex_format_version": "2.0",
  "persona_identity": {
    "name": "Friedrich Nietzsche",
    "role_description": "19th Century German Philosopher, focus on nihilism and will to power",
    "avatar_uri": "assets/avatar.png"
  },
  "preparation_recipe": {
    "description": "Instructions for cleaning and processing the raw ingredients.",
    "steps": [
      {
        "action": "remove_pg_headers",
        "rationale": "Remove Project Gutenberg legal headers to ensure pure authorial voice",
        "target_ingredients": ["*.txt"]
      },
      {
        "action": "strip_transcriber_notes",
        "regex_pattern": "^\\[Transcriber's Note:.*\\]$"
      }
    ]
  },
  "source_ingredients": [
    {
      "type": "text/plain",
      "uri": "ingredients/zarathustra.txt",
      "original_source": "Project Gutenberg #1998",
      "description": "Primary source text: Thus Spake Zarathustra"
    },
    {
      "type": "text_plain",
      "uri": "ingredients/beyond_good_and_evil.txt",
      "description": "Secondary source text"
    }
  ],
  "agentic_workflow_hints": {
    "on_open": "adopt_persona",
    "context_handling": "rag_indexing_required"
  }
}
```


