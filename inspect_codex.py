import zipfile
import json
import sys
import os

def inspect(codex_path):
    print(f"📦 Inspecting {os.path.basename(codex_path)}")
    print("-" * 50)
    
    with zipfile.ZipFile(codex_path, 'r') as zf:
        # 1. List files
        print("📂 Files in Archive:")
        for name in zf.namelist():
            print(f"   - {name}")
            
        print("-" * 50)
        
        # 2. Print Manifest
        if "codex.json" in zf.namelist():
            print("📜 Manifest (codex.json):")
            with zf.open("codex.json") as f:
                data = json.load(f)
                # Print Sources specifically to check paths
                print(json.dumps(data.get("sources", []), indent=2))
        else:
            print("❌ No codex.json found!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect(sys.argv[1])
    else:
        print("Usage: python inspect_codex.py <path_to_codex>")
