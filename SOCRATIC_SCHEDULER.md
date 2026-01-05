# Socratic Scheduler (MOTD) Specification

**Component Status:** 📋 Specification Phase
**Purpose:** Proactively engage the user with philosophical prompts on a schedule ("Socratic Alarm Clock").

---

## 1. Feature Overview

The system will wake up at user-defined times to deliver a "provocation" or "thought of the day."

**Key Capabilities:**

- **Schedule:** Daily, specific days, or interval-based (e.g., "Every morning at 8:00 AM").
- **Persona:** Specific philosopher (e.g., "Nietzsche only") or Random.
- **Interaction Type:**
    1. **Rhetorical:** A standalone quote or aphorism (e.g., "He who has a why to live...").
    2. **Question:** A direct challenge to the user (e.g., "Are you acting freely today, or merely reacting?").
    3. **Custom Prompt:** User defines the seed (e.g., "Roast my morning routine").

## 2. Configuration Schema

Stored in `scheduler_config.json`:

```json
{
  "schedules": [
    {
      "id": "morning_glory",
      "time": "08:00",
      "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "enabled": true,
      "persona": "random",  // or precise name "nietzsche"
      "type": "question",   // "rhetorical", "question", "custom"
      "custom_prompt": null // set string if type is "custom"
    },
    {
      "id": "friday_reflection",
      "time": "17:00",
      "days": ["Fri"],
      "enabled": true,
      "persona": "marcus aurelius",
      "type": "rhetorical",
      "custom_prompt": null
    }
  ]
}
```

## 3. Implementation Strategy

### Python `schedule` Library

Since the app runs as a service, we can use the lightweight `schedule` python library running in a background thread within `philosopher_app.py`.

```python
import schedule
import time
import threading

def interaction_job(config):
    # 1. Load Persona
    # 2. Generate content via LLM
    # 3. Trigger "Poke" (Display update / Audio chime)
    pass

scheduler.every().day.at("08:00").do(interaction_job, config=morning_config)
```

### The "Poke" Mechanism

How does the device get attention?

1. **Audio:** Play a subtle chime or "throat clearing" sound.
2. **Display:** Update E-Ink with the text.
3. **LED:** Pulse specific color (e.g., Cyan for "Thought Ready").
4. **TTS:** Optionally read it aloud immediately (configurable).

## 4. User Interface

Added to **Settings Menu**:

```
4: Socratic Scheduler
   > 1. Add Schedule
   > 2. List/Edit Schedules
   > 3. Toggle Global Scheduler (ON/OFF)
```
