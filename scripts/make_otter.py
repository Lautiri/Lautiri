"""One-off: builds assets/otter_cycle.json from otterminal's mascot frames (the work cycle shown on the card).

    python scripts/make_otter.py <otterminal>/frontend/dist/assets/mascot

Each state keeps a continuous 3 s stretch of the original 20 fps clip, sampled every other frame, so the
otter moves at real speed at 10 fps while the card stays light.
"""
import json
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "assets/otter_cycle.json"
PER_STATE = 30
STATES = [
    ("PLANNING", "armando el plan"),
    ("CODING", "programando"),
    ("TESTING", "corriendo los tests"),
    ("GITHUB", "git push"),
    ("SUCCESS", "todo en verde"),
]

states = []
for name, label in STATES:
    raw = json.loads((SRC / f"otter_{name.lower()}_frames.json").read_text())
    stride = 2 if len(raw) >= PER_STATE * 2 else max(1, len(raw) // PER_STATE)
    picked = raw[::stride][:PER_STATE]
    frames = [[line.rstrip() for line in f.split("\n")[1:48]] for f in picked]
    states.append({"name": name, "label": label, "frames": frames})
    print(name, len(raw), "->", len(frames))
OUT.write_text(json.dumps({"cols": 120, "rows": 47, "fps": 10, "states": states}, separators=(",", ":")))
print(OUT, OUT.stat().st_size)
