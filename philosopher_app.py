# The Whetstone Project - Orchestrator Script
# Version 7.0 - The Ollama Edition (Persona-Specific RAG)
# -----------------------------------------
# v7.0 Update: Added a library_filter to personas, allowing a persona
#              to be restricted to a specific set of texts in the library.



import os
import glob
import logging
import json
import subprocess
import sys
import time
import socket
from openai import OpenAI

# --- Configuration ---
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Ollama Server Auto-Launch ---
def is_ollama_running(host="127.0.0.1", port=11434):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

def launch_ollama_server():
    print("[INFO] Ollama server not detected. Launching 'ollama serve' with 16k context window...")
    env = os.environ.copy()
    env["OLLAMA_CONTEXT_LENGTH"] = "16384"
    if sys.platform.startswith("win"):
        # Windows: creationflags=DETACHED_PROCESS
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(["ollama", "serve"], creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    else:
        # Unix: start new session
        subprocess.Popen(["ollama", "serve"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    # Wait for server to be ready
    for _ in range(30):
        if is_ollama_running():
            print("[INFO] Ollama server is now running.")
            return
        time.sleep(1)
    print("[ERROR] Ollama server did not start within 30 seconds. Please check your installation.")
    sys.exit(1)


# --- Persona Config ---
PERSONAS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "philosophy_library", "personas.json")

def load_personas():
    if not os.path.exists(PERSONAS_PATH):
        logging.warning(f"Personas config not found at {PERSONAS_PATH}. Run the persona update script.")
        return {}
    with open(PERSONAS_PATH, "r", encoding="utf-8") as f:
        personas = json.load(f)
    return personas


# --- Paths ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_DIR, "philosophy_library")

# --- Connect to the Ollama Server ---
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Default LLM model for all completions
LLM_MODEL = "qwen3:8b"

# --- Knowledge Base / RAG Functions ---

def load_knowledge_base():
    """Loads all .txt files from the philosophy_library directory."""
    logging.info(f"Loading knowledge base from: {KNOWLEDGE_BASE_PATH}")
    docs = []
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        logging.warning(f"Knowledge base directory not found. RAG will be empty.")
        return []
    for filepath in glob.glob(os.path.join(KNOWLEDGE_BASE_PATH, "*.txt")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                filename = os.path.basename(filepath)
                content = f.read()
                docs.append({"filename": filename, "content": content})
                logging.info(f"  - Loaded '{filename}'")
        except Exception as e:
            logging.error(f"Failed to load {filepath}: {e}")
    return docs

def simple_keyword_search(query, documents, library_filter, num_results=3):
    """
    A simple RAG implementation. Finds documents with the most matching keywords,
    now with an added filtering step based on the selected persona.
    """
    # Step 1: Filter the documents based on the persona's library_filter
    filtered_documents = documents
    if library_filter:
        logging.info(f"Applying library filter: {library_filter}")
        filtered_documents = []
        for doc in documents:
            # Check if any of the filter keywords are in the document's filename
            if any(f.lower() in doc['filename'].lower() for f in library_filter):
                filtered_documents.append(doc)
    
    logging.info(f"Searching within {len(filtered_documents)} filtered documents.")

    # Step 2: Perform keyword search on the (potentially filtered) documents
    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    if not query_words: return []
    
    scored_docs = []
    for doc in filtered_documents:
        content_lower = doc['content'].lower()
        score = sum(1 for word in query_words if word in content_lower)
        if score > 0:
            snippet = ' '.join(doc['content'].split()[:500])
            scored_docs.append({"score": score, "snippet": snippet, "source": doc['filename']})
    
    scored_docs.sort(key=lambda x: x['score'], reverse=True)
    logging.info(f"Found {len(scored_docs)} relevant snippets for the query.")
    return scored_docs[:num_results]

def construct_prompt(query, context_snippets, selected_persona):
    """Constructs the final prompt for the LLM, using the selected persona."""
    persona_prompt = selected_persona["prompt"]

    if context_snippets:
        context_str = "\n\n---\n\n".join(
            f"Reference from '{item['source']}':\n{item['snippet']}..."
            for item in context_snippets
        )
        prompt_template = f"""{persona_prompt}

Here is some context from your library that may be relevant to the user's query:
---
{context_str}
---

Now, carefully consider the user's question and respond in character, grounding your response in the provided texts.
User's Question: {query}
AI Philosopher:"""
    else:
        prompt_template = f"""{persona_prompt}

Carefully consider the user's question and respond in character.
User's Question: {query}
AI Philosopher:"""
    return prompt_template

# --- Main Application Loop ---



def select_persona(personas):
    """Prompts the user to select a persona for the session, excluding placeholders like 'example'."""
    # Exclude keys like 'example', 'test', or empty names
    persona_keys = [k for k in personas.keys() if k.lower() not in {"example", "test", "placeholder"} and personas[k].get("name", "").strip()]
    if not persona_keys:
        print("No valid personas found.")
        return None
    print("\nPlease select a persona for this session:")
    for idx, key in enumerate(persona_keys, 1):
        print(f"  {idx}: {personas[key]['name']}")
    while True:
        choice = input("Enter the number of your choice: ")
        if choice.isdigit() and 1 <= int(choice) <= len(persona_keys):
            selected = personas[persona_keys[int(choice)-1]]
            print(f"\n--- Session starting with {selected['name']} persona ---")
            return selected
        else:
            print("Invalid selection. Please try again.")

def main():
    """The main function to run the philosopher chat."""
    scan_mode = "shallow"  # default
    while True:
        print("\n--- The Whetstone Philosopher ---")
        print("1: Start chat")
        print("2: Settings")
        print("3: Quit")
        menu_choice = input("Select an option: ").strip()
        if menu_choice == "1":
            personas = load_personas()
            if not personas:
                print("No personas found. Please run the persona update script first.")
                continue
            knowledge_base = load_knowledge_base()
            selected_persona = select_persona(personas)
            print("AI is ready. Type your question and press Enter. Type 'quit' to end chat and return to the main menu.")

            while True:
                try:
                    user_query = input("\nYou: ")
                    if user_query.lower() in ['quit', 'exit']:
                        print("\nChat ended. Returning to main menu.")
                        break
                    if not user_query:
                        continue

                    # Pass the persona's library filter to the search function
                    library_filter = selected_persona.get('library_filter', [])
                    context = simple_keyword_search(user_query, knowledge_base, library_filter)
                    
                    prompt = construct_prompt(user_query, context, selected_persona)

                    print(f"\n{selected_persona['name']}: ", end="", flush=True)

                    stream = client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        stream=True,
                    )
                    for chunk in stream:
                        print(chunk.choices[0].delta.content or "", end="", flush=True)
                    print()

                except KeyboardInterrupt:
                    print("\nExiting chat and returning to main menu...")
                    break
                except Exception as e:
                    logging.error(f"An error occurred: {e}")
                    print(f"\nSorry, an error occurred: {e}")
        elif menu_choice == "2":
            while True:
                print("\n--- Settings ---")
                print(f"1: Persona Generation Scan Mode (current: {scan_mode})")
                print("2: Update Personas (run generator)")
                print("3: Back to Main Menu")
                settings_choice = input("Select a settings option: ").strip()
                if settings_choice == "1":
                    print("\nSelect scan mode for persona generation:")
                    print("1: Shallow (sample only, faster)")
                    print("2: Deep (full text, slower, more accurate)")
                    scan_input = input("Enter 1 or 2: ").strip()
                    if scan_input == "1":
                        scan_mode = "shallow"
                        print("Scan mode set to shallow.")
                    elif scan_input == "2":
                        scan_mode = "deep"
                        print("Scan mode set to deep.")
                    else:
                        print("Invalid selection.")
                elif settings_choice == "2":
                    print("Updating personas by scanning the library...")
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "philosophy_library", "generate_personas.py")
                    cmd = [sys.executable, script_path]
                    if scan_mode == "deep":
                        cmd.append("--deep")
                    result = subprocess.run(cmd, cwd=os.path.dirname(script_path))
                    if result.returncode != 0:
                        print(f"[ERROR] Persona generation failed with exit code {result.returncode}")
                    print("Reloading personas...")
                elif settings_choice == "3":
                    break
                else:
                    print("Invalid selection. Please try again.")
        elif menu_choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    if not is_ollama_running():
        launch_ollama_server()
    main()

