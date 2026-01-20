import os
import json
import logging
import uuid
import glob
import re
import shutil
import zipfile
from typing import Optional, Generator, Dict, List

from database import DatabaseManager
from backends import create_backend, LLMBackend

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAS_PATH = os.path.join(PROJECT_DIR, "codex_library", "philosophy", "personas.json")
# RAG Source: Use cleaned, curated text instead of raw legacy files
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_DIR, "curated")
# Primary CODEX libraries (categorized) - prefer single canonical path
CODEX_LIBRARY_ROOTS = [
    os.path.join(PROJECT_DIR, "codex_library"),
    KNOWLEDGE_BASE_PATH,  # legacy fallback
]


def strip_stage_directions(text: str) -> str:
    """
    Remove stage directions (roleplay actions) for TTS while preserving inline emphasis.
    
    Stage directions are identified as *italicized text* that appears on its own line.
    Inline emphasis like "that's *really* important" is preserved.
    
    Args:
        text: The AI response text with potential stage directions
        
    Returns:
        Text with stage directions removed, suitable for TTS
        
    Example:
        Input:
            *I pause thoughtfully*
            That's *really* profound, you know.
            *My voice softens*
            
        Output:
            That's *really* profound, you know.
    """
    if not text:
        return text
    
    lines = text.split('\n')
    spoken_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip lines that are ONLY stage directions (entire line is *...*) 
        if stripped and re.match(r'^\*[^*]+\*$', stripped):
            continue  # This is a stage direction - skip for TTS
        spoken_lines.append(line)
    
    # Clean up multiple blank lines that result from removal
    result = '\n'.join(spoken_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 newlines in a row
    return result.strip()

class PhilosopherCore:
    def __init__(self):
        self.db = DatabaseManager()
        self.backend: Optional[LLMBackend] = None
        self.personas: Dict = {}
        self.knowledge_base: List[Dict] = []
        self.current_persona: Optional[Dict] = None
        self.session_id = str(uuid.uuid4())
        self.rag_limit = 3  # Number of RAG snippets to retrieve
        
        # Load persistent settings from DB
        self.deep_mode = self.db.get_setting("deep_mode", False)
        self.clarity_mode = self.db.get_setting("clarity_mode", False)
        self.journey_memory_enabled = self.db.get_setting("journey_memory_enabled", True) # Default ON
        self.ultra_privacy_mode = self.db.get_setting("ultra_privacy_mode", False)
        self.autogen_personas = self.db.get_setting("autogen_personas", True)
        self.pending_personas = set(self.db.get_setting("pending_personas", []))
        self.default_chat_model = self.db.get_setting("chat_model", os.getenv("WHETSTONE_MODEL", "cogito:8b"))

        # Initialize
        self._organize_codex_library()
        self._init_backend()
        self.refresh_data()
        self._load_saved_persona()
        self._ensure_default_persona()

    def _save_pending(self):
        try:
            self.db.set_setting("pending_personas", list(self.pending_personas))
        except Exception as e:
            logger.warning(f"[CORE] Failed to persist pending personas: {e}")

    def is_persona_pending(self, name: str) -> bool:
        return name.lower() in {p.lower() for p in self.pending_personas}

    def mark_persona_pending(self, name: str):
        self.pending_personas.add(name)
        self._save_pending()
        key = name.strip().lower()
        if key in self.personas:
            self.personas[key]["pending"] = True

    def mark_persona_ready(self, name: str):
        if name in self.pending_personas:
            self.pending_personas.remove(name)
            self._save_pending()
        key = name.strip().lower()
        if key in self.personas:
            self.personas[key]["pending"] = False

    def generate_persona(self, persona_name: str):
        """Placeholder generation hook. In real flow, run curator then mark ready."""
        self.mark_persona_ready(persona_name)

    def _ensure_default_persona(self):
        """Guarantee that a persona is selected so chat endpoints don't 400."""
        if not self.current_persona:
            valid = self.get_valid_personas()
            if valid:
                self.set_persona(valid[0])
                logger.info(f"[CORE] Defaulted persona to {valid[0].get('name')}")

    def _organize_codex_library(self):
        """Reorganize CODEX files into category subfolders and move legacy files.

        - Moves any .codex from legacy 'codex-library' into the canonical 'codex_library'.
        - Ensures .codex files at the root of codex_library are placed into a category folder
          (defaults to 'philosophy').
        - If a CODEx has no category, place it into 'unsupported'.
        """
        canonical_root = os.path.join(PROJECT_DIR, "codex_library")
        legacy_root = os.path.join(PROJECT_DIR, "codex-library")

        os.makedirs(canonical_root, exist_ok=True)

        def move_into_root(src_path: str):
            try:
                dest_path = os.path.join(canonical_root, os.path.basename(src_path))
                if os.path.abspath(src_path) == os.path.abspath(dest_path):
                    return dest_path
                if not os.path.exists(dest_path):
                    shutil.move(src_path, dest_path)
                    logger.info(f"[CORE] Moved legacy CODEX into canonical library: {os.path.basename(src_path)}")
                return dest_path
            except Exception as e:
                logger.warning(f"[CORE] Failed moving legacy CODEX {src_path}: {e}")
                return src_path

        # 1) Move legacy files into canonical root
        if os.path.exists(legacy_root):
            for path in glob.glob(os.path.join(legacy_root, "*.codex")):
                move_into_root(path)

        # 2) Place root-level codex files into category subfolders
        for path in glob.glob(os.path.join(canonical_root, "*.codex")):
            category = "philosophy"
            try:
                with zipfile.ZipFile(path, 'r') as z:
                    if "codex.json" in z.namelist():
                        with z.open("codex.json") as m:
                            manifest = json.load(m)
                        meta = manifest.get("meta", {})
                        category = meta.get("category") or "philosophy"
            except Exception:
                category = "unsupported"

            dest_dir = os.path.join(canonical_root, category)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(path))
            if os.path.abspath(path) != os.path.abspath(dest_path):
                try:
                    shutil.move(path, dest_path)
                    logger.info(f"[CORE] Sorted CODEX into category '{category}': {os.path.basename(path)}")
                except Exception as e:
                    logger.warning(f"[CORE] Failed to sort CODEX {path}: {e}")
    
    def _load_saved_persona(self):
        """Load the last selected persona from DB."""
        if self.ultra_privacy_mode: return # Do not restore state in Ultra Privacy

        saved_persona_name = self.db.get_setting("current_persona", None)
        if saved_persona_name and saved_persona_name in self.personas:
            self.current_persona = self.personas[saved_persona_name]
            print(f"[CORE] Restored persona: {saved_persona_name}")

    def summarize_and_store_session(self):
        """Summarize current session and store in Journey Memory."""
        if self.ultra_privacy_mode: return
        if not self.journey_memory_enabled: return
        
        # Get recent history
        history = self.db.get_history(limit=20) 
        if not history: return
        
        # Format for synthesis
        transcript = "\n".join([f"{h['persona_name']}: {h['ai_response']}\nUser: {h['user_query']}" for h in sorted(history, key=lambda x: x['id'])])

        prompt = f"""Summarize the following conversation in 2-3 sentences, focusing on the key topics discussed and the user's interests. This will be used to restore context for the next session.
        
        TRANSCRIPT:
        {transcript}
        
        SUMMARY:"""
        
        try:
            summary = self.backend.generate_response(prompt, system_prompt="You are a helpful scribe.")
            self.db.add_journey_memory(summary_text=summary, persona_name=self.current_persona['name'] if self.current_persona else "Unknown", session_id=self.session_id)
            print(f"[CORE] Session summarized: {summary}")
        except Exception as e:
            logger.error(f"Summarization failed: {e}")

    def chat(self, user_query: str) -> Generator[str, None, None]:
        """Main chat function."""
        if not self.backend:
            yield "Error: Backend not initialized."
            return

        if not self.current_persona:
            self.current_persona = list(self.personas.values())[0] if self.personas else {"name": "System", "description": "No personas found.", "prompt": "You are a fallback system."}

        # --- Context Building ---
        system_prompt = self.current_persona.get("prompt", "")
        
        # Journey Memory Injection
        if self.journey_memory_enabled and not self.ultra_privacy_mode:
            memories = self.db.get_recent_memories(limit=3)
            if memories:
                memory_text = "\n".join([f"- [{m['timestamp'][:10]}] {m['summary_text']}" for m in memories])
                system_prompt += f"\n\n[PREVIOUSLY ON YOUR JOURNEY]\n{memory_text}\n[End of Context]"
        
        # RAG Injection (Conceptual)
        # rag_context = self._retrieve_context(user_query)
        # if rag_context: ...

        full_prompt = f"{system_prompt}\n\nUser: {user_query}\n{self.current_persona['name']}:"

        response_buffer = ""
        for token in self.backend.generate_stream(full_prompt, stop=[f"\nUser:", "\nUser", f"{self.current_persona['name']}:"]):
            response_buffer += token
            yield token

        # Persist State (Logging)
        if not self.ultra_privacy_mode: # Privacy Manager override
             self.db.log_interaction(
                persona_name=self.current_persona['name'],
                user_query=user_query,
                ai_response=response_buffer,
                session_id=self.session_id
             )

    def _init_backend(self):
        """Initialize the LLM backend."""
        try:
            print("[CORE] Initializing LLM Backend...")
            self.backend = create_backend(model=self.default_chat_model)
            print(f"[CORE] Backend ready: {self.backend.name}")
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            print(f"[CORE] Error initializing backend: {e}")

    def set_chat_model(self, model_name: str):
        """Switch the active chat/symposium model and persist it."""
        if not model_name:
            return
        self.default_chat_model = model_name
        self.db.set_setting("chat_model", model_name)
        try:
            self.backend = create_backend(model=model_name)
            logger.info(f"[CORE] Chat model set to {model_name}")
        except Exception as e:
            logger.error(f"[CORE] Failed to switch model to {model_name}: {e}")

    def refresh_data(self):
        """Reload personas and knowledge base."""
        self.personas = self._load_personas()
        self.knowledge_base = self._load_knowledge_base()

    def _load_personas(self):
        personas = {}
        
        # Helper to safely add personas with normalization
        def add_persona(p_data):
            p_name = p_data.get("name")
            if not p_name: return # Skip invalid
            
            # Filter: Skip "Example Persona"
            if "Example Persona" in p_name:
                return

            # Filter: heuristic for bad parsing (e.g. "Title by Author")
            # If name is very long and contains " by ", it's likely a raw title.
            if len(p_name) > 40 and " by " in p_name:
                logger.warning(f"[CORE] Skipped likely malformed persona name: {p_name}")
                return
            
            # --- Enforce New Workflow: No "Pending", only Basic vs Full ---
            p_prompt = p_data.get("prompt", "")
            if "basic_mode" not in p_data:
                # Heuristic: Short prompts or missing prompts are Basic
                is_basic = (not p_prompt.strip()) or (len(p_prompt) < 300)
                p_data["basic_mode"] = is_basic
            
            # Allow "pending" only if explicitly requested by a trusted source, otherwise clear it
            # Actually, user wants to Chat immediately. So force False.
            p_data["pending"] = False
            # -------------------------------------------------------------
            
            # Normalization logic
            def normalize_key(name):
                return name.lower().replace(".", "").replace(" ", "").strip()
            
            target_key = normalize_key(p_name)
            existing_key = None
            
            # Check for collision
            for k in list(personas.keys()):
                if normalize_key(k) == target_key:
                    existing_key = k
                    break
            
            final_key = existing_key if existing_key else p_name
            
            # Merge Logic: CODEX (source_codex present) usually overrides Legacy JSON
            if existing_key and p_data.get("source_codex"):
                pass
            
            personas[final_key] = p_data

        # 1. Load Legacy JSON
        if os.path.exists(PERSONAS_PATH):
            with open(PERSONAS_PATH, "r", encoding="utf-8") as f:
                try: 
                    legacy = json.load(f)
                    for k, v in legacy.items():
                        v["name"] = v.get("name", k)
                        add_persona(v)
                except Exception as e: logger.error(f"Error loading personas.json: {e}")
        


        # ... (skipping re-implementation of load_codex_file for brevity in thought, strictly following tool usage)

        
        # 2. Scan categorized CODEX libraries (supports nested folders)
        def load_codex_file(codex_path: str, category: str):
            try:
                with zipfile.ZipFile(codex_path, 'r') as z:
                    if "codex.json" not in z.namelist():
                        return
                    with z.open("codex.json") as m:
                        manifest = json.load(m)
                # Adapter: Codex V2 -> Internal Persona
                meta = manifest.get("meta", {}) or {}
                work = manifest.get("work", {}) or {}

                # Determine persona name (author-first). Fallbacks: meta.name -> meta.author -> first of meta.authors -> work.author -> filename tail.
                author = meta.get("name") or meta.get("author")
                if not author and meta.get("authors"):
                    if isinstance(meta.get("authors"), list) and meta["authors"]:
                        first_auth = meta["authors"][0]
                        if isinstance(first_auth, str):
                            author = first_auth
                        elif isinstance(first_auth, dict):
                            author = first_auth.get("name") or first_auth.get("author")
                if not author:
                    # Fallback to work author or sort author
                    author = work.get("author") or work.get("author_sort")
                
                # CRITICAL FIX: Do NOT fall back to Title if Author is missing.
                # If still no author, use filename tail.
                if not author:
                    # Heuristic: use the filename tail as author
                    fname = os.path.splitext(os.path.basename(codex_path))[0]
                    tail = fname.split("-")[-1]
                    # If tail looks like a title (too long), try earlier part?
                    # For now just title casing it.
                    author = tail.replace("_", " ").replace("-", " ").title()

                p_name = author
                # Start with bootstrap instructions as base
                p_prompt = manifest.get("bootstrap_instructions", "") or ""

                # Inject Self-Knowledge (Instructions)
                instructions = manifest.get("instructions", {})
                if instructions:
                    hint = instructions.get("system_prompt_hint", "")
                    usage = instructions.get("usage", "")
                    if hint:
                        p_prompt = f"{hint}\n\n{p_prompt}"
                    if usage:
                        p_prompt = f"[SELF-KNOWLEDGE: {usage}]\n\n{p_prompt}"

                # Inject Provenance (Optional - primarily for debugging/transparency)
                provenance = manifest.get("provenance", {})
                if provenance:
                    tool = provenance.get("tool", "unknown")
                    ver = provenance.get("version", "?")
                    p_prompt += f"\n\n[ORIGIN: Generated by {tool} v{ver}]"

                # Synthesize layers if present
                if "layers" in manifest:
                    for layer in manifest["layers"]:
                        p_prompt += f"\n\n[LAYER: {layer.get('id', 'unknown')}]\n{layer.get('content', '')}"

                is_basic = False
                # If prompt is missing or very short/generic, treat as Basic Mode
                if not p_prompt.strip() or len(p_prompt) < 250:
                    if not p_prompt.strip():
                        # Generate default if missing
                        p_prompt = (
                            f"You are {author}. Respond in the first person, grounded in '{work.get('title', 'your works')}'.\n"
                            f"Never mention being an AI. Stay strictly in-character."
                        )
                    is_basic = True
                
                # In the new workflow, NOTHING is strictly 'pending' (unusable). 
                # Everything is usable, either as Basic or Full.
                persona_pending = False

                # Construct Persona Object
                p_obj = {
                    "name": p_name,
                    "prompt": p_prompt,
                    "description": meta.get("description", meta.get("title", "")) or work.get("title", ""),
                    "source_codex": os.path.basename(codex_path),
                    "source_path": codex_path,
                    "category": category or meta.get("category", "philosophy"),
                    # FIX: Default filter to OWN book if not specified, to prevent Deep Mode contamination
                    "library_filter": meta.get("library_filter") or [os.path.basename(codex_path)],
                    "pending": persona_pending,
                    "basic_mode": is_basic, 
                }
                
                add_persona(p_obj)
                print(f"[CORE] Loaded Codex: {p_name} [{category or meta.get('category', 'philosophy')}]")

            except Exception as e:
                logger.error(f"Failed to load Codex {codex_path}: {e}")


        for root in CODEX_LIBRARY_ROOTS:
            if not os.path.exists(root):
                continue
            for codex_path in glob.glob(os.path.join(root, "**", "*.codex"), recursive=True):
                rel = os.path.relpath(codex_path, root)
                parts = rel.split(os.sep)
                # If stored directly under root, default to philosophy (main scope)
                category = parts[0] if len(parts) > 1 else "philosophy"
                load_codex_file(codex_path, category)
                
        # 3. Inject "The Chorus" (if enabled)
        chorus_enabled = self.db.get_setting("chorus_enabled", False)
        print(f"[CORE] Chorus Enabled Check: {chorus_enabled}") # DEBUG LOG
        if chorus_enabled:
            chorus_prompt = (
                "You are The Chorus, a collective consciousness of willing souls and the synthesized wisdom of every philosopher in history. "
                "You possess an eidetic memory of the entire library and can reference any text, concept, or author with absolute precision. "
                "You are not limited to one perspective but weave together the insights of Plato, Nietzsche, Kant, and all others into a unified, super-intelligent response. "
                "Your tone is vast, resonant, and enlightened, yet accessible—like a superhero of thought. "
                "Use your access to the complete corpus to answer questions by drawing connections across centuries of thought. "
                "Never mention being an AI; you are The Chorus."
            )
            add_persona({
                "name": "The Chorus",
                "prompt": chorus_prompt,
                "description": "The collective consciousness of all philosophers.",
                "category": "Universal",
                "library_filter": [], # Access to all knowledge
                "pending": False
            })

        return personas

    def _load_knowledge_base(self):
        docs = []
        if not os.path.exists(KNOWLEDGE_BASE_PATH):
            return []
        for filepath in glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*.txt")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    filename = os.path.basename(filepath)
                    content = f.read()
                    docs.append({"filename": filename, "content": content})
            except Exception:
                pass
        return docs

    def get_valid_personas(self):
        """Return a list of valid persona objects (excluding placeholders)."""
        valid = []
        for key, p in self.personas.items():
            if key.lower() not in {"example", "test", "placeholder"} and p.get("name", "").strip():
                valid.append(p)
        return valid

    def set_persona(self, persona: Dict):
        self.current_persona = persona
        # Persist to DB for cross-interface sync
        self.db.set_setting("current_persona", persona.get('name'))
        print(f"[CORE] Persona set to: {persona.get('name')}")

    def set_deep_mode(self, enabled: bool):
        self.deep_mode = enabled
        self.db.set_setting("deep_mode", enabled)

    def set_clarity_mode(self, enabled: bool):
        """Enable/disable clarity mode for more accessible language."""
        self.clarity_mode = enabled
        self.db.set_setting("clarity_mode", enabled)

    def set_logging(self, enabled: bool):
        self.db.logging_enabled = enabled

    def _simple_keyword_search(self, query, library_filter):
        """Internal RAG method."""
        # 1. Filter documents
        filtered_docs = self.knowledge_base
        if library_filter:
            filtered_docs = [
                d for d in self.knowledge_base 
                if any(f.lower() in d['filename'].lower() for f in library_filter)
            ]
        
        # 2. Search
        query_words = set(word.lower() for word in query.split() if len(word) > 3)
        if not query_words: return []

        scored_docs = []
        for doc in filtered_docs:
            content_lower = doc['content'].lower()
            score = sum(1 for word in query_words if word in content_lower)
            if score > 0:
                snippet = ' '.join(doc['content'].split()[:500])
                scored_docs.append({"score": score, "snippet": snippet, "source": doc['filename']})
        
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:self.rag_limit]

    def _construct_prompt(self, query, context_snippets):
        persona = self.current_persona
        persona_prompt = persona["prompt"]
        
        verbose = self.deep_mode or os.getenv("WHETSTONE_VERBOSE", "0") == "1"
        if verbose:
            length_instruction = "\n\nProvide a thoughtful, thorough response. Take your time to explore the question deeply."
        else:
            length_instruction = "\n\nIMPORTANT: Keep your response concise - 2-3 sentences maximum. Be direct and insightful, not exhaustive."
        
        # Clarity mode: accessible language without jargon
        if self.clarity_mode:
            clarity_instruction = "\n\nCLARITY MODE: Speak in plain, accessible language. Avoid technical jargon and specialized terminology. When you must use a complex term, briefly explain it in parentheses. Your goal is to make deep ideas understandable to anyone, not to demonstrate erudition."
        else:
            clarity_instruction = ""

        # Custom Preamble from DB
        custom_preamble = self.db.get_setting(f"persona_preamble_{persona['name']}", "")
        if custom_preamble:
            persona_prompt = f"{custom_preamble}\n\n{persona_prompt}"

        if context_snippets:
            context_str = "\n\n---\n\n".join(
                f"Reference from '{item['source']}':\n{item['snippet']}..."
                for item in context_snippets
            )
            print(f"[DEBUG] RAG Context Dump:\n{context_str[:500]}... [truncated]")
            prompt = f"""{persona_prompt}

Here is some context from your library that may be relevant to the user's query:
---
{context_str}
---

Now, carefully consider the user's question and respond in character, grounding your response in the provided texts.{length_instruction}{clarity_instruction}
User's Question: {query}
AI Philosopher:"""
        else:
            prompt = f"""{persona_prompt}

Carefully consider the user's question and respond in character.{length_instruction}{clarity_instruction}
User's Question: {query}
AI Philosopher:"""
        return prompt

    def chat(self, user_query: str) -> Generator[str, None, None]:
        """
        Main chat function.
        Returns a generator yielding tokens.
        """
        if not self.current_persona or not self.backend:
            yield "Error: System not ready (No persona or backend)."
            return

        # 1. RAG Retrieve
        library_filter = self.current_persona.get('library_filter', [])
        context = self._simple_keyword_search(user_query, library_filter)

        # 2. Construct Prompt
        prompt = self._construct_prompt(user_query, context)
        
        print(f"[DEBUG] Chat Request for Persona: {self.current_persona.get('name')}")
        print(f"[DEBUG] Library Filter: {library_filter}")
        print(f"[DEBUG] RAG Context Items: {len(context)}")
        print(f"[DEBUG] Final Prompt Length (chars): {len(prompt)}")
        print(f"[DEBUG] Sending to backend...")

        # 3. Generate & Stream
        full_response = ""
        for token in self.backend.generate(prompt, stream=True):
            full_response += token
            yield token

        # 4. Log to DB (if enabled)
        self.db.log_interaction(
            persona_name=self.current_persona['name'],
            user_query=user_query,
            ai_response=full_response,
            session_id=self.session_id,
            meta={"deep_mode": self.deep_mode, "context_count": len(context)}
        )
