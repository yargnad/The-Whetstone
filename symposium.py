import time
import logging
from typing import Dict, List, Generator

from core import PhilosopherCore

logger = logging.getLogger(__name__)

class Symposium:
    """
    Manages a Socratic Debate (Symposium) between two AI personas.
    """
    def __init__(self, core: PhilosopherCore, persona_a: Dict, persona_b: Dict, topic: str):
        self.core = core
        self.persona_a = persona_a
        self.persona_b = persona_b
        self.topic = topic
        self.history = []  # List of turns: {"speaker": "Plato", "text": "..."}
        self.turn_count = 0
        self.is_active = True

    def _construct_debate_prompt(self, speaker_persona: Dict, opponent_persona: Dict, last_turn_text: str = None) -> str:
        """
        Constructs a prompt specifically for debate/dialectical mode.
        """
        prompt = f"""{speaker_persona['prompt']}

You are currently in a debate (The Symposium).
Your opponent is: {opponent_persona['name']}.
The topic is: "{self.topic}".

"""
        if not last_turn_text:
            # Opening statement
            prompt += f"You are making the opening statement on this topic. State your position clearly and provocatively."
        else:
            # Rebuttal
            prompt += f"""Your opponent ({opponent_persona['name']}) just said:
---
{last_turn_text}
---

Respond to their points directly. Challenge their assumptions. Use your specific philosophical framework to deconstruct their argument. 
Keep your response concise (2-4 sentences) but dense with insight. Do not be polite; be dialectical."""

        prompt += f"\n\n{speaker_persona['name']}:"
        return prompt

    def next_turn(self) -> Generator[Dict, None, None]:
        """
        Executes the next turn in the debate.
        Yields tokens for streaming, then returns the full turn object.
        """
        # Determine speaker
        if self.turn_count % 2 == 0:
            speaker = self.persona_a
            opponent = self.persona_b
        else:
            speaker = self.persona_b
            opponent = self.persona_a

        # Get last turn text for context
        last_text = self.history[-1]['text'] if self.history else None

        # prompt
        prompt = self._construct_debate_prompt(speaker, opponent, last_text)
        
        # Use a temporary "current persona" context for the core RAG (optional, maybe skip RAG for pure debate to keep flow?)
        # For now, let's use the core's generation directly without RAG to keep it focused on the opponent.
        
        full_response = ""
        
        # Stream the response
        # We manually call backend here to avoid the chat() method's RAG/Prompt logic
        for token in self.core.backend.generate(prompt, stream=True):
            full_response += token
            yield {"type": "token", "content": token, "speaker": speaker['name']}
        
        # Record history
        turn_data = {
            "speaker": speaker['name'],
            "text": full_response,
            "turn": self.turn_count + 1
        }
        self.history.append(turn_data)
        
        # Log to DB (if enabled)
        # We treat this as a "System" interaction or link it to the user who started it
        if self.core.db.logging_enabled:
            self.core.db.log_interaction(
                persona_name=speaker['name'],
                user_query=f"[Symposium vs {opponent['name']}] Context: {last_text[:50]}...",
                ai_response=full_response,
                session_id=self.core.session_id,
                meta={"type": "symposium", "topic": self.topic, "turn": self.turn_count}
            )

        self.turn_count += 1
        yield {"type": "complete", "content": turn_data}
