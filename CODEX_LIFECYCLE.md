# CODEX Lifecycle & Ecosystem: Architecture and Workflows

This document outlines the detailed workflows for the CODEX ecosystem, separating the responsibilities of **The Whetstone** (domain logic, philosophy) and **codepax** (format, distribution). It also establishes the vision for future forks like *Eidolon Triptych* (fiction).

## 1. The Ecosystem Model

The CODEX format (`.codex`) is the universal container. **codepax** is the package manager. **The Whetstone** (and future apps) are the "Editors" or "Runtimes".

- **The Whetstone**: Philosophy-centric. Uses `auto_curator_v3` (exclusion-based) to process public-domain texts into curated sources and CODEX manifests.
- **Eidolon Triptych**: Fiction-centric. Uses similar logic to create character personas from fiction texts.
- **codepax**: The "Jack of All Trades" Builder. A universal tool to build, pack, and validate CODEX files without knowing what's inside.
- **The Whetstone**: The Interface. It uses `codepax` to package its specific domain knowledge (philosophy, curated text) into the standard format.

> **Note on Philosophy**: The concepts below (Ingredients, Recipes, Workflows) are design principles for the CODEX specifications. They ensure the format is self-describing and ubiquitous. The Whetstone's core loop remains: watch the library for raw text, curate, and generate personas. CODEX is the *interchange layer* the device now emits automatically.

---

## 2. Unpaxing (Import Workflow)

The import process is designed to be "unpaxing" rather than "loading". It treats the CODEX file as a self-contained archive that explodes into the system seamlessly.

### Path A: The Archive Drop (CODEX)
1.  **Watcher**: Monitors `codex_library/` for `.codex` files.
2.  **Explosion**: Unpacks to `curated_library/` (Runtime Cache).
3.  **Result**: Instant availability to RAG.

### Path B: The Raw Drop (Hybrid)
1.  **Watcher**: Monitors `raw/` for text files (e.g., `nietzsche_notes.txt`).
2.  **The Fork**:
    -   *If CODEX exists:* Appends the file to `codex_library/Friedrich_Nietzsche.codex`.
    -   *If New:* Generates a new `New_Persona.codex` in `codex_library/`.
3.  **The Merge**: Once the CODEX is updated/created, it triggers **Path A** automatically.
4.  **Result**: Raw files are never processed directly; they are always "paxed" first for auditability.

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
    - *If receipts don't exist:* The system triggers **auto_curator_v3** (using Qwen3 8B or similar local LLM) to analyze the source files.
    - **Logic**: The Curator uses exclusion ranges (headers, footnotes, translator/editor notes) instead of start/end boundaries.
    - **Output**: Exclusion ranges are stored; curated text is written; a CODEX manifest is updated with raw+clean hashes, exclusions, provenance, and prompts when persona generation runs.
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
- **Runtime (Fast Path)**: The RAG engine and Persona System only ever look at `curated_library/` (the exploded cache). This ensures zero-latency access.
- **Storage (Source of Truth)**: `codex_library/` holds the immutable `.codex` containers.
- **Updates (The Cycle)**:
    1.  **Ingest**: You drop a new raw text file (e.g., `notes.txt`) for a persona.
    2.  **Pack**: The system immediately *appends* this file to the existing `.codex` container (creating a new version).
    3.  **Explode**: The system "re-explodes" the updated CODEX into `curated_library/`, making the new knowledge available to RAG.
    4.  **Result**: The CODEX remains the master record; the curated folder is just a disposable cache.

### Interchange Workflow (CODEX)
- **Export**: Generates a `.codex` file from the current state.
- **Import**: Dropping a `.codex` file triggers the "Explosion" workflow described above.


---

## 5. Future Vision: Self-Executing Workflows
CODEX files will evolve beyond static data into **Agentic Workflows**.

- **Structure**: A CODEX file could contain a `workflow.yaml` defining a sequence of actions.
- **Self-Description**: Opening the file tells the AI agent exactly what to do (e.g., "This contains a Python script and a dataset; run the script on the data and summarize the output").
- **IDE Assistant**: A "project" could be a CODEX file. The AI opens it, understands the context, and becomes a specialized assistant for that specific domain immediately.
- **IDE Assistant**: A "project" could be a CODEX file. The AI opens it, understands the context, and becomes a specialized assistant for that specific domain immediately.
- **Plugins**: `codepax` plugins will allow third-party tools to define their own execution logic for these workflow files.

