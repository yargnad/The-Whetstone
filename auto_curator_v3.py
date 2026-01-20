"""
Auto Curator v3.0 - Exclusion-Based Approach
Instead of finding start/end boundaries, we identify what to EXCLUDE.
Everything else is assumed to be author text.
"""
import os
import glob
import re
import json
import sys
import hashlib
import uuid
import zipfile
from datetime import datetime
from openai import OpenAI
from utils import is_ollama_running, launch_ollama_server

# Configuration
MODEL_NAME = os.getenv("WHETSTONE_MODEL", "qwen3:8b")

BASE_DIR = os.path.dirname(__file__)
LIBRARY_DIR = os.path.abspath(os.path.join(BASE_DIR, "."))
METADATA_DIR = os.path.abspath(os.path.join(BASE_DIR, ".metadata_v3"))
CURATED_DIR = os.path.abspath(os.path.join(BASE_DIR, "curated"))
CODEX_DIR = os.path.abspath(os.path.join(BASE_DIR, "codex_library", "philosophy"))

os.makedirs(METADATA_DIR, exist_ok=True)
os.makedirs(CURATED_DIR, exist_ok=True)
os.makedirs(CODEX_DIR, exist_ok=True)

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def check_ollama_connection():
    """Check if Ollama server is reachable, launching it if necessary."""
    print("   📡 Checking AI Server status...")
    
    if is_ollama_running():
        print("   ✅ AI Server is online.")
        return True
        
    print("   ⚠️ AI Server not running. Attempting to launch...")
    launch_ollama_server()
    
    if is_ollama_running():
        print("   ✅ AI Server launched successfully.")
        return True
    else:
        print("   ❌ AI Server failed to start.")
        return False

def char_to_line(text, char_idx):
    """Convert character index to line number."""
    return text[:char_idx].count('\n') + 1

def find_gutenberg_boundaries(raw_text):
    """Find Project Gutenberg header/footer for exclusion."""
    exclusions = []
    
    # Find header
    header_match = re.search(
        r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG EBOOK .*? \*\*\*",
        raw_text,
        re.IGNORECASE
    )
    
    if header_match:
        exclusions.append({
            "start_char": 0,
            "end_char": header_match.end(),
            "start_line": 1,
            "end_line": char_to_line(raw_text, header_match.end()),
            "reason": "Project Gutenberg header"
        })
    
    # Find footer
    footer_match = re.search(
        r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG EBOOK .*? \*\*\*",
        raw_text,
        re.IGNORECASE
    )
    
    if footer_match:
        exclusions.append({
            "start_char": footer_match.start(),
            "end_char": len(raw_text),
            "start_line": char_to_line(raw_text, footer_match.start()),
            "end_line": char_to_line(raw_text, len(raw_text)),
            "reason": "Project Gutenberg footer and license"
        })
    
    return exclusions

def find_structural_exclusions(raw_text):
    """Find obvious structural elements to exclude."""
    exclusions = []
    
    # Pattern 1: Dense footnote blocks
    # Look for sections with many consecutive [123] patterns
    lines = raw_text.split('\n')
    footnote_block_start = None
    footnote_count = 0
    
    for i, line in enumerate(lines):
        if re.match(r'^\s*\[\d+\]', line):
            if footnote_block_start is None:
                footnote_block_start = i
            footnote_count += 1
        else:
            # If we had a block of 5+ footnotes, mark it
            if footnote_count >= 5:
                start_char = sum(len(l) + 1 for l in lines[:footnote_block_start])
                end_char = sum(len(l) + 1 for l in lines[:i])
                
                exclusions.append({
                    "start_char": start_char,
                    "end_char": end_char,
                    "start_line": footnote_block_start + 1,
                    "end_line": i,
                    "reason": "Dense footnote block (auto-detected)"
                })
            
            footnote_block_start = None
            footnote_count = 0
    
    # Pattern 2: "NOTES" or "FOOTNOTES" sections
    notes_pattern = r'^\s*(NOTES|FOOTNOTES|ENDNOTES):?\s*$'
    for match in re.finditer(notes_pattern, raw_text, re.MULTILINE | re.IGNORECASE):
        # Find the end (usually runs to end of content or next major section)
        # For now, assume it runs to the Gutenberg footer
        start_char = match.start()
        
        # Look for next major section or end
        end_search = raw_text[start_char + 100:]  # Skip the "NOTES" line itself
        next_section = re.search(r'\n\n[A-Z][A-Z\s]{10,}\n', end_search)
        
        if next_section:
            end_char = start_char + 100 + next_section.start()
        else:
            # Runs to end (or will be caught by footer exclusion)
            end_char = len(raw_text)
        
        exclusions.append({
            "start_char": start_char,
            "end_char": end_char,
            "start_line": char_to_line(raw_text, start_char),
            "end_line": char_to_line(raw_text, end_char),
            "reason": f"Notes section starting with '{match.group()}'"
        })
    
    return exclusions

