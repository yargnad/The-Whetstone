import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import PhilosopherCore

def debug_chat():
    print("--- Initializing Core ---")
    core = PhilosopherCore()
    
    print("\n--- Selecting Persona: Solomon Northup ---")
    # Finding the persona key
    target = None
    for p in core.get_valid_personas():
        if "Solomon" in p['name']:
            target = p
            break
            
    if not target:
        print("ERROR: Solomon Northup persona not found!")
        return

    core.set_persona(target)
    print(f"Active Persona: {core.current_persona['name']}")
    print(f"System Prompt: {core.current_persona['prompt'][:100]}...")

    print("\n--- Attempting Chat ---")
    try:
        response_gen = core.chat("Hello, who are you?")
        full_response = ""
        for token in response_gen:
            print(token, end="", flush=True)
            full_response += token
        print("\n\n[DONE]")
        if not full_response:
            print("FAILURE: Received empty response.")
    except Exception as e:
        print(f"\nCRASH: {e}")

debug_chat()
