
import os
import time
import json
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from auto_curator_v3 import process_book, emit_codex_for_author, normalize_author_name, slugify, apply_exclusions, explode_codex

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
CODEX_DIR = os.path.join(BASE_DIR, "codex_library", "philosophy")
CURATED_DIR = os.path.join(BASE_DIR, "curated")
# We expect personas.json to be in codex_library after migration
PERSONAS_PATH = os.path.join(CODEX_DIR, "personas.json")
# Fallback
OLD_PERSONAS_PATH = os.path.join(BASE_DIR, "philosophy_library", "personas.json")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CODEX_DIR, exist_ok=True)
os.makedirs(CURATED_DIR, exist_ok=True)

class HybridIngestHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        self.process(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.process(event.src_path)

    def process(self, filepath):
        try:
            filename = os.path.basename(filepath)
            
            # 1. Handle CODEX files (The Explosion)
            if filepath.startswith(CODEX_DIR) and (filename.endswith('.codex')):
                print(f"[Watcher] 📦 CODEX detected: {filename}")
                explode_codex(filepath)
                return

            # 2. Handle Raw Files (The Auto-Packer)
            if filepath.startswith(RAW_DIR) and filename.endswith('.txt'):
                print(f"[Watcher] 📝 Raw text detected: {filename}")
                self.handle_raw_text(filepath)

        except Exception as e:
            print(f"[Watcher] ❌ Error processing {filepath}: {e}")

    def handle_raw_text(self, filepath):
        # A. Process the text (Clean it)
        print("   Running Auto-Curator logic...")
        metadata = process_book(filepath)
        curated_path = metadata.get("curated_path")
        
        if not curated_path:
            print("   ⚠️ processing failed, no curated path.")
            return

        # B. Check for existing Persona (The Fork)
        author = metadata.get("author", "Unknown")
        norm = normalize_author_name(author)
        slug = slugify(norm)
        
        personas = {}
        if os.path.exists(PERSONAS_PATH):
            with open(PERSONAS_PATH, 'r', encoding='utf-8') as f:
                personas = json.load(f)
        elif os.path.exists(OLD_PERSONAS_PATH):
             with open(OLD_PERSONAS_PATH, 'r', encoding='utf-8') as f:
                personas = json.load(f)
        
        system_prompt = None
        
        if norm in personas:
            print(f"   👤 Existing persona found: {personas[norm].get('name')}")
            # Use existing prompt
            system_prompt = personas[norm].get("prompt")
        else:
            print(f"   🆕 New persona detected: {author}")
            # Create a placeholder prompt or leave empty
            system_prompt = f"You are {author}. Answer as you would in your writings."

        # C. Create/Update CODEX (The Merge)
        # We need to structure the entry for 'emit_codex_for_author'
        entry = {
            "metadata": metadata,
            "raw_path": filepath,
            "curated_path": curated_path
        }
        
        # NOTE: existing logic in 'auto_curator_v3.main' aggregates ALL files for an author.
        # Here we are handling ONE file. We should probably load the existing CODEX manifest 
        # to preserve history, but 'emit_codex_for_author' does load existing manifest 
        # and appends/upserts. So valid.
        
        print(f"   📦 Packaging into {slug}.codex...")
        emit_codex_for_author(author, slug, [entry], system_prompt=system_prompt)
        print("   ✅ Ingest complete.")


if __name__ == "__main__":
    observer = Observer()
    event_handler = HybridIngestHandler()
    
    print(f"🔭 Watcher Service v1.0")
    print(f"   Watching {RAW_DIR}")
    print(f"   Watching {CODEX_DIR}")
    
    observer.schedule(event_handler, RAW_DIR, recursive=False)
    observer.schedule(event_handler, CODEX_DIR, recursive=False)
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
