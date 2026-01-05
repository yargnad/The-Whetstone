import os
import json
import logging
import uuid
import glob
from typing import Optional, Generator, Dict, List

from database import DatabaseManager
from backends import create_backend, LLMBackend

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAS_PATH = os.path.join(PROJECT_DIR, "philosophy_library", "personas.json")
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_DIR, "philosophy_library")

class PhilosopherCore:
    def __init__(self):
        self.db = DatabaseManager()
        self.backend: Optional[LLMBackend] = None
        self.personas: Dict = {}
        self.knowledge_base: List[Dict] = []
        self.current_persona: Optional[Dict] = None
        self.session_id = str(uuid.uuid4())
        self.deep_mode = False
        self.rag_limit = 3  # Number of RAG snippets to retrieve

        # Initialize
        self._init_backend()
        self.refresh_data()

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
        if not os.path.exists(PERSONAS_PATH):
            logger.warning(f"Personas config not found at {PERSONAS_PATH}")
            return {}
        with open(PERSONAS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

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
        print(f"[CORE] Persona set to: {persona.get('name')}")

    def set_deep_mode(self, enabled: bool):
        self.deep_mode = enabled

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

Now, carefully consider the user's question and respond in character, grounding your response in the provided texts.{length_instruction}
User's Question: {query}
AI Philosopher:"""
        else:
            prompt = f"""{persona_prompt}

Carefully consider the user's question and respond in character.{length_instruction}
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