### 5a. The Codepax Persona Plugin (Future)
To decouple persona generation from *The Whetstone*, a "Persona Plugin" for `codepax` will be developed.
-   **Function**: Wraps the `auto_curator` logic into a set of tools (functions) callable by `functiongemma`.
-   **Usage**: `codepax build --plugin persona --url http://gutenberg.org/ebooks/1234`
-   **Result**: A valid Whetstone-compatible CODEX file generated entirely within the `codepax` environment, without needing the full Whetstone app.

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

## 9. Persona Tiers & On-Demand Refinement
To optimize resource usage (since generating a rich psychological profile requires reading the entire corpus), we use a two-tier system:

### 9.1 Basic Persona (Ingest Default)
-   **Trigger**: Automatic on drag-and-drop or migration.
-   **Methodology**:
    -   *Text*: Cleaned via Auto-Curator (Regex/AI).
    -   *Prompt*: Uses a generic template: "You are {Author}. Answer as you would in your writings."
-   **Cost**: Almost zero.
-   **Status**: Ready immediately.

### 9.2 Refined Persona (User Activated)
-   **Trigger**: **Manual User Action** ("Refine Persona" button on the card).
-   **Methodology**:
    -   *Analysis*: AI reads the full corpus to detect themes, writing style, and philosophy.
    -   *Generation*: Writes a detailed `system_prompt` (psychological profile).
-   **Cost**: High (Token/Compute intensive).
-   **Status**: "Refined" tag applied to CODEX.

### 9.3 The Refinement Workflow
1.  **Ingest**: User drops `nietzsche.txt`. System creates **Basic** Nietzsche instantly.
2.  **Evaluate**: User chats. If satisfied, they stop here.
3.  **Refine**: User clicks **"Refine Persona"**.
    -   System runs `generate_personas.py --author nietzsche`.
    -   Detailed profile replaces the generic prompt.
    -   CODEX is updated to version `vX.X-refined`.

## 10. Semantic Schema Specification (v2.0)
To maximize interpretability by AI agents, key names are verbose and self-descriptive.

> **Architecture Note**: The CODEX Core Specification defines the container (`manifest`, `ingredients`, `recipes`). The **Persona Schema** below is a *Whetstone-specific extension* payload carried within that container. Future apps (e.g., *Codepax*) will validate the container structure but ignore the specific domain payload unless configured to understand it.

### `codex_manifest.json` Structure (Whetstone Persona Variant)
```json
{
  "codex_format_version": "2.0",
  "meta": {
      "curation_level": "refined",  // or "basic"
      "latest_layer_version": "v1.2"
  },
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
  "analysis_artifacts": {
      "notes": "Stored outputs from the Persona Generator to avoid re-reading execution.",
      "style_summary": "Aphoristic, incendiary, prone to exclamation...",
      "philosophical_pillars": ["Will to Power", "Eternal Recurrence", "Amor Fati"]
  },
  "layers": [
      {
          "id": "v1.0-basic",
          "name": "Basic Import",
          "curation_level": "basic",
          "model": "regex",
          "prompt": "You are Friedrich Nietzsche...",
          "created_at": "2024-01-19T10:00:00Z"
      },
      {
          "id": "v1.2-refined",
          "name": "Deep Clean (Qwen3)",
          "curation_level": "refined",
          "model": "qwen2.5:32b",
          "prompt": "You are the Dynamite...",
          "created_at": "2024-01-20T12:00:00Z"
      }
  ],
  "agentic_workflow_hints": {
    "on_open": "adopt_active_layer", 
    "context_handling": "rag_indexing_required"
  }
}
```

## 11. Distribution & Packaging Strategies
To balance portability vs. "out-of-the-box" readiness, The Whetstone supports three release bundles:

| Bundle Type | Contents | Pros | Cons | Startup Action |
| :--- | :--- | :--- | :--- | :--- |
| **Lightweight** (Source) | App + `raw/` | Smallest size; Max flexibility | Longest startup (must curate & generate) | **Full Ingest**: Curation -> CODEX Gen -> Explosion |
| **Standard** (Default) | App + `codex_library/` | Balanced; No AI Curation needed | Moderate size; Must unzip on launch | **Explosion**: Unpacks CODEX -> `curated/` |
| **Heavy** (Runtime) | App + `codex_library/` + `curated/` | Zero setup; Instant RAG | Largest size (>2x storage) | **None**: Ready to query immediately |

