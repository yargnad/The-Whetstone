import schedule
import time
import threading
import logging
import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from core import PhilosopherCore

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    id: str
    name: str
    interval_minutes: int
    action_type: str  # "toast", "modal", "audio"
    persona_name: str # "Random" or specific name
    topic: str
    enabled: bool = True
    last_run: float = 0.0

class SocraticScheduler:
    """
    Background service that schedules 'Socratic Pokes' and Dream Mode tasks.
    """
    def __init__(self, core: PhilosopherCore):
        self.core = core
        self.running = False
        self.thread = None
        self.tasks: List[ScheduledTask] = []
        self.ui_callback: Optional[Callable[[str, str, str], None]] = None # (title, message, type) -> None

    def set_ui_callback(self, callback: Callable):
        """Register a callback for UI updates (thread-safe calls handled by caller/wrapper)."""
        self.ui_callback = callback

    def start(self):
        """Start the scheduler thread."""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("[SCHEDULER] Service started.")

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("[SCHEDULER] Service stopped.")

    def _run_loop(self):
        """Main loop for the background thread."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def add_task(self, name: str, interval: int, action: str, persona: str = "Random", topic: str = ""):
        """Create and register a new task."""
        task_id = str(uuid.uuid4())[:8]
        new_task = ScheduledTask(
            id=task_id,
            name=name,
            interval_minutes=interval,
            action_type=action,
            persona_name=persona,
            topic=topic
        )
        self.tasks.append(new_task)
        
        # Determine strict schedule
        # Note: schedule library keeps job in memory. We need to associate it to remove later.
        # For simplicity in this V2 prototype, we clear and rebuild schedule on change, or use tags.
        self._register_job(new_task)
        
        logger.info(f"Added task: {name} ({interval}m)")
        return new_task

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        schedule.clear(task_id) # Use ID as tag

    def _register_job(self, task: ScheduledTask):
        """Register the schedule job with a tag."""
        job = schedule.every(task.interval_minutes).minutes.do(self._execute_wrapper, task)
        job.tag(task.id)

    def _execute_wrapper(self, task: ScheduledTask):
        """Wrapper to pass the task object to execution logic."""
        if not task.enabled: return
        self.execute_task(task)

    def execute_task(self, task: ScheduledTask):
        """
        The Action: Pick persona, generate content, trigger callback.
        """
        logger.info(f"Executing task: {task.name}")
        
        # 1. Pick Persona
        if task.persona_name.lower() == "random":
            valid_personas = self.core.get_valid_personas()
            if not valid_personas: return
            persona = random.choice(valid_personas)
        else:
            # Find specific
            persona = next((p for p in self.core.get_valid_personas() if p['name'] == task.persona_name), None)
            if not persona: return

        # 2. Generate Content
        # Contextualize based on task type
        if task.action_type == "dream_mode":
            prompt_context = f"Generate a profound, dream-like aphorism{' about ' + task.topic if task.topic else ''}."
        else: # Poke/Toast
            prompt_context = f"Generate a short, sharp {random.choice(['question', 'insight'])} to wake the user up."

        prompt = f"""{persona['prompt']}

TASK: {prompt_context}
Limit: 1-2 sentences. No small talk.
"""
        try:
            response_gen = self.core.backend.generate(prompt, stream=False)
            response_text = "".join(list(response_gen)).strip()
            
            # 3. Deliver via Callback
            if self.ui_callback:
                self.ui_callback(title=f"{persona['name']} ({task.name})", message=response_text, type=task.action_type)
                
            # Log
            if self.core.db.logging_enabled:
                 self.core.db.log_interaction(
                    persona_name=persona['name'],
                    user_query=f"[SCHEDULED: {task.name}]",
                    ai_response=response_text,
                    session_id="scheduler",
                    meta={"type": task.action_type}
                )
        except Exception as e:
            logger.error(f"Task execution failed: {e}")

    # --- Pre-sets ---
    def load_demo_defaults(self):
        """Load the default 'Dream Mode' 1 min poke."""
        self.add_task("Dream Mode Demo", 1, "dream_mode", "Random", "Philosophy")
