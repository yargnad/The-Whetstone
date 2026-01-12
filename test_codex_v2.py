"""Quick test of CODEX v2 spec"""
from codex_v2_spec import CodexV2, create_minimal_codex, upgrade_v1_to_v2, detect_version
import json

# Test 1: Create minimal CODEX
print("Test 1: Creating minimal CODEX...")
codex = create_minimal_codex("Marcus Aurelius", "You are Marcus Aurelius, speaking from Meditations.", "Marcus Aurelius")
print(f"✓ Created: {codex.metadata.name}")

# Test 2: Serialize to JSON
print("\nTest 2: Serializing to JSON...")
json_str = codex.to_json()
parsed = json.loads(json_str)
print(f"✓ Serialized {len(json_str)} bytes")
print(f"✓ Format: {parsed['format']}, Version: {parsed['version']}")

# Test 3: Deserialize from JSON
print("\nTest 3: Deserializing from JSON...")
codex2 = CodexV2.from_json(json_str)
print(f"✓ Deserialized: {codex2.metadata.name}")

# Test 4: v1 compatibility
print("\nTest 4: Testing v1 compatibility...")
v1_data = codex.to_v1()
print(f"✓ v1 format: {v1_data.keys()}")

# Test 5: Upgrade v1 to v2
print("\nTest 5: Upgrading v1 to v2...")
v1_sample = {
    "name": "Nietzsche",
    "prompt": "You are Friedrich Nietzsche...",
    "library_filter": ["Friedrich Wilhelm Nietzsche"],
    "description": "The philosopher of power"
}
version = detect_version(v1_sample)
print(f"✓ Detected version: {version}")
upgraded = upgrade_v1_to_v2(v1_sample)
print(f"✓ Upgraded to v{upgraded.version}")

print("\n✅ All tests passed!")
