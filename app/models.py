from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Segment:
    seq: int
    kind: str          # "dialog" 或 "narration"
    text: str
    emo_text: str
    start_idx: int = 0
    meta: Dict = field(default_factory=dict)
