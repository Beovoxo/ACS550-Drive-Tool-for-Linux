"""Local parameter-set storage. Values are user supplied, not drive defaults."""
import csv
import json
from pathlib import Path

FIELDS = ("number", "name", "value", "unit", "note")


def load_parameters(path: str):
    p = Path(path)
    if not p.exists():
        return []
    if p.suffix.lower() == ".csv":
        with p.open(newline="", encoding="utf-8-sig") as f:
            return [{k: row.get(k, "") for k in FIELDS} for row in csv.DictReader(f)]
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Parameter file must contain a list")
    return [{k: str(row.get(k, "")) for k in FIELDS} for row in data]


def save_parameters(path: str, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: str(row.get(k, "")) for k in FIELDS} for row in rows]
    if p.suffix.lower() == ".csv":
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(clean)
    else:
        p.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def compare_sets(left, right):
    a = {r.get("number", ""): r for r in left}
    b = {r.get("number", ""): r for r in right}
    changes = []
    for number in sorted(set(a) | set(b)):
        av, bv = a.get(number), b.get(number)
        if av is None or bv is None or av.get("value", "") != bv.get("value", ""):
            changes.append((number, av, bv))
    return changes
