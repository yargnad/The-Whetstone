import os
import json
import logging
import uuid
import glob
import re
from typing import Optional, Generator, Dict, List

from database import DatabaseManager
from backends import create_backend, LLMBackend

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAS_PATH = os.path.join(PROJECT_DIR, "philosophy_library", "personas.json")
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_DIR, "philosophy_library")


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

        # Initialize
        self._init_backend()
        self.refresh_data()
        self._load_saved_persona()
    
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
            self.backend = create_backend()
            print(f"[CORE] Backend ready: {self.backend.name}")
        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            print(f"[CORE] Error initializing backend: {e}")

    def refresh_data(self):
        """Reload personas and knowledge base."""
        self.personas = self._load_personas()
        self.knowledge_base = self._load_knowledge_base()

    def _load_personas(self):
        personas = {}
        # 1. Load Legacy JSON
        if os.path.exists(PERSONAS_PATH):
            with open(PERSONAS_PATH, "r", encoding="utf-8") as f:
                try: personas = json.load(f)
                except Exception as e: logger.error(f"Error loading personas.json: {e}")
        
        # 2. Scan for .codex files
        codex_files = glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*.codex"))
        import zipfile
        
        for codex_path in codex_files:
            try:
                with zipfile.ZipFile(codex_path, 'r') as z:
                    # Check for codex.json
                    if "codex.json" in z.namelist():
                        with z.open("codex.json") as m:
                            manifest = json.load(m)
                            # Adapter: Codex V2 -> Internal Persona
                            p_name = manifest.get("meta", {}).get("name", "Unknown Codex")
                            
                            # Start with bootstrap instructions as base
                            p_prompt = manifest.get("bootstrap_instructions", "")
                            
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
                            
                            personas[p_name] = {
                                "name": p_name,
                                "prompt": p_prompt,
                                "description": manifest.get("meta", {}).get("description", ""),
                                "source_codex": os.path.basename(codex_path)
                            }
                            print(f"[CORE] Loaded Codex: {p_name}")
            except Exception as e:
                logger.error(f"Failed to load Codex {codex_path}: {e}")
                
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
