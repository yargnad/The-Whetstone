import os
import glob
import re
import shutil
import subprocess
import time
import ollama
import urllib.request
import urllib.error

# Configuration for the EVO-X2 Rig
MODEL_NAME = "deepseek-r1:8b" # Or your specific high-res model alias
# Resolve library paths relative to this script for robustness
BASE_DIR = os.path.dirname(__file__)
LIBRARY_DIR = os.path.abspath(os.path.join(BASE_DIR, "../philosophy_library"))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../philosophy_library/curated"))
SCAN_HEAD_SIZE = 30000  # Characters to scan at start for Intro
SCAN_TAIL_SIZE = 10000  # Characters to scan at end for Index/Footnotes

def get_true_start_phrase(text_chunk, author):
    """
    Asks the 235B model to identify the first sentence of the actual work.
    """
    prompt = f"""
    You are an expert archivist. 
    Analyze the following text sample from a file containing works by {author}.
    The file contains metadata, introductions by other scholars, prefaces, and then the actual work.
    
    Your Goal: Identify the EXACT phrase (approx 10-20 words) where {author}'s actual writing begins.
    Ignore "Introduction", "Preface" (unless by the author), "Contents", or Project Gutenberg headers.
    
    Return ONLY the exact phrase found in the text. Do not add commentary.
    
    TEXT SAMPLE:
    {text_chunk}
    """
    
    def _extract_content(response):
        content = None
        if isinstance(response, dict):
            content = response.get('message', {}).get('content') or response.get('content')
            if not content:
                choices = response.get('choices')
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict):
                        content = first.get('message', {}).get('content') or first.get('text') or first.get('content')
        else:
            content = getattr(response, 'content', None)
        if content is None:
            content = str(response)
        return content

    def ensure_ollama_running(timeout=15, poll_interval=1):
        # Quick check: if ollama CLI not present, can't start
        cli = shutil.which('ollama')
        if not cli:
            print("   ⚠️ 'ollama' CLI not found in PATH; cannot auto-start Ollama.")
            return False

        # Helper to check HTTP models endpoint (doesn't load heavy models)
        host = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')
        models_url = host.rstrip('/') + '/v1/models'

        def _models_endpoint_ok():
            try:
                req = urllib.request.Request(models_url, method='GET')
                with urllib.request.urlopen(req, timeout=1) as resp:
                    return resp.status == 200
            except Exception:
                return False

        # If already responsive, we're done
        if _models_endpoint_ok():
            return True

        # Try to start common daemon commands until one succeeds
        candidates = [
            [cli, 'daemon'],
            [cli, 'serve'],
            [cli, 'start']
        ]

        for cmd in candidates:
            try:
                print(f"   - Attempting to start Ollama with: {' '.join(cmd)}")
                # Start detached process
                creationflags = 0
                try:
                    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                except AttributeError:
                    creationflags = 0

                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=creationflags)
                # Poll until models endpoint responsive or timeout
                deadline = time.time() + timeout
                while time.time() < deadline:
                    if _models_endpoint_ok():
                        return True
                    time.sleep(poll_interval)
            except Exception as e:
                print(f"   ⚠️ Failed to launch with {' '.join(cmd)}: {e}")

        return False

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}],
            options={"temperature": 0.1} # Strict adherence
        )
    except Exception as e:
        # If connection-related, attempt to start Ollama and retry once
        msg = str(e)
        print(f"❌ AI Error: {e}")
        if 'Failed to connect' in msg or 'Connection' in msg or 'connect' in msg:
            started = ensure_ollama_running()
            if started:
                try:
                    response = ollama.chat(
                        model=MODEL_NAME,
                        messages=[{'role': 'user', 'content': prompt}],
                        options={"temperature": 0.1}
                    )
                except Exception as e2:
                    print(f"❌ AI Error after attempting to start Ollama: {e2}")
                    return None, None
            else:
                return None, None
        else:
            return None, None

    content = _extract_content(response)
    first_line = next((ln for ln in content.splitlines() if ln.strip()), "").strip()
    first_line = first_line.strip('"\u201c\u201d\u2018\u2019')
    return first_line, content

def process_book(filepath):
    filename = os.path.basename(filepath)
    print(f"\n📘 Processing: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 1. Basic Gutenberg Scrub (Low hanging fruit)
    # (Regex logic similar to previous discussions)
    # ...

    # 2. AI Semantic Detection
    # Guess author from filename (e.g. "nietzsche_Thus Spoke...")
    author = filename.split('_')[0].capitalize()

    print("   - Asking AI to find the true start...")
    head_sample = raw_text[:SCAN_HEAD_SIZE]
    start_phrase, raw_ai = get_true_start_phrase(head_sample, author)

    final_text = raw_text

    def _normalize_quotes(s: str) -> str:
        return s.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")

    if start_phrase:
        # Try a direct find first (fast and exact)
        direct_index = raw_text.find(start_phrase)
        if direct_index != -1:
            print(f"   ✅ Found start at index {direct_index}: '{start_phrase[:30]}...'")
            final_text = raw_text[:direct_index] + "\n<<<CONTENT_START>>>\n" + raw_text[direct_index:]
        else:
            # Fallback: try a tolerant regex search using the first several words
            normalized_phrase = _normalize_quotes(start_phrase).strip()
            words = re.findall(r"\w+", normalized_phrase)
            if len(words) == 0:
                print("   ⚠️ AI returned an empty or non-word start phrase.")
            else:
                max_words = min(len(words), 12)
                pattern = r"\b" + r"\s+".join(re.escape(w) for w in words[:max_words]) + r"\b"
                m = re.search(pattern, _normalize_quotes(raw_text), flags=re.IGNORECASE | re.DOTALL)
                if m:
                    start_index = m.start()
                    print(f"   ✅ Fuzzy matched start at index {start_index}: '{raw_text[start_index:start_index+60]}...'")
                    final_text = raw_text[:start_index] + "\n<<<CONTENT_START>>>\n" + raw_text[start_index:]
                else:
                    print(f"   ⚠️ AI proposed phrase not found in raw text. Phrase repr: {repr(start_phrase)}")
                    # Write debug file for inspection
                    try:
                        debug_path = os.path.join(OUTPUT_DIR, filename + ".ai_debug.txt")
                        os.makedirs(OUTPUT_DIR, exist_ok=True)
                        with open(debug_path, 'w', encoding='utf-8') as dbg:
                            dbg.write("-- AI raw response --\n")
                            dbg.write((raw_ai or "<none>") + "\n\n")
                            dbg.write("-- Proposed phrase --\n")
                            dbg.write(repr(start_phrase) + "\n\n")
                            dbg.write("-- Head sample (truncated) --\n")
                            dbg.write(head_sample[:2000])
                        print(f"   🐞 Wrote debug dump to {debug_path}")
                    except Exception as e:
                        print(f"   ⚠️ Could not write debug file: {e}")
    else:
        print("   ⚠️ AI could not determine start.")

    # 3. Save to Curated Folder
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    print(f"   💾 Saved to {out_path}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    files = glob.glob(os.path.join(LIBRARY_DIR, "*.txt"))
    for f in files:
        if "curated" not in f:
            process_book(f)

if __name__ == "__main__":
    main()