import asyncio
import unittest

import web_api
from core import PhilosopherCore


class DummyDB:
    def __init__(self):
        self.settings = {}
        self.logging_enabled = True

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value

    def get_history(self, limit=50):
        return []


class DummyCore(PhilosopherCore):
    def __init__(self):
        # Do not call super().__init__ to avoid file and backend side-effects
        self.db = DummyDB()
        self.backend = None
        self.personas = {}
        self.knowledge_base = []
        self.current_persona = None
        self.session_id = "test"
        self.rag_limit = 3
        self.deep_mode = False
        self.clarity_mode = False
        self.journey_memory_enabled = True
        self.ultra_privacy_mode = False
        self.autogen_personas = True
        self.pending_personas = set()

    # Override methods that the API might call but are not under test
    def get_valid_personas(self):
        return list(self.personas.values())

    def _ensure_default_persona(self):
        if not self.current_persona and self.personas:
            self.current_persona = next(iter(self.personas.values()))


class PersonaPendingTests(unittest.TestCase):
    def setUp(self):
        self.core = DummyCore()
        web_api.core = self.core

    def test_mark_pending_and_ready_syncs_flags(self):
        self.core.personas = {
            "marcus aurelius": {"name": "Marcus Aurelius", "pending": False}
        }
        self.core.mark_persona_pending("Marcus Aurelius")
        self.assertIn("Marcus Aurelius", self.core.pending_personas)
        self.assertTrue(self.core.personas["marcus aurelius"].get("pending"))
        self.core.mark_persona_ready("Marcus Aurelius")
        self.assertNotIn("Marcus Aurelius", self.core.pending_personas)
        self.assertFalse(self.core.personas["marcus aurelius"].get("pending"))

    def test_list_personas_includes_pending_flag(self):
        self.core.personas = {
            "plato": {
                "name": "Plato",
                "description": "",
                "library_filter": [],
                "category": "philosophy",
                "source_codex": "plato.codex",
                "pending": True,
            }
        }
        result = asyncio.run(web_api.list_personas())
        personas = result["personas"]
        self.assertEqual(len(personas), 1)
        self.assertTrue(personas[0]["pending"])


if __name__ == "__main__":
    unittest.main()
