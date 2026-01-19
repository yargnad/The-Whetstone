
import os
import glob
import json
import re
import sys
import zipfile
from datetime import datetime
from openai import OpenAI
from auto_curator_v3 import apply_exclusions


LIBRARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophy_library')
CURATED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'curated')
METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.metadata_v3')
PERSONAS_PATH = os.path.join(LIBRARY_PATH, 'personas.json')
CODEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codex_library', 'philosophy')

# Connect to Ollama server (OpenAI API compatible)
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Persona generation model can be independent of curation
PERSONA_MODEL = os.getenv("WHETSTONE_PERSONA_MODEL", os.getenv("WHETSTONE_MODEL", "cogito:8b"))


def normalize_author_name(name):
    """Normalize author names for merging (e.g., 'nietzsche', 'Friedrich Wilhelm Nietzsche')."""
    name = name.lower().replace('.', '').replace('-', ' ').replace('_', ' ').strip()
    # Remove common first names for merging (e.g., Friedrich, Wilhelm)
    tokens = [t for t in name.split() if t not in {"friedrich", "wilhelm", "george", "william", "joseph", "st", "saint"}]
    # Special case for 'nietzsche'
    if "nietzsche" in tokens:
        return "nietzsche"
    if "plato" in tokens:
        return "plato"
    if "epictetus" in tokens:
        return "epictetus"
    if "marcus" in tokens or "aurelius" in tokens:
        return "marcus aurelius"
    if "arnold" in tokens:
        return "arnold"
    if "stock" in tokens:
        return "stock"
    if "ken" in tokens and "tsugi" in tokens:
        return "ken tsugi"
    return " ".join(tokens)


def slugify(text):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug.lower() or "codex"


def bump_version(existing_version):
    try:
        parts = existing_version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            return ".".join(parts)
    except Exception:
        pass
    return "0.1.0"


def load_codex_manifest(slug):
    json_path = os.path.join(CODEX_PATH, f"{slug}.codex.json")
    zip_path = os.path.join(CODEX_PATH, f"{slug}.codex")

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                with zf.open('codex.json') as mf:
                    return json.loads(mf.read().decode('utf-8'))
        except Exception:
            return None
    return None


