
import os
import shutil
import glob
from watcher_service import HybridIngestHandler
from auto_curator_v3 import check_ollama_connection

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_LIB = os.path.join(BASE_DIR, "philosophy_library")
RAW_DIR = os.path.join(BASE_DIR, "raw")
CODEX_DIR = os.path.join(BASE_DIR, "codex_library", "philosophy")
OLD_PERSONAS = os.path.join(OLD_LIB, "personas.json")
NEW_PERSONAS = os.path.join(CODEX_DIR, "personas.json")

def migrate():
    print("🚀 Starting Library Migration...")

    if not check_ollama_connection():
        print("   🛑 Migration aborted due to missing AI server.")
        return
    
    # 1. Setup Directories
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)
        print(f"   Created {RAW_DIR}")
        
    if not os.path.exists(CODEX_DIR):
        os.makedirs(CODEX_DIR)
        print(f"   Created {CODEX_DIR}")

    # 2. Migrate Personas JSON
    if os.path.exists(OLD_PERSONAS):
        if not os.path.exists(NEW_PERSONAS):
            shutil.copy2(OLD_PERSONAS, NEW_PERSONAS)
            print(f"   ✅ Copied personas.json to {NEW_PERSONAS}")
        else:
            print(f"   ℹ️  personas.json already exists in {NEW_PERSONAS}, skipping copy.")
    else:
        print("   ⚠️  No personas.json found in old library.")

    # 3. Migrate and Process Text Files
    # 3. Move all remaining files to RAW_DIR
    txt_files_to_move = glob.glob(os.path.join(OLD_LIB, "*.txt"))
    print(f"   found {len(txt_files_to_move)} files waiting to move.")

    for src_path in txt_files_to_move:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(RAW_DIR, filename)
        if not os.path.exists(dest_path):
             shutil.copy2(src_path, dest_path)
             print(f"   Copied {filename} -> raw/")
        else:
             print(f"   {filename} already in raw/")

    # 4. Sweep RAW_DIR and Process Everything (Idempotent Repair)
    raw_files = glob.glob(os.path.join(RAW_DIR, "*.txt"))
    handler = HybridIngestHandler()
    
    print(f"   🚀 PROCESSING: Scanning {len(raw_files)} files in raw/...")
    
    for filepath in raw_files:
        filename = os.path.basename(filepath)
        print(f"   👉 Checking {filename}...")
        try:
            handler.handle_raw_text(filepath)
        except Exception as e:
            print(f"   ❌ Failed to ingest {filename}: {e}")

    print("\n🎉 Migration Complete.")
    print("   The system is now using the Hybrid Ingest workflow.")
    print(f"   Raw files are in: {RAW_DIR}")
    print(f"   CODEX files are in: {CODEX_DIR}")

if __name__ == "__main__":
    migrate()
