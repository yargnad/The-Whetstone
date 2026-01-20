import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import PhilosopherCore

def test_names():
    print("Initializing Core...")
    core = PhilosopherCore()
    personas = core.get_valid_personas()
    
    print(f"\nFound {len(personas)} personas.")
    print("Sample Names:")
    
    # Check specific problematic ones
    targets = ["Shaw", "Russell", "Pascal"]
    found_full = []
    
    for p in personas:
        name = p['name']
        if "Shaw" in name or "Russell" in name or "Pascal" in name:
            print(f" - {name}")
            
test_names()
