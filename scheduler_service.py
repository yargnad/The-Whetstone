import schedule
import time
import threading
import logging
import random
from typing import Dict, List, Optional

from core import PhilosopherCore

logger = logging.getLogger(__name__)

class SocraticScheduler:
    """
    Background service that schedules 'Socratic Pokes' - proactive interventions.
    """
    def __init__(self, core: PhilosopherCore):
        self.core = core
        self.running = False
        self.thread = None
        self.schedules = [] # List of job objects

        # Default configuration (Hardcoded for prototype phase)
        # In Phase 3, load this from JSON
        self.config = {
            "enabled": True,
            "jobs": [
                # Example: Explicitly defined jobs could go here
            ]
        }

    def start(self):
        """Start the scheduler thread."""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[SCHEDULER] Service started.")

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[SCHEDULER] Service stopped.")

    def _run_loop(self):
        """Main loop for the background thread."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    # --- Job Definers ---

    def schedule_random_poke(self, interval_minutes: int = 60):
        """Schedule a random philosophical poke every X minutes."""
        print(f"[SCHEDULER] Registering random poke every {interval_minutes} minutes.")
        schedule.every(interval_minutes).minutes.do(self.execute_poke)

    def execute_poke(self):
        """
        The Action: Pick a random persona and generate a short provocation.
        """
        # 1. Pick Persona
        valid_personas = self.core.get_valid_personas()
        if not valid_personas: return
        persona = random.choice(valid_personas)

        # 2. Pick Type
        poke_type = random.choice(["rhetorical", "question"])
        
        # 3. Generate
        prompt = f"""{persona['prompt']}

You are "poking" the user to wake them up from their daily routine.
Generate a sudden, short, 1-sentence {poke_type} insight.
Do not say "Hello". Just deliver the insight like a lightning bolt.
"""
        response = self.core.backend.generate(prompt)

        # 4. Deliver (Currently just Print + Log)
        self._deliver_payload(persona['name'], response)

    def _deliver_payload(self, speaker: str, text: str):
        """
        Handles the output mechanism (CLI print, Audio, E-Ink).
        """
        timestamp = time.strftime("%H:%M")
        
        # CLI Output (Visual interrupt)
        print(f"\n\n[🔔 SOCRATIC ALARM {timestamp}]")
        print(f"{speaker}: {text}")
        print(f"[Press Enter to resume...]\n")
        
        # Log it
        if self.core.db.logging_enabled:
            self.core.db.log_interaction(
                persona_name=speaker,
                user_query="[SYSTEM SCHEDULED POKE]",
                ai_response=text,
                session_id="scheduler",
                meta={"type": "poke"}
            )

    # --- Test Helper ---
    def test_poke_now(self):
        """Run a poke immediately (for verification)."""
        print("[SCHEDULER] Testing Poke...")
        self.execute_poke()
