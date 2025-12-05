import re
from typing import Dict, List

# Using the V-Scale and FB-Scale dictionaries implied by your previous code snippets
V_SCALE = {
    "V0": 0.05, "V1": 0.10, "V2": 0.15,
    "V3": 0.25, "V4": 0.35, "V5": 0.45,
    "V6": 0.55, "V7": 0.60, "V8": 0.70,
    "V9": 0.78, "V10": 0.85, "V11": 0.92,
    "V12": 0.96, "V13": 0.98, "V14": 1.00
}

FB_SCALE = {
    "5A": 0.10, "5B": 0.15, "5C": 0.20,
    "6A": 0.30, "6A+": 0.35,
    "6B": 0.40, "6B+": 0.45,
    "6C": 0.50, "6C+": 0.55,
    "7A": 0.60, "7A+": 0.65,
    "7B": 0.70, "7B+": 0.75,
    "7C": 0.80, "7C+": 0.85,
    "8A": 0.90, "8A+": 0.92,
    "8B": 0.94, "8B+": 0.96,
    "8C": 0.98, "8C+": 1.00
}

def parse_style(active_styles: List[str]) -> Dict:
    """
    Parses a list of active style keywords into style parameters for the GA.
    """
    
    # --- DEFAULT PARAMETERS ---
    params = {
        "avg_move_dist": 0.18,      # Normalized distance (default)
        "variance_penalty": 5.0,    # Penalty for move distance inconsistency
        "dynamic_weight": 0.0,      # Weight towards big moves
        "reach_min": 0.05,          # Minimum move length (normalized)
        "reach_max": 0.35,          # Maximum move length (normalized)
    }
    # --------------------------

    # Apply style modifications based on active keywords
    for style in active_styles:
        if style == "Dynamic":
            # Favors bigger, less consistent moves
            params["avg_move_dist"] = 0.25 
            params["variance_penalty"] = 2.0 
            params["dynamic_weight"] = 0.5
            params["reach_max"] = 0.45
            
        elif style == "Crimpy/Technical":
            # Favors smaller, more precise moves
            params["avg_move_dist"] = 0.12 
            params["variance_penalty"] = 7.0 
            params["reach_max"] = 0.25
            
        elif style == "Traverse/Endurance":
            # Favors consistent, medium-sized moves for endurance
            params["avg_move_dist"] = 0.15 
            
        elif style == "Sloper/Pinch":
            # Placeholder for future hold type preference (affects hold selection/scoring)
             params["avg_hold_size"] = 0.7 # Prefer larger holds (slopers/pinches often bigger)
             
    return params

def parse_difficulty(diff_input: str) -> float:
    """
    Convert a user difficulty input ('V4', '6B+', 'soft 7A') 
    into a normalized difficulty value.
    """

    text = diff_input.strip().upper()

    # Handle soft/hard modifiers
    soft = "SOFT" in text
    hard = "HARD" in text

    # Remove words
    text = text.replace("SOFT", "").replace("HARD", "").strip()

    # Detect V-scale
    v_match = re.match(r"V(\d+)", text)
    if v_match:
        grade = "V" + v_match.group(1)
        if grade in V_SCALE:
            base = V_SCALE[grade]
            if soft: base -= 0.03
            if hard: base += 0.03
            return max(0.0, min(1.0, base))

    # Detect Fontainebleau
    fb_grade = text
    if fb_grade in FB_SCALE:
        base = FB_SCALE[fb_grade]
        if soft: base -= 0.03
        if hard: base += 0.03
        return max(0.0, min(1.0, base))

    # Handle ranges (e.g., "V3-V5")
    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2:
            val1 = parse_difficulty(parts[0])
            val2 = parse_difficulty(parts[1])
            # Return the average of the range
            return (val1 + val2) / 2.0
            
    # Default to V5 equivalent if parsing fails
    return 0.45