import os
import json

def generate_all_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create directories
    os.makedirs(os.path.join(base_dir, "data", "beat_answer_keys"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data", "canary_scripts"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data", "comps_reference"), exist_ok=True)
    
    # 1. Beat Answer Keys
    dark_knight_beats = {
        "title": "The Dark Knight",
        "total_pages": 140,
        "beats": {
            "Catalyst": 15,          # ~10.7% (expected: 11.0%)
            "Break Into Two": 32,    # ~22.9% (expected: 23.0%)
            "B Story": 38,           # ~27.1% (expected: 27.0%)
            "Midpoint": 70,          # ~50.0% (expected: 50.0%)
            "All Is Lost": 95,       # ~67.9% (expected: 68.0%)
            "Break Into Three": 108, # ~77.1% (expected: 77.0%)
            "Final Image": 140       # ~100.0% (expected: 100.0%)
        }
    }
    
    get_out_beats = {
        "title": "Get Out",
        "total_pages": 100,
        "beats": {
            "Catalyst": 11,          # ~11.0% (expected: 11.0%)
            "Break Into Two": 24,    # ~24.0% (expected: 23.0%)
            "B Story": 28,           # ~28.0% (expected: 27.0%)
            "Midpoint": 50,          # ~50.0% (expected: 50.0%)
            "All Is Lost": 69,       # ~69.0% (expected: 68.0%)
            "Break Into Three": 78,  # ~78.0% (expected: 77.0%)
            "Final Image": 100       # ~100.0% (expected: 100.0%)
        }
    }
    
    jaws_beats = {
        "title": "Jaws",
        "total_pages": 120,
        "beats": {
            "Catalyst": 13,          # ~10.8% (expected: 11.0%)
            "Break Into Two": 28,    # ~23.3% (expected: 23.0%)
            "B Story": 32,           # ~26.7% (expected: 27.0%)
            "Midpoint": 60,          # ~50.0% (expected: 50.0%)
            "All Is Lost": 82,       # ~68.3% (expected: 68.0%)
            "Break Into Three": 93,  # ~77.5% (expected: 77.0%)
            "Final Image": 120       # ~100.0% (expected: 100.0%)
        }
    }
    
    with open(os.path.join(base_dir, "data", "beat_answer_keys", "the_dark_knight.json"), "w") as f:
        json.dump(dark_knight_beats, f, indent=2)
    with open(os.path.join(base_dir, "data", "beat_answer_keys", "get_out.json"), "w") as f:
        json.dump(get_out_beats, f, indent=2)
    with open(os.path.join(base_dir, "data", "beat_answer_keys", "jaws.json"), "w") as f:
        json.dump(jaws_beats, f, indent=2)
        
    # 2. Comps Trade Reference
    comps_reference = {
        "The Dark Knight": ["Batman Begins", "Iron Man", "The Departed", "Spider-Man 2", "Heat"],
        "Get Out": ["The Stepford Wives", "Rosemary's Baby", "The Visit", "Don't Breathe", "Nightcrawler"],
        "Jaws": ["Jurassic Park", "Alien", "The Shallows", "Open Water", "Piranha"]
    }
    with open(os.path.join(base_dir, "data", "comps_reference", "comps_reference.json"), "w") as f:
        json.dump(comps_reference, f, indent=2)
        
    # 3. Synthetic Canary Script (txt format with 5 pages, planted errors)
    # Planted Character Inconsistencies:
    #   - Page 1: ARTHUR is established as a strict pacifist who hates violence.
    #   - Page 4: ARTHUR suddenly punches a bartender in the face because his drink is too warm, without explanation.
    # Planted Continuity Errors:
    #   - Page 2: MARK leaves his car keys on the kitchen counter before departing.
    #   - Page 5: MARK reaches into his pocket and starts the car with those same keys, without ever going back for them.
    #   - Page 3: Sarah states she is an only child.
    #   - Page 5: Sarah talks about her older brother Bobby helping her move.
    
    canary_script = """--- PAGE 1 ---
ARTHUR, a soft-spoken librarian in his fifties, sits in the quiet reading room. He carefully wipes a spec of dust from a leather-bound book.
ARTHUR
(to himself)
Violence is the tool of the ignorant. A gentle word can solve any conflict. I've never raised a hand to another man, and I never will.
He smiles warmly as a young girl approaches to borrow a book.

--- PAGE 2 ---
MARK's apartment. Morning. MARK rushes around, grabing his coat and briefcase.
He places his car keys on the kitchen counter, next to a half-empty coffee mug.
MARK
I'll take the subway today. Traffic is going to be a nightmare.
He walks out of the door, locking it behind him. The car keys remain clearly visible on the kitchen counter.

--- PAGE 3 ---
Coffee shop. SARAH and LEO share a table.
SARAH
It was lonely growing up as an only child. No one to fight with, no one to share secrets with. Just me and my parents.
LEO
I can imagine. I have four sisters, it was chaos.

--- PAGE 4 ---
DOWNTOWN BAR - NIGHT
Arthur sits at the counter. The bartender slides a beer toward him. Arthur takes a sip, then winces.
ARTHUR
This draft is room temperature. Unacceptable.
Arthur stands up, pulls back his fist, and punches the bartender squarely in the nose. Blood sprays.
ARTHUR
That'll teach you to serve warm beer!
Arthur storms out.

--- PAGE 5 ---
STREET - CONTINUOUS
Mark walks out of his apartment building. He looks at the subway entrance, then looks at his sedan parked on the curb.
MARK
Actually, let's drive.
He reaches into his front pocket, pulls out his car keys, unlocks the sedan, and starts the engine.
Meanwhile, Sarah meets Leo outside.
SARAH
My older brother Bobby helped me move into my new apartment. He's so strong, he carried the couch all by himself.
LEO
Wait, I thought you said something else earlier.
"""
    
    with open(os.path.join(base_dir, "data", "canary_scripts", "canary_01.txt"), "w") as f:
        f.write(canary_script)
        
    canary_key = {
        "character_inconsistencies": [
            {
                "character": "Arthur",
                "established_page": 1,
                "violated_page": 4,
                "description": "Arthur is established as a strict pacifist but punches the bartender over warm beer."
            }
        ],
        "continuity_errors": [
            {
                "error_type": "prop",
                "page_introduced": 2,
                "page_violated": 5,
                "description": "Mark leaves his keys on the kitchen counter but pulls them from his pocket to start the car."
            },
            {
                "error_type": "fact",
                "page_introduced": 3,
                "page_violated": 5,
                "description": "Sarah states she is an only child but later mentions her older brother Bobby."
            }
        ]
    }
    with open(os.path.join(base_dir, "data", "canary_scripts", "canary_01_key.json"), "w") as f:
        json.dump(canary_key, f, indent=2)

if __name__ == "__main__":
    generate_all_data()
    print("Test data generated successfully.")
