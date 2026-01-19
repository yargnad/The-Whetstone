"""
Auto Curator File Watcher
Monitors the philosophy_library folder and automatically curates new .txt files.
"""
import os
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
LIBRARY_DIR = Path(__file__).parent
# Prefer the exclusion-based curator and emit CODEX artifacts for caching
CURATOR_SCRIPT = LIBRARY_DIR / "auto_curator_v3.py"
CODEX_SCRIPT = LIBRARY_DIR / "auto_curator_codex.py"
CURATED_DIR = LIBRARY_DIR / "curated"

class LibraryWatcher(FileSystemEventHandler):
    """Handles file system events in the library directory."""
    
    def __init__(self):
        self.processing = set()  # Track files currently being processed
        
    def on_created(self, event):
        """Triggered when a new file is created."""
        if event.is_directory:
            return
            
        filepath = Path(event.src_path)
        
        # Only process .txt files in the root library directory
        if filepath.suffix.lower() != '.txt':
            return
            
        if filepath.parent != LIBRARY_DIR:
            return  # Ignore files in subdirectories
            
        # Ignore curated directory
        if 'curated' in str(filepath):
            return
            
        print(f"\n📚 New file detected: {filepath.name}")
        self.process_file(filepath)
    
    def on_modified(self, event):
        """Triggered when a file is modified."""
        # Optional: You can enable this if you want to re-curate modified files
        pass
        
    def process_file(self, filepath):
        """Process a single file with the curator."""
        if filepath in self.processing:
            print(f"   ⏭️  Already processing {filepath.name}, skipping...")
            return
            
        try:
            self.processing.add(filepath)
            
            # Small delay to ensure file write is complete
            time.sleep(2)
            
                print(f"   🔄 Running auto_curator_v3 on {filepath.name}...")

                # 1) Exclusion-based curation (writes metadata + clean text)
                result = subprocess.run(
                    ['python', str(CURATOR_SCRIPT), str(filepath)],
                    cwd=str(LIBRARY_DIR),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per file
                )

                if result.returncode == 0:
                    print(f"   ✅ Successfully curated {filepath.name}")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"   ❌ Error curating {filepath.name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr}")

                # 2) Generate CODEX cache artifact (best-effort; keep going even if it fails)
                print(f"   📦 Creating CODEX cache for {filepath.name}...")
                codex_result = subprocess.run(
                    ['python', str(CODEX_SCRIPT), str(filepath)],
                    cwd=str(LIBRARY_DIR),
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if codex_result.returncode == 0:
                    print(f"   ✅ CODEX cached for {filepath.name}")
                    if codex_result.stdout:
                        print(codex_result.stdout)
                else:
                    print(f"   ⚠️  CODEX cache generation failed for {filepath.name}")
                    if codex_result.stderr:
                        print(f"   Error: {codex_result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print(f"   ⏱️  Timeout processing {filepath.name} (>5 minutes)")
        except Exception as e:
            print(f"   ❌ Exception processing {filepath.name}: {e}")
        finally:
            self.processing.remove(filepath)

def main():
    """Start the file watcher."""
    print("=" * 60)
    print("📖 Philosophy Library Auto-Curator Watcher")
    print("=" * 60)
    print(f"Monitoring: {LIBRARY_DIR}")
    print(f"Curator:    {CURATOR_SCRIPT}")
    print(f"Output:     {CURATED_DIR}")
    print("\nWaiting for new .txt files...")
    print("Press Ctrl+C to stop.\n")
    
    # Ensure the curated directory exists
    CURATED_DIR.mkdir(exist_ok=True)
    
    # Set up the observer
    event_handler = LibraryWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(LIBRARY_DIR), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping watcher...")
        observer.stop()
        observer.join()
        print("✅ Watcher stopped.")

if __name__ == "__main__":
    main()
