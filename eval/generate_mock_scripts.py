import os

def generate_mock_scripts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "data", "canary_scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    # 1. The Dark Knight Mock Script (140 pages, beats at 15, 32, 38, 70, 95, 108, 140)
    dk_lines = []
    for p in range(1, 141):
        dk_lines.append(f"--- PAGE {p} ---")
        if p == 1:
            dk_lines.append("A bank heist in Gotham. Men in clown masks rob a mob bank.")
        elif p == 15:
            dk_lines.append("CATALYST BEAT: The Joker interrupts the mob bosses' meeting. He proposes to kill Batman for half their money.")
        elif p == 32:
            dk_lines.append("BREAK INTO TWO BEAT: Bruce Wayne decides to host a fundraiser for Harvey Dent, committing to Harvey as the hero Gotham needs so Bruce can step down.")
        elif p == 38:
            dk_lines.append("B STORY BEAT: Rachel and Harvey talk. Bruce looks on. The emotional core of the film centers on Rachel, Harvey, and Bruce's relationship.")
        elif p == 70:
            dk_lines.append("MIDPOINT BEAT: Batman captures the Joker in a high-speed chase. Jim Gordon is revealed to be alive. False victory as Joker is locked up.")
        elif p == 95:
            dk_lines.append("ALL IS LOST BEAT: Rachel is killed in the warehouse explosion. Harvey Dent is horribly burned. The Joker escapes. Bruce is in despair.")
        elif p == 108:
            dk_lines.append("BREAK INTO THREE BEAT: Batman decides to use the sonar machine to find Joker. Harvey Dent becomes Two-Face. The final confrontation begins.")
        elif p == 140:
            dk_lines.append("FINAL IMAGE BEAT: Batman runs into the night, taking the blame for Dent's crimes. The Dark Knight rises.")
        else:
            dk_lines.append(f"Scene on page {p}. Batman patrols Gotham. Gordon does police work.")
    
    with open(os.path.join(scripts_dir, "the_dark_knight.txt"), "w") as f:
        f.write("\n".join(dk_lines))

    # 2. Get Out Mock Script (100 pages, beats at 11, 24, 28, 50, 69, 78, 100)
    go_lines = []
    for p in range(1, 101):
        go_lines.append(f"--- PAGE {p} ---")
        if p == 1:
            go_lines.append("Chris packs his camera. Rose prepares to visit her parents.")
        elif p == 11:
            go_lines.append("CATALYST BEAT: They hit a deer on the highway. A police officer acts suspiciously. Incident disrupts their trip.")
        elif p == 24:
            go_lines.append("BREAK INTO TWO BEAT: Chris enters the Armitage house. He officially crosses the threshold into the strange estate.")
        elif p == 28:
            go_lines.append("B STORY BEAT: Missy Armitage offers to hypnotize Chris to cure his smoking. The psychological manipulation begins.")
        elif p == 50:
            go_lines.append("MIDPOINT BEAT: The party. Logan King, another black man, breaks character and screams 'GET OUT!' at Chris.")
        elif p == 69:
            go_lines.append("ALL IS LOST BEAT: Chris is strapped to a chair in the basement. He is hypnotized into the sunken place. He is helpless.")
        elif p == 78:
            go_lines.append("BREAK INTO THREE BEAT: Chris scratches cotton stuffing from the chair, plugs his ears, and escapes the hypnosis. He fights back.")
        elif p == 100:
            go_lines.append("FINAL IMAGE BEAT: Chris and Rod drive away. The burning house is behind them. Chris is free.")
        else:
            go_lines.append(f"Scene on page {p}. Chris notices the servants acting strange.")
            
    with open(os.path.join(scripts_dir, "get_out.txt"), "w") as f:
        f.write("\n".join(go_lines))

    # 3. Jaws Mock Script (120 pages, beats at 13, 28, 32, 60, 82, 93, 120)
    jaws_lines = []
    for p in range(1, 121):
        jaws_lines.append(f"--- PAGE {p} ---")
        if p == 1:
            jaws_lines.append("Chrissie swims in the ocean. She is pulled under by an unseen force.")
        elif p == 13:
            jaws_lines.append("CATALYST BEAT: A young boy, Alex Kintner, is killed by the shark in front of a crowded beach. The threat is public.")
        elif p == 28:
            jaws_lines.append("BREAK INTO TWO BEAT: Brody decides to hire Quint. Brody, Quint, and Hooper board the Orca to hunt the shark.")
        elif p == 32:
            jaws_lines.append("B STORY BEAT: Onboard the Orca, the men share stories, drink, and bond. The thematic arguments about nature and man develop.")
        elif p == 60:
            jaws_lines.append("MIDPOINT BEAT: They tie the barrel to the shark. The shark pulls the barrel down. A false sense of progress.")
        elif p == 82:
            jaws_lines.append("ALL IS LOST BEAT: The Orca's engine dies. Hooper goes down in the cage and is lost. The boat is sinking. Quint is eaten.")
        elif p == 93:
            jaws_lines.append("BREAK INTO THREE BEAT: Brody climbs the mast. He has the rifle and the oxygen tank. It's the final struggle.")
        elif p == 120:
            jaws_lines.append("FINAL IMAGE BEAT: Brody and Hooper paddle back to shore on the yellow barrels. They survive.")
        else:
            jaws_lines.append(f"Scene on page {p}. The town mayor refuses to close the beaches.")
            
    with open(os.path.join(scripts_dir, "jaws.txt"), "w") as f:
        f.write("\n".join(jaws_lines))

if __name__ == "__main__":
    generate_mock_scripts()
    print("Mock screenplay files generated successfully.")
