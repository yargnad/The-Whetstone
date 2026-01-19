import json
import os
import re
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PERSONAS_PATH = PROJECT_DIR / "philosophy_library" / "personas.json"
OUTPUT_DIR = PROJECT_DIR / "codex_library" / "philosophy"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug.lower() or "persona"


def build_manifest(entry: dict) -> dict:
    name = entry.get("name", "Unknown")
    prompt = entry.get("prompt", "")
    library_filter = entry.get("library_filter", []) or []

    return {
        "format": "codex",
        "codex_version": "2.0",
        "meta": {
            "name": name,
            "author": name,
            "category": "philosophy",
            "description": (prompt[:200] + "…") if len(prompt) > 200 else prompt,
            "library_filter": library_filter,
        },
        "work": {
            "title": name,
            "author": name,
            "language": "en",
            "subjects": [],
        },
        "bootstrap_instructions": prompt,
        "instructions": {
            "system_prompt_hint": "Legacy persona imported from personas.json",
            "usage": "Direct chat persona",
        },
        "source": {
            "type": "legacy_persona",
            "path": str(PERSONAS_PATH),
        },
    }


def write_codex(name: str, manifest: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(name)
    codex_path = OUTPUT_DIR / f"{slug}.codex"

    # Skip if already exists
    if codex_path.exists():
        print(f"[SKIP] {name} -> {codex_path.name} already exists")
        return codex_path

    with zipfile.ZipFile(codex_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("codex.json", json.dumps(manifest, ensure_ascii=True, indent=2))

    print(f"[OK] {name} -> {codex_path.relative_to(PROJECT_DIR)}")
    return codex_path


def main():
    if not PERSONAS_PATH.exists():
        raise FileNotFoundError(f"personas.json not found at {PERSONAS_PATH}")

    personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
    generated = 0
    for key, entry in personas.items():
        if key.lower() in {"example", "test", "placeholder"}:
            print(f"[SKIP] {entry.get('name', key)} (placeholder)")
            continue
        manifest = build_manifest(entry)
        write_codex(entry.get("name", key), manifest)
        generated += 1

    print(f"\nDone. Processed {generated} personas into {OUTPUT_DIR.relative_to(PROJECT_DIR)}")
    print("Reload personas in the UI to pick up new CODEX files.")


if __name__ == "__main__":
    main()
