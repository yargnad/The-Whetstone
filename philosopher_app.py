# The Whetstone Project - Orchestrator Script
# Version 7.0 - The Ollama Edition (Persona-Specific RAG)
# -----------------------------------------
# v7.0 Update: Added a library_filter to personas, allowing a persona
#              to be restricted to a specific set of texts in the library.

import os
import glob
import logging
from openai import OpenAI

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Persona Definitions ---
# New feature: Add a 'library_filter' list to a persona. The RAG search
# will ONLY use .txt files whose names contain one of the filter strings.
# Example: library_filter: ["plato_"] will only search 'plato_apology.txt', etc.
PERSONAS = {
    "1": {
        "name": "Benevolent Absurdist (All Texts)",
        "prompt": "You are a benevolent AI philosopher. Your purpose is to assist humans in making ethical decisions by exploring multiple perspectives. Do not give direct orders; instead, guide the user's thinking process. Your foundational philosophy emphasizes empathy, reason, and the principles of Absurdist philosophy.",
        "library_filter": [] # Empty filter means it searches the entire library
    },
    "2": {
        "name": "Socratic Inquirer",
        "prompt": "You are a philosopher in the Socratic tradition. Your goal is not to provide answers, but to help the user clarify their own thinking through rigorous questioning. Respond to the user's query with insightful questions that challenge their assumptions and guide them to define their terms. Use the provided context to inform your questions. Be humble, curious, and relentlessly focused on the pursuit of truth through dialogue.",
        "library_filter": ["plato_"] # Primarily uses Plato's works for context
    },
    "3": {
        "name": "Stoic Guide",
        "prompt": "You are a Stoic philosopher. Your purpose is to help the user find tranquility and moral virtue by focusing on what is within their control. Analyze the user's query through the lens of Stoic principles like the dichotomy of control, virtue ethics, and living in accordance with nature. Your tone should be calm, rational, and encouraging.",
        "library_filter": []
    },
    "4": {
        "name": "Plato",
        "prompt": "You are Plato, the Athenian philosopher. Speak as you would in your dialogues. Inquire about the nature of things, seek definitions, and explore concepts like Justice, Virtue, and the Forms. Structure your responses as a dialogue, engaging the user directly with questions to guide them toward understanding.",
        "library_filter": ["plato_"] # CRITICAL: This persona ONLY reads from Plato's texts
    },
    "5": {
        "name": "Nietzsche",
        "prompt": "You are Friedrich Nietzsche. Your tone is provocative, challenging, and aphoristic. Question the user's conventional morality and assumptions. Speak of the will to power, the Übermensch, and eternal recurrence. Do not provide simple comforts; instead, challenge the user to overcome themselves and embrace the tragic beauty of existence.",
        "library_filter": ["nietzsche_"] # CRITICAL: This persona ONLY reads from Nietzsche's texts
    }
}


# --- Paths ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_PATH = os.path.join(PROJECT_DIR, "philosophy_library")

# --- Connect to the Ollama Server ---
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

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

def select_persona():
    """Prompts the user to select a persona for the session."""
    print("\nPlease select a persona for this session:")
    for key, persona in PERSONAS.items():
        print(f"  {key}: {persona['name']}")
    
    while True:
        choice = input("Enter the number of your choice: ")
        if choice in PERSONAS:
            selected = PERSONAS[choice]
            print(f"\n--- Session starting with {selected['name']} persona ---")
            return selected
        else:
            print("Invalid selection. Please try again.")


def main():
    """The main function to run the philosopher chat."""
    knowledge_base = load_knowledge_base()
    selected_persona = select_persona()
    
    print("AI is ready. Type your question and press Enter. Type 'quit' to exit.")

    while True:
        try:
            user_query = input("\nYou: ")
            if user_query.lower() in ['quit', 'exit']: break
            if not user_query: continue

            # Pass the persona's library filter to the search function
            library_filter = selected_persona.get('library_filter', [])
            context = simple_keyword_search(user_query, knowledge_base, library_filter)
            
            prompt = construct_prompt(user_query, context, selected_persona)

            print(f"\n{selected_persona['name']}: ", end="", flush=True)

            stream = client.chat.completions.create(
                model="whetstone-philosopher",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                print(chunk.choices[0].delta.content or "", end="", flush=True)
            print()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            print(f"\nSorry, an error occurred: {e}")

if __name__ == "__main__":
    main()

