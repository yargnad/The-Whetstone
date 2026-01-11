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

    def interject(self, message: str, target: str = None):
        """
        Injects a user/moderator message into the debate.
        target: 'a', 'b', or None (both/general)
        """
        turn_data = {
            "speaker": "Moderator",
            "text": message,
            "turn": self.turn_count + 1,
            "type": "interjection",
            "target": target
        }
        self.history.append(turn_data)
        self.turn_count += 1
        return turn_data

    def _construct_debate_prompt(self, speaker_persona: Dict, opponent_persona: Dict, last_turn: Dict = None) -> str:
        """
        Constructs a prompt specifically for debate/dialectical mode.
        """
        prompt = f"""{speaker_persona['prompt']}

You are currently in a debate (The Symposium).
Your opponent is: {opponent_persona['name']}.
The topic is: "{self.topic}".

"""
        if not last_turn:
            # Opening statement
            prompt += f"You are making the opening statement on this topic. State your position clearly and provocatively."
        elif last_turn.get("type") == "interjection":
            # Responding to Moderator
            prompt += f"""The Debate Moderator just interjected with:
---
{last_turn['text']}
---

Address this point directly. It may be a new question, a challenge to the previous point, or a redirection. Integrate it into your philosophical stance."""
        else:
            # Rebuttal
            prompt += f"""Your opponent ({opponent_persona['name']}) just said:
---
{last_turn['text']}
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
        # Check if last turn was an interjection with a specific target
        last_turn = self.history[-1] if self.history else None
        forced_speaker = None
        
        if last_turn and last_turn.get("type") == "interjection":
            target = last_turn.get("target")
            if target == "a":
                forced_speaker = self.persona_a
            elif target == "b":
                forced_speaker = self.persona_b
        
        if forced_speaker:
            speaker = forced_speaker
            opponent = self.persona_b if speaker == self.persona_a else self.persona_a
        else:
            # Standard logic: find who spoke LAST (ignoring moderator) to find who speaks NEXT.
            last_philosopher_turn = -1
            for i in range(len(self.history) - 1, -1, -1):
                if self.history[i].get("type") != "interjection":
                    # Check if it was A or B
                    if self.history[i]["speaker"] == self.persona_a["name"]:
                        last_philosopher_turn = 0 # A spoke last
                    else:
                        last_philosopher_turn = 1 # B spoke last
                    break
            
            if last_philosopher_turn == -1:
                # No philosophers have spoken yet, start with A
                speaker = self.persona_a
                opponent = self.persona_b
            elif last_philosopher_turn == 0:
                # A spoke last, so B speaks
                speaker = self.persona_b
                opponent = self.persona_a
            else:
                # B spoke last, so A speaks
                speaker = self.persona_a
                opponent = self.persona_b

        # prompt
        prompt = self._construct_debate_prompt(speaker, opponent, last_turn)
        
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
            context_text = last_turn['text'][:50] if last_turn else "Opening"
            self.core.db.log_interaction(
                persona_name=speaker['name'],
                user_query=f"[Symposium vs {opponent['name']}] Context: {context_text}...",
                ai_response=full_response,
                session_id=self.core.session_id,
                meta={"type": "symposium", "topic": self.topic, "turn": self.turn_count}
            )

        self.turn_count += 1
        yield {"type": "complete", "content": turn_data}