def find_meta_text_with_ai(raw_text, author):
    """Use AI to identify translator notes, editor comments, etc."""
    system_msg = "You are a text analysis tool. Identify NON-AUTHOR content in the text."
    
    prompt = f"""
Task: Find ALL sections that are NOT written by {author}.

FIND AND LIST (with exact start/end phrases):
1. "Translator's Note:" or "Translator's Preface"
2. "Editor's Note:" or "Editor's Introduction"  
3. "[Editor's comment in brackets]"
4. "Introduction by [someone other than {author}]"
5. Any section clearly marked as not by the author

For each found section, return in this format:
START: [exact first 10-20 words]
END: [exact last 10-20 words]
REASON: [why this should be excluded]
---

If nothing found, respond with: "NONE"

Text to analyze:
{raw_text[:8000]}
    """
    
    content = None
    retries = 3
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.1,
                extra_body={"options": {"num_ctx": 16384}}
            )
            content = response.choices[0].message.content.strip()
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            break # Success
        except Exception as e:
            print(f"   ⚠️ AI Error (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                print("   🔄 Attempting to reconnect to AI Server...")
                if check_ollama_connection():
                    print("   ✅ Server connection restored.")
                else:
                    print("   ❌ Server unavailable.")
                time.sleep(5)
            else:
               # Final attempt failed
               print("   ❌ AI Unresponsive. Resorting to BASIC curation (Regex only).")
               return [] # Resiliency: Return empty list to continue

    if not content or content.upper() == "NONE":
        return []
    
    # Parse the response
    # This is a simple parser - could be improved
    exclusions = []
    try:
        sections = content.split('---')
        
        for section in sections:
            if not section.strip():
                continue
            
            start_match = re.search(r'START:\s*(.+)', section, re.IGNORECASE)
            end_match = re.search(r'END:\s*(.+)', section, re.IGNORECASE)
            reason_match = re.search(r'REASON:\s*(.+)', section, re.IGNORECASE)
            
            if start_match and end_match:
                start_phrase = start_match.group(1).strip()
                end_phrase = end_match.group(1).strip()
                reason = reason_match.group(1).strip() if reason_match else "AI-detected meta-text"
                
                # Find these phrases in the text
                start_idx = raw_text.find(start_phrase)
                end_idx = raw_text.find(end_phrase)
                
                if start_idx != -1 and end_idx != -1:
                    exclusions.append({
                        "start_char": start_idx,
                        "end_char": end_idx + len(end_phrase),
                        "start_line": char_to_line(raw_text, start_idx),
                        "end_line": char_to_line(raw_text, end_idx + len(end_phrase)),
                        "reason": reason,
                        "start_phrase": start_phrase[:50],
                        "end_phrase": end_phrase[:50]
                    })
        
        return exclusions
    except Exception as e:
        print(f"   ⚠️ Error parsing AI response: {e}")
        return []


def sha256_of_path(path):
    """Compute sha256 hash of a file path."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_text(text):
    """Compute sha256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(text):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug.lower() or "codex"


def normalize_author_name(name):
    name = name.lower().replace('.', '').replace('-', ' ').replace('_', ' ').strip()
    # PRESERVE FULL NAME: Do not strip first names.
    # tokens = [t for t in name.split() if t not in {"friedrich", "wilhelm", "george", "william", "joseph", "st", "saint"}]
    tokens = name.split()
    
    if "nietzsche" in tokens:
        return "nietzsche"
    if "plato" in tokens:
        return "plato"
    if "epictetus" in tokens:
        return "epictetus"
    if "marcus" in tokens and "aurelius" in tokens:
        return "marcus-aurelius"
    if "ken" in tokens and "tsugi" in tokens:
        return "ken tsugi"
    
    return "-".join(tokens) or "unknown"


def load_existing_manifest(slug):
    """Load an existing CODEX manifest (.codex.json or zipped .codex)."""
    json_path = os.path.join(CODEX_DIR, f"{slug}.codex.json")
    zip_path = os.path.join(CODEX_DIR, f"{slug}.codex")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                with zf.open("codex.json") as manifest:
                    return json.loads(manifest.read().decode("utf-8"))
        except Exception:
            return None

    return None


def load_existing_assets(slug):
    """Load all files from an existing CODEX zip into an assets dict (excluding codex.json)."""
    zip_path = os.path.join(CODEX_DIR, f"{slug}.codex")
    assets = {}
    
    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    if name == "codex.json":
                        continue
                    # FILTER: Only load raw sources, skip legacy clean files
                    if "-clean-" in name:
                        continue
                        
                    with zf.open(name) as f:
                        assets[name] = f.read().decode("utf-8")
        except Exception as e:
            print(f"   ⚠️ Warning: Failed to load existing assets from {slug}.codex: {e}")
            
    return assets


def bump_version(existing_version):
    """Bump patch version of a semantic string like '0.1.0'."""
    try:
        parts = existing_version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            return ".".join(parts)
    except Exception:
        pass
    return "0.1.0"


def write_codex(slug, manifest, assets):
    """Write both lite JSON and dense .codex (zip) with embedded assets."""
    json_path = os.path.join(CODEX_DIR, f"{slug}.codex.json")
    zip_path = os.path.join(CODEX_DIR, f"{slug}.codex")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("codex.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for relpath, content in assets.items():
            zf.writestr(relpath, content)

    print(f"   📦 CODEX updated: {zip_path}")


def ensure_manifest_base(display_name, existing):
    """Create or update a manifest scaffold."""
    now = datetime.utcnow().isoformat() + "Z"
    if existing:
        manifest = existing
        meta = manifest.setdefault("meta", {})
        meta.setdefault("name", display_name)
        meta.setdefault("state", "dense")
        meta.setdefault("category", "philosophy")
        meta["updated_at"] = now
        if "version" in meta:
            meta["version"] = bump_version(meta.get("version", "0.1.0"))
        else:
            meta["version"] = "0.1.0"
        manifest.setdefault("spec_version", "0.1")
        manifest.setdefault("provenance", {})
        manifest.setdefault("sources", [])
        manifest.setdefault("layers", [])
        manifest.setdefault("history", [])
        return manifest

    return {
        "spec_version": "0.1",
        "uuid": str(uuid.uuid4()),
        "meta": {
            "name": display_name,
            "version": "0.1.0",
            "state": "dense",
            "category": "philosophy",
            "description": f"Curation artifacts for {display_name}",
            "created_at": now,
            "updated_at": now,
        },
        "provenance": {
            "tool": "auto_curator_v3",
            "tool_version": "3.0",
        },
        "sources": [],
        "layers": [],
        "history": [],
    }


def upsert_source(manifest, source):
    """Insert or replace a source entry keyed by uri + type."""
    key = (source.get("uri"), source.get("type"), source.get("id"))
    existing = manifest.get("sources", [])
    for idx, s in enumerate(existing):
        if (s.get("uri"), s.get("type"), s.get("id")) == key:
            existing[idx] = source
            return
    existing.append(source)
    manifest["sources"] = existing


def emit_codex_for_author(display_name, slug, entries, system_prompt=None):
    """Build and write a CODEX manifest for an author from curated entries."""
    existing = load_existing_manifest(slug)
    manifest = ensure_manifest_base(display_name, existing)

    # FILTER: Remove legacy "curated" sources from manifest
    if "sources" in manifest:
        manifest["sources"] = [
            s for s in manifest["sources"] 
            if "clean" not in s.get("id", "") and "curated" not in s.get("type", "")
        ]

    # Inject system prompt if provided
    if system_prompt:
        manifest.setdefault("instructions", {})["system_prompt_hint"] = system_prompt

    # Inject Curation Recipes (Auditability)
    manifest["recipes"] = [
        {
            "id": "gutenberg-regex-v1",
            "type": "regex",
            "description": "Standard Project Gutenberg header/footer removal",
            "active": True
        },
        {
            "id": "structure-cleaner-v1",
            "type": "heuristic",
            "description": "Removal of dense footnote blocks and endnotes",
            "active": True
        },
        {
            "id": "ai-meta-filter-v1",
            "type": "ai-filter",
            "description": "LLM-based detection of translator notes and introductions",
            "model": MODEL_NAME,
            "active": True
        }
    ]

    # Load existing assets to preserve previous books
    assets = load_existing_assets(slug)
    now = datetime.utcnow().isoformat() + "Z"

    for idx, entry in enumerate(entries, 1):
        metadata = entry["metadata"]
        raw_path = entry["raw_path"]
        curated_path = entry["curated_path"]

        # Load content
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        with open(curated_path, "r", encoding="utf-8") as f:
            curated_text = f.read()

        raw_hash = sha256_of_text(raw_text)

        # Raw source entry
        raw_id = f"{slug}-raw-{idx}"
        raw_source = {
            "id": raw_id,
            "uri": f"sources/{raw_id}.txt",
            "type": "text/plain",
            "hash": f"sha256:{raw_hash}",
            "size_bytes": len(raw_text.encode("utf-8")),
            "encoding": "utf-8",
            "curation": {
                "exclusions": metadata.get("exclusions", []),
                "model": metadata.get("model"),
                "notes": metadata.get("notes"),
            },
            "title": metadata.get("title"),
            "author": metadata.get("author"),
        }

        upsert_source(manifest, raw_source)

        # Bundle assets into the dense zip
        assets[f"sources/{raw_id}.txt"] = raw_text

    manifest.setdefault("history", []).append({
        "version": manifest.get("meta", {}).get("version"),
        "date": now,
        "action": "curation-update",
        "notes": f"Updated with {len(entries)} source file(s)",
    })

    write_codex(slug, manifest, assets)

def merge_overlapping_exclusions(exclusions):
    """Merge overlapping or adjacent exclusion ranges."""
    if not exclusions:
        return []
    
    # Sort by start position
    sorted_excl = sorted(exclusions, key=lambda x: x['start_char'])
    
    merged = [sorted_excl[0]]
    
    for current in sorted_excl[1:]:
        last = merged[-1]
        
        # If current overlaps or is adjacent to last, merge
        if current['start_char'] <= last['end_char']:
            # Extend the last exclusion
            last['end_char'] = max(last['end_char'], current['end_char'])
            last['end_line'] = max(last['end_line'], current['end_line'])
            
            # Combine reasons
            if current['reason'] not in last['reason']:
                last['reason'] = f"{last['reason']} + {current['reason']}"
        else:
            merged.append(current)
    
    return merged

def apply_exclusions(raw_text, exclusions):
    """Return cleaned text with exclusion ranges removed."""
    if not exclusions:
        return raw_text

    cleaned = []
    cursor = 0

    for excl in sorted(exclusions, key=lambda e: e['start_char']):
        start = excl['start_char']
        end = excl['end_char']
        if start > cursor:
            cleaned.append(raw_text[cursor:start])
        cursor = max(cursor, end)

    if cursor < len(raw_text):
        cleaned.append(raw_text[cursor:])

    return ''.join(cleaned)

def process_book(filepath):
    """Process a book using exclusion-based approach and emit clean text."""
    filename = os.path.basename(filepath)
    metadata_filename = os.path.splitext(filename)[0] + ".metadata.json"
    metadata_path = os.path.join(METADATA_DIR, metadata_filename)
    curated_path = os.path.join(CURATED_DIR, filename)
    
    # Check if already processed
    metadata = None
    if os.path.exists(metadata_path):
        print(f"\n📘 {filename}")
        print(f"   ✅ Metadata already exists (v3), reusing")
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception:
            print("   ⚠️ Metadata file corrupted, re-processing.")
            metadata = None

    if metadata is None:
        print(f"\n📘 Processing: {filename}")


        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        # Extract author from filename
        author = filename.split(' by ')[-1].replace('.txt', '') if ' by ' in filename else "Unknown"

        all_exclusions = []

        # Step 1: Gutenberg header/footer
        print("   🔍 Finding Gutenberg boundaries...")
        gutenberg_excl = find_gutenberg_boundaries(raw_text)
        all_exclusions.extend(gutenberg_excl)
        print(f"      Found {len(gutenberg_excl)} Gutenberg sections")

        # Step 2: Structural patterns (footnotes, notes sections)
        print("   🔍 Finding structural exclusions...")
        structural_excl = find_structural_exclusions(raw_text)
        all_exclusions.extend(structural_excl)
        print(f"      Found {len(structural_excl)} structural patterns")

        # Step 3: AI-detected meta-text
        print("   🤖 Using AI to find translator/editor notes...")
        ai_excl = find_meta_text_with_ai(raw_text, author)
        all_exclusions.extend(ai_excl)
        print(f"      Found {len(ai_excl)} AI-detected sections")

        # Merge overlapping exclusions
        print("   🔄 Merging overlapping exclusions...")
        merged_exclusions = merge_overlapping_exclusions(all_exclusions)
        print(f"      Final: {len(merged_exclusions)} exclusion ranges")

        # Create metadata
        metadata = {
            "filename": filename,
            "author": author,
            "title": os.path.splitext(filename)[0],
            "version": "3.0-exclusions",
            "total_chars": len(raw_text),
            "exclusions": merged_exclusions,
            "curated_by": "auto_curator v3.0 (exclusion-based)",
            "model": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "notes": "This uses exclusion-based curation. All text EXCEPT exclusions is author text."
        }

        # Calculate author text percentage
        excluded_chars = sum(e['end_char'] - e['start_char'] for e in merged_exclusions)
        author_chars = len(raw_text) - excluded_chars
        author_percentage = (author_chars / len(raw_text)) * 100 if len(raw_text) > 0 else 0

        metadata = {
            "filename": filename,
            "author": author,
            "title": os.path.splitext(filename)[0],
            "version": "3.0-exclusions",
            "total_chars": len(raw_text),
            "exclusions": merged_exclusions,
            "curated_by": "auto_curator v3.0 (exclusion-based)",
            "model": MODEL_NAME,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "notes": "This uses exclusion-based curation. All text EXCEPT exclusions is author text.",
            "stats": {
                "total_chars": len(raw_text),
                "excluded_chars": excluded_chars,
                "author_chars": author_chars,
                "author_percentage": round(author_percentage, 2)
            }
        }

        # Save metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"   💾 Saved to {metadata_path}")
        print(f"   📊 Author text: {author_percentage:.1f}% ({author_chars:,} chars)")
    
    # Always produce a clean text artifact from metadata
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        cleaned = apply_exclusions(raw_text, metadata.get('exclusions', []))
        with open(curated_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"   🧹 Clean text saved to {curated_path}")
    except Exception as e:
        print(f"   ⚠️ Failed to write clean text: {e}")

    metadata["curated_path"] = curated_path
    metadata["raw_path"] = filepath
    return metadata

def explode_codex(codex_path):
    """
    Hydrate a CODEX file: Extract raw text, apply exclusions, and write clean text to curated/.
    This is the "Explosion" or "Unpaxing" step in the CODEX Lifecycle.
    """
    print(f"💥 Exploding (Hydrating) {os.path.basename(codex_path)}...")
    
    try:
        with zipfile.ZipFile(codex_path, "r") as zf:
            # 1. Load Manifest
            with zf.open("codex.json") as f:
                manifest = json.loads(f.read().decode("utf-8"))
            
            # 2. Process Sources
            for source in manifest.get("sources", []):
                uri = source.get("uri")
                if not uri:
                    continue
                
                # Check if it's a raw source (we only care about hydrating raw sources)
                # In the new format, we only store raw sources.
                
                try:
                    # Read Raw Text from Zip
                    with zf.open(uri) as f:
                        raw_text = f.read().decode("utf-8")
                    
                    # Get Exclusions
                    exclusions = source.get("curation", {}).get("exclusions", [])
                    
                    # Apply Exclusions (The Recipe)
                    clean_text = apply_exclusions(raw_text, exclusions)
                    
                    # Determine Output Filename
                    # We try to reconstruct the original filename or use the title
                    title = source.get("title", "Unknown Title")
                    author = source.get("author", "Unknown Author")
                    # Sanitize filename
                    safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
                    safe_author = re.sub(r'[<>:"/\\|?*]', '', author)
                    out_filename = f"{safe_title} by {safe_author}.txt"
                    
                    out_path = os.path.join(CURATED_DIR, out_filename)
                    
                    # Write Clean Text
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(clean_text)
                        
                    print(f"   ✨ Hydrated: {out_filename}")
                    
                except KeyError:
                    print(f"   ⚠️ Could not find {uri} in archive.")
                except Exception as e:
                    print(f"   ⚠️ Failed to hydrate source {uri}: {e}")
                    
    except Exception as e:
        print(f"   ❌ Failed to explode {codex_path}: {e}")

def main():
    """Process all txt files or a specific file if provided."""
    args = sys.argv[1:]
    if args:
        txt_files = args
    else:
        txt_files = glob.glob(os.path.join(LIBRARY_DIR, "*.txt"))
    
    if not txt_files:
        print("No .txt files found.")
        return
    
    print(f"Found {len(txt_files)} text file(s).")
    print("="*60)
    
    processed = {}

    for filepath in txt_files:
        try:
            metadata = process_book(filepath)
            author = metadata.get("author", "Unknown")
            norm = normalize_author_name(author)
            processed.setdefault(norm, {"display": author, "items": []})
            processed[norm]["items"].append({
                "metadata": metadata,
                "raw_path": filepath,
                "curated_path": metadata.get("curated_path", os.path.join(CURATED_DIR, os.path.basename(filepath)))
            })
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Emit CODEX per author
    for norm, bundle in processed.items():
        display = bundle.get("display", norm)
        slug = slugify(norm)
        emit_codex_for_author(display, slug, bundle.get("items", []))

if __name__ == "__main__":
    if not check_ollama_connection():
        sys.exit(1)
    main()
