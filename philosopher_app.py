# The Whetstone Project - Orchestrator Script
# Version 10.0 - Symposium & Scheduler Edition
# -----------------------------------------
# v10.0 Update: Integrated 'The Symposium' (AI-AI Debate) and 'Socratic Scheduler'.
# v9.0 Update: Refactored to use PhilosopherCore (core.py) and Database (database.py).

import os
import sys
import logging
import subprocess
import socket
import time

# Import Core & Services
from core import PhilosopherCore
from symposium import Symposium
from scheduler_service import SocraticScheduler

# --- Configuration ---
logging.basicConfig(
    filename='philosopher_debug.log',
    level=logging.WARNING, # Keep warning level default but log to file
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- CLI Functions ---
from utils import is_ollama_running, launch_ollama_server

def select_persona_cli(core: PhilosopherCore, prompt_text="Please select a persona:"):
    """CLI wrapper for selecting a persona."""
    valid_personas = core.get_valid_personas()
    if not valid_personas:
        print("No Valid Personas found. Please update library.")
        return None
        
    print(f"\n{prompt_text}")
    for idx, p in enumerate(valid_personas, 1):
        print(f"  {idx}: {p['name']}")
        
    while True:
        choice = input("Enter number (or 'q' to cancel): ")
        if choice.lower() == 'q': return None
        if choice.isdigit() and 1 <= int(choice) <= len(valid_personas):
            selected = valid_personas[int(choice)-1]
            return selected
        else:
            print("Invalid selection.")

def run_symposium(core: PhilosopherCore):
    """Run the AI-AI Debate Loop."""
    print("\n--- The Symposium (AI Debate) ---")
    print("Select two philosophers to debate a topic.")
    
    p1 = select_persona_cli(core, "Select First Philosopher:")
    if not p1: return
    
    p2 = select_persona_cli(core, "Select Second Philosopher:")
    if not p2: return
    
    topic = input("\nEnter the Debate Topic: ").strip()
    if not topic: return
    
    symposium = Symposium(core, p1, p2, topic)
    print(f"\n--- BEGIN SYMPOSIUM: {p1['name']} vs. {p2['name']} on '{topic}' ---")
    print("[Press Enter after each turn to continue, or type 'q' to quit]")
    
    try:
        # Initial turn
        input("\n[Press Enter to start opening statement...]")
        
        while True:
            current_turn = None
            speaker_label_printed = False
            
            for token_obj in symposium.next_turn():
                if token_obj['type'] == 'token':
                    if not speaker_label_printed:
                        print(f"\n[{token_obj['speaker']}]: ", end="", flush=True)
                        speaker_label_printed = True
                    print(token_obj['content'], end="", flush=True)
                elif token_obj['type'] == 'complete':
                    current_turn = token_obj['content']
            print("\n")
            
            user_action = input("> ")
            if user_action.lower() == 'q':
                print("Ending Symposium.")
                break
                
    except KeyboardInterrupt:
        print("\nSymposium interrupted.")

def run_cli_mode():
    """Main CLI Loop."""
    
    # Initialize Core
    core = PhilosopherCore()
    
    # Initialize Scheduler (Background Service)
    scheduler = SocraticScheduler(core)
    # For prototype: auto-start scheduler logic if enabled in config (later)
    # scheduler.start()  # Uncomment to auto-start, or use menu
    
    scan_mode = "shallow"
    
    try:
        while True:
            mode_indicator = "🔍 DEEP" if core.deep_mode else "⚡ QUICK"
            privacy_indicator = "🛑 PRIVATE" if not core.db.logging_enabled else "💾 RECORDING"
            sched_indicator = "⏰ SCHED ON" if scheduler.running else "💤 SCHED OFF"
            
            print(f"\n--- The Whetstone Philosopher [{mode_indicator}] [{privacy_indicator}] [{sched_indicator}] ---")
            print("1: Start Chat (You vs AI)")
            print("2: The Symposium (AI vs AI)")
            print("3: Settings (Privacy, Scheduler, Modes)")
            print("4: Quit")
            menu_choice = input("Select an option: ").strip()

            if menu_choice == "1":
                # Regular Chat
                persona = select_persona_cli(core)
                if persona:
                    core.set_persona(persona)
                    print(f"\n--- Session starting with {persona['name']} ---")
                    print("AI is ready. Type your question and press Enter.")
                    print("Commands: 'quit' to exit, '/deep' to toggle deep mode")
                    
                    while True:
                        try:
                            mode_tag = "[DEEP] " if core.deep_mode else ""
                            rec_tag = "[REC] " if core.db.logging_enabled else ""
                            
                            user_query = input(f"\n{rec_tag}{mode_tag}You: ")
                            
                            if user_query.lower() in ['quit', 'exit']:
                                break
                            
                            if user_query.lower() == '/deep':
                                core.deep_mode = not core.deep_mode
                                print(f"Deep Mode: {'ON' if core.deep_mode else 'OFF'}")
                                continue

                            if not user_query: continue
                            
                            print(f"\n{core.current_persona['name']}: ", end="", flush=True)
                            for token in core.chat(user_query):
                                print(token, end="", flush=True)
                            print()
                            
                        except KeyboardInterrupt:
                            break
                        except Exception as e:
                            print(f"Error: {e}")

            elif menu_choice == "2":
                run_symposium(core)
                
            elif menu_choice == "3":
                while True:
                    deep_str = "ON" if core.deep_mode else "OFF"
                    priv_str = "ENABLED" if core.db.logging_enabled else "DISABLED"
                    sched_str = "RUNNING" if scheduler.running else "STOPPED"
                    
                    print("\n--- Settings ---")
                    print(f"1: Deep Reasoning Mode (current: {deep_str})")
                    print(f"2: Privacy/Research Log (current: {priv_str})")
                    print(f"3: Socratic Scheduler (current: {sched_str})")
                    print(f"4: Persona Scan Mode (current: {scan_mode})")
                    print("5: Update Personas")
                    print("6: Back")
                    
                    choice = input("Option: ").strip()
                    
                    if choice == "1":
                        core.deep_mode = not core.deep_mode
                    elif choice == "2":
                        if not core.db.logging_enabled:
                            if input("Enable logging? (y/N): ").lower() == 'y':
                                core.set_logging(True)
                        else:
                            core.set_logging(False)
                    elif choice == "3":
                        if not scheduler.running:
                            print("Starting Socratic Scheduler...")
                            # For demo, add a 1-minute poke
                            scheduler.schedule_random_poke(1) 
                            scheduler.start()
                            print("Scheduler STARTED. Expect a poke every 1 minute (Demo Mode).")
                        else:
                            scheduler.stop()
                            print("Scheduler STOPPED.")
                    elif choice == "4":
                        scan_mode = "deep" if scan_mode == "shallow" else "shallow"
                    elif choice == "5":
                         script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "philosophy_library", "generate_personas.py")
                         cmd = [sys.executable, script_path]
                         if scan_mode == "deep": cmd.append("--deep")
                         subprocess.run(cmd, cwd=os.path.dirname(script_path))
                         core.refresh_data()
                    elif choice == "6":
                        break

            elif menu_choice == "4":
                scheduler.stop() # Clean up thread
                print("Goodbye.")
                break

    except KeyboardInterrupt:
        scheduler.stop()
        print("\nForce Quit.")

if __name__ == "__main__":
    if os.getenv("WHETSTONE_BACKEND", "ollama") == "ollama":
        if not is_ollama_running():
            launch_ollama_server()
    run_cli_mode()