def write_codex_manifest(slug, manifest):
    json_path = os.path.join(CODEX_PATH, f"{slug}.codex.json")
    zip_path = os.path.join(CODEX_PATH, f"{slug}.codex")

    os.makedirs(CODEX_PATH, exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('codex.json', json.dumps(manifest, ensure_ascii=False, indent=2))


def extract_author(filename):
    # Try to extract author from filename: e.g. "nietzsche_Beyond Good and Evil by Friedrich Wilhelm Nietzsche.txt"
    base = os.path.splitext(filename)[0]
    match = re.search(r' by ([^_]+)', base, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if '_' in base:
        return base.split('_')[0].strip()
    if ' ' in base:
        return base.split(' ')[0].strip()
    return base.strip()



def load_clean_text(filename):
    """Load curated text if available; otherwise apply exclusions from metadata."""
    curated_file = os.path.join(CURATED_PATH, filename)
    metadata_file = os.path.join(METADATA_PATH, os.path.splitext(filename)[0] + ".metadata.json")
    raw_file = os.path.join(LIBRARY_PATH, filename)
    provenance_model = None

    try:
        if os.path.exists(curated_file):
            with open(curated_file, 'r', encoding='utf-8') as f:
                return f.read(), provenance_model

        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            provenance_model = metadata.get("model")
            exclusions = metadata.get("exclusions", [])
            clean_text = apply_exclusions(raw_text, exclusions)
            return clean_text, provenance_model

        return raw_text, provenance_model
    except Exception:
        return "", provenance_model


def load_text_from_codex(norm):
    """Return aggregated curated text and provenance from a CODEX if present."""
    slug = slugify(norm)
    manifest = load_codex_manifest(slug)
    if not manifest:
        return None, None

    curated = []
    provenance_model = None

    for src in manifest.get("sources", []):
        if src.get("type", "").startswith("text/plain"):
            content = src.get("content")
            if not content:
                continue
            if src.get("type") == "text/plain+curated":
                curated.append(content)
            elif src.get("curation", {}).get("exclusions"):
                curated.append(apply_exclusions(content, src["curation"]["exclusions"]))
            else:
                curated.append(content)
            if not provenance_model:
                provenance_model = src.get("curation", {}).get("model")

    if not curated:
        return None, provenance_model

    return "\n".join(curated), provenance_model


def sample_text_for_author(files, max_chars=1200, deep_scan=False, norm=None):
    """Use CODEX if available; otherwise sample curated text for the author."""

    if norm:
        codex_text, prov = load_text_from_codex(norm)
        if codex_text:
            return (codex_text if deep_scan else codex_text[:max_chars]), prov

    text = ""
    provenance_model = None
    for fname in files:
        content, model_used = load_clean_text(fname)
        if model_used:
            provenance_model = model_used
        match = re.search(r'---BEGIN AUTHOR TEXT---(.*?)---END AUTHOR TEXT---', content, re.DOTALL | re.IGNORECASE)
        if match:
            author_text = match.group(1).strip()
            text += author_text + "\n"
        else:
            text += content + "\n"
    # For deep scan, cap the total text length and sample from start, middle, and end for diversity
    if deep_scan:
        max_deep_chars = 5000  # Further reduced to help prevent LLM input truncation
        if len(text) <= max_deep_chars:
            return text, provenance_model
        # Sample: first 1/3, middle 1/3, last 1/3 (each ~max_deep_chars//3)
        chunk = max_deep_chars // 3
        first = text[:chunk]
        middle_start = max((len(text) // 2) - (chunk // 2), 0)
        middle = text[middle_start:middle_start + chunk]
        last = text[-chunk:]
        sampled = first + "\n...\n" + middle + "\n...\n" + last
        print(f"[INFO] Deep scan: sampled {len(sampled)} chars from {len(text)} total.")
        return sampled, provenance_model
    return text[:max_chars], provenance_model


def generate_meta_prompt(author, sample_text):
    """Two-step LLM: (1) summarize style/tone/philosophy, (2) generate persona prompt from summary."""
    # Step 1: Style summary (pass the sampled text, capped for deep scan)
    style_system = (
        f"You are an expert in philosophy and literary analysis.\n"
        f"Given the following sample text from {{author}}, write a detailed summary of the author's style, tone, and core philosophical ideas.\n"
        f"Do NOT copy or paraphrase the sample text. Focus on describing how the author writes, their voice, and their main philosophical themes."
    ).replace("{author}", author)
    style_user = f"Sample text from {author}:\n---\n{sample_text}\n---\nWrite only the summary:"
    style_summary = None
    for attempt in range(3):
        try:
            print(f"[INFO] Requesting style summary for {author} using {PERSONA_MODEL} (attempt {attempt+1}/3)...")
            response = client.chat.completions.create(
                model=PERSONA_MODEL,
                messages=[
                    {"role": "system", "content": style_system},
                    {"role": "user", "content": style_user}
                ],
                max_tokens=1200,  # Increased to allow much longer summaries
                temperature=0.7
            )
            style_summary = response.choices[0].message.content.strip()
            if style_summary and len(style_summary) > 40:
                if len(style_summary) > 1100:
                    print(f"[WARN] Style summary for {author} may be truncated (length: {len(style_summary)} chars, max_tokens=1200). Consider increasing max_tokens if needed.")
                break
        except Exception as e:
            print(f"[WARN] LLM style summary failed for {author}: {e}")
            break
    if not style_summary:
        return f"You are {author}, a philosopher. Answer as {author} would, using their style and core ideas."

    # Step 2: Persona prompt from summary (pass ONLY the summary, not the full text)
    prompt_system = (
        f"You are an expert in prompt engineering.\n"
        f"Given the following summary of an author's style, tone, and philosophy, write a concise persona prompt that instructs an AI assistant to always answer as if they are {author}, in the first person, never breaking character, and never referring to themselves as an AI, assistant, or simulation.\n"
        f"The persona prompt must make it clear: always respond as the author, in the first person, and never break character.\n"
        f"Do NOT copy or paraphrase the summary. The result must be a short, clear instruction for how to answer in the manner of {author}, not a sample, excerpt, or narrative.\n"
        f"Example persona prompt for Marcus Aurelius: 'Always respond in the first person as if you are Marcus Aurelius, using the style, tone, and philosophy found in Meditations. Never refer to yourself as an AI or assistant or speak in the third person.'\n"
        f"Example persona prompt for Nietzsche: 'Always answer as if you are Friedrich Nietzsche, in the first person, using your signature provocative and aphoristic style. Never break character or mention being an AI.'\n"
    )
    prompt_user = f"Summary of {author}'s style, tone, and philosophy:\n---\n{style_summary}\n---\nWrite only the persona prompt:"

    # Debug: print the full style summary being sent to the persona prompt step
    print(f"[DEBUG] Style summary for {author} being sent to persona prompt step (length: {len(style_summary)} chars):\n{style_summary}\n---")

    def is_meta_prompt(text):
        if text and text.strip():
            return True
        return False

    for attempt in range(3):
        try:
            print(f"[INFO] Requesting persona prompt for {author} using {PERSONA_MODEL} (attempt {attempt+1}/3)...")
            response = client.chat.completions.create(
                model=PERSONA_MODEL,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": prompt_user}
                ],
                max_tokens=1200,  # Increased to allow much longer persona prompts
                temperature=0.7
            )
            result = response.choices[0].message.content.strip()
            print(f"[DEBUG] Raw LLM output for {author}:\n{result}\n---")
            if len(result) > 1100:
                print(f"[WARN] Persona prompt for {author} may be truncated (length: {len(result)} chars, max_tokens=1200). Consider increasing max_tokens if needed.")
            if not result or len(result) < 40:
                print(f"[WARN] Persona prompt for {author} is suspiciously short (length: {len(result)}). Retrying...")
                continue
            if is_meta_prompt(result):
                return result
        except Exception as e:
            print(f"[WARN] LLM prompt generation failed for {author}: {e}")
            break
    print(f"[ERROR] Failed to generate a valid persona prompt for {author} after 3 attempts. Using fallback.")
    return f"You are {author}, a philosopher. Answer as {author} would, using their style and core ideas."


def update_codex_with_persona(norm, display_name, prompt, source_files, provenance_model):
    """Append persona prompt provenance into the author's CODEX if present."""
    slug = slugify(norm)
    manifest = load_codex_manifest(slug)
    if not manifest:
        return

    now = datetime.utcnow().isoformat() + "Z"
    meta = manifest.setdefault("meta", {})
    meta.setdefault("name", display_name)
    meta.setdefault("category", "philosophy")
    meta.setdefault("version", "0.1.0")
    meta["updated_at"] = now
    meta["version"] = bump_version(meta.get("version", "0.1.0"))
    manifest.setdefault("instructions", {})["system_prompt_hint"] = prompt

    prov = manifest.setdefault("provenance", {})
    persona_logic = prov.setdefault("persona_generation", {})
    persona_logic.update({
        "model": PERSONA_MODEL,
        "generated_at": now,
        "source_files": source_files,
        "curation_model": provenance_model,
    })

    manifest.setdefault("history", []).append({
        "version": meta.get("version"),
        "date": now,
        "action": "persona-update",
        "notes": "Persona prompt refreshed",
    })

    write_codex_manifest(slug, manifest)



def main():
    deep_scan = False
    if len(sys.argv) > 1 and sys.argv[1] in ["--deep", "--full", "-d"]:
        deep_scan = True
        print("[INFO] Deep scan enabled: using full text of all works for each author.")

    txt_files = glob.glob(os.path.join(LIBRARY_PATH, '*.txt'))
    author_files = {}
    author_display = {}
    for path in txt_files:
        filename = os.path.basename(path)
        author = extract_author(filename)
        norm = normalize_author_name(author)
        if norm not in author_files:
            author_files[norm] = []
            author_display[norm] = author  # Use first encountered display name
        author_files[norm].append(filename)

    # Load existing personas if present
    if os.path.exists(PERSONAS_PATH):
        with open(PERSONAS_PATH, 'r', encoding='utf-8') as f:
            personas = json.load(f)
    else:
        personas = {}

    # Add new/merged authors to personas config, using LLM for prompt
    updated = False
    for norm, files in author_files.items():
        display_name = author_display[norm]
        if norm not in personas:
            sample, provenance_model = sample_text_for_author(files, deep_scan=deep_scan, norm=norm)
            prompt = generate_meta_prompt(display_name, sample)
            personas[norm] = {
                "name": display_name,
                "prompt": prompt,
                "library_filter": [display_name],
                "built_with_model": PERSONA_MODEL,
                "provenance_model": provenance_model,
                "is_mod": False,
                "source_files": files
            }
            update_codex_with_persona(norm, display_name, prompt, files, provenance_model)
            print(f"Added persona for {display_name} (key: {norm}).")
            updated = True
        else:
            persona = personas[norm]
            if "built_with_model" not in persona:
                persona["built_with_model"] = PERSONA_MODEL
                updated = True
            if "provenance_model" not in persona:
                persona["provenance_model"] = None
                updated = True
            if "is_mod" not in persona:
                persona["is_mod"] = False
                updated = True
            if "source_files" not in persona:
                persona["source_files"] = files
                updated = True
            # Update CODEX with existing prompt if present
            if persona.get("prompt"):
                update_codex_with_persona(norm, display_name, persona["prompt"], files, persona.get("provenance_model"))

    if updated:
        with open(PERSONAS_PATH, 'w', encoding='utf-8') as f:
            json.dump(personas, f, indent=2, ensure_ascii=False)
        print(f"Updated personas.json with {len(personas)} authors.")
    else:
        print("No new authors found. personas.json is up to date.")

if __name__ == "__main__":
    main()
