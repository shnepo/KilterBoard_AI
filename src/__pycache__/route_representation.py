from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math

@dataclass
class Hold:
    id: int
    x: float       # 0.0 to 1.0 (normalized width)
    y: float       # 0.0 to 1.0 (normalized height)
    orientation: float # 0 to 360 degrees (0 = Up) - simplified for this model
    size: float    # 0.0 (tiny crimp) to 1.0 (huge jug)

@dataclass
class Route:
    holds: List[int]                       # Sequence of hold IDs
    parent_id: Optional[str] = None        # To track lineage for fitness boosting
    
    # These are populated after linking to the dataset
    hold_objects: Dict[int, Hold] = field(default_factory=dict)
    
    @property
    def start_holds(self) -> List[int]:
        """First 2 holds are usually starts, or just the first one."""
        return self.holds[:2] if len(self.holds) >= 2 else self.holds[:1]

    @property
    def top_hold(self) -> Optional[int]:
        return self.holds[-1] if self.holds else None

    def get_coordinates(self) -> Dict[str, List[float]]:
        """Helper for plotting."""
        xs = [self.hold_objects[h].x for h in self.holds]
        ys = [self.hold_objects[h].y for h in self.holds]
        return {"x": xs, "y": ys}

def generate_kilter_board_layout() -> Dict[int, Hold]:
    """
    Generates a 12x12 staggered grid approximation of a Kilter Board.
    Rows are offset to create triangles.
    """
    holds = {}
    hold_id = 0
    rows = 12
    cols = 12
    
    for r in range(rows):
        # Kilter rows are staggered. 
        # Odd rows might be shifted right by 0.5 units
        x_offset = 0.5 if (r % 2 != 0) else 0.0
        
        for c in range(cols):
            # Normalize coordinates to 0-10 range for easier math, then scale down
            # y is straightforward (0 at bottom)
            # x is staggered
            
            x_pos = (c * 1.0) + x_offset
            y_pos = r * 1.0
            
            # Normalize to 0.0 - 1.0 relative to board size
            norm_x = x_pos / 12.0
            norm_y = y_pos / 12.0
            
            # Heuristic: Lower holds are bigger (feet), higher are crimpier
            # This is a simplification. Real board data is a static JSON.
            size_val = 1.0 if r < 3 else 0.4
            
            holds[hold_id] = Hold(
                id=hold_id,
                x=norm_x,
                y=norm_y,
                orientation=0, # Placeholder
                size=size_val
            )
            hold_id += 1
            
    return holds