### Strategy Recommendation
-   **GitHub / Source**: Use **Lightweight**. Git tracks raw text better than binaries.
-   **General User Download**: Use **Standard**. Offers the best balance; "installing" (exploding) is a familiar one-time cost.
-   **Demo / Kiosk**: Use **Heavy**. When immediate performance is critical and disk space is irrelevant.

## 12. Hardware Paradigms
The Whetstone ecosystem spans two distinct hardware profiles:

### A. The Tabletop Device (Offline / Air-Gapped)
-   **Philosophy**: "Digital Monastery". A focused, distraction-free reading and contemplation device.
-   **Connectivity**: Offline by design.
-   **Content Source**: Imports content exclusively via physical media (USB) or local network drops (`codex_library/`).
-   **Role**: The pure runtime and consumption engine.

### B. The Whetstone PC (Connected / Creator)
-   **Philosophy**: "The Scriptorium". A connected research and curation station.
-   **Connectivity**: Online.
-   **Features**:
    -   **PG Browser**: Built-in browser for Project Gutenberg to find and download texts directly.
    -   **1-Click Curate**: Download -> Auto-Curate -> Pack to CODEX in one seamless flow.
    -   **Sync**: Pushes generated CODEX files to the Tabletop Device via USB or local sync.

## 13. The AI-Powered Package Manager (Codepax Ecosystem)
The `codepax` CLI encapsulates the world's first **AI-Powered Package Ecosystem**. It uses a modular plugin architecture orchestrated by `functiongemma`.

### Architecture
-   **The Engine**: `functiongemma` (or equivalent). It reads schemas and decides which plugin functions to call to satisfy a user request.
-   **Core Plugin (Project Gutenberg)**:
    -   *Role*: The trusted supply chain.
    -   *Function*: Browses, validates, and fetches raw text from PG. Builds a generic, valid CODEX container.
-   **Extension Plugins**:
    -   **The Whetstone Plugin**: Extends the Core. Analyzes texts to generate **Philosophical Personas**.
    -   **Eidolon Plugin**: Extends the Core. Analyzes texts to destructure and reconstruct **Fictional Characters** (e.g., Tyler Durden).
    -   **Codekeeper Plugin**: Analyzes source code to generate **Code Assistants**.

### The Flow
1.  **User**: `codepax install --url http://pg.org/1234 --as "Tyler Durden"`
2.  **Engine**:
    -   Calls **Core Plugin** to fetch text.
    -   Detects intent ("Tyler Durden" = Character).
    -   Calls **Eidolon Plugin** to extract character traits and dialogue.
    -   Calls **Eidolon Plugin** to extract character traits and dialogue.
3.  **Result**: A fully hydrated, highly specialized CODEX file generated on-the-fly.

## 14. The Universal Compiler (Ops Use Case)
The user's vision extends CODEX to be a "Universal Dependency Compiler" (similar to Docker + Ansible).

-   **Concept**: A CODEX file is a **self-deploying environment**.
-   **Example**: `wordpress-win11.codex`
    -   **Ingredients**:
        -   `php-8.3-installer.exe` (URI)
        -   `mysql-installer.msi` (URI)
        -   `wordpress-core.zip` (Source)
    -   **Recipes**:
        -   `install_php`: Unattended install flags for Windows.
        -   `config_db`: SQL initialization scripts.
    -   **Agentic Hint**: `"on_hydrate": "deploy_stack"`
-   **Workflow**:
    -   User: `codepax hydrate wordpress.codex`
    -   Engine: Reads the recipe, pulls executables (Ingredients), runs installation (Recipes) indiscriminately handles versions and dependencies.
-   **Significance**: CODEX becomes the universal "Instruction Set" for computing, whether that instructions is "How to be Nietzsche" or "How to install WordPress".

### Advanced Use Case: Disaster Recovery (The "Lazarus" Protocol)
The user envisions CODEX as a nuclear-option recovery tool.
-   **Scenario**: Total system failure.
-   **Input**: `infrastructure-recovery.codex` + `database-backup.sql`.
-   **Process**:
    1.  **AI Orchestration**: Analyzes the CODEX manifest to understand the required environment.
    2.  **Rebuild**: Pulls dependencies, builds Docker containers, compiles code.
    3.  **Restore**: Reads domain capabilities to understand how to ingest the raw data backup (e.g., "This is a Postgres dump, pipe it to the db container").
-   **Result**: A fully restored, running application state from cold storage, zero human intervention required.